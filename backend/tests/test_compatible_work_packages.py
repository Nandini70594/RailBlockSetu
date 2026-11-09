import json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models.request import MaintenanceRequest, RequestStatus
from app.models.resource import Resource, ResourceType
from app.models.schedule import MaintenanceBlock
from app.models.section import RailwaySection
from app.optimization.compatibility import are_compatible
from app.optimization.scheduler import optimizer_scheduler
from app.routers.optimization import get_work_packages


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


@pytest.fixture
def section(db):
    item = RailwaySection(
        section_code="PACKAGE-SECTION",
        section_name="Work Package Test Section",
        start_km=0,
        end_km=10,
    )
    db.add(item)
    db.flush()
    return item


def add_resource(db, section, department, resource_type, code, name=None):
    resource = Resource(
        resource_type=resource_type,
        name=name or code,
        code=f"{code}-{department}",
        department=department,
        total_quantity=20 if resource_type == ResourceType.STAFF else 1,
        available_quantity=20 if resource_type == ResourceType.STAFF else 1,
        base_station=f"{section.section_code} depot",
        operational_status="READY",
    )
    db.add(resource)
    db.flush()
    return resource


def add_task(
    db,
    section,
    department,
    code,
    title,
    machinery=None,
    description="Routine maintenance work",
):
    now = datetime.now(IST).replace(tzinfo=None)
    request = MaintenanceRequest(
        request_id=code,
        task_title=title,
        description=description,
        department=department,
        railway_division="Delhi",
        railway_section=section.section_code,
        section_id=section.id,
        asset_id=f"ASSET-{code}",
        required_start_date=now,
        deadline=now + timedelta(hours=12),
        estimated_duration=1,
        required_staff=1,
        required_machinery=json.dumps(machinery or []),
        required_materials="[]",
        safety_requirements="[]",
        obtained_safety_requirements="[]",
        task_dependencies="[]",
        current_status=RequestStatus.SUBMITTED,
    )
    db.add(request)
    db.flush()
    return request


def add_department_resources(db, section, departments):
    for department in departments:
        add_resource(
            db, section, department, ResourceType.STAFF, f"CREW-{department}"
        )


def test_compatible_cross_department_tasks_share_work_package(db, section):
    add_department_resources(db, section, ["Engineering", "S&T"])
    add_task(db, section, "Engineering", "REQ-WP-ENG", "Track inspection")
    add_task(db, section, "S&T", "REQ-WP-ST", "Signal inspection")
    db.commit()

    result = optimizer_scheduler.run_optimization(db, horizon_hours=12)

    assert result["blocks_scheduled"] == 2
    scheduled = result["schedule"]
    assert max(
        datetime.fromisoformat(block["scheduled_start"]) for block in scheduled
    ) < min(
        datetime.fromisoformat(block["scheduled_end"]) for block in scheduled
    )
    assert len(result["work_packages"]) == 1
    package = result["work_packages"][0]
    assert set(package["departments"]) == {"Engineering", "S&T"}
    assert package["compatibility_status"] == "COMPATIBLE"
    assert all(block["work_package_id"] == package["id"] for block in scheduled)
    assert all(
        block.work_package_id == package["id"]
        for block in db.query(MaintenanceBlock).all()
    )
    api_packages = get_work_packages(db)
    assert api_packages[0]["id"] == package["id"]
    assert len(api_packages[0]["tasks"]) == 2


def test_tasks_requiring_same_machine_are_not_overlapped(db, section):
    add_department_resources(db, section, ["Engineering"])
    add_resource(
        db, section, "Engineering", ResourceType.MACHINERY, "SHARED-CRANE"
    )
    add_task(
        db, section, "Engineering", "REQ-SAME-MACHINE-A", "Crane task A",
        machinery=["SHARED-CRANE-Engineering"],
    )
    add_task(
        db, section, "Engineering", "REQ-SAME-MACHINE-B", "Crane task B",
        machinery=["SHARED-CRANE-Engineering"],
    )
    db.commit()

    result = optimizer_scheduler.run_optimization(db, horizon_hours=12)

    assert result["blocks_scheduled"] == 2
    blocks = [
        (datetime.fromisoformat(item["scheduled_start"]),
         datetime.fromisoformat(item["scheduled_end"]))
        for item in result["schedule"]
    ]
    assert blocks[0][1] <= blocks[1][0] or blocks[1][1] <= blocks[0][0]


def test_heavy_machine_and_live_ohe_without_isolation_do_not_share(db, section):
    add_department_resources(db, section, ["Engineering", "TRD"])
    add_resource(db, section, "Engineering", ResourceType.MACHINERY, "CSM-952")
    heavy_task = add_task(
        db,
        section,
        "Engineering",
        "REQ-HEAVY-MACHINE",
        "Track maintenance",
        machinery=["CSM-952-Engineering"],
    )
    live_ohe_task = add_task(
        db,
        section,
        "TRD",
        "REQ-LIVE-OHE",
        "Live OHE inspection",
    )
    compatible, reason = are_compatible(heavy_task, live_ohe_task)
    assert not compatible
    assert "power isolation" in reason
    db.commit()

    result = optimizer_scheduler.run_optimization(db, horizon_hours=12)

    assert result["blocks_scheduled"] == 2
    blocks = [
        (datetime.fromisoformat(item["scheduled_start"]),
         datetime.fromisoformat(item["scheduled_end"]))
        for item in result["schedule"]
    ]
    assert blocks[0][1] <= blocks[1][0] or blocks[1][1] <= blocks[0][0]
    assert result["work_packages"] == []
