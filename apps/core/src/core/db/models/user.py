from typing import TYPE_CHECKING, List
from uuid import UUID

from sqlalchemy.dialects.postgresql import UUID as UUID_PG
from sqlmodel import (
    Column,
    Field,
    Relationship,
    SQLModel,
    Text,
)

from core.core.config import settings

if TYPE_CHECKING:
    from ._link_model import UserTeamLink
    from .folder import Folder
    from .job import Job
    from .scenario import Scenario
    from .system_setting import SystemSetting


class User(SQLModel, table=True):
    __tablename__ = "user"
    __table_args__ = {"schema": settings.ACCOUNTS_SCHEMA}

    id: UUID = Field(
        sa_column=Column(UUID_PG(as_uuid=True), primary_key=True, nullable=False)
    )
    firstname: str = Field(sa_column=Column(Text, nullable=True))
    lastname: str = Field(sa_column=Column(Text, nullable=True))
    avatar: str = Field(sa_column=Column(Text, nullable=True))

    # Relationships
    scenarios: List["Scenario"] = Relationship(
        back_populates="user", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    folders: List["Folder"] = Relationship(
        back_populates="user", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    system_setting: "SystemSetting" = Relationship(
        back_populates="user", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    jobs: List["Job"] = Relationship(
        back_populates="user", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    team_links: List["UserTeamLink"] = Relationship(
        back_populates="user", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
