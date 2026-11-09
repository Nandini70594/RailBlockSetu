from fastapi import APIRouter, Depends, Depends
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.section import RailwaySection
from app.utils.security import get_current_user

router = APIRouter(
    prefix="/sections",
    tags=["Railway Sections & Infrastructure"],
    dependencies=[Depends(get_current_user)],
)

@router.get("")
def get_all_sections(db: Session = Depends(get_db)):
    return db.query(RailwaySection).all()
