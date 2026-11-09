import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, Enum, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class DisruptionType(str, enum.Enum):
    TRAIN_DELAY = "TRAIN_DELAY"
    OHE_BREAKDOWN = "OHE_BREAKDOWN"
    TRACK_DEFECT = "TRACK_DEFECT"
    SIGNAL_FAILURE = "SIGNAL_FAILURE"
    WEATHER_CYCLONE = "WEATHER_CYCLONE"
    ROLLING_STOCK_DERAILMENT = "ROLLING_STOCK_DERAILMENT"
    EMERGENCY_FREIGHT_PRIORITY = "EMERGENCY_FREIGHT_PRIORITY"

class DisruptionSeverity(str, enum.Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

class Disruption(Base):
    __tablename__ = "disruptions"
    
    id = Column(Integer, primary_key=True, index=True)
    disruption_code = Column(String(50), unique=True, index=True, nullable=False)
    title = Column(String(200), nullable=False)
    disruption_type = Column(Enum(DisruptionType), nullable=False)
    section_id = Column(Integer, ForeignKey("railway_sections.id"), nullable=False)
    
    affected_from = Column(DateTime, nullable=False)
    affected_until = Column(DateTime, nullable=False)
    severity = Column(Enum(DisruptionSeverity), default=DisruptionSeverity.HIGH, nullable=False)
    impact_description = Column(Text, nullable=False)
    
    # State tracking
    is_active = Column(Boolean, default=True)
    replan_triggered = Column(Boolean, default=False)
    replanned_at = Column(DateTime, nullable=True)
    affected_blocks_count = Column(Integer, default=0)
    preserved_blocks_count = Column(Integer, default=0)
    schedule_snapshot = Column(Text, nullable=True)
    replan_diff = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    section = relationship("RailwaySection")
