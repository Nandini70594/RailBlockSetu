import json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models.audit import AuditLog
from app.models.disruption import (
    Disruption,
    DisruptionSeverity,
    DisruptionType,
)
from app.models.request import MaintenanceRequest, RequestStatus
from app.models.resource import Resource, ResourceType
from app.models.schedule import BlockStatus, MaintenanceBlock
from app.models.section import RailwaySection
from app.optimization.replanner import disruption_replanner


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


def test_replan_moves_only_affected_block_and_returns_persisted_diff(db):
    base = datetime.now(IST).replace(
        tzinfo=None, minute=0, second=0, microsecond=0
    ) + timedelta(hours=1)
    section = RailwaySection(
        section_code="REPLAN-SECTION",
        section_name="Replan Stability Test Section",
        start_km=0,
        end_km=10,
    )
    db.add(section)
    db.flush()
    db.add(Resource(
        resource_type=ResourceType.STAFF,
        name="Engineering crew",
        code="REPLAN-ENG-CREW",
        department="Engineering",
        total_quantity=10,
        available_quantity=10,
        base_station="Replan depot",
        operational_status="READY",
    ))
    db.flush()

    requests = []
    blocks = []
    for index, start_offset in enumerate((60, 240), start=1):
        start = base + timedelta(minutes=start_offset)
        request = MaintenanceRequest(
            request_id=f"REQ-REPLAN-{index}",
            task_title=f"Maintenance task {index}",
            description="Replan stability test",
            department="Engineering",
            railway_division="Delhi",
            railway_section=section.section_code,
            section_id=section.id,
            asset_id=f"ASSET-{index}",
            required_start_date=base,
            deadline=base + timedelta(hours=24),
            estimated_duration=1,
            required_staff=1,
            required_machinery="[]",
            required_materials="[]",
            safety_requirements="[]",
            obtained_safety_requirements="[]",
            task_dependencies="[]",
            current_status=RequestStatus.APPROVED,
        )
        db.add(request)
        db.flush()
        block = MaintenanceBlock(
            block_code=f"BLK-REPLAN-{index}",
            request_id=request.id,
            section_id=section.id,
            scheduled_start=start,
            scheduled_end=start + timedelta(hours=1),
            duration_hours=1,
            status=BlockStatus.APPROVED,
            is_pinned=True,
        )
        db.add(block)
        db.flush()
        requests.append(request)
        blocks.append(block)

    disruption = Disruption(
        disruption_code="DIS-REPLAN-TEST",
        title="Track incident",
        disruption_type=DisruptionType.TRACK_DEFECT,
        section_id=section.id,
        affected_from=base + timedelta(minutes=60),
        affected_until=base + timedelta(minutes=180),
        severity=DisruptionSeverity.HIGH,
        impact_description="Blocks the first task window.",
        is_active=True,
    )
    db.add(disruption)
    db.commit()
    db.refresh(disruption)

    result = disruption_replanner.execute_disruption_replan(disruption.id, db)

    db.refresh(disruption)
    stored_snapshot = json.loads(disruption.schedule_snapshot)
    stored_diff = json.loads(disruption.replan_diff)
    assert len(stored_snapshot) == 2
    assert result["snapshot"] == stored_snapshot
    assert result["diff"] == stored_diff
    assert stored_diff["summary"]["retained_count"] == 1
    assert stored_diff["summary"]["rescheduled_count"] == 1
    assert stored_diff["summary"]["newly_assigned_count"] == 0
    assert stored_diff["summary"]["unschedulable_count"] == 0

    db.refresh(blocks[0])
    db.refresh(blocks[1])
    first_before = next(
        item for item in stored_snapshot if item["block_id"] == blocks[0].id
    )
    assert blocks[0].scheduled_start != datetime.fromisoformat(
        first_before["start"]
    ) and (
        blocks[0].status == BlockStatus.PROPOSED
    )
    assert blocks[0].status != BlockStatus.APPROVED
    assert blocks[1].scheduled_start == datetime.fromisoformat(
        next(item for item in stored_snapshot if item["block_id"] == blocks[1].id)["start"]
    )
    assert blocks[1].status == BlockStatus.APPROVED

    active_blocks = db.query(MaintenanceBlock).filter(
        MaintenanceBlock.status.in_([
            BlockStatus.PROPOSED,
            BlockStatus.APPROVED,
            BlockStatus.IN_PROGRESS,
        ])
    ).all()
    assert len(stored_diff["retained"]) == sum(
        1 for block in active_blocks
        if block.status == BlockStatus.APPROVED
    )
    assert len(stored_diff["rescheduled"]) == sum(
        1 for block in active_blocks
        if block.status == BlockStatus.PROPOSED
    )
    audit = db.query(AuditLog).filter(
        AuditLog.action == "TRIGGER_REPLAN"
    ).one()
    assert json.loads(audit.details)["diff"] == stored_diff
