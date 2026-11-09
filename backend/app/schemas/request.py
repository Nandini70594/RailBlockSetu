from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime
from app.models.request import MaintenanceType, AssetCriticality, UrgencyLevel, RequestStatus

class MaintenanceRequestBase(BaseModel):
    task_title: str
    description: str
    department: str
    railway_division: str = "Delhi"
    railway_section: str
    section_id: Optional[int] = None
    asset_id: str
    asset_type: str = "Track"
    maintenance_type: MaintenanceType = MaintenanceType.PREVENTIVE
    required_start_date: datetime
    deadline: datetime
    estimated_duration: float
    required_staff: int = 4
    required_machinery: Optional[str] = "[]"
    required_materials: Optional[str] = "[]"
    safety_requirements: Optional[str] = "[]"
    obtained_safety_requirements: Optional[str] = "[]"
    task_dependencies: Optional[str] = "[]"
    asset_criticality: AssetCriticality = AssetCriticality.HIGH
    urgency_level: UrgencyLevel = UrgencyLevel.ROUTINE

class MaintenanceRequestCreate(MaintenanceRequestBase):
    pass

class MaintenanceRequestUpdate(BaseModel):
    task_title: Optional[str] = None
    description: Optional[str] = None
    department: Optional[str] = None
    railway_section: Optional[str] = None
    section_id: Optional[int] = None
    asset_id: Optional[str] = None
    asset_type: Optional[str] = None
    maintenance_type: Optional[MaintenanceType] = None
    required_start_date: Optional[datetime] = None
    deadline: Optional[datetime] = None
    estimated_duration: Optional[float] = None
    required_staff: Optional[int] = None
    required_machinery: Optional[str] = None
    required_materials: Optional[str] = None
    safety_requirements: Optional[str] = None
    obtained_safety_requirements: Optional[str] = None
    task_dependencies: Optional[str] = None
    asset_criticality: Optional[AssetCriticality] = None
    urgency_level: Optional[UrgencyLevel] = None
    current_status: Optional[RequestStatus] = None

class MaintenanceRequestResponse(MaintenanceRequestBase):
    id: int
    request_id: str
    current_status: RequestStatus
    ai_priority_score: Optional[float] = None
    ai_risk_factor: Optional[str] = None
    ai_explanation: Optional[str] = None
    readiness_score: Optional[float] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
