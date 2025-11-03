from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID as UUID_PG
from sqlmodel import Column, DateTime, Field, SQLModel, text

from core.core.config import settings


class DateTimeBase(SQLModel):
    """Base class for models with created_at and updated_at fields."""

    updated_at: datetime | None = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={
            "onupdate": datetime.now(timezone.utc),
        },
        nullable=False,
    )
    created_at: datetime | None = Field(
        default=None,
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={
            "server_default": text(
                """to_char(CURRENT_TIMESTAMP AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SSOF')::timestamptz"""
            ),
        },
        nullable=False,
    )


class ContentBaseAttributes(SQLModel):
    """Base model for content attributes."""

    folder_id: UUID | None = Field(
        default=None,
        sa_column=Column(
            UUID_PG(as_uuid=True),
            ForeignKey(f"{settings.CUSTOMER_SCHEMA}.folder.id", ondelete="CASCADE"),
            nullable=False,
        ),
        description="Layer folder ID",
    )
    name: str | None = Field(
        default=None,
        sa_type=Text, description="Layer name", max_length=255, nullable=False
    )
    description: str | None = Field(
        default=None,
        sa_type=Text,
        description="Layer description",
        max_length=2000,
    )


content_base_example = {
    "folder_id": "c97b577f-7f8b-4713-8250-1518e189e822",
    "name": "Layer name",
    "description": "Layer description",
    "tags": ["tag1", "tag2"],
}


# TODO: Reevaluate the use of this - it doesn't seem to be used as a parent class for most models
# @as_declarative()
# class Base:
#     id: Any
#     __name__: str
#
#     # Generate __tablename__ automatically
#     @declared_attr
#     def __tablename__(cls) -> str:
#         return cls.__name__.lower()
