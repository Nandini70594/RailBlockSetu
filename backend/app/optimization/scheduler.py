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
from app.models.work_package import WorkPackage
from app.optimization.readiness import readiness_validator
from app.optimization.compatibility import are_compatible
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
        disruption: Optional[Disruption] = None,
        stability_snapshot: Optional[List[Dict[str, Any]]] = None,
        directly_affected_block_ids: Optional[List[int]] = None,
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
        prior_by_task = {
            item["task_id"]: item
            for item in (stability_snapshot or [])
            if item.get("task_id") is not None
        }
        directly_affected = set(directly_affected_block_ids or [])

        # 3. Model Decision Variables
        task_vars = {}
        task_info = {}
        soft_train_penalties = []
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

            # Machinery capacity tracking
            machines = []
            if req.required_machinery:
                try:
                    machines = json.loads(req.required_machinery) if isinstance(req.required_machinery, str) else req.required_machinery
                except Exception:
                    machines = [req.required_machinery]
            for m in machines:
                m_key = str(m).strip().casefold()
                if m_key not in machine_intervals:
                    machine_intervals[m_key] = []
                machine_intervals[m_key].append((interval_var, 1))

            # Department staff gang tracking
            dept = req.department
            if dept not in department_intervals:
                department_intervals[dept] = []
            staff_req = req.required_staff
            department_intervals[dept].append((interval_var, staff_req))

        # 4. Enforce section occupancy pairwise; compatible cross-department
        # work can overlap and earns an objective bonus for shared minutes.
        work_package_bonus_terms = []
        stability_penalties = []
        prior_block_by_task = {
            item["task_id"]: item for item in prior_by_task.values()
        }
        old_block_ids_by_task = {
            item["task_id"]: item.get("block_id")
            for item in prior_by_task.values()
        }
        request_ids = list(task_vars)
        for index, first_id in enumerate(request_ids):
            first = task_info[first_id]
            first_vars = task_vars[first_id]
            for second_id in request_ids[index + 1:]:
                second = task_info[second_id]
                if first_vars["section_id"] != task_vars[second_id]["section_id"]:
                    continue
                compatible, _ = are_compatible(first, second)
                second_vars = task_vars[second_id]
                if not compatible:
                    first_before_second = model.NewBoolVar(
                        f"task_{first_id}_before_{second_id}"
                    )
                    second_before_first = model.NewBoolVar(
                        f"task_{second_id}_before_{first_id}"
                    )
                    model.Add(
                        first_vars["end"] <= second_vars["start"]
                    ).OnlyEnforceIf(first_before_second)
                    model.Add(
                        second_vars["end"] <= first_vars["start"]
                    ).OnlyEnforceIf(second_before_first)
                    model.AddBoolOr([first_before_second, second_before_first])
                    continue

                overlap_start = model.NewIntVar(
                    0, horizon_minutes, f"overlap_start_{first_id}_{second_id}"
                )
                overlap_end = model.NewIntVar(
                    0, horizon_minutes, f"overlap_end_{first_id}_{second_id}"
                )
                model.AddMaxEquality(
                    overlap_start,
                    [first_vars["start"], second_vars["start"]],
                )
                model.AddMinEquality(
                    overlap_end,
                    [first_vars["end"], second_vars["end"]],
                )
                overlap_delta = model.NewIntVar(
                    -horizon_minutes,
                    horizon_minutes,
                    f"overlap_delta_{first_id}_{second_id}",
                )
                model.Add(overlap_delta == overlap_end - overlap_start)
                overlap_minutes = model.NewIntVar(
                    0, horizon_minutes, f"overlap_minutes_{first_id}_{second_id}"
                )
                model.AddMaxEquality(overlap_minutes, [overlap_delta, 0])
                work_package_bonus_terms.append(
                    -overlap_minutes * settings.COMPATIBILITY_OVERLAP_BONUS_WEIGHT
                )

        for rid, tv in task_vars.items():
            prior = prior_block_by_task.get(rid)
            if prior is None or not prior.get("start"):
                continue
            old_start = datetime.fromisoformat(prior["start"])
            old_offset = int((old_start - base_time).total_seconds() // 60)
            movement = model.NewIntVar(
                0,
                max(
                    horizon_minutes,
                    abs(old_offset),
                    abs(horizon_minutes - old_offset),
                ),
                f"movement_minutes_{rid}",
            )
            model.AddAbsEquality(movement, tv["start"] - old_offset)
            moved = model.NewBoolVar(f"task_moved_{rid}")
            model.Add(movement == 0).OnlyEnforceIf(moved.Not())
            model.Add(movement >= 1).OnlyEnforceIf(moved)
            stability_penalties.append(
                movement * settings.REPLAN_MOVE_MINUTE_PENALTY
            )
            fixed_penalty = settings.REPLAN_MOVE_FIXED_PENALTY
            old_block_id = old_block_ids_by_task.get(rid)
            if (
                prior.get("status") == BlockStatus.APPROVED.value
                and old_block_id not in directly_affected
            ):
                fixed_penalty += settings.REPLAN_UNAFFECTED_APPROVED_MOVE_PENALTY
            stability_penalties.append(moved * fixed_penalty)

        # 5. Add Cumulative Resource Constraints for Machinery
        for m_key, items in machine_intervals.items():
            if len(items) > 1:
                intervals = [it[0] for it in items]
                demands = [it[1] for it in items]
                # Default max capacity 1 for heavy machinery (e.g. 1 Tamping Machine per division corridor)
                model.AddCumulative(intervals, demands, 1)

        # 6. Add Cumulative Constraints for Gang Personnel
        dept_staff_caps = settings.COMPATIBILITY_RULES["department_crew_limits"]
        for dept, items in department_intervals.items():
            cap = dept_staff_caps.get(
                dept,
                settings.COMPATIBILITY_RULES["default_crew_limit"],
            )
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
        objective_terms.extend(work_package_bonus_terms)
        objective_terms.extend(stability_penalties)

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
                    old_block_start = existing_b.scheduled_start
                    existing_b.scheduled_start = block_start_dt
                    existing_b.scheduled_end = block_end_dt
                    existing_b.duration_hours = round(tv["duration"] / 60.0, 1)
                    existing_b.or_tools_score = round(float(tv["priority_score"]), 1)
                    if (
                        stability_snapshot is not None
                        and old_block_start != block_start_dt
                    ):
                        existing_b.status = BlockStatus.PROPOSED
                        existing_b.is_pinned = False
                    elif existing_b.status != BlockStatus.APPROVED:
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
                details=(
                    f"CP-SAT scheduled {len(result_blocks)} blocks across "
                    f"{len({tv['section_id'] for tv in task_vars.values()})} "
                    f"sections with status {solver.StatusName(solver_status)}."
                )
            )
            db.add(audit)
            db.commit()
            packages = rebuild_work_packages(db)
            packages_by_request = {
                task_id: package["id"]
                for package in packages
                for task_id in package["included_task_ids"]
            }
            for result_block in result_blocks:
                result_block["work_package_id"] = packages_by_request.get(
                    result_block["request_id"]
                )
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
            "work_packages": packages if is_success else [],
            "unscheduled": unscheduled,
            "excluded": excluded,
            "train_intervals_checked": train_intervals_checked,
        }

optimizer_scheduler = BlockOptimizationScheduler()


def rebuild_work_packages(db: Session) -> List[Dict[str, Any]]:
    for block in db.query(MaintenanceBlock).all():
        block.work_package_id = None
    db.flush()
    active_blocks = db.query(MaintenanceBlock).filter(
        MaintenanceBlock.status.in_([
            BlockStatus.PROPOSED,
            BlockStatus.APPROVED,
            BlockStatus.IN_PROGRESS,
        ])
    ).order_by(MaintenanceBlock.scheduled_start, MaintenanceBlock.id).all()
    db.query(WorkPackage).delete(synchronize_session=False)
    db.flush()

    candidates = [
        (block, block.request)
        for block in active_blocks
        if block.request is not None
    ]
    groups: List[List[Tuple[MaintenanceBlock, MaintenanceRequest]]] = []
    for candidate in candidates:
        block, request = candidate
        matching_group = None
        for group in groups:
            if group[0][0].section_id != block.section_id:
                continue
            group_start = max(
                [block.scheduled_start]
                + [member.scheduled_start for member, _ in group]
            )
            group_end = min(
                [block.scheduled_end]
                + [member.scheduled_end for member, _ in group]
            )
            if group_start >= group_end:
                continue
            if all(are_compatible(request, member_request)[0]
                   for _, member_request in group):
                matching_group = group
                break
        if matching_group is None:
            groups.append([candidate])
        else:
            matching_group.append(candidate)

    packages: List[Dict[str, Any]] = []
    for group in groups:
        if len(group) < 2:
            continue
        blocks = [block for block, _ in group]
        requests = [request for _, request in group]
        window_start = max(block.scheduled_start for block in blocks)
        window_end = min(block.scheduled_end for block in blocks)
        window_minutes = (window_end - window_start).total_seconds() / 60
        if window_minutes <= 0:
            continue
        reasons = sorted({
            are_compatible(request_a, request_b)[1]
            for index, request_a in enumerate(requests)
            for request_b in requests[index + 1:]
        })
        task_ids = [request.id for request in requests]
        package = WorkPackage(
            section_id=blocks[0].section_id,
            departments=json.dumps(sorted({request.department for request in requests})),
            included_task_ids=json.dumps(task_ids),
            shared_window_start=window_start,
            shared_window_end=window_end,
            expected_utilization=(
                sum(
                    (block.scheduled_end - block.scheduled_start).total_seconds()
                    / 60
                    for block in blocks
                )
                / window_minutes
            ),
            compatibility_status="COMPATIBLE",
            compatibility_reasons=json.dumps(reasons),
        )
        db.add(package)
        db.flush()
        for block in blocks:
            block.work_package_id = package.id
        packages.append({
            "id": package.id,
            "section_id": package.section_id,
            "departments": json.loads(package.departments),
            "included_task_ids": task_ids,
            "shared_window_start": package.shared_window_start.isoformat(),
            "shared_window_end": package.shared_window_end.isoformat(),
            "expected_utilization": package.expected_utilization,
            "compatibility_status": package.compatibility_status,
            "compatibility_reasons": reasons,
            "tasks": [
                {"id": request.id, "title": request.task_title}
                for request in requests
            ],
        })
    db.commit()
    return packages
