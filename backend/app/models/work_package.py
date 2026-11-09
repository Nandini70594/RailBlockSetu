from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class WorkPackage(Base):
    __tablename__ = "work_packages"

    id = Column(Integer, primary_key=True, index=True)
    section_id = Column(Integer, ForeignKey("railway_sections.id"), nullable=False)
    departments = Column(Text, nullable=False)
    included_task_ids = Column(Text, nullable=False)
    shared_window_start = Column(DateTime, nullable=False)
    shared_window_end = Column(DateTime, nullable=False)
    expected_utilization = Column(Float, nullable=False)
    compatibility_status = Column(String(30), nullable=False)
    compatibility_reasons = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    section = relationship("RailwaySection")
