import os
import time
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy.exc import OperationalError

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://postgres:postgres@db:5432/app")

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

class Base(DeclarativeBase):
    pass

def wait_for_db(max_retries: int = 30, wait_seconds: int = 2):
    """
    DBが接続可能になるまで待つ
    """
    for i in range(max_retries):
        try:
            with engine.connect():
                print("✅ Database connection established")
                return
        except OperationalError:
            print(f"⏳ Waiting for DB... ({i + 1}/{max_retries})")
            time.sleep(wait_seconds)
    raise RuntimeError("❌ Database not available after waiting")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

