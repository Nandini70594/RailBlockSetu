import json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models.request import MaintenanceRequest, RequestStatus
from app.models.resource import Resource, ResourceType
from app.models.schedule import MaintenanceBlock
from app.models.section import RailwaySection
from app.optimization.scheduler import optimizer_scheduler
from app.optimization.readiness import readiness_validator
from app.main import ensure_readiness_columns
from app.routers.optimization import get_all_blocks


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


def create_section(db):
    section = RailwaySection(
        section_code="READINESS-SECTION",
        section_name="Readiness Test Section",
        start_km=0,
        end_km=10,
    )
    db.add(section)
    db.flush()
    return section


def add_resource(
    db,
    resource_type,
    name,
    code,
    department="Engineering",
    available=1,
    total=1,
    status="READY",
):
    resource = Resource(
        resource_type=resource_type,
        name=name,
        code=code,
        department=department,
        total_quantity=total,
        available_quantity=available,
        operational_status=status,
        base_station="Test Depot",
    )
    db.add(resource)
    db.flush()
    return resource


def create_request(
    db,
    section,
    machines="[]",
    materials="[]",
    safety="[]",
    obtained="[]",
):
    now = datetime.now(IST).replace(tzinfo=None)
    request = MaintenanceRequest(
        request_id="REQ-READINESS-1",
        task_title="Replace track equipment",
        description="Readiness test maintenance",
        department="Engineering",
        railway_division="Delhi",
        railway_section=section.section_code,
        section_id=section.id,
        asset_id="TRACK-1",
        required_start_date=now,
        deadline=now + timedelta(hours=24),
        estimated_duration=2,
        required_staff=4,
        required_machinery=machines,
        required_materials=materials,
        safety_requirements=safety,
        obtained_safety_requirements=obtained,
        task_dependencies="[]",
        current_status=RequestStatus.SUBMITTED,
    )
    db.add(request)
    db.commit()
    db.refresh(request)
    return request


def add_crew(db):
    add_resource(
        db, ResourceType.STAFF, "Engineering crew", "CREW-ENG",
        available=8, total=8,
    )


def test_machine_under_maintenance_excludes_request_with_reason(db):
    section = create_section(db)
    add_crew(db)
    add_resource(
        db,
        ResourceType.MACHINERY,
        "Track Tamping Machine",
        "TAMPER-42",
        status="UNDER_MAINTENANCE",
        available=0,
    )
    request = create_request(db, section, machines='["TAMPER-42"]')

    result = optimizer_scheduler.run_optimization(db, horizon_hours=24)

    assert result["blocks_scheduled"] == 0
    assert len(result["excluded"]) == 1
    excluded = result["excluded"][0]
    assert excluded["request_id"] == request.id
    assert "machinery" in excluded["failing_pillars"]
    assert "TAMPER-42" in excluded["recommended_action"]


def test_available_resources_allow_schedule_and_save_readiness_snapshot(db):
    section = create_section(db)
    add_crew(db)
    add_resource(
        db, ResourceType.MACHINERY, "Track Tamping Machine", "TAMPER-42"
    )
    add_resource(
        db, ResourceType.MATERIAL, "Track Bolt", "BOLT-7",
        available=20, total=20,
    )
    request = create_request(
        db,
        section,
        machines='["TAMPER-42"]',
        materials='["BOLT-7"]',
    )

    result = optimizer_scheduler.run_optimization(db, horizon_hours=24)

    assert result["blocks_scheduled"] == 1
    block_result = result["schedule"][0]
    assert block_result["readiness_verdict"] == "READY"
    saved_block = db.query(MaintenanceBlock).filter_by(
        request_id=request.id
    ).one()
    snapshot = json.loads(saved_block.readiness_snapshot)
    api_block = get_all_blocks(db=db)[0]
    assert snapshot["verdict"] == "READY"
    assert saved_block.readiness_verdict == "READY"
    assert api_block.readiness_verdict == "READY"
    assert api_block.readiness_snapshot["verdict"] == "READY"


def test_pending_safety_clearance_yields_partial_verdict_and_is_kept_on_block(db):
    section = create_section(db)
    add_crew(db)
    request = create_request(
        db,
        section,
        safety='["Track possession permit"]',
        obtained="[]",
    )

    readiness = readiness_validator.validate_request_readiness(request, db)
    result = optimizer_scheduler.run_optimization(db, horizon_hours=24)

    assert readiness["verdict"] == "PARTIALLY_READY"
    assert readiness["pillars"]["safety_isolation"]["status"] == "PENDING"
    assert result["blocks_scheduled"] == 1
    assert result["schedule"][0]["readiness_verdict"] == "PARTIALLY_READY"


def test_missing_crew_record_is_not_assumed_available(db):
    section = create_section(db)
    request = create_request(db, section)

    readiness = readiness_validator.validate_request_readiness(request, db)

    assert readiness["pillars"]["staff"]["status"] == "FAILED"
    assert readiness["pillars"]["staff"]["available"] is None
    assert "No crew record found" in readiness["pillars"]["staff"]["notes"]
    assert readiness["overall_readiness_score"] is None


def test_machine_identifier_requires_an_exact_match(db):
    section = create_section(db)
    add_crew(db)
    add_resource(
        db, ResourceType.MACHINERY, "Track Tamping Machine", "TAMPER-42"
    )
    request = create_request(db, section, machines='["TAMPER"]')

    readiness = readiness_validator.validate_request_readiness(request, db)

    assert readiness["pillars"]["machinery"]["status"] == "FAILED"
    assert "No exact machine record found" in (
        readiness["pillars"]["machinery"]["reasons"][0]
    )


def test_mandatory_pillars_can_be_configured(db, monkeypatch):
    section = create_section(db)
    add_crew(db)
    request = create_request(
        db,
        section,
        safety='["Track possession permit"]',
        obtained="[]",
    )
    monkeypatch.setattr(
        "app.optimization.readiness.settings.READINESS_MANDATORY_PILLARS",
        ["staff", "machinery", "materials", "traffic_window"],
    )

    readiness = readiness_validator.validate_request_readiness(request, db)

    assert readiness["pillars"]["safety_isolation"]["status"] == "PENDING"
    assert readiness["verdict"] == "READY"


def test_readiness_migration_adds_columns_to_existing_database():
    engine = create_engine("sqlite://")
    with engine.begin() as connection:
        connection.exec_driver_sql(
            "CREATE TABLE maintenance_requests "
            "(id INTEGER PRIMARY KEY, readiness_score REAL)"
        )
        connection.exec_driver_sql(
            "CREATE TABLE maintenance_blocks (id INTEGER PRIMARY KEY)"
        )
        connection.exec_driver_sql(
            "CREATE TABLE disruptions (id INTEGER PRIMARY KEY)"
        )
        connection.exec_driver_sql(
            "INSERT INTO maintenance_requests (readiness_score) VALUES (85.0)"
        )

    ensure_readiness_columns(engine)

    inspector = inspect(engine)
    assert "obtained_safety_requirements" in {
        column["name"] for column in inspector.get_columns("maintenance_requests")
    }
    assert {"readiness_verdict", "readiness_snapshot"} <= {
        column["name"] for column in inspector.get_columns("maintenance_blocks")
    }
    assert {"schedule_snapshot", "replan_diff"} <= {
        column["name"] for column in inspector.get_columns("disruptions")
    }
    with engine.connect() as connection:
        assert connection.exec_driver_sql(
            "SELECT readiness_score FROM maintenance_requests"
        ).scalar_one() is None
    engine.dispose()
