from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from settings import DB_URL

# Create the engine using the DB URL from .env
engine = create_engine(DB_URL, echo=False, future=True)

# Session factory for dependency injection in FastAPI
# Autoflush=False and autocommit=False give us explicit control.
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
