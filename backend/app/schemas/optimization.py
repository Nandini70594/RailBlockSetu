from pydantic import BaseModel
from typing import Optional, List, Any, Dict
from datetime import datetime
from app.models.schedule import BlockStatus, TrackType

class OptimizationTriggerRequest(BaseModel):
    horizon_hours: int = 72
    pinned_block_ids: Optional[List[int]] = None

class BlockApprovalRequest(BaseModel):
    status: BlockStatus  # APPROVED or REJECTED
    approval_notes: Optional[str] = None

class MaintenanceBlockResponse(BaseModel):
    id: int
    block_code: str
    request_id: int
    section_id: int
    work_package_id: Optional[int] = None
    scheduled_start: datetime
    scheduled_end: datetime
    duration_hours: float
    track_type: TrackType
    power_block_required: bool
    signal_disconnection_required: bool
    status: BlockStatus
    is_pinned: bool
    or_tools_score: float
    approval_notes: Optional[str] = None
    readiness_verdict: Optional[str] = None
    readiness_snapshot: Optional[Dict[str, Any]] = None
    conflict_detected: bool = False
    conflict_details: Optional[List[Dict[str, Any]]] = None
    task_title: Optional[str] = None
    department: Optional[str] = None
    section_code: Optional[str] = None

    class Config:
        from_attributes = True
