from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.section import RailwaySection

router = APIRouter(prefix="/sections", tags=["Railway Sections & Infrastructure"])

@router.get("")
def get_all_sections(db: Session = Depends(get_db)):
    return db.query(RailwaySection).all()
