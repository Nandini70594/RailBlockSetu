import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Enum, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class MaintenanceType(str, enum.Enum):
    PREVENTIVE = "PREVENTIVE"
    CORRECTIVE = "CORRECTIVE"
    EMERGENCY = "EMERGENCY"
    OVERHAUL = "OVERHAUL"

class AssetCriticality(str, enum.Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

class UrgencyLevel(str, enum.Enum):
    EMERGENCY = "EMERGENCY"
    URGENT = "URGENT"
    ROUTINE = "ROUTINE"

class RequestStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    VALIDATED = "VALIDATED"
    OPTIMIZED = "OPTIMIZED"
    APPROVED = "APPROVED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    REJECTED = "REJECTED"

class MaintenanceRequest(Base):
    __tablename__ = "maintenance_requests"
    
    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(String(50), unique=True, index=True, nullable=False)
    task_title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    department = Column(String(50), nullable=False)  # Engineering, TRD, S&T
    railway_division = Column(String(100), nullable=False, default="Delhi")
    railway_section = Column(String(100), nullable=False)
    section_id = Column(Integer, ForeignKey("railway_sections.id"), nullable=True)
    asset_id = Column(String(100), nullable=False)
    asset_type = Column(String(100), nullable=False, default="Track")
    maintenance_type = Column(Enum(MaintenanceType), default=MaintenanceType.PREVENTIVE, nullable=False)
    
    required_start_date = Column(DateTime, nullable=False)
    deadline = Column(DateTime, nullable=False)
    estimated_duration = Column(Float, nullable=False)  # in hours
    
    # Resource requirements
    required_staff = Column(Integer, nullable=False, default=4)
    required_machinery = Column(Text, nullable=True)  # JSON list of machine codes/names
    required_materials = Column(Text, nullable=True)  # JSON list of materials
    
    # Operational constraints
    safety_requirements = Column(Text, nullable=True)  # JSON: power block, speed restriction, caution order
    task_dependencies = Column(Text, nullable=True)  # JSON list of request IDs this task depends on
    asset_criticality = Column(Enum(AssetCriticality), default=AssetCriticality.HIGH, nullable=False)
    urgency_level = Column(Enum(UrgencyLevel), default=UrgencyLevel.ROUTINE, nullable=False)
    current_status = Column(Enum(RequestStatus), default=RequestStatus.SUBMITTED, nullable=False)
    
    # AI / ML Prioritization & Analytics
    ai_priority_score = Column(Float, default=50.0)  # 0 to 100
    ai_risk_factor = Column(String(50), default="MODERATE")  # LOW, MODERATE, HIGH, SEVERE
    ai_explanation = Column(Text, nullable=True)
    readiness_score = Column(Float, default=0.0)  # 0 to 100%
    
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    section = relationship("RailwaySection")
    created_by = relationship("User")
