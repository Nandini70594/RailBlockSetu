from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Sequence, Tuple
from zoneinfo import ZoneInfo

from app.database import get_db
from app.models.request import MaintenanceRequest, RequestStatus, AssetCriticality, UrgencyLevel
from app.models.schedule import MaintenanceBlock, BlockStatus
from app.models.resource import Resource
from app.models.section import RailwaySection
from app.models.disruption import Disruption
from app.models.train import TrainSchedule
from app.models.audit import AuditLog
from app.utils.network_graph import railway_network
from app.utils.security import get_current_user
from app.config import settings
from app.optimization.train_windows import build_train_intervals
from app.optimization.validator import (
    ACTIVE_BLOCK_STATUSES,
    refresh_schedule_validation,
)


IST = ZoneInfo("Asia/Kolkata")


def _merge_intervals(intervals: Sequence[Tuple[int, int]]) -> List[Tuple[int, int]]:
    merged: List[Tuple[int, int]] = []
    for start, end in sorted(intervals):
        if start >= end:
            continue
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    return merged


def _free_gaps(
    horizon_minutes: int,
    occupied: Sequence[Tuple[int, int]],
) -> List[Tuple[int, int]]:
    gaps = []
    cursor = 0
    for start, end in _merge_intervals(occupied):
        if start > cursor:
            gaps.append((cursor, start))
        cursor = max(cursor, end)
    if cursor < horizon_minutes:
        gaps.append((cursor, horizon_minutes))
    return gaps


def _dashboard_window_metrics(db: Session, now: datetime) -> Tuple[int, int, int]:
    horizon_minutes = 7 * 24 * 60
    trains = db.query(TrainSchedule).all()
    intervals = build_train_intervals(
        trains,
        now,
        horizon_minutes,
        buffer_minutes=settings.TRAIN_BUFFER_MINUTES,
    )
    approved_blocks = db.query(MaintenanceBlock).filter(
        MaintenanceBlock.status == BlockStatus.APPROVED,
        MaintenanceBlock.scheduled_end > now,
        MaintenanceBlock.scheduled_start < now + timedelta(minutes=horizon_minutes),
    ).all()
    active_blocks = db.query(MaintenanceBlock).filter(
        MaintenanceBlock.status.in_(ACTIVE_BLOCK_STATUSES),
        MaintenanceBlock.scheduled_end > now,
        MaintenanceBlock.scheduled_start < now + timedelta(minutes=horizon_minutes),
    ).all()
    scheduled_minutes = 0
    for block in active_blocks:
        start = max(block.scheduled_start, now)
        end = min(block.scheduled_end, now + timedelta(minutes=horizon_minutes))
        scheduled_minutes += max(0, int((end - start).total_seconds() // 60))

    section_ids = [section_id for (section_id,) in db.query(RailwaySection.id).all()]
    available_window_count = 0
    usable_window_minutes = 0
    for section_id in section_ids:
        train_occupied = _merge_intervals([
            (interval.start_minute, interval.end_minute)
            for interval in intervals
            if interval.section_id == section_id
        ])
        usable_window_minutes += sum(
            end - start for start, end in _free_gaps(horizon_minutes, train_occupied)
        )
        approved_occupied = []
        for block in approved_blocks:
            if block.section_id != section_id:
                continue
            start = block.scheduled_start.replace(tzinfo=None)
            end = block.scheduled_end.replace(tzinfo=None)
            start_minute = max(
                0, int((start - now).total_seconds() // 60)
            )
            end_minute = min(
                horizon_minutes, int((end - now).total_seconds() // 60)
            )
            if start_minute < end_minute:
                approved_occupied.append((start_minute, end_minute))
        free_gaps = _free_gaps(
            horizon_minutes,
            [*train_occupied, *approved_occupied],
        )
        available_window_count += sum(
            end - start >= settings.MIN_USEFUL_WINDOW_MINUTES
            for start, end in free_gaps
        )
    return available_window_count, scheduled_minutes, usable_window_minutes


def _resource_readiness_percentage(
    resources: Sequence[Resource],
    blocks: Sequence[MaintenanceBlock],
) -> Optional[float]:
    observed_scores: List[float] = []
    total_quantity = sum(resource.total_quantity for resource in resources)
    if total_quantity > 0:
        available_quantity = sum(
            resource.available_quantity
            for resource in resources
            if resource.operational_status != "UNDER_MAINTENANCE"
        )
        observed_scores.append(
            min(100.0, max(0.0, available_quantity / total_quantity * 100.0))
        )

    snapshots_by_request = {}
    for block in blocks:
        if block.request_id in snapshots_by_request or not block.readiness_snapshot:
            continue
        try:
            snapshot = json.loads(block.readiness_snapshot)
        except json.JSONDecodeError:
            continue
        for pillar_name in ("staff", "machinery", "materials"):
            pillar = snapshot.get("pillars", {}).get(pillar_name, {})
            score = pillar.get("score")
            if isinstance(score, (int, float)):
                snapshots_by_request[(block.request_id, pillar_name)] = float(score)
    observed_scores.extend(snapshots_by_request.values())
    if not observed_scores:
        return None
    return round(sum(observed_scores) / len(observed_scores), 1)

router = APIRouter(
    prefix="/dashboard",
    tags=["Command Center Dashboard"],
    dependencies=[Depends(get_current_user)],
)

@router.get("/metrics")
def get_dashboard_metrics(db: Session = Depends(get_db)) -> Dict[str, Any]:
    # Dashboard and train timetable calculations use naive IST wall times.
    now = datetime.now(IST).replace(tzinfo=None)
    
    # 1. Requests metrics
    total_requests = db.query(MaintenanceRequest).count()
    pending_requests = db.query(MaintenanceRequest).filter(
        MaintenanceRequest.current_status.in_([RequestStatus.SUBMITTED, RequestStatus.VALIDATED, RequestStatus.OPTIMIZED])
    ).count()
    critical_tasks = db.query(MaintenanceRequest).filter(
        (MaintenanceRequest.asset_criticality == AssetCriticality.CRITICAL) |
        (MaintenanceRequest.urgency_level == UrgencyLevel.EMERGENCY)
    ).count()
    completed_tasks = db.query(MaintenanceRequest).filter(
        MaintenanceRequest.current_status == RequestStatus.COMPLETED
    ).count()

    # 2. Blocks metrics
    approved_blocks = db.query(MaintenanceBlock).filter(
        MaintenanceBlock.status == BlockStatus.APPROVED
    ).count()
    proposed_blocks = db.query(MaintenanceBlock).filter(
        MaintenanceBlock.status == BlockStatus.PROPOSED
    ).count()
    
    # Sections currently or scheduled under maintenance
    active_block_sections = db.query(MaintenanceBlock.section_id).filter(
        MaintenanceBlock.status.in_([BlockStatus.APPROVED, BlockStatus.IN_PROGRESS])
    ).distinct().count()

    # 3. Resource readiness from recorded inventory and saved request snapshots.
    all_resources = db.query(Resource).all()
    active_blocks = db.query(MaintenanceBlock).filter(
        MaintenanceBlock.status.in_(ACTIVE_BLOCK_STATUSES)
    ).all()
    resource_readiness_pct = _resource_readiness_percentage(
        all_resources, active_blocks
    )

    # 4. Count real train-free gaps remaining after approved work is placed.
    available_windows, scheduled_minutes, usable_window_minutes = (
        _dashboard_window_metrics(db, now)
    )

    # 5. Active disruptions and independently revalidated schedule conflicts.
    active_disruptions = db.query(Disruption).filter(Disruption.is_active == True).count()
    # Metrics are read-only. Revalidating here must not commit conflict flags on
    # every dashboard refresh, especially when the database is remote.
    violations = refresh_schedule_validation(
        db,
        active_blocks,
        commit=False,
        persist=False,
    )
    conflicts_count = len(violations)

    # 6. Department Breakdown
    dept_counts = db.query(
        MaintenanceRequest.department,
        func.count(MaintenanceRequest.id)
    ).group_by(MaintenanceRequest.department).all()
    dept_distribution = {dept: count for dept, count in dept_counts}

    # 7. Priority Distribution (P1, P2, P3, P4)
    priority_counts = {
        "P1_CRITICAL": db.query(MaintenanceRequest).filter(MaintenanceRequest.ai_priority_score >= 85).count(),
        "P2_HIGH": db.query(MaintenanceRequest).filter((MaintenanceRequest.ai_priority_score >= 70) & (MaintenanceRequest.ai_priority_score < 85)).count(),
        "P3_MEDIUM": db.query(MaintenanceRequest).filter((MaintenanceRequest.ai_priority_score >= 50) & (MaintenanceRequest.ai_priority_score < 70)).count(),
        "P4_ROUTINE": db.query(MaintenanceRequest).filter(MaintenanceRequest.ai_priority_score < 50).count(),
    }

    # 8. Block utilization uses scheduled minutes over real train-free minutes.
    total_hours_requested = db.query(func.sum(MaintenanceRequest.estimated_duration)).scalar() or 0.0
    total_hours_granted = scheduled_minutes / 60.0
    utilization_rate = (
        round(scheduled_minutes / usable_window_minutes * 100.0, 1)
        if usable_window_minutes
        else None
    )

    return {
        "total_maintenance_requests": total_requests,
        "pending_requests": pending_requests,
        "approved_maintenance_blocks": approved_blocks,
        "proposed_maintenance_blocks": proposed_blocks,
        "completed_maintenance_tasks": completed_tasks,
        "critical_maintenance_tasks": critical_tasks,
        "resource_readiness_percentage": resource_readiness_pct,
        "available_maintenance_windows": available_windows,
        "railway_sections_under_maintenance": active_block_sections,
        "current_scheduling_conflicts": conflicts_count,
        "upcoming_disruptions": active_disruptions,
        "department_distribution": dept_distribution,
        "priority_distribution": priority_counts,
        "block_utilization": {
            "hours_requested": round(float(total_hours_requested), 1),
            "hours_granted": round(float(total_hours_granted), 1),
            "utilization_percentage": utilization_rate,
            "scheduled_minutes": scheduled_minutes,
            "usable_window_minutes": usable_window_minutes,
        }
    }

@router.get("/activity-feed")
def get_activity_feed(limit: int = 15, db: Session = Depends(get_db)):
    logs = db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit).all()
    return logs

@router.get("/network-topology")
def get_topology():
    return railway_network.get_network_topology()

@router.get("/weekly-timeline")
def get_weekly_timeline(db: Session = Depends(get_db)):
    """Fetch blocks scheduled in the upcoming week for visual Gantt / Timeline"""
    blocks = db.query(MaintenanceBlock).options(
        joinedload(MaintenanceBlock.request),
        joinedload(MaintenanceBlock.section),
    ).all()
    timeline_items = []
    for b in blocks:
        req = b.request
        sec = b.section
        timeline_items.append({
            "block_id": b.id,
            "block_code": b.block_code,
            "request_id": req.request_id if req else "REQ-NA",
            "task_title": req.task_title if req else "Maintenance Activity",
            "department": req.department if req else "Engineering",
            "section_code": sec.section_code if sec else "LINE",
            "start": b.scheduled_start.isoformat(),
            "end": b.scheduled_end.isoformat(),
            "duration_hours": b.duration_hours,
            "track_type": b.track_type.value,
            "status": b.status.value,
            "is_pinned": b.is_pinned,
            "power_block": b.power_block_required,
            "signal_disconnection": b.signal_disconnection_required,
            "ai_priority_score": req.ai_priority_score if req else 50.0
        })
    return timeline_items
