from typing import TYPE_CHECKING, Any, Dict, List
from uuid import UUID

from pydantic import HttpUrl, field_validator
from sqlalchemy import Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as UUID_PG
from sqlalchemy.sql import text
from sqlmodel import (
    ARRAY,
    Column,
    Field,
    Float,
    ForeignKey,
    Integer,
    Relationship,
    UniqueConstraint,
)

from core.core.config import settings
from core.db.models._base_class import DateTimeBase
from core.db.models.layer import ContentBaseAttributes

if TYPE_CHECKING:
    from core.db.models._link_model import (
        LayerProjectLink,
        ProjectOrganizationLink,
        ProjectTeamLink,
        UserProjectLink,
    )

    from .scenario import Scenario


class Project(ContentBaseAttributes, DateTimeBase, table=True):
    __tablename__ = "project"
    __table_args__ = {"schema": settings.CUSTOMER_SCHEMA}

    id: UUID | None = Field(
        sa_column=Column(
            UUID_PG(as_uuid=True),
            primary_key=True,
            nullable=False,
            server_default=text("uuid_generate_v4()"),
        ),
        description="Layer ID",
    )
    user_id: UUID = Field(
        sa_column=Column(
            UUID_PG(as_uuid=True),
            ForeignKey(f"{settings.ACCOUNTS_SCHEMA}.user.id", ondelete="CASCADE"),
            nullable=False,
        ),
        description="Project owner ID",
    )
    folder_id: UUID = Field(
        sa_column=Column(
            UUID_PG(as_uuid=True),
            ForeignKey(f"{settings.CUSTOMER_SCHEMA}.folder.id", ondelete="CASCADE"),
            nullable=False,
        ),
        description="Project folder ID",
    )
    active_scenario_id: UUID | None = Field(
        sa_column=Column(
            UUID_PG(as_uuid=True),
            nullable=True,
        ),
        description="Active scenario ID",
    )
    layer_order: List[int] | None = Field(
        sa_column=Column(
            ARRAY(Integer),
            nullable=True,
        ),
        description="Layer order in project",
    )
    basemap: str | None = Field(
        sa_column=Column(Text, nullable=True),
        description="Project basemap",
    )
    thumbnail_url: str | None = Field(
        sa_column=Column(Text, nullable=True),
        description="Project thumbnail URL",
        default=settings.DEFAULT_PROJECT_THUMBNAIL,
    )
    max_extent: list[float] | None = Field(
        sa_column=Column(
            ARRAY(Float),
            nullable=True,
        ),
        description="Max extent of the project",
    )
    builder_config: Dict[str, Any] | None = Field(
        sa_column=Column(
            JSONB,
            nullable=True,
        ),
        description="Builder config",
    )
    tags: List[str] | None = Field(
        default=None,
        sa_column=Column(ARRAY(Text), nullable=True),
        description="Layer tags",
    )

    # Relationships
    user_projects: List["UserProjectLink"] = Relationship(
        back_populates="project",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
    layer_projects: List["LayerProjectLink"] = Relationship(
        back_populates="project",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
    scenarios: List["Scenario"] = Relationship(
        back_populates="project",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
    team_links: List["ProjectTeamLink"] = Relationship(
        back_populates="project",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
    organization_links: List["ProjectOrganizationLink"] = Relationship(
        back_populates="project",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )

    project_public: "ProjectPublic" = Relationship(
        back_populates="project",
        sa_relationship_kwargs={"cascade": "all, delete-orphan", "uselist": False},
    )

    @field_validator("thumbnail_url", mode="before")
    @classmethod
    def convert_httpurl_to_str(cls: type["Project"], value: str | HttpUrl | None) -> str | None:
        if value is None:
            return value
        elif isinstance(value, HttpUrl):
            return str(value)
        assert HttpUrl(value)
        return value


class ProjectPublic(DateTimeBase, table=True, extend_existing=True):
    """
    A table representing a public project. A public project is a project that is accessible to the public.

    Attributes:
        password (str): The password required to access the project.
        config (dict): The configuration of the project. This is a JSON object which includes project settings, layers etc.
        project_id (UUID): The unique identifier for the project.
    """

    __tablename__ = "project_public"
    __table_args__ = {"schema": settings.CUSTOMER_SCHEMA}
    id: UUID | None = Field(
        sa_column=Column(
            UUID_PG(as_uuid=True),
            server_default=text("uuid_generate_v4()"),
            nullable=False,
            index=True,
            primary_key=True,
        )
    )
    password: str | None = Field(sa_column=Column(Text, nullable=True), max_length=255)
    config: Dict[str, Any] = Field(sa_column=Column(JSONB, nullable=False))
    project_id: UUID = Field(
        sa_column=Column(
            UUID_PG(as_uuid=True),
            ForeignKey(f"{settings.CUSTOMER_SCHEMA}.project.id", ondelete="CASCADE"),
            nullable=False,
        ),
    )

    project: Project = Relationship(back_populates="project_public")


    # Constraints
    UniqueConstraint("folder_id", "name")
