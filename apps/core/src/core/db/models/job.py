from typing import TYPE_CHECKING, Any, Dict, List
from uuid import UUID

from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as UUID_PG
from sqlmodel import ARRAY, Boolean, Column, Field, ForeignKey, Relationship, Text, text

from core.core.config import settings
from core.schemas.job import JobStatusType, JobType

from ._base_class import DateTimeBase

if TYPE_CHECKING:
    from .user import User


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
        )
    )
    user_id: UUID = Field(
        sa_column=Column(
            UUID_PG(as_uuid=True),
            ForeignKey(f"{settings.ACCOUNTS_SCHEMA}.user.id", ondelete="CASCADE"),
            nullable=False,
        ),
        description="User ID of the user who created the job",
    )
    project_id: UUID | None = Field(
        default=None,
        sa_column=Column(UUID_PG(as_uuid=True), nullable=True),
        description="Project ID of the project the job belongs to",
    )
    type: JobType = Field(
        sa_column=Column(Text, nullable=False), description="Type of the job"
    )
    layer_ids: List[UUID] | None = Field(
        default=None,
        sa_column=Column(
            ARRAY(UUID_PG()),
            nullable=True,
            index=True,
        ),
        description="Layer IDs that are produced by the job",
    )
    status: Dict[str, Any] = Field(
        sa_column=Column(JSONB, nullable=False), description="Status of the job"
    )
    status_simple: JobStatusType = Field(
        sa_column=Column(Text, nullable=False, index=True),
        description="Simple status of the job",
    )
    msg_simple: str | None = Field(
        default=None,
        sa_column=Column(Text, nullable=True), description="Simple message of the job"
    )
    read: bool | None = Field(
        default=False,
        sa_column=Column(Boolean, nullable=False, server_default="False"),
        description="Whether the user has marked the job as read",
    )
    payload: Dict[str, Any] | None = Field(
        default=None,
        sa_column=Column(JSONB, nullable=True), description="Payload of the job"
    )

    # Relationships
    user: "User" = Relationship(back_populates="jobs")
