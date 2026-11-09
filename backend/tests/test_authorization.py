from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import DEVELOPMENT_SECRET_KEY, settings, warn_if_default_secret_key
from app.database import Base, get_db
from app.main import app
from app.models.request import MaintenanceRequest, RequestStatus
from app.models.schedule import BlockStatus, MaintenanceBlock
from app.models.section import RailwaySection
from app.models.user import DepartmentType, User, UserRole
from app.utils.security import create_access_token, get_password_hash


@pytest.fixture
def api():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    test_session = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    def override_get_db():
        db = test_session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    db = test_session()
    try:
        yield client, db
    finally:
        db.close()
        client.close()
        app.dependency_overrides.clear()
        engine.dispose()


def make_user(db, username, role, department):
    user = User(
        username=username,
        email=f"{username}@example.test",
        full_name=username,
        hashed_password=get_password_hash("test-password"),
        role=role,
        department=department,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def auth_headers(user):
    token = create_access_token({"sub": user.username})
    return {"Authorization": f"Bearer {token}"}


def make_request(db, section, department="TRD", current_status=RequestStatus.SUBMITTED):
    request = MaintenanceRequest(
        request_id=f"REQ-{department}-{current_status.value}",
        task_title="Inspect rail equipment",
        description="Routine maintenance inspection",
        department=department,
        railway_division="Delhi",
        railway_section=section.section_code,
        section_id=section.id,
        asset_id="ASSET-1",
        asset_type="Track",
        required_start_date=datetime.utcnow() + timedelta(hours=1),
        deadline=datetime.utcnow() + timedelta(days=2),
        estimated_duration=1.0,
        required_staff=4,
        current_status=current_status,
    )
    db.add(request)
    db.commit()
    db.refresh(request)
    return request


def make_section(db):
    section = RailwaySection(
        section_code="TEST-SECTION",
        section_name="Test railway section",
        start_km=0,
        end_km=10,
    )
    db.add(section)
    db.commit()
    db.refresh(section)
    return section


@pytest.mark.parametrize(
    "path",
    [
        "/api/v1/auth/me",
        "/api/v1/dashboard/metrics",
        "/api/v1/requests",
        "/api/v1/resources",
        "/api/v1/sections",
        "/api/v1/trains",
        "/api/v1/optimization/blocks",
        "/api/v1/disruptions",
        "/api/v1/admin/users",
    ],
)
def test_unauthenticated_get_endpoints_return_401(api, path):
    client, _ = api

    response = client.get(path)

    assert response.status_code == 401


def test_public_endpoints_remain_accessible(api):
    client, _ = api

    assert client.get("/").status_code == 200
    assert client.get("/api/health").status_code == 200
    assert client.get("/api/v1/auth/demo-credentials").status_code == 200


@pytest.mark.parametrize(
    "path,body",
    [
        ("/api/v1/optimization/run", {"horizon_hours": 72, "pinned_block_ids": []}),
        (
            "/api/v1/optimization/blocks/1/review",
            {"status": "APPROVED", "approval_notes": "reviewed"},
        ),
    ],
)
def test_department_officer_cannot_run_or_approve_blocks(api, path, body):
    client, db = api
    officer = make_user(
        db, "st_officer", UserRole.DEPARTMENT_OFFICER, DepartmentType.ST
    )

    response = client.post(path, json=body, headers=auth_headers(officer))

    assert response.status_code == 403
    assert "required role" in response.json()["detail"]


def test_engineering_officer_cannot_edit_trd_request(api):
    client, db = api
    officer = make_user(
        db, "engg_officer", UserRole.DEPARTMENT_OFFICER, DepartmentType.ENGINEERING
    )
    request = make_request(db, make_section(db), department="TRD")

    response = client.put(
        f"/api/v1/requests/{request.id}",
        json={"task_title": "Unauthorized edit"},
        headers=auth_headers(officer),
    )

    assert response.status_code == 403
    assert "own department" in response.json()["detail"]


def test_operations_officer_cannot_manage_resources_or_admin_routes(api):
    client, db = api
    officer = make_user(
        db, "ops_officer", UserRole.OPERATIONS_OFFICER, DepartmentType.OPERATIONS
    )
    headers = auth_headers(officer)
    resource = {
        "resource_type": "MACHINERY",
        "name": "Test machine",
        "code": "M-1",
        "department": "Engineering",
        "total_quantity": 1,
        "available_quantity": 1,
    }

    create_response = client.post(
        "/api/v1/resources", json=resource, headers=headers
    )
    update_response = client.put(
        "/api/v1/resources/1", json={"name": "Changed machine"}, headers=headers
    )
    admin_response = client.get("/api/v1/admin/users", headers=headers)

    assert create_response.status_code == 403
    assert update_response.status_code == 403
    assert admin_response.status_code == 403
    assert "required role" in admin_response.json()["detail"]


def test_department_officer_cannot_create_or_replan_disruptions(api):
    client, db = api
    officer = make_user(
        db, "engg_officer", UserRole.DEPARTMENT_OFFICER, DepartmentType.ENGINEERING
    )
    headers = auth_headers(officer)
    disruption = {
        "title": "Track obstruction",
        "disruption_type": "TRACK_DEFECT",
        "section_id": 1,
        "affected_from": datetime.utcnow().isoformat(),
        "affected_until": (datetime.utcnow() + timedelta(hours=1)).isoformat(),
        "severity": "HIGH",
        "impact_description": "Test disruption",
    }

    create_response = client.post(
        "/api/v1/disruptions", json=disruption, headers=headers
    )
    replan_response = client.post(
        "/api/v1/disruptions/1/replan", headers=headers
    )

    assert create_response.status_code == 403
    assert replan_response.status_code == 403


def test_ops_officer_can_approve_and_run_optimization(api, monkeypatch):
    client, db = api
    officer = make_user(
        db, "ops_officer", UserRole.OPERATIONS_OFFICER, DepartmentType.OPERATIONS
    )
    section = make_section(db)
    request = make_request(db, section)
    block = MaintenanceBlock(
        block_code="BLK-TEST-1",
        request_id=request.id,
        section_id=section.id,
        scheduled_start=datetime.utcnow(),
        scheduled_end=datetime.utcnow() + timedelta(hours=1),
        duration_hours=1,
        status=BlockStatus.PROPOSED,
    )
    db.add(block)
    db.commit()

    from app.routers import optimization

    monkeypatch.setattr(
        optimization.optimizer_scheduler,
        "run_optimization",
        lambda **kwargs: {"status": "OPTIMIZED", "blocks_scheduled": 1},
    )

    headers = auth_headers(officer)
    approve_response = client.post(
        f"/api/v1/optimization/blocks/{block.id}/review",
        json={"status": "APPROVED", "approval_notes": "Reviewed"},
        headers=headers,
    )
    run_response = client.post(
        "/api/v1/optimization/run",
        json={"horizon_hours": 72, "pinned_block_ids": []},
        headers=headers,
    )

    assert approve_response.status_code == 200
    assert run_response.status_code == 200
    assert run_response.json()["status"] == "OPTIMIZED"


def test_department_officer_can_only_edit_draft_or_submitted_own_requests(api):
    client, db = api
    officer = make_user(
        db, "trd_officer", UserRole.DEPARTMENT_OFFICER, DepartmentType.TRD
    )
    section = make_section(db)
    editable = make_request(db, section, department="TRD")
    locked = make_request(db, section, department="TRD", current_status=RequestStatus.OPTIMIZED)

    allowed = client.put(
        f"/api/v1/requests/{editable.id}",
        json={"task_title": "Updated inspection"},
        headers=auth_headers(officer),
    )
    denied = client.delete(
        f"/api/v1/requests/{locked.id}",
        headers=auth_headers(officer),
    )

    assert allowed.status_code == 200
    assert denied.status_code == 403
    assert "DRAFT or PENDING" in denied.json()["detail"]


def test_default_development_secret_key_emits_startup_warning(monkeypatch, capsys):
    monkeypatch.setattr(settings, "SECRET_KEY", DEVELOPMENT_SECRET_KEY)

    warn_if_default_secret_key()

    assert "SECURITY WARNING" in capsys.readouterr().out


def test_custom_secret_key_does_not_emit_startup_warning(monkeypatch, capsys):
    monkeypatch.setattr(settings, "SECRET_KEY", "test-only-custom-secret")

    warn_if_default_secret_key()

    assert capsys.readouterr().out == ""
