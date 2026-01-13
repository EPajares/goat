from enum import Enum
from typing import TYPE_CHECKING, Any, Dict
from uuid import UUID

from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as UUID_PG
from sqlmodel import Column, Field, ForeignKey, Relationship, Text, text

from core.core.config import settings

from ._base_class import DateTimeBase

if TYPE_CHECKING:
    from .user import User


class JobStatusType(str, Enum):
    """Job status types."""

    accepted = "accepted"
    running = "running"
    successful = "successful"
    failed = "failed"
    dismissed = "dismissed"


class Job(DateTimeBase, table=True):
    """Analysis Request model."""

    __tablename__ = "job"
    __table_args__ = {"schema": settings.CUSTOMER_SCHEMA}

    id: UUID | None = Field(
        default=None,
        sa_column=Column(
            UUID_PG(as_uuid=True),
            primary_key=True,
            nullable=False,
            server_default=text("uuid_generate_v4()"),
        ),
    )
    user_id: UUID = Field(
        sa_column=Column(
            UUID_PG(as_uuid=True),
            ForeignKey(f"{settings.ACCOUNTS_SCHEMA}.user.id", ondelete="CASCADE"),
            nullable=False,
        ),
        description="User ID of the user who created the job",
    )
    type: str = Field(
        sa_column=Column(Text, nullable=False),
        description="Type of the job (e.g., file_import, buffer, clip)",
    )
    status: JobStatusType = Field(
        sa_column=Column(Text, nullable=False, index=True),
        description="Simple status of the job",
    )
    payload: Dict[str, Any] | None = Field(
        default=None,
        sa_column=Column(JSONB, nullable=True),
        description="Payload of the job",
    )

    # Relationships
    user: "User" = Relationship(back_populates="jobs")
