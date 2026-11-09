from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from sqlalchemy import inspect, text

from app.config import settings, warn_if_default_secret_key
from app.database import engine, Base, SessionLocal
from app.seed.demo_data import seed_database
from app.models.work_package import WorkPackage

def ensure_readiness_columns(database_engine=engine) -> None:
    clear_legacy_readiness_scores = False
    column_additions = {
        "maintenance_requests": {"obtained_safety_requirements": "TEXT"},
        "maintenance_blocks": {
            "readiness_verdict": "VARCHAR(30)",
            "readiness_snapshot": "TEXT",
            "work_package_id": "INTEGER",
        },
        "disruptions": {
            "schedule_snapshot": "TEXT",
            "replan_diff": "TEXT",
        },
    }
    with database_engine.begin() as connection:
        inspector = inspect(connection)
        existing_tables = set(inspector.get_table_names())
        for table_name, columns in column_additions.items():
            if table_name not in existing_tables:
                continue
            existing_columns = {
                column["name"] for column in inspector.get_columns(table_name)
            }
            for column_name, column_type in columns.items():
                if column_name not in existing_columns:
                    if (
                        table_name == "maintenance_requests"
                        and column_name == "obtained_safety_requirements"
                    ):
                        clear_legacy_readiness_scores = True
                    connection.execute(text(
                        f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"
                    ))
                    existing_columns.add(column_name)
        request_columns = {
            column["name"]
            for column in inspector.get_columns("maintenance_requests")
        }
        if clear_legacy_readiness_scores and "readiness_score" in request_columns:
            connection.execute(text(
                "UPDATE maintenance_requests SET readiness_score = NULL "
                "WHERE readiness_score IS NOT NULL"
            ))

# Routers
from app.routers import (
    auth,
    dashboard,
    requests,
    resources,
    sections,
    trains,
    optimization,
    disruptions,
    admin
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    warn_if_default_secret_key()

    initialize_database()
    yield


def initialize_database() -> None:
    """Create missing tables/columns and seed a new database."""
    Base.metadata.create_all(bind=engine)
    ensure_readiness_columns()

    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()

app = FastAPI(
    title="RailBlockSetu - Intelligent Railway Maintenance Platform",
    description="Decision-support system for integrated railway maintenance planning, resource validation, CP-SAT optimization and disruption replanning.",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers under /api/v1
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(dashboard.router, prefix=settings.API_V1_STR)
app.include_router(requests.router, prefix=settings.API_V1_STR)
app.include_router(resources.router, prefix=settings.API_V1_STR)
app.include_router(sections.router, prefix=settings.API_V1_STR)
app.include_router(trains.router, prefix=settings.API_V1_STR)
app.include_router(optimization.router, prefix=settings.API_V1_STR)
app.include_router(disruptions.router, prefix=settings.API_V1_STR)
app.include_router(admin.router, prefix=settings.API_V1_STR)

@app.get("/")
def root():
    return {
        "platform": "RailBlockSetu",
        "category": "AI / Smart Infrastructure",
        "event": "NOVEX 2026",
        "status": "OPERATIONAL",
        "docs_url": "/docs"
    }

@app.get("/api/health")
def health_check():
    return {"status": "HEALTHY", "engine": "Google OR-Tools CP-SAT + Scikit-Learn"}
