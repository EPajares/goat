from typing import TYPE_CHECKING, List
from uuid import UUID

from sqlalchemy.dialects.postgresql import UUID as UUID_PG
from sqlmodel import (
    Column,
    Field,
    Relationship,
    SQLModel,
    Text,
    text,
)

from core.core.config import settings

from ._base_class import DateTimeBase

if TYPE_CHECKING:
    from core.schemas.data_store import DataStoreType

    from .layer import Layer


# TODO: Add further attributes for the different data store types
class DataStoreBase(SQLModel):
    type: "DataStoreType" = Field(
        sa_column=Column(Text, nullable=False), description="Data store type"
    )


class DataStore(DataStoreBase, DateTimeBase, table=True):
    """Data store model."""

    __tablename__ = "data_store"
    __table_args__ = {"schema": settings.CUSTOMER_SCHEMA}

    id: UUID | None = Field(
        sa_column=Column(
            UUID_PG(as_uuid=True),
            primary_key=True,
            nullable=False,
            server_default=text("uuid_generate_v4()"),
        )
    )
    # Relationships
    layers: List["Layer"] = Relationship(back_populates="data_store")
