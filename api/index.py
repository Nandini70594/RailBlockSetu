"""Vercel entry point for the RailBlockSetu FastAPI application."""

from pathlib import Path
import sys

backend_directory = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(backend_directory))

from app.main import app, initialize_database

# Vercel's Python runtime can invoke the ASGI app without sending a lifespan
# event. Keep schema initialization available for that entry point as well.
initialize_database()

__all__ = ["app"]
