from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import settings
from app.database import Base
from app.models.request import MaintenanceRequest, RequestStatus
from app.models.resource import Resource, ResourceType
from app.models.section import RailwaySection
from app.models.train import TrainSchedule, TrainType
from app.optimization.scheduler import optimizer_scheduler
from app.optimization.train_windows import build_train_intervals


IST = ZoneInfo("Asia/Kolkata")


@pytest.fixture
def db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    test_session = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = test_session()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


def add_section(db):
    section = RailwaySection(
        section_code="TEST-TRAIN-SECTION",
        section_name="Test Train Section",
        start_km=0,
        end_km=10,
    )
    db.add(section)
    db.flush()
    db.add(Resource(
        resource_type=ResourceType.STAFF,
        name="Engineering test crew",
        code=f"CREW-{section.id}",
        department="Engineering",
        total_quantity=10,
        available_quantity=10,
        base_station="Test depot",
    ))
    db.flush()
    return section


def add_train(db, section, entry, exit_time, priority=1):
    train = TrainSchedule(
        train_number=f"TEST-{entry.replace(':', '')}-{priority}",
        train_name="Test Train",
        train_type=TrainType.VANDE_BHARAT if priority <= 2 else TrainType.FREIGHT,
        origin="Origin",
        destination="Destination",
        priority_level=priority,
        section_id=section.id,
        scheduled_entry_time=entry,
        scheduled_exit_time=exit_time,
        current_status="ON_TIME",
    )
    db.add(train)
    db.flush()
    return train


def add_request(db, section, duration_hours, deadline_hours=48):
    now = datetime.now(IST).replace(tzinfo=None)
    request = MaintenanceRequest(
        request_id=f"REQ-{section.id}-{duration_hours}",
        task_title="Test scheduled maintenance",
        description="Test train occupancy constraint",
        department="Engineering",
        railway_division="Delhi",
        railway_section=section.section_code,
        section_id=section.id,
        asset_id="TEST-ASSET",
        required_start_date=now,
        deadline=now + timedelta(hours=deadline_hours),
        estimated_duration=duration_hours,
        required_staff=1,
        required_machinery="[]",
        task_dependencies="[]",
        current_status=RequestStatus.SUBMITTED,
    )
    db.add(request)
    db.commit()
    db.refresh(request)
    return request


def test_scheduled_task_avoids_buffered_protected_train(db):
    section = add_section(db)
    add_train(db, section, "00:00", "21:30", priority=1)
    add_request(db, section, duration_hours=2)
    base_time = datetime.now(IST).replace(
        tzinfo=None, minute=0, second=0, microsecond=0
    )

    result = optimizer_scheduler.run_optimization(db, horizon_hours=48)

    assert result["blocks_scheduled"] == 1
    assert result["train_intervals_checked"] > 0
    block = result["schedule"][0]
    assert block["train_conflicts"] == 0
    start = datetime.fromisoformat(block["scheduled_start"])
    end = datetime.fromisoformat(block["scheduled_end"])
    start_minute = int((start - base_time).total_seconds() // 60)
    end_minute = int((end - base_time).total_seconds() // 60)
    train_intervals = build_train_intervals(
        db.query(TrainSchedule).all(),
        base_time,
        48 * 60,
        settings.TRAIN_BUFFER_MINUTES,
    )

    assert all(
        start_minute >= interval.end_minute
        or end_minute <= interval.start_minute
        for interval in train_intervals
    )


def test_task_with_no_train_free_gap_is_returned_as_unscheduled(db):
    section = add_section(db)
    add_train(db, section, "00:00", "23:55", priority=2)
    request = add_request(db, section, duration_hours=1, deadline_hours=24)

    result = optimizer_scheduler.run_optimization(db, horizon_hours=24)

    assert result["blocks_scheduled"] == 0
    assert result["unscheduled"] == [
        {
            "request_id": request.id,
            "task_title": request.task_title,
            "reason": (
                "no train-free gap of 60 minutes on section "
                f"{section.section_code} within its deadline"
            ),
        }
    ]


def test_soft_train_overlap_is_penalized_not_forbidden(db):
    section = add_section(db)
    add_train(db, section, "00:00", "23:55", priority=5)
    add_request(db, section, duration_hours=1, deadline_hours=2)

    result = optimizer_scheduler.run_optimization(db, horizon_hours=2)

    assert result["blocks_scheduled"] == 1
    assert result["schedule"][0]["train_conflicts"] == 0
