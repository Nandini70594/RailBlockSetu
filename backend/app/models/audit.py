from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text
from app.database import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_name = Column(String(100), default="System")
    role = Column(String(50), default="SYSTEM")
    action = Column(String(100), nullable=False)  # CREATE_REQUEST, RUN_OPTIMIZATION, APPROVE_BLOCK, TRIGGER_DISRUPTION, REPLAN_SUCCESS
    department = Column(String(50), default="All")
    details = Column(Text, nullable=True)
    badge_type = Column(String(50), default="info")  # success, warning, danger, info
    created_at = Column(DateTime, default=datetime.utcnow)
