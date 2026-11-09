from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.database import get_db
from app.models.schedule import MaintenanceBlock, BlockStatus
from app.models.request import MaintenanceRequest, RequestStatus
from app.models.user import User, UserRole
from app.models.audit import AuditLog
from app.schemas.optimization import OptimizationTriggerRequest, BlockApprovalRequest, MaintenanceBlockResponse
from app.utils.security import get_current_user
from app.optimization.scheduler import optimizer_scheduler

router = APIRouter(prefix="/optimization", tags=["Block Optimization & Scheduling"])

@router.post("/run")
def trigger_optimization(
    trigger_data: OptimizationTriggerRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Run Google OR-Tools CP-SAT multi-objective solver"""
    res = optimizer_scheduler.run_optimization(
        db=db,
        horizon_hours=trigger_data.horizon_hours,
        pinned_block_ids=trigger_data.pinned_block_ids
    )
    return res

@router.get("/blocks", response_model=List[MaintenanceBlockResponse])
def get_all_blocks(
    status: Optional[str] = None,
    section_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    query = db.query(MaintenanceBlock)
    if status and status != "ALL":
        query = query.filter(MaintenanceBlock.status == status)
    if section_id:
        query = query.filter(MaintenanceBlock.section_id == section_id)
        
    blocks = query.order_by(MaintenanceBlock.scheduled_start.asc()).all()
    results = []
    for b in blocks:
        results.append(MaintenanceBlockResponse(
            id=b.id,
            block_code=b.block_code,
            request_id=b.request_id,
            section_id=b.section_id,
            scheduled_start=b.scheduled_start,
            scheduled_end=b.scheduled_end,
            duration_hours=b.duration_hours,
            track_type=b.track_type,
            power_block_required=b.power_block_required,
            signal_disconnection_required=b.signal_disconnection_required,
            status=b.status,
            is_pinned=b.is_pinned,
            or_tools_score=b.or_tools_score,
            approval_notes=b.approval_notes,
            task_title=b.request.task_title if b.request else "Maintenance Task",
            department=b.request.department if b.request else "Engineering",
            section_code=b.section.section_code if b.section else "CORRIDOR"
        ))
    return results

@router.post("/blocks/{block_id}/review")
def review_block(
    block_id: int,
    review_data: BlockApprovalRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Railway Operations Officer authority: Approve or Reject proposed maintenance block"""
    b = db.query(MaintenanceBlock).filter(MaintenanceBlock.id == block_id).first()
    if not b:
        raise HTTPException(status_code=404, detail="Maintenance block not found")
        
    b.status = review_data.status
    b.approval_notes = review_data.approval_notes
    b.approved_by_id = current_user.id
    b.approved_at = datetime.utcnow()
    
    if review_data.status == BlockStatus.APPROVED:
        b.is_pinned = True
        if b.request:
            b.request.current_status = RequestStatus.APPROVED
    elif review_data.status == BlockStatus.REJECTED:
        b.is_pinned = False
        if b.request:
            b.request.current_status = RequestStatus.REJECTED

    db.commit()
    db.refresh(b)

    # Log to audit feed
    action_type = "APPROVE_BLOCK" if review_data.status == BlockStatus.APPROVED else "REJECT_BLOCK"
    badge = "success" if review_data.status == BlockStatus.APPROVED else "danger"
    audit = AuditLog(
        user_name=current_user.full_name,
        role=current_user.role.value,
        action=action_type,
        department="Operations",
        badge_type=badge,
        details=f"Block {b.block_code} on {b.section.section_code if b.section else 'corridor'} set to {b.status.value}. Notes: {review_data.approval_notes or 'No notes provided.'}"
    )
    db.add(audit)
    db.commit()

    return {"message": f"Block {b.block_code} updated to {b.status.value}", "block": b}

@router.post("/blocks/{block_id}/toggle-pin")
def toggle_pin_block(
    block_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    b = db.query(MaintenanceBlock).filter(MaintenanceBlock.id == block_id).first()
    if not b:
        raise HTTPException(status_code=404, detail="Maintenance block not found")
        
    b.is_pinned = not b.is_pinned
    db.commit()
    db.refresh(b)
    return {"message": f"Block pin status toggled to {b.is_pinned}", "is_pinned": b.is_pinned}
