import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.audit import AuditLog
from app.models.disruption import Disruption
from app.models.request import MaintenanceRequest
from app.models.resource import Resource
from app.models.schedule import BlockStatus, MaintenanceBlock
from app.optimization.scheduler import optimizer_scheduler
from app.optimization.validator import refresh_schedule_validation


ACTIVE_STATUSES = (
    BlockStatus.APPROVED,
    BlockStatus.PROPOSED,
    BlockStatus.IN_PROGRESS,
)


def _requirements(value: Optional[str]) -> List[str]:
    if not value:
        return []
    try:
        parsed = json.loads(value)
    except (TypeError, json.JSONDecodeError):
        parsed = value
    if isinstance(parsed, str):
        return [parsed]
    if isinstance(parsed, list):
        return [str(item) for item in parsed]
    return []


def _assigned_resources(
    request: Optional[MaintenanceRequest],
    db: Session,
) -> Dict[str, Any]:
    if request is None:
        return {"staff": [], "machinery": [], "materials": []}
    requirements = {
        "machinery": _requirements(request.required_machinery),
        "materials": _requirements(request.required_materials),
    }
    result: Dict[str, Any] = {
        "staff": [{"department": request.department, "quantity": request.required_staff}],
        "machinery": [],
        "materials": [],
    }
    for kind, values in requirements.items():
        for value in values:
            resource = db.query(Resource).filter(
                Resource.department == request.department,
                (Resource.code == value) | (Resource.name == value),
            ).first()
            result[kind].append({
                "id": resource.id if resource else None,
                "code": resource.code if resource else value,
                "name": resource.name if resource else value,
                "quantity": 1,
            })
    return result


def _make_snapshot(
    blocks: List[MaintenanceBlock],
    db: Session,
) -> List[Dict[str, Any]]:
    return [
        {
            "task_id": block.request_id,
            "task_code": block.request.request_id if block.request else None,
            "task_title": block.request.task_title if block.request else None,
            "block_id": block.id,
            "start": block.scheduled_start.isoformat(),
            "end": block.scheduled_end.isoformat(),
            "section_id": block.section_id,
            "assigned_resources": _assigned_resources(block.request, db),
            "status": block.status.value,
        }
        for block in blocks
    ]


def _resource_changes(
    snapshot: List[Dict[str, Any]],
    current_by_request: Dict[int, MaintenanceBlock],
    db: Session,
) -> List[Dict[str, Any]]:
    changes = []
    for old in snapshot:
        block = current_by_request.get(old["task_id"])
        if block is None:
            continue
        current = _assigned_resources(block.request, db)
        if current != old["assigned_resources"]:
            changes.append({
                "task_id": old["task_id"],
                "old_resources": old["assigned_resources"],
                "new_resources": current,
            })
    return changes


class DisruptionReplanner:
    def execute_disruption_replan(
        self,
        disruption_id: int,
        db: Session,
    ) -> Dict[str, Any]:
        disruption = db.query(Disruption).filter(
            Disruption.id == disruption_id
        ).first()
        if not disruption:
            return {"error": f"Disruption with ID {disruption_id} not found."}

        all_blocks = db.query(MaintenanceBlock).filter(
            MaintenanceBlock.status.in_([
                BlockStatus.APPROVED,
                BlockStatus.PROPOSED,
            ])
        ).order_by(MaintenanceBlock.scheduled_start, MaintenanceBlock.id).all()

        # Persist the pre-replan state before changing pins, blocks, or request statuses.
        snapshot = _make_snapshot(all_blocks, db)
        disruption.schedule_snapshot = json.dumps(snapshot)
        db.commit()

        affected_blocks = [
            block for block in all_blocks
            if block.section_id == disruption.section_id
            and block.scheduled_start < disruption.affected_until
            and block.scheduled_end > disruption.affected_from
        ]
        affected_ids = {block.id for block in affected_blocks}
        unaffected_approved_ids = []
        for block in all_blocks:
            if block.id in affected_ids:
                block.is_pinned = False
            elif block.status == BlockStatus.APPROVED:
                block.is_pinned = True
                unaffected_approved_ids.append(block.id)
        db.commit()

        opt_result = optimizer_scheduler.run_optimization(
            db=db,
            horizon_hours=96,
            pinned_block_ids=unaffected_approved_ids,
            disruption=disruption,
            stability_snapshot=snapshot,
            directly_affected_block_ids=sorted(affected_ids),
        )

        unschedulable_by_request = {
            item["request_id"]: item["reason"]
            for item in opt_result.get("unscheduled", [])
        }
        for item in opt_result.get("excluded", []):
            unschedulable_by_request[item["request_id"]] = (
                "Readiness failed: " + ", ".join(item.get("failing_pillars", []))
            )

        scheduled_task_ids = {
            item["request_id"] for item in opt_result.get("schedule", [])
        }
        unschedulable = []
        for task_id, reason in unschedulable_by_request.items():
            request = db.query(MaintenanceRequest).filter(
                MaintenanceRequest.id == task_id
            ).first()
            unschedulable.append({
                "task_id": task_id,
                "task_title": request.task_title if request else None,
                "reason": reason,
            })
            old_block = next(
                (block for block in affected_blocks if block.request_id == task_id),
                None,
            )
            if old_block is not None and task_id not in scheduled_task_ids:
                old_block.status = BlockStatus.CANCELLED
                old_block.is_pinned = False

        db.flush()
        current_blocks = db.query(MaintenanceBlock).filter(
            MaintenanceBlock.status.in_(ACTIVE_STATUSES)
        ).all()
        current_by_request = {block.request_id: block for block in current_blocks}
        old_by_request = {item["task_id"]: item for item in snapshot}
        retained = []
        rescheduled = []
        newly_assigned = []
        total_movement_minutes = 0

        for task_id, block in current_by_request.items():
            old = old_by_request.get(task_id)
            if old is None:
                newly_assigned.append({
                    "task_id": task_id,
                    "task_title": block.request.task_title if block.request else None,
                    "block_id": block.id,
                    "new_start": block.scheduled_start.isoformat(),
                    "new_end": block.scheduled_end.isoformat(),
                    "section_id": block.section_id,
                    "status": block.status.value,
                })
                continue
            old_start = datetime.fromisoformat(old["start"])
            old_end = datetime.fromisoformat(old["end"])
            if (
                old_start == block.scheduled_start
                and old_end == block.scheduled_end
                and old["section_id"] == block.section_id
            ):
                retained.append({
                    "task_id": task_id,
                    "task_title": block.request.task_title if block.request else None,
                    "block_id": block.id,
                    "start": block.scheduled_start.isoformat(),
                    "end": block.scheduled_end.isoformat(),
                    "status": block.status.value,
                })
                continue
            delta = int(
                (block.scheduled_start - old_start).total_seconds() // 60
            )
            total_movement_minutes += abs(delta)
            rescheduled.append({
                "task_id": task_id,
                "task_title": block.request.task_title if block.request else None,
                "block_id": block.id,
                "old_start": old_start.isoformat(),
                "new_start": block.scheduled_start.isoformat(),
                "old_end": old_end.isoformat(),
                "new_end": block.scheduled_end.isoformat(),
                "delta_minutes": delta,
                "old_section_id": old["section_id"],
                "new_section_id": block.section_id,
                "status": block.status.value,
            })

        resources_changed = _resource_changes(snapshot, current_by_request, db)
        diff = {
            "retained": retained,
            "rescheduled": rescheduled,
            "newly_assigned": newly_assigned,
            "unschedulable": unschedulable,
            "resource_changes": resources_changed,
            "summary": {
                "retained_count": len(retained),
                "rescheduled_count": len(rescheduled),
                "newly_assigned_count": len(newly_assigned),
                "unschedulable_count": len(unschedulable),
                "resource_change_count": len(resources_changed),
                "total_movement_minutes": total_movement_minutes,
            },
        }

        disruption.replan_triggered = True
        disruption.replanned_at = datetime.utcnow()
        disruption.affected_blocks_count = len(affected_blocks)
        disruption.preserved_blocks_count = len(unaffected_approved_ids)
        disruption.replan_diff = json.dumps(diff)
        audit = AuditLog(
            user_name="Replanning Engine",
            role="OPERATIONS",
            action="TRIGGER_REPLAN",
            department="Operations",
            badge_type="warning",
            details=json.dumps({
                "disruption_id": disruption.id,
                "snapshot": snapshot,
                "diff": diff,
                "optimization_status": opt_result.get("status"),
                "optimization_unscheduled": opt_result.get("unscheduled", []),
                "optimization_excluded": opt_result.get("excluded", []),
            }),
        )
        db.add(audit)
        db.commit()
        refresh_schedule_validation(db)

        return {
            "disruption_code": disruption.disruption_code,
            "disruption_type": disruption.disruption_type.value,
            "disruption_section_id": disruption.section_id,
            "severity": disruption.severity.value,
            "affected_from": disruption.affected_from.isoformat(),
            "affected_until": disruption.affected_until.isoformat(),
            "snapshot": snapshot,
            "diff": diff,
            "affected_blocks_count": len(affected_blocks),
            "preserved_blocks_count": len(unaffected_approved_ids),
            "optimization_result": opt_result,
            "message": (
                f"Replanning complete: {len(retained)} retained, "
                f"{len(rescheduled)} rescheduled, {len(newly_assigned)} newly assigned, "
                f"and {len(unschedulable)} unschedulable."
            ),
        }


disruption_replanner = DisruptionReplanner()
