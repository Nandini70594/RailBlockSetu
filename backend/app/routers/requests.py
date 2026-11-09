from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import json

from app.database import get_db
from app.models.request import MaintenanceRequest, RequestStatus
from app.models.section import RailwaySection
from app.models.user import User, UserRole
from app.models.audit import AuditLog
from app.schemas.request import MaintenanceRequestCreate, MaintenanceRequestUpdate, MaintenanceRequestResponse
from app.utils.security import get_current_user, require_roles
from app.ml.priority_model import priority_engine
from app.optimization.readiness import readiness_validator

router = APIRouter(
    prefix="/requests",
    tags=["Maintenance Request Management"],
    dependencies=[Depends(get_current_user)],
)


def _ensure_request_modifiable(req: MaintenanceRequest, current_user: User) -> None:
    if current_user.role == UserRole.ADMIN:
        return

    if req.department != current_user.department.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Department officers may only modify requests in their own department.",
        )

    if req.current_status not in {RequestStatus.DRAFT, RequestStatus.SUBMITTED}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Requests may only be modified while in DRAFT or PENDING (SUBMITTED) state.",
        )

@router.get("", response_model=List[MaintenanceRequestResponse])
def get_all_requests(
    department: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(MaintenanceRequest)
    if department and department != "All":
        query = query.filter(MaintenanceRequest.department == department)
    if status and status != "ALL":
        query = query.filter(MaintenanceRequest.current_status == status)
    return query.order_by(MaintenanceRequest.ai_priority_score.desc()).all()

@router.get("/{request_id}", response_model=MaintenanceRequestResponse)
def get_request_by_id(request_id: int, db: Session = Depends(get_db)):
    req = db.query(MaintenanceRequest).filter(MaintenanceRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Maintenance request not found")
    return req

@router.post("", response_model=MaintenanceRequestResponse)
def create_request(
    request_data: MaintenanceRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.DEPARTMENT_OFFICER]))
):
    if (
        current_user.role != UserRole.ADMIN
        and request_data.department != current_user.department.value
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Department officers may only create requests for their own department.",
        )

    # Auto-generate request ID
    dept_prefix = request_data.department[:3].upper() if request_data.department else "REQ"
    count = db.query(MaintenanceRequest).count() + 1
    req_code = f"REQ-{dept_prefix}-{datetime.utcnow().year}-{count:03d}"
    
    # Resolve section if section_code passed
    section_id = request_data.section_id
    if not section_id and request_data.railway_section:
        sec = db.query(RailwaySection).filter(
            RailwaySection.section_code == request_data.railway_section
        ).first()
        if sec:
            section_id = sec.id

    # Compute AI Priority Score using Machine Learning
    req_dict = request_data.dict()
    req_dict["department"] = request_data.department
    ml_eval = priority_engine.predict(req_dict)

    new_req = MaintenanceRequest(
        request_id=req_code,
        task_title=request_data.task_title,
        description=request_data.description,
        department=request_data.department,
        railway_division=request_data.railway_division,
        railway_section=request_data.railway_section,
        section_id=section_id,
        asset_id=request_data.asset_id,
        asset_type=request_data.asset_type,
        maintenance_type=request_data.maintenance_type,
        required_start_date=request_data.required_start_date,
        deadline=request_data.deadline,
        estimated_duration=request_data.estimated_duration,
        required_staff=request_data.required_staff,
        required_machinery=request_data.required_machinery,
        required_materials=request_data.required_materials,
        safety_requirements=request_data.safety_requirements,
        obtained_safety_requirements=request_data.obtained_safety_requirements,
        task_dependencies=request_data.task_dependencies,
        asset_criticality=request_data.asset_criticality,
        urgency_level=request_data.urgency_level,
        current_status=RequestStatus.SUBMITTED,
        ai_priority_score=ml_eval["ai_priority_score"],
        ai_risk_factor=ml_eval["ai_risk_factor"],
        ai_explanation=ml_eval["ai_explanation"],
        created_by_id=current_user.id
    )
    
    db.add(new_req)
    db.commit()
    db.refresh(new_req)

    # Calculate initial readiness
    readiness_report = readiness_validator.validate_request_readiness(new_req, db)
    new_req.readiness_score = readiness_report["overall_readiness_score"]
    db.commit()
    db.refresh(new_req)

    # Log to audit trail
    audit = AuditLog(
        user_name=current_user.full_name,
        role=current_user.role.value,
        action="CREATE_REQUEST",
        department=new_req.department,
        badge_type="success",
        details=f"Created request {new_req.request_id}: {new_req.task_title}. AI Priority Score: {new_req.ai_priority_score}."
    )
    db.add(audit)
    db.commit()

    return new_req

@router.put("/{request_id}", response_model=MaintenanceRequestResponse)
def update_request(
    request_id: int,
    update_data: MaintenanceRequestUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.DEPARTMENT_OFFICER]))
):
    req = db.query(MaintenanceRequest).filter(MaintenanceRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Maintenance request not found")

    _ensure_request_modifiable(req, current_user)
    update_dict = update_data.dict(exclude_unset=True)
    if (
        current_user.role != UserRole.ADMIN
        and update_dict.get("department", req.department) != current_user.department.value
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Department officers may only modify requests in their own department.",
        )
    if (
        current_user.role != UserRole.ADMIN
        and update_dict.get("current_status") not in (None, RequestStatus.DRAFT, RequestStatus.SUBMITTED)
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Department officers cannot move requests beyond DRAFT or PENDING (SUBMITTED) state.",
        )

    for field, val in update_dict.items():
        setattr(req, field, val)

    # Recalculate AI score
    req_dict = {
        "department": req.department,
        "asset_criticality": req.asset_criticality.value,
        "urgency_level": req.urgency_level.value,
        "estimated_duration": req.estimated_duration,
        "deadline": req.deadline
    }
    ml_eval = priority_engine.predict(req_dict)
    req.ai_priority_score = ml_eval["ai_priority_score"]
    req.ai_risk_factor = ml_eval["ai_risk_factor"]
    req.ai_explanation = ml_eval["ai_explanation"]

    req.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(req)
    return req

@router.delete("/{request_id}")
def delete_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.DEPARTMENT_OFFICER]))
):
    req = db.query(MaintenanceRequest).filter(MaintenanceRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Maintenance request not found")

    _ensure_request_modifiable(req, current_user)
    db.delete(req)
    db.commit()
    return {"message": f"Request {req.request_id} deleted successfully"}

@router.get("/{request_id}/readiness")
def get_readiness_report(request_id: int, db: Session = Depends(get_db)):
    """Explainable block readiness validation report"""
    req = db.query(MaintenanceRequest).filter(MaintenanceRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Maintenance request not found")
    report = readiness_validator.validate_request_readiness(req, db)
    return report
