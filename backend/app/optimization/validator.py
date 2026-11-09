import json
from collections import defaultdict
from datetime import datetime, time, timedelta
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from sqlalchemy.orm import Session

from app.config import settings
from app.models.request import MaintenanceRequest
from app.models.resource import Resource, ResourceType
from app.models.schedule import BlockStatus, MaintenanceBlock, TrackType
from app.models.train import TrainSchedule
from app.optimization.train_windows import build_train_intervals


ACTIVE_BLOCK_STATUSES = (
    BlockStatus.PROPOSED,
    BlockStatus.APPROVED,
    BlockStatus.IN_PROGRESS,
)


def _overlaps(start_a: datetime, end_a: datetime, start_b: datetime, end_b: datetime) -> bool:
    return start_a < end_b and end_a > start_b


def _track_types_conflict(track_a: Any, track_b: Any) -> bool:
    value_a = track_a.value if isinstance(track_a, TrackType) else str(track_a)
    value_b = track_b.value if isinstance(track_b, TrackType) else str(track_b)
    if "BOTH" in (value_a, value_b):
        return True
    if value_a == value_b:
        return True
    return {value_a, value_b} != {"UP_LINE", "DOWN_LINE"} and (
        "YARD" in (value_a, value_b)
    )


def _string_requirements(raw: Optional[str]) -> List[str]:
    if not raw:
        return []
    try:
        parsed = json.loads(raw)
    except (TypeError, json.JSONDecodeError):
        parsed = raw
    if isinstance(parsed, str):
        return [parsed.strip()] if parsed.strip() else []
    if isinstance(parsed, list):
        return [str(value).strip() for value in parsed if str(value).strip()]
    return []


def _request_dependencies(request: MaintenanceRequest) -> List[str]:
    return _string_requirements(request.task_dependencies)


def _interval_for_block(block: MaintenanceBlock) -> Tuple[datetime, datetime]:
    start = block.scheduled_start
    end = block.scheduled_end
    if start.tzinfo is not None:
        start = start.replace(tzinfo=None)
    if end.tzinfo is not None:
        end = end.replace(tzinfo=None)
    return start, end


def validate_schedule(
    blocks: Sequence[MaintenanceBlock],
    db: Session,
) -> List[Dict[str, Any]]:
    """Independently verify hard schedule constraints for active proposed blocks."""
    active = [
        block for block in blocks
        if block.status in ACTIVE_BLOCK_STATUSES
        and block.scheduled_start is not None
        and block.scheduled_end is not None
    ]
    if not active:
        return []

    requests = {
        request.id: request
        for request in db.query(MaintenanceRequest).filter(
            MaintenanceRequest.id.in_([block.request_id for block in active])
        ).all()
    }
    all_requests = db.query(MaintenanceRequest).all()
    request_ids = {
        request.request_id: request.id
        for request in all_requests
        if request.request_id
    }
    block_by_request = {block.request_id: block for block in active}
    violations: List[Dict[str, Any]] = []

    def add_violation(
        violation_type: str,
        violating_blocks: Iterable[MaintenanceBlock],
        reason: str,
        **details: Any,
    ) -> None:
        ids = sorted({block.id for block in violating_blocks if block.id is not None})
        if not ids:
            return
        violations.append({
            "type": violation_type,
            "block_ids": ids,
            "reason": reason,
            **details,
        })

    for index, first in enumerate(active):
        start_a, end_a = _interval_for_block(first)
        request_a = requests.get(first.request_id)
        for second in active[index + 1:]:
            start_b, end_b = _interval_for_block(second)
            if (
                first.section_id == second.section_id
                and _track_types_conflict(first.track_type, second.track_type)
                and _overlaps(start_a, end_a, start_b, end_b)
            ):
                add_violation(
                    "section_overlap",
                    (first, second),
                    f"Blocks overlap on incompatible tracks in section {first.section_id}.",
                    section_id=first.section_id,
                )

            request_b = requests.get(second.request_id)
            machines_a = set(_string_requirements(
                request_a.required_machinery if request_a else None
            ))
            machines_b = set(_string_requirements(
                request_b.required_machinery if request_b else None
            ))
            shared_machines = sorted(machines_a & machines_b)
            if shared_machines and _overlaps(start_a, end_a, start_b, end_b):
                add_violation(
                    "machine_double_booking",
                    (first, second),
                    f"Machine(s) {', '.join(shared_machines)} are assigned to overlapping blocks.",
                    machine_ids=shared_machines,
                )

    # Crew capacity can only be asserted when the department has recorded crew.
    crew_capacity: Dict[str, float] = defaultdict(float)
    crew_departments = set()
    for resource in db.query(Resource).filter(
        Resource.resource_type == ResourceType.STAFF
    ).all():
        crew_departments.add(resource.department)
        if resource.operational_status != "UNDER_MAINTENANCE":
            crew_capacity[resource.department] += resource.available_quantity

    for department in crew_departments:
        department_blocks = [
            block for block in active
            if requests.get(block.request_id) is not None
            and requests[block.request_id].department == department
        ]
        points = sorted({
            point
            for block in department_blocks
            for point in _interval_for_block(block)
        })
        seen_crews = set()
        for segment_start, segment_end in zip(points, points[1:]):
            overlapping = [
                block for block in department_blocks
                if _overlaps(*_interval_for_block(block), segment_start, segment_end)
            ]
            required = sum(
                requests[block.request_id].required_staff for block in overlapping
            )
            signature = tuple(sorted(block.id for block in overlapping if block.id is not None))
            if (
                overlapping
                and required > crew_capacity[department]
                and signature not in seen_crews
            ):
                seen_crews.add(signature)
                add_violation(
                    "crew_overallocation",
                    overlapping,
                    f"Overlapping blocks require {required:g} staff, but department "
                    f"{department} has {crew_capacity[department]:g} available.",
                    department=department,
                    required_staff=required,
                    available_staff=crew_capacity[department],
                )

    for block in active:
        request = requests.get(block.request_id)
        if request is None:
            continue
        block_start, block_end = _interval_for_block(block)
        if request.deadline and block_end > request.deadline:
            add_violation(
                "deadline",
                (block,),
                f"Block ends after request deadline {request.deadline.isoformat()}.",
                deadline=request.deadline.isoformat(),
            )

        for dependency in _request_dependencies(request):
            dependency_id = request_ids.get(dependency)
            if dependency_id is None:
                try:
                    dependency_id = int(dependency)
                except ValueError:
                    add_violation(
                        "dependency_order",
                        (block,),
                        f"Dependency {dependency!r} does not identify a maintenance request.",
                    )
                    continue
            dependency_block = block_by_request.get(dependency_id)
            if dependency_block is None:
                add_violation(
                    "dependency_order",
                    (block,),
                    f"Required dependency request {dependency} has no active scheduled block.",
                    dependency_request_id=dependency_id,
                )
                continue
            _, dependency_end = _interval_for_block(dependency_block)
            if block_start < dependency_end + timedelta(minutes=30):
                add_violation(
                    "dependency_order",
                    (dependency_block, block),
                    f"Dependent block must start at least 30 minutes after block "
                    f"{dependency_block.id} ends.",
                    dependency_block_id=dependency_block.id,
                )

    trains = db.query(TrainSchedule).all()
    for block in active:
        block_start, block_end = _interval_for_block(block)
        base_time = datetime.combine(block_start.date(), time.min)
        horizon_minutes = max(
            1,
            int((block_end - base_time).total_seconds() // 60) + 1,
        )
        train_intervals = build_train_intervals(
            trains,
            base_time,
            horizon_minutes,
            buffer_minutes=settings.TRAIN_BUFFER_MINUTES,
        )
        start_minute = int((block_start - base_time).total_seconds() // 60)
        end_minute = int((block_end - base_time).total_seconds() // 60)
        for interval in train_intervals:
            if (
                interval.is_hard
                and interval.section_id == block.section_id
                and start_minute < interval.end_minute
                and end_minute > interval.start_minute
            ):
                add_violation(
                    "protected_train_overlap",
                    (block,),
                    f"Block overlaps a protected train interval on section {block.section_id}.",
                    section_id=block.section_id,
                    train_number=interval.train_number,
                )

    return violations


def refresh_schedule_validation(
    db: Session,
    blocks: Optional[Sequence[MaintenanceBlock]] = None,
    commit: bool = True,
) -> List[Dict[str, Any]]:
    active = list(blocks) if blocks is not None else db.query(MaintenanceBlock).filter(
        MaintenanceBlock.status.in_(ACTIVE_BLOCK_STATUSES)
    ).all()
    violations = validate_schedule(active, db)
    violations_by_block: Dict[int, List[Dict[str, Any]]] = defaultdict(list)
    for violation in violations:
        for block_id in violation["block_ids"]:
            violations_by_block[block_id].append(violation)
    for block in active:
        block.conflict_detected = bool(block.id in violations_by_block)
        block.conflict_details = json.dumps(violations_by_block.get(block.id, []))
    db.flush()
    if commit:
        db.commit()
    return violations
