import os
from pydantic import BaseModel
from typing import Any, Dict, List
from dotenv import load_dotenv

load_dotenv()

DEVELOPMENT_SECRET_KEY = "railblocksetu-ultra-secure-secret-key-2026-novex"

def get_database_url() -> str:
    database_url = os.getenv("DATABASE_URL", "sqlite:///./railblocksetu.db")
    if database_url.startswith("postgres://"):
        return database_url.replace("postgres://", "postgresql+psycopg://", 1)
    if database_url.startswith("postgresql://"):
        return database_url.replace("postgresql://", "postgresql+psycopg://", 1)
    return database_url

class Settings(BaseModel):
    PROJECT_NAME: str = "RailBlockSetu"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = os.getenv("SECRET_KEY") or DEVELOPMENT_SECRET_KEY
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    # SQLite default with PostgreSQL compatibility
    DATABASE_URL: str = get_database_url()
    
    # Optimization settings
    DEFAULT_SLOT_DURATION_MINUTES: int = 30
    DEFAULT_PLANNING_HORIZON_DAYS: int = 7
    DISRUPTION_PENALTY_WEIGHT: int = 150
    UNSCHEDULED_PENALTY_WEIGHT: int = 1000
    TRAIN_BUFFER_MINUTES: int = int(os.getenv("TRAIN_BUFFER_MINUTES", "10"))
    MIN_USEFUL_WINDOW_MINUTES: int = int(
        os.getenv("MIN_USEFUL_WINDOW_MINUTES", "30")
    )
    TRAIN_SOFT_PENALTY_WEIGHT: int = int(
        os.getenv("TRAIN_SOFT_PENALTY_WEIGHT", "1000000")
    )
    COMPATIBILITY_OVERLAP_BONUS_WEIGHT: int = int(
        os.getenv("COMPATIBILITY_OVERLAP_BONUS_WEIGHT", "10000")
    )
    REPLAN_MOVE_MINUTE_PENALTY: int = int(
        os.getenv("REPLAN_MOVE_MINUTE_PENALTY", "1000")
    )
    REPLAN_MOVE_FIXED_PENALTY: int = int(
        os.getenv("REPLAN_MOVE_FIXED_PENALTY", "100000")
    )
    REPLAN_UNAFFECTED_APPROVED_MOVE_PENALTY: int = int(
        os.getenv("REPLAN_UNAFFECTED_APPROVED_MOVE_PENALTY", "100000000")
    )
    # These compatibility assumptions require validation by railway domain experts.
    COMPATIBILITY_RULES: Dict[str, Any] = {
        "require_different_departments": True,
        "require_same_section": True,
        "exclusive_flags": ["exclusive", "exclusive_section", "exclusive_possession"],
        "exclusive_terms": ["exclusive possession", "exclusive block"],
        "heavy_machine_tokens": ["csm", "bcm"],
        "trd_department": "TRD",
        "live_ohe_tokens": ["live ohe", "ohe live", "energized ohe"],
        "power_isolation_tokens": ["power isolation", "power block", "ohe isolation"],
        "department_crew_limits": {
            "Engineering": 35,
            "TRD": 25,
            "S&T": 20,
        },
        "default_crew_limit": 30,
    }
    READINESS_MANDATORY_PILLARS: List[str] = os.getenv(
        "READINESS_MANDATORY_PILLARS",
        "staff,machinery,materials,traffic_window,safety_isolation",
    ).split(",")

settings = Settings()

def warn_if_default_secret_key() -> None:
    if settings.SECRET_KEY == DEVELOPMENT_SECRET_KEY:
        print(
            "!!! SECURITY WARNING: SECRET_KEY is unset or uses the default development key. "
            "Set a unique SECRET_KEY environment variable before deployment. !!!",
            flush=True,
        )
