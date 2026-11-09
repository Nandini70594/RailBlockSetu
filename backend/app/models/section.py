from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from app.database import Base

class RailwaySection(Base):
    __tablename__ = "railway_sections"
    
    id = Column(Integer, primary_key=True, index=True)
    section_code = Column(String(50), unique=True, index=True, nullable=False)
    section_name = Column(String(200), nullable=False)
    division = Column(String(100), nullable=False, default="Delhi")
    zone = Column(String(100), nullable=False, default="Northern Railway")
    start_km = Column(Float, nullable=False)
    end_km = Column(Float, nullable=False)
    track_count = Column(String(50), default="DOUBLE")  # SINGLE, DOUBLE, QUAD
    electrification_type = Column(String(50), default="25kV_AC")
    max_speed_kmh = Column(Integer, default=130)
    signaling_system = Column(String(100), default="Automatic Block Signaling (ABS) with KAVACH")
    traffic_density = Column(String(50), default="HIGH")  # CRITICAL, HIGH, MEDIUM, LOW
    coordinates_json = Column(Text, nullable=True)  # JSON lat/long for map
    created_at = Column(DateTime, default=datetime.utcnow)
