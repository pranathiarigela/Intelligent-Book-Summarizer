# utils/database_sqlalchemy.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from logging_config import DB_PATH  # assumes you have config.py as discussed earlier
from pathlib import Path
from .models import Base

DB_URL = f"sqlite:///{DB_PATH}"

# create data dir if missing
Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)

# echo=False in production; True helpful during debugging
engine = create_engine(DB_URL, connect_args={"check_same_thread": False}, echo=False, future=True)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

def create_tables():
    # create all tables from models
    Base.metadata.create_all(bind=engine)
