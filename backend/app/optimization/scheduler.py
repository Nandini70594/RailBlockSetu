from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from zoneinfo import ZoneInfo
import json
from ortools.sat.python import cp_model
from sqlalchemy.orm import Session

from app.config import settings
from app.models.request import MaintenanceRequest, RequestStatus
from app.models.schedule import MaintenanceBlock, BlockStatus, TrackType
from app.models.train import TrainSchedule
from app.models.disruption import Disruption
from app.models.audit import AuditLog
from app.optimization.readiness import readiness_validator
from app.optimization.train_windows import (
    build_train_intervals,
    has_train_free_gap,
)
from app.optimization.validator import refresh_schedule_validation

IST = ZoneInfo("Asia/Kolkata")

class BlockOptimizationScheduler:
    def __init__(self):
        pass

    def run_optimization(
        self,
        db: Session,
        horizon_hours: int = 72,
        pinned_block_ids: Optional[List[int]] = None,
        disruption: Optional[Disruption] = None
    ) -> Dict[str, Any]:
        """
        Google OR-Tools CP-SAT multi-objective maintenance block scheduler.
        Considers:
        - Track possession non-overlap
        - Limited machinery and staff crew capacities (Cumulative constraints)
        - Train corridor headway and peak exclusion
        - Task dependency graph
        - Preservation of pinned approved blocks
        """
        # Scheduler datetimes are naive IST wall times, matching HH:MM train times.
        now = datetime.now(IST).replace(tzinfo=None, minute=0, second=0, microsecond=0)
        base_time = now
        horizon_minutes = horizon_hours * 60
        
        # 1. Fetch eligible maintenance requests
        # Submitted, Validated, or already Optimized/Approved if replanning
        query = db.query(MaintenanceRequest).filter(
            MaintenanceRequest.current_status.in_([
                RequestStatus.SUBMITTED,
                RequestStatus.VALIDATED,
                RequestStatus.OPTIMIZED,
                RequestStatus.APPROVED
            ])
        )
        all_requests: List[MaintenanceRequest] = query.all()
        
        if not all_requests:
            refresh_schedule_validation(db)
            return {
                "status": "NO_REQUESTS",
                "message": "No maintenance requests found eligible for scheduling.",
                "blocks_scheduled": 0,
                "schedule": [],
                "unscheduled": [],
                "excluded": [],
                "train_intervals_checked": 0,
            }

        trains: List[TrainSchedule] = db.query(TrainSchedule).all()
        train_intervals = build_train_intervals(
            trains,
            base_time,
            horizon_minutes,
            settings.TRAIN_BUFFER_MINUTES,
        )

        schedulable_requests: List[MaintenanceRequest] = []
        readiness_by_request: Dict[int, Dict[str, Any]] = {}
        excluded: List[Dict[str, Any]] = []
        unscheduled: List[Dict[str, Any]] = []
        train_intervals_checked = 0
        for req in all_requests:
            section_trains = [
                interval for interval in train_intervals
                if interval.section_id == req.section_id
            ]
            train_intervals_checked += len(section_trains)
            readiness = readiness_validator.validate_request_readiness(
                req,
                db,
                base_time=base_time,
                horizon_minutes=horizon_minutes,
                train_intervals=train_intervals,
            )
            readiness_by_request[req.id] = readiness
            if readiness["verdict"] == "NOT_READY":
                excluded.append({
                    "request_id": req.id,
                    "task_title": req.task_title,
                    "failing_pillars": readiness["failing_pillars"],
                    "recommended_action": readiness["recommended_action"],
                    "readiness": readiness,
                })
                traffic = readiness["pillars"]["traffic_window"]
                if traffic["status"] == "FAILED":
                    duration_minutes = int(req.estimated_duration * 60)
                    unscheduled.append({
                        "request_id": req.id,
                        "task_title": req.task_title,
                        "reason": (
                            f"no train-free gap of {duration_minutes} minutes on "
                            f"section {req.railway_section or req.section_id} "
                            "within its deadline"
                        ),
                    })
                continue
            schedulable_requests.append(req)

        if not schedulable_requests:
            refresh_schedule_validation(db)
            return {
                "status": "NO_SCHEDULABLE_REQUESTS",
                "message": "All eligible requests failed mandatory readiness checks.",
                "solver_status_name": None,
                "wall_time_seconds": None,
                "objective_value": None,
                "blocks_scheduled": 0,
                "schedule": [],
                "unscheduled": unscheduled,
                "excluded": excluded,
                "train_intervals_checked": train_intervals_checked,
            }

        model = cp_model.CpModel()

        # 2. Map existing pinned blocks
        pinned_ids = set(pinned_block_ids or [])
        existing_blocks = db.query(MaintenanceBlock).filter(
            MaintenanceBlock.status == BlockStatus.APPROVED
        ).all()
        
        pinned_start_times = {}
        for b in existing_blocks:
            if b.id in pinned_ids or b.is_pinned:
                offset_mins = int((b.scheduled_start - base_time).total_seconds() / 60)
                if 0 <= offset_mins < horizon_minutes:
                    pinned_start_times[b.request_id] = offset_mins

        # 3. Model Decision Variables
        task_vars = {}
        task_info = {}
        soft_train_penalties = []
        section_intervals: Dict[int, List[Any]] = {}
        machine_intervals: Dict[str, List[Tuple[Any, int]]] = {}
        department_intervals: Dict[str, List[Tuple[Any, int]]] = {}

        for req in schedulable_requests:
            rid = req.id
            dur_mins = int(req.estimated_duration * 60)
            req_start_offset = max(
                0,
                int((req.required_start_date - base_time).total_seconds() // 60),
            )
            deadline_offset = min(
                horizon_minutes,
                int((req.deadline - base_time).total_seconds() // 60),
            )
            section_id = req.section_id or 1
            section_trains = [
                interval
                for interval in train_intervals
                if interval.section_id == section_id
            ]
            hard_train_intervals = [
                interval for interval in section_trains if interval.is_hard
            ]

            if (
                req_start_offset + dur_mins > deadline_offset
                or not has_train_free_gap(
                    req_start_offset,
                    deadline_offset,
                    dur_mins,
                    hard_train_intervals,
                )
            ):
                unscheduled.append({
                    "request_id": rid,
                    "task_title": req.task_title,
                    "reason": (
                        f"no train-free gap of {dur_mins} minutes on section "
                        f"{req.railway_section or section_id} within its deadline"
                    ),
                })
                continue

            # Decision variables for this task
            start_var = model.NewIntVar(req_start_offset, deadline_offset - dur_mins, f"start_{rid}")
            end_var = model.NewIntVar(req_start_offset + dur_mins, deadline_offset, f"end_{rid}")
            interval_var = model.NewIntervalVar(start_var, dur_mins, end_var, f"interval_{rid}")

            for train_index, train_interval in enumerate(section_trains):
                if train_interval.is_hard:
                    before_train = model.NewBoolVar(
                        f"task_{rid}_before_train_{train_index}"
                    )
                    after_train = model.NewBoolVar(
                        f"task_{rid}_after_train_{train_index}"
                    )
                    model.AddBoolOr([before_train, after_train])
                    model.Add(end_var <= train_interval.start_minute).OnlyEnforceIf(
                        before_train
                    )
                    model.Add(start_var >= train_interval.end_minute).OnlyEnforceIf(
                        after_train
                    )
                else:
                    before_train = model.NewBoolVar(
                        f"task_{rid}_before_soft_train_{train_index}"
                    )
                    after_train = model.NewBoolVar(
                        f"task_{rid}_after_soft_train_{train_index}"
                    )
                    overlaps_train = model.NewBoolVar(
                        f"task_{rid}_overlaps_soft_train_{train_index}"
                    )
                    model.AddBoolOr(
                        [before_train, after_train, overlaps_train]
                    )
                    model.Add(end_var <= train_interval.start_minute).OnlyEnforceIf(
                        before_train
                    )
                    model.Add(start_var >= train_interval.end_minute).OnlyEnforceIf(
                        after_train
                    )
                    model.Add(
                        end_var >= train_interval.start_minute + 1
                    ).OnlyEnforceIf(overlaps_train)
                    model.Add(
                        start_var <= train_interval.end_minute - 1
                    ).OnlyEnforceIf(overlaps_train)
                    soft_train_penalties.append(
                        overlaps_train * settings.TRAIN_SOFT_PENALTY_WEIGHT
                    )

            # Check if this task is affected by active disruption
            if disruption and req.section_id == disruption.section_id:
                disr_start = int((disruption.affected_from - base_time).total_seconds() / 60)
                disr_end = int((disruption.affected_until - base_time).total_seconds() / 60)
                if disr_end > 0 and disr_start < horizon_minutes:
                    # Task CANNOT be scheduled during disruption window on this section
                    disruption_interval = model.NewIntervalVar(
                        max(0, disr_start),
                        max(15, disr_end - disr_start),
                        max(disr_start + 15, disr_end),
                        f"disruption_{rid}"
                    )
                    model.AddNoOverlap([interval_var, disruption_interval])

            # If pinned, lock the start time!
            if rid in pinned_start_times:
                model.Add(start_var == pinned_start_times[rid])

            task_vars[rid] = {
                "start": start_var,
                "end": end_var,
                "interval": interval_var,
                "duration": dur_mins,
                "priority_score": req.ai_priority_score or 50.0,
                "urgency": req.urgency_level.value,
                "department": req.department,
                "section_id": section_id
            }
            task_info[rid] = req

            # Group for Section No-Overlap (Same track section cannot have multiple non-synergized maintenance)
            sec_id = req.section_id or 1
            if sec_id not in section_intervals:
                section_intervals[sec_id] = []
            section_intervals[sec_id].append(interval_var)

            # Machinery capacity tracking
            machines = []
            if req.required_machinery:
                try:
                    machines = json.loads(req.required_machinery) if isinstance(req.required_machinery, str) else req.required_machinery
                except Exception:
                    machines = [req.required_machinery]
            for m in machines:
                m_key = str(m).strip()
                if m_key not in machine_intervals:
                    machine_intervals[m_key] = []
                machine_intervals[m_key].append((interval_var, 1))

            # Department staff gang tracking
            dept = req.department
            if dept not in department_intervals:
                department_intervals[dept] = []
            staff_req = req.required_staff
            department_intervals[dept].append((interval_var, staff_req))

        # 4. Add Section Non-Overlap Constraints
        for sec_id, intervals in section_intervals.items():
            if len(intervals) > 1:
                model.AddNoOverlap(intervals)

        # 5. Add Cumulative Resource Constraints for Machinery
        for m_key, items in machine_intervals.items():
            if len(items) > 1:
                intervals = [it[0] for it in items]
                demands = [it[1] for it in items]
                # Default max capacity 1 for heavy machinery (e.g. 1 Tamping Machine per division corridor)
                model.AddCumulative(intervals, demands, 1)

        # 6. Add Cumulative Constraints for Gang Personnel
        dept_staff_caps = {"Engineering": 35, "TRD": 25, "S&T": 20}
        for dept, items in department_intervals.items():
            cap = dept_staff_caps.get(dept, 30)
            intervals = [it[0] for it in items]
            demands = [it[1] for it in items]
            model.AddCumulative(intervals, demands, cap)

        # 7. Add Dependencies (DAG order)
        for rid, req in task_info.items():
            if req.task_dependencies:
                deps = []
                try:
                    deps = json.loads(req.task_dependencies) if isinstance(req.task_dependencies, str) else req.task_dependencies
                except Exception:
                    deps = [req.task_dependencies]
                for dep_id in deps:
                    try:
                        dep_int = int(dep_id)
                        if dep_int in task_vars:
                            # 30-minute safety buffer between dependent maintenance steps
                            model.Add(task_vars[rid]["start"] >= task_vars[dep_int]["end"] + 30)
                    except Exception:
                        pass

        # 8. Multi-Objective Function Formulation
        # - Maximize early completion of high AI priority score tasks
        # - Encourage night shadow blocks (00:00 to 05:00) for high disruption work
        objective_terms = []
        for rid, tv in task_vars.items():
            weight = int(tv["priority_score"] * 10)
            # Higher priority = stronger pull toward earlier start
            objective_terms.append(tv["start"] * weight)
        objective_terms.extend(soft_train_penalties)

        model.Minimize(sum(objective_terms))

        # 9. Solve with CP-SAT
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = 8.0
        solver.parameters.num_workers = 2
        solver_status = solver.Solve(model)

        result_blocks = []
        is_success = solver_status in (cp_model.OPTIMAL, cp_model.FEASIBLE)
        
        if is_success:
            for rid, tv in task_vars.items():
                start_mins = solver.Value(tv["start"])
                end_mins = solver.Value(tv["end"])
                
                block_start_dt = base_time + timedelta(minutes=start_mins)
                block_end_dt = base_time + timedelta(minutes=end_mins)
                req = task_info[rid]
                hard_train_conflicts = sum(
                    start_mins < train_interval.end_minute
                    and end_mins > train_interval.start_minute
                    for train_interval in train_intervals
                    if train_interval.is_hard
                    and train_interval.section_id == tv["section_id"]
                )
                
                # Check track assignment
                track_type = TrackType.BOTH_LINES if req.department == "Engineering" and "Tamping" in req.task_title else TrackType.UP_LINE
                
                # Check if block exists or create proposed
                existing_b = db.query(MaintenanceBlock).filter(
                    MaintenanceBlock.request_id == rid
                ).first()
                
                if existing_b:
                    existing_b.scheduled_start = block_start_dt
                    existing_b.scheduled_end = block_end_dt
                    existing_b.duration_hours = round(tv["duration"] / 60.0, 1)
                    existing_b.or_tools_score = round(float(tv["priority_score"]), 1)
                    if existing_b.status != BlockStatus.APPROVED:
                        existing_b.status = BlockStatus.PROPOSED
                    target_b = existing_b
                else:
                    b_code = f"BLK-{block_start_dt.strftime('%Y%m%d')}-{rid:03d}"
                    target_b = MaintenanceBlock(
                        block_code=b_code,
                        request_id=rid,
                        section_id=req.section_id or 1,
                        scheduled_start=block_start_dt,
                        scheduled_end=block_end_dt,
                        duration_hours=round(tv["duration"] / 60.0, 1),
                        track_type=track_type,
                        power_block_required=(req.department == "TRD"),
                        signal_disconnection_required=(req.department == "S&T"),
                        status=BlockStatus.PROPOSED,
                        is_pinned=False,
                        or_tools_score=round(float(tv["priority_score"]), 1),
                    )
                    db.add(target_b)
                readiness = readiness_by_request[rid]
                target_b.readiness_verdict = readiness["verdict"]
                target_b.readiness_snapshot = json.dumps(readiness)
                
                # Update request status to OPTIMIZED if it was SUBMITTED/VALIDATED
                if req.current_status in (RequestStatus.SUBMITTED, RequestStatus.VALIDATED):
                    req.current_status = RequestStatus.OPTIMIZED
                    
                result_blocks.append({
                    "request_id": rid,
                    "task_title": req.task_title,
                    "department": req.department,
                    "section_code": req.railway_section,
                    "scheduled_start": block_start_dt.isoformat(),
                    "scheduled_end": block_end_dt.isoformat(),
                    "duration_hours": round(tv["duration"] / 60.0, 1),
                    "ai_priority_score": tv["priority_score"],
                    "track_type": track_type.value,
                    "is_pinned": target_b.is_pinned if hasattr(target_b, "is_pinned") else False,
                    "train_conflicts": hard_train_conflicts,
                    "readiness_verdict": readiness["verdict"],
                    "readiness_snapshot": readiness,
                })

            db.commit()

            # Record audit log
            audit = AuditLog(
                user_name="Optimization Engine",
                role="SYSTEM",
                action="RUN_OPTIMIZATION",
                department="All",
                badge_type="success",
                details=f"CP-SAT scheduled {len(result_blocks)} blocks across {len(section_intervals)} sections with status {solver.StatusName(solver_status)}."
            )
            db.add(audit)
            db.commit()
        elif task_vars:
            for rid, req in task_info.items():
                unscheduled.append({
                    "request_id": rid,
                    "task_title": req.task_title,
                    "reason": (
                        "no feasible schedule within the requested window under "
                        "resource, dependency, and train constraints"
                    ),
                })

        refresh_schedule_validation(db)
        return {
            "status": "OPTIMIZED" if is_success else "INFEASIBLE",
            "solver_status_name": solver.StatusName(solver_status),
            "wall_time_seconds": round(solver.WallTime(), 3),
            "objective_value": solver.ObjectiveValue() if is_success else None,
            "blocks_scheduled": len(result_blocks),
            "schedule": result_blocks,
            "unscheduled": unscheduled,
            "excluded": excluded,
            "train_intervals_checked": train_intervals_checked,
        }

optimizer_scheduler = BlockOptimizationScheduler()
