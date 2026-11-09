import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Enum, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class TrainType(str, enum.Enum):
    VANDE_BHARAT = "VANDE_BHARAT"
    RAJDHANI = "RAJDHANI"
    SHATABDI = "SHATABDI"
    SUPERFAST = "SUPERFAST"
    MAIL_EXPRESS = "MAIL_EXPRESS"
    FREIGHT = "FREIGHT"

class TrainSchedule(Base):
    __tablename__ = "train_schedules"
    
    id = Column(Integer, primary_key=True, index=True)
    train_number = Column(String(20), unique=True, index=True, nullable=False)
    train_name = Column(String(100), nullable=False)
    train_type = Column(Enum(TrainType), default=TrainType.SUPERFAST, nullable=False)
    origin = Column(String(100), nullable=False)
    destination = Column(String(100), nullable=False)
    
    # Priority for corridor clearance (1 = highest e.g. Vande Bharat/Rajdhani, 5 = freight)
    priority_level = Column(Integer, default=2, nullable=False)
    
    # Daily or weekly operating schedule
    frequency = Column(String(50), default="DAILY")
    section_id = Column(Integer, ForeignKey("railway_sections.id"), nullable=True)
    
    # Timing relative to section
    scheduled_entry_time = Column(String(10), nullable=False)  # HH:MM e.g. "06:15"
    scheduled_exit_time = Column(String(10), nullable=False)   # HH:MM e.g. "07:05"
    typical_delay_minutes = Column(Integer, default=0)
    current_status = Column(String(50), default="ON_TIME")  # ON_TIME, DELAYED, CANCELLED, DIVERTED
    
    section = relationship("RailwaySection")
