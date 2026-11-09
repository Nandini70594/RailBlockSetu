from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta

from app.database import get_db
from app.models.user import User, UserRole, DepartmentType
from app.schemas.auth import Token, UserResponse, UserLogin, UserCreate
from app.utils.security import verify_password, create_access_token, get_password_hash, get_current_user
from app.config import settings

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login", response_model=Token)
def login(login_data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(
        (User.username == login_data.username) | (User.email == login_data.username)
    ).first()
    
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user account")
        
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role.value, "dept": user.department.value},
        expires_delta=access_token_expires,
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }

@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.get("/demo-credentials")
def get_demo_credentials():
    """Returns quick credentials for the demo role switcher in UI"""
    return [
        {
            "role": "ADMIN",
            "title": "System Administrator",
            "username": "admin",
            "password": "admin123",
            "name": "Rajesh Sharma",
            "department": "All",
            "description": "Full access to infrastructure, resources, parameters and system administration"
        },
        {
            "role": "OPERATIONS_OFFICER",
            "title": "Railway Operations Officer",
            "username": "ops_officer",
            "password": "ops123",
            "name": "Amitabh Verma",
            "department": "Operations",
            "description": "Reviews train timetables, approves/rejects CP-SAT blocks, and triggers disruption replanning"
        },
        {
            "role": "DEPARTMENT_OFFICER",
            "title": "Engineering Officer",
            "username": "engg_officer",
            "password": "engg123",
            "name": "Suresh Chandra",
            "department": "Engineering",
            "description": "Submits track maintenance requests, tracks Gang/BCM/Tamping machine readiness"
        },
        {
            "role": "DEPARTMENT_OFFICER",
            "title": "TRD Officer (Electrical)",
            "username": "trd_officer",
            "password": "trd123",
            "name": "Deepak Khurana",
            "department": "TRD",
            "description": "Submits 25kV OHE traction & tower wagon maintenance requests"
        },
        {
            "role": "DEPARTMENT_OFFICER",
            "title": "S&T Officer (Signaling)",
            "username": "st_officer",
            "password": "st123",
            "name": "Pooja Singhania",
            "department": "S&T",
            "description": "Submits Point Machine, Interlocking & KAVACH ATP maintenance requests"
        }
    ]
