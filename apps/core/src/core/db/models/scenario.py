from typing import TYPE_CHECKING, List
from uuid import UUID

from sqlalchemy.dialects.postgresql import UUID as UUID_PG
from sqlmodel import (
    Column,
    Field,
    ForeignKey,
    Relationship,
    Text,
    text,
)

from core.core.config import settings

from ._base_class import DateTimeBase

if TYPE_CHECKING:
    from ._link_model import ScenarioScenarioFeatureLink
    from .project import Project
    from .user import User


class Scenario(DateTimeBase, table=True):
    __tablename__ = "scenario"
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
    name: str = Field(sa_column=Column(Text, nullable=False), max_length=255)
    project_id: UUID = Field(
        sa_column=Column(
            UUID_PG(as_uuid=True),
            ForeignKey(f"{settings.CUSTOMER_SCHEMA}.project.id", ondelete="CASCADE"),
            nullable=False,
        ),
    )
    user_id: UUID = Field(
        default=None,
        sa_column=Column(
            UUID_PG(as_uuid=True),
            ForeignKey(f"{settings.ACCOUNTS_SCHEMA}.user.id", ondelete="CASCADE"),
            nullable=False,
        ),
    )

    user: "User" = Relationship(back_populates="scenarios")
    project: "Project" = Relationship(back_populates="scenarios")

    scenario_features_links: List["ScenarioScenarioFeatureLink"] = Relationship(
        back_populates="scenario",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
