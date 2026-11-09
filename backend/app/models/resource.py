import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Enum
from app.database import Base

class ResourceType(str, enum.Enum):
    MACHINERY = "MACHINERY"
    STAFF = "STAFF"
    MATERIAL = "MATERIAL"

class Resource(Base):
    __tablename__ = "resources"
    
    id = Column(Integer, primary_key=True, index=True)
    resource_type = Column(Enum(ResourceType), nullable=False)
    name = Column(String(200), nullable=False)
    code = Column(String(100), unique=True, index=True, nullable=False)
    department = Column(String(50), nullable=False)  # Engineering, TRD, S&T, Operations
    total_quantity = Column(Float, nullable=False, default=1.0)
    available_quantity = Column(Float, nullable=False, default=1.0)
    allocated_quantity = Column(Float, nullable=False, default=0.0)
    unit = Column(String(50), default="Units")  # Units, Persons, Meters, Metric Tons
    specifications = Column(String(255), nullable=True)
    base_station = Column(String(100), default="New Delhi Central Depot")
    operational_status = Column(String(50), default="READY")  # READY, IN_USE, UNDER_MAINTENANCE
    created_at = Column(DateTime, default=datetime.utcnow)
