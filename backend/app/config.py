import os
from pydantic import BaseModel

class Settings(BaseModel):
    PROJECT_NAME: str = "RailBlockSetu"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "railblocksetu-ultra-secure-secret-key-2026-novex")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    # SQLite default with PostgreSQL compatibility
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./railblocksetu.db")
    
    # Optimization settings
    DEFAULT_SLOT_DURATION_MINUTES: int = 30
    DEFAULT_PLANNING_HORIZON_DAYS: int = 7
    DISRUPTION_PENALTY_WEIGHT: int = 150
    UNSCHEDULED_PENALTY_WEIGHT: int = 1000

settings = Settings()
