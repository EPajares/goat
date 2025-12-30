"""Database utilities for processes app.

Provides lightweight database access without importing core dependencies.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import Column, DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from lib.config import get_settings

Base = declarative_base()


class Job(Base):
    """Lightweight Job model for reading from core's job table.
    
    This mirrors core.db.models.job.Job but without all the dependencies.
    Only includes fields needed for OGC job status queries and writes.
    """

    __tablename__ = "job"
    __table_args__ = {"schema": "customer"}

    id = Column(PGUUID(as_uuid=True), primary_key=True)
    user_id = Column(PGUUID(as_uuid=True), nullable=False)
    type = Column(String(255))  # JobType enum value
    status = Column(String(50))  # JobStatusType enum value
    payload = Column(Text, nullable=True)  # JSON string
    created_at = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True))


async def get_async_session():
    """Create an async database session."""
    settings = get_settings()
    engine = create_async_engine(
        settings.ASYNC_POSTGRES_DATABASE_URI,
        echo=False,
    )
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    return engine, async_session
