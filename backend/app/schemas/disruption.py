from pydantic import BaseModel
from typing import Any, Dict, List, Optional
from datetime import datetime
from app.models.disruption import DisruptionType, DisruptionSeverity

class DisruptionCreate(BaseModel):
    title: str
    disruption_type: DisruptionType
    section_id: int
    affected_from: datetime
    affected_until: datetime
    severity: DisruptionSeverity = DisruptionSeverity.HIGH
    impact_description: str

class DisruptionResponse(BaseModel):
    id: int
    disruption_code: str
    title: str
    disruption_type: DisruptionType
    section_id: int
    affected_from: datetime
    affected_until: datetime
    severity: DisruptionSeverity
    impact_description: str
    is_active: bool
    replan_triggered: bool
    replanned_at: Optional[datetime] = None
    affected_blocks_count: int
    preserved_blocks_count: int
    schedule_snapshot: Optional[str] = None
    replan_diff: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
