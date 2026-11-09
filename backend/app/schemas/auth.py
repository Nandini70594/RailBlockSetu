from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.models.user import UserRole, DepartmentType

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserResponse"

class TokenData(BaseModel):
    username: Optional[str] = None

class UserCreate(BaseModel):
    email: str
    username: str
    full_name: str
    password: str
    role: UserRole = UserRole.DEPARTMENT_OFFICER
    department: DepartmentType = DepartmentType.ENGINEERING

class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    full_name: str
    role: UserRole
    department: DepartmentType
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
