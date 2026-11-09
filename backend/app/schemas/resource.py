from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.models.resource import ResourceType

class ResourceBase(BaseModel):
    resource_type: ResourceType
    name: str
    code: str
    department: str
    total_quantity: float
    available_quantity: float
    unit: str = "Units"
    specifications: Optional[str] = None
    base_station: str = "New Delhi Central Depot"
    operational_status: str = "READY"

class ResourceCreate(ResourceBase):
    pass

class ResourceUpdate(BaseModel):
    name: Optional[str] = None
    total_quantity: Optional[float] = None
    available_quantity: Optional[float] = None
    operational_status: Optional[str] = None
    specifications: Optional[str] = None

class ResourceResponse(ResourceBase):
    id: int
    allocated_quantity: float
    created_at: datetime

    class Config:
        from_attributes = True
