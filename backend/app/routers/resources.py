from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.models.resource import Resource, ResourceType
from app.schemas.resource import ResourceCreate, ResourceUpdate, ResourceResponse
from app.models.user import User, UserRole
from app.utils.security import get_current_user, require_roles

router = APIRouter(
    prefix="/resources",
    tags=["Resource Management"],
    dependencies=[Depends(get_current_user)],
)

@router.get("", response_model=List[ResourceResponse])
def get_all_resources(
    department: Optional[str] = None,
    resource_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Resource)
    if department and department != "All":
        query = query.filter(Resource.department == department)
    if resource_type and resource_type != "ALL":
        query = query.filter(Resource.resource_type == resource_type)
    return query.all()

@router.post("", response_model=ResourceResponse)
def create_resource(
    resource_data: ResourceCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles([UserRole.ADMIN]))
):
    r = Resource(**resource_data.dict())
    db.add(r)
    db.commit()
    db.refresh(r)
    return r

@router.put("/{resource_id}", response_model=ResourceResponse)
def update_resource(
    resource_id: int,
    update_data: ResourceUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles([UserRole.ADMIN]))
):
    r = db.query(Resource).filter(Resource.id == resource_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Resource not found")
        
    for k, v in update_data.dict(exclude_unset=True).items():
        setattr(r, k, v)
    db.commit()
    db.refresh(r)
    return r
