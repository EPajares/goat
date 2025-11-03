from enum import Enum
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.dialects.postgresql import UUID as UUID_PG
from sqlmodel import Column, Field, SQLModel, Text

from core.core.config import settings


class StatusType(str, Enum):
    """Layer types that are supported."""

    running = "running"
    maintenance = "maintenance"


class Status(SQLModel, table=True):
    __tablename__ = "status"
    __table_args__ = {"schema": settings.CUSTOMER_SCHEMA}

    id: UUID | None = Field(
        sa_column=Column(
            UUID_PG(as_uuid=True),
            primary_key=True,
            nullable=False,
            server_default=text("uuid_generate_v4()"),
        )
    )
    status: StatusType = Field(sa_column=Column(Text, nullable=False))
