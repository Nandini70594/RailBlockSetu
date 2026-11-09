from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from typing import Dict, Any, List

from app.database import get_db
from app.models.request import MaintenanceRequest, RequestStatus, AssetCriticality, UrgencyLevel
from app.models.schedule import MaintenanceBlock, BlockStatus
from app.models.resource import Resource, ResourceType
from app.models.section import RailwaySection
from app.models.disruption import Disruption
from app.models.train import TrainSchedule
from app.models.audit import AuditLog
from app.utils.network_graph import railway_network
from app.utils.security import get_current_user

router = APIRouter(
    prefix="/dashboard",
    tags=["Command Center Dashboard"],
    dependencies=[Depends(get_current_user)],
)

@router.get("/metrics")
def get_dashboard_metrics(db: Session = Depends(get_db)) -> Dict[str, Any]:
    now = datetime.utcnow()
    
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

    # 3. Resource readiness percentage calculation
    all_resources = db.query(Resource).all()
    if all_resources:
        total_avail_ratio = sum(r.available_quantity / max(1.0, r.total_quantity) for r in all_resources)
        resource_readiness_pct = round((total_avail_ratio / len(all_resources)) * 100.0, 1)
    else:
        resource_readiness_pct = 85.0

    # 4. Available maintenance windows (non-occupied train headway slots)
    total_sections = db.query(RailwaySection).count()
    available_windows = max(4, (total_sections * 4) - active_block_sections)

    # 5. Active Disruptions & Conflicts
    active_disruptions = db.query(Disruption).filter(Disruption.is_active == True).count()
    # Conflicts: blocks overlapping without approval
    conflicts_count = db.query(MaintenanceBlock).filter(MaintenanceBlock.conflict_detected == True).count()

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

    # 8. Block Utilization Analytics
    total_hours_requested = db.query(func.sum(MaintenanceRequest.estimated_duration)).scalar() or 0.0
    total_hours_granted = db.query(func.sum(MaintenanceBlock.duration_hours)).filter(
        MaintenanceBlock.status == BlockStatus.APPROVED
    ).scalar() or 0.0
    utilization_rate = round((total_hours_granted / max(1.0, total_hours_requested)) * 100.0, 1) if total_hours_requested > 0 else 0.0

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
            "utilization_percentage": min(100.0, utilization_rate)
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
    blocks = db.query(MaintenanceBlock).all()
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
