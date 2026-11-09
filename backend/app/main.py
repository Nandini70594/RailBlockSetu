from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings, warn_if_default_secret_key
from app.database import engine, Base, SessionLocal
from app.seed.demo_data import seed_database

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

    # Initialize database tables
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()
    yield

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
