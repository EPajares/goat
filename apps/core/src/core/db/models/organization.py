from typing import TYPE_CHECKING, List
from uuid import UUID

from sqlalchemy import Column, text
from sqlalchemy.dialects.postgresql import UUID as UUID_PG
from sqlmodel import Field, Relationship, Text

from core.core.config import settings
from core.db.models._base_class import DateTimeBase

if TYPE_CHECKING:
    from ._link_model import LayerOrganizationLink, ProjectOrganizationLink

class Organization(DateTimeBase, table=True):
    """
    A stub representation of the Layer model from another repository.
    """

    __tablename__ = "organization"
    __table_args__ = {"schema": settings.ACCOUNTS_SCHEMA}

    id: UUID | None = Field(
        sa_column=Column(
            UUID_PG(as_uuid=True),
            primary_key=True,
            nullable=False,
            server_default=text("uuid_generate_v4()"),
        ),
        description="Organization ID",
    )
    name: str = Field(
        sa_column=Column(Text, nullable=False), description="Organization name", max_length=255
    )
    avatar: str | None = Field(sa_column=Column(Text, nullable=True))

    # Relationships
    layer_links: List["LayerOrganizationLink"] = Relationship(
        back_populates="organization", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    project_links: List["ProjectOrganizationLink"] = Relationship(
        back_populates="organization", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
