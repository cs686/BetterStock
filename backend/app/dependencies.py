"""Reusable dependencies for FastAPI routes."""
from __future__ import annotations

from typing import Generator

from fastapi import Depends
from sqlalchemy.orm import Session

from .database import SessionLocal


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
