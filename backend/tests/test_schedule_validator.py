from datetime import datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models.request import MaintenanceRequest, RequestStatus
from app.models.schedule import BlockStatus, MaintenanceBlock
from app.models.section import RailwaySection
from app.optimization.validator import refresh_schedule_validation, validate_schedule
from app.routers.dashboard import get_dashboard_metrics


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


def _add_block(db, section, request_code, start, end):
    request = MaintenanceRequest(
        request_id=request_code,
        task_title=f"Test work {request_code}",
        description="Schedule validation test",
        department="Engineering",
        railway_section=section.section_code,
        section_id=section.id,
        asset_id=f"ASSET-{request_code}",
        required_start_date=start,
        deadline=end + timedelta(hours=2),
        estimated_duration=1,
        required_staff=0,
        current_status=RequestStatus.OPTIMIZED,
    )
    db.add(request)
    db.flush()
    block = MaintenanceBlock(
        block_code=f"BLOCK-{request_code}",
        request_id=request.id,
        section_id=section.id,
        scheduled_start=start,
        scheduled_end=end,
        duration_hours=1,
        status=BlockStatus.PROPOSED,
    )
    db.add(block)
    db.flush()
    return block


@pytest.fixture
def section(db):
    item = RailwaySection(
        section_code="VALIDATOR-SECTION",
        section_name="Validator Test Section",
        start_km=0,
        end_km=10,
    )
    db.add(item)
    db.flush()
    return item


def test_dashboard_counts_overlapping_blocks_from_validator(db, section):
    start = datetime.now().replace(second=0, microsecond=0) + timedelta(hours=1)
    first = _add_block(db, section, "REQ-OVERLAP-A", start, start + timedelta(hours=1))
    _add_block(
        db,
        section,
        "REQ-OVERLAP-B",
        start + timedelta(minutes=30),
        start + timedelta(minutes=90),
    )
    db.commit()

    metrics = get_dashboard_metrics(db)

    assert metrics["current_scheduling_conflicts"] == 1
    assert first.conflict_detected is True
    assert '"section_overlap"' in first.conflict_details


def test_dashboard_reports_zero_conflicts_for_clean_schedule(db, section):
    start = datetime.now().replace(second=0, microsecond=0) + timedelta(hours=1)
    _add_block(db, section, "REQ-CLEAN-A", start, start + timedelta(hours=1))
    _add_block(
        db,
        section,
        "REQ-CLEAN-B",
        start + timedelta(hours=2),
        start + timedelta(hours=3),
    )
    db.commit()

    metrics = get_dashboard_metrics(db)

    assert metrics["current_scheduling_conflicts"] == 0
    assert validate_schedule(
        db.query(MaintenanceBlock).all(), db
    ) == []
