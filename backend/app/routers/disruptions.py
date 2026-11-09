from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from app.database import get_db
from app.models.disruption import Disruption, DisruptionType, DisruptionSeverity
from app.models.user import User, UserRole
from app.models.audit import AuditLog
from app.schemas.disruption import DisruptionCreate, DisruptionResponse
from app.utils.security import get_current_user, require_roles
from app.optimization.replanner import disruption_replanner

router = APIRouter(
    prefix="/disruptions",
    tags=["Disruption Management & Replanning"],
    dependencies=[Depends(get_current_user)],
)

@router.get("", response_model=List[DisruptionResponse])
def get_all_disruptions(db: Session = Depends(get_db)):
    return db.query(Disruption).order_by(Disruption.created_at.desc()).all()

@router.post("", response_model=DisruptionResponse)
def create_disruption(
    disruption_data: DisruptionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.OPERATIONS_OFFICER]))
):
    count = db.query(Disruption).count() + 1
    d_code = f"DIS-{datetime.utcnow().year}-{count:03d}"
    
    d = Disruption(
        disruption_code=d_code,
        title=disruption_data.title,
        disruption_type=disruption_data.disruption_type,
        section_id=disruption_data.section_id,
        affected_from=disruption_data.affected_from,
        affected_until=disruption_data.affected_until,
        severity=disruption_data.severity,
        impact_description=disruption_data.impact_description,
        is_active=True,
        replan_triggered=False
    )
    db.add(d)
    db.commit()
    db.refresh(d)

    audit = AuditLog(
        user_name=current_user.full_name,
        role=current_user.role.value,
        action="INJECT_DISRUPTION",
        department="Operations",
        badge_type="danger",
        details=f"Disruption logged: {d.title} on section ID {d.section_id}. Severity: {d.severity.value}."
    )
    db.add(audit)
    db.commit()

    return d

@router.post("/{disruption_id}/replan")
def trigger_disruption_replan(
    disruption_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.OPERATIONS_OFFICER]))
):
    """
    Railway Operations Officer replanning trigger:
    Pins unaffected approved blocks and re-runs CP-SAT on affected tasks!
    """
    res = disruption_replanner.execute_disruption_replan(disruption_id, db)
    return res
