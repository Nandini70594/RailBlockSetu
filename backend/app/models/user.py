import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum
from app.database import Base

class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    DEPARTMENT_OFFICER = "DEPARTMENT_OFFICER"
    OPERATIONS_OFFICER = "OPERATIONS_OFFICER"

class DepartmentType(str, enum.Enum):
    ENGINEERING = "Engineering"
    TRD = "TRD"
    ST = "S&T"
    OPERATIONS = "Operations"
    ALL = "All"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.DEPARTMENT_OFFICER, nullable=False)
    department = Column(Enum(DepartmentType), default=DepartmentType.ENGINEERING, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
