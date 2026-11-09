from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db, Base, engine
from app.models.user import User, UserRole
from app.schemas.auth import UserResponse
from app.seed.demo_data import seed_database
from app.utils.security import require_roles
from typing import List

router = APIRouter(
    prefix="/admin",
    tags=["Admin & System Controls"],
    dependencies=[Depends(require_roles([UserRole.ADMIN]))],
)

@router.get("/users", response_model=List[UserResponse])
def get_users(db: Session = Depends(get_db)):
    return db.query(User).all()

@router.post("/reset-demo-data")
def reset_demo_data(db: Session = Depends(get_db)):
    """Reset database and re-seed clean realistic demo data"""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    seed_database(db)
    return {"message": "Database reset and successfully re-seeded with realistic Indian Railways demo data."}
