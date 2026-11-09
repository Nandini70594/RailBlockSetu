import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, Enum, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class BlockStatus(str, enum.Enum):
    PROPOSED = "PROPOSED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

class TrackType(str, enum.Enum):
    UP_LINE = "UP_LINE"
    DOWN_LINE = "DOWN_LINE"
    BOTH_LINES = "BOTH_LINES"
    YARD = "YARD"

class MaintenanceBlock(Base):
    __tablename__ = "maintenance_blocks"
    
    id = Column(Integer, primary_key=True, index=True)
    block_code = Column(String(50), unique=True, index=True, nullable=False)
    request_id = Column(Integer, ForeignKey("maintenance_requests.id"), nullable=False)
    section_id = Column(Integer, ForeignKey("railway_sections.id"), nullable=False)
    
    scheduled_start = Column(DateTime, nullable=False)
    scheduled_end = Column(DateTime, nullable=False)
    duration_hours = Column(Float, nullable=False)
    
    track_type = Column(Enum(TrackType), default=TrackType.UP_LINE, nullable=False)
    power_block_required = Column(Boolean, default=False)  # TRD OHE isolation
    signal_disconnection_required = Column(Boolean, default=False)  # S&T interlocking disconnection
    speed_restriction_kmh = Column(Integer, nullable=True)  # e.g., 30 km/h caution order
    
    status = Column(Enum(BlockStatus), default=BlockStatus.PROPOSED, nullable=False)
    is_pinned = Column(Boolean, default=False)  # If pinned/approved, replanning will preserve it!
    
    # Validation & Optimization telemetry
    or_tools_score = Column(Float, default=0.0)
    conflict_detected = Column(Boolean, default=False)
    conflict_details = Column(Text, nullable=True)
    readiness_verdict = Column(String(30), nullable=True)
    readiness_snapshot = Column(Text, nullable=True)
    
    # Review & Approval workflow
    approved_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    approval_notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    request = relationship("MaintenanceRequest")
    section = relationship("RailwaySection")
    approved_by = relationship("User")
