import sys
print("Step 1: Importing database models...", flush=True)
from app.database import Base, engine, SessionLocal
from app.models import *

print("Step 2: Creating tables...", flush=True)
Base.metadata.create_all(bind=engine)

print("Step 3: Seeding database...", flush=True)
from app.seed.demo_data import seed_database
db = SessionLocal()
try:
    seed_database(db)
    print("Step 4: Seeding finished successfully!", flush=True)
finally:
    db.close()
