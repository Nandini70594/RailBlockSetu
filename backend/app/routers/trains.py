from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload
from typing import List

from app.database import get_db
from app.models.train import TrainSchedule
from app.models.schedule import MaintenanceBlock, BlockStatus
from app.utils.security import get_current_user

router = APIRouter(
    prefix="/trains",
    tags=["Train Schedules & Corridor Traffic"],
    dependencies=[Depends(get_current_user)],
)

@router.get("")
def get_train_schedules(db: Session = Depends(get_db)):
    trains = db.query(TrainSchedule).options(
        joinedload(TrainSchedule.section),
    ).all()
    results = []
    for t in trains:
        results.append({
            "id": t.id,
            "train_number": t.train_number,
            "train_name": t.train_name,
            "train_type": t.train_type.value,
            "origin": t.origin,
            "destination": t.destination,
            "priority_level": t.priority_level,
            "section_id": t.section_id,
            "section_code": t.section.section_code if t.section else "CORRIDOR",
            "entry_time": t.scheduled_entry_time,
            "exit_time": t.scheduled_exit_time,
            "typical_delay_minutes": t.typical_delay_minutes,
            "current_status": t.current_status
        })
    return results
