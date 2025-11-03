from typing import TYPE_CHECKING, Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as UUID_PG
from sqlmodel import (
    Column,
    Field,
    ForeignKey,
    Integer,
    Relationship,
    SQLModel,
    Text,
    UniqueConstraint,
)

from core.core.config import settings
from core.db.models._base_class import DateTimeBase
from core.db.models.organization import Organization

if TYPE_CHECKING:
    from core.db.models.organization import Organization

    from .layer import Layer
    from .project import Project
    from .scenario import Scenario
    from .scenario_feature import ScenarioFeature
    from .team import Team
    from .user import User


class LayerProjectLink(DateTimeBase, table=True):
    __tablename__ = "layer_project"
    __table_args__ = {"schema": settings.CUSTOMER_SCHEMA}

    id: int | None = Field(
        default=None,
        sa_column=Column(Integer, primary_key=True, autoincrement=True)
    )
    group: str | None = Field(
        default=None,
        sa_column=Column(Text, nullable=True),
        description="Layer group name",
        max_length=255,
    )
    layer_id: UUID = Field(
        sa_column=Column(
            UUID_PG(as_uuid=True),
            ForeignKey(f"{settings.CUSTOMER_SCHEMA}.layer.id", ondelete="CASCADE"),
        ),
        description="Layer ID",
    )
    project_id: UUID = Field(
        sa_column=Column(
            UUID_PG(as_uuid=True),
            ForeignKey(f"{settings.CUSTOMER_SCHEMA}.project.id", ondelete="CASCADE"),
        ),
        description="Project ID",
    )
    name: str = Field(
        sa_column=Column(Text, nullable=False),
        description="Layer name within the project",
        max_length=255,
    )
    properties: Dict[str, Any] | None = Field(
        sa_column=Column(JSONB, nullable=True), description="Layer properties"
    )
    other_properties: Dict[str, Any] | None = Field(
        sa_column=Column(JSONB, nullable=True), description="Layer other properties"
    )
    query: Dict[str, Any] | None = Field(
        default=None,
        sa_column=Column(JSONB, nullable=True),
        description="CQL2-JSON filter to query the layer",
    )
    charts: Dict[str, Any] | None = Field(
        default=None,
        sa_column=Column(JSONB, nullable=True), description="Chart configuration"
    )

    # Relationships
    project: "Project" = Relationship(back_populates="layer_projects")
    layer: "Layer" = Relationship(back_populates="layer_projects")

    scenario_features: List["ScenarioFeature"] = Relationship(
        back_populates="layer_project",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )


class ScenarioScenarioFeatureLink(DateTimeBase, table=True):
    __tablename__ = "scenario_scenario_feature"
    __table_args__ = {"schema": settings.CUSTOMER_SCHEMA}

    id: int | None = Field(
        sa_column=Column(Integer, primary_key=True, autoincrement=True)
    )
    scenario_id: UUID | None = Field(
        sa_column=Column(
            UUID_PG(as_uuid=True),
            ForeignKey(f"{settings.CUSTOMER_SCHEMA}.scenario.id", ondelete="CASCADE"),
            primary_key=True,
            nullable=False,
        ),
        description="Scenario ID",
    )
    scenario_feature_id: UUID | None = Field(
        sa_column=Column(
            UUID_PG(as_uuid=True),
            ForeignKey(
                f"{settings.CUSTOMER_SCHEMA}.scenario_feature.id", ondelete="CASCADE"
            ),
            primary_key=True,
            nullable=False,
        ),
        description="Scenario Feature ID",
    )

    scenario: "Scenario" = Relationship(back_populates="scenario_features_links")
    scenario_feature: "ScenarioFeature" = Relationship(back_populates="scenarios_links")


class UserProjectLink(DateTimeBase, table=True):
    __tablename__ = "user_project"
    __table_args__ = {"schema": settings.CUSTOMER_SCHEMA}

    id: int | None = Field(
        default=None,
        sa_column=Column(Integer, primary_key=True, autoincrement=True)
    )
    user_id: UUID = Field(
        sa_column=Column(
            UUID_PG(as_uuid=True),
            ForeignKey(f"{settings.ACCOUNTS_SCHEMA}.user.id", ondelete="CASCADE"),
        ),
        description="User ID",
    )
    project_id: UUID = Field(
        sa_column=Column(
            UUID_PG(as_uuid=True),
            ForeignKey(f"{settings.CUSTOMER_SCHEMA}.project.id", ondelete="CASCADE"),
        ),
        description="Project ID",
    )
    initial_view_state: Dict[str, Any] = Field(
        sa_column=Column(JSONB, nullable=False),
        description="Initial view state of the project",
    )

    # Relationships
    project: "Project" = Relationship(back_populates="user_projects")

    # Constraints
    UniqueConstraint("project_id", "user_id", name="unique_user_project"),


class UserTeamLink(SQLModel, table=True):
    """
    A table representing the relation between users and teams.

    Attributes:
        id (int): The unique identifier for the user team.
        team_id (str): The unique identifier for the team the user belongs to.
        user_id (str): The unique identifier for the user that belongs to the team.
    """

    __tablename__ = "user_team"
    __table_args__ = {"schema": settings.ACCOUNTS_SCHEMA}

    id: Optional[int] = Field(
        sa_column=Column(Integer, primary_key=True, autoincrement=True)
    )
    team_id: UUID = Field(
        sa_column=Column(
            UUID_PG(as_uuid=True),
            ForeignKey(f"{settings.ACCOUNTS_SCHEMA}.team.id", ondelete="CASCADE"),
            nullable=False,
        )
    )
    user_id: UUID = Field(
        sa_column=Column(
            UUID_PG(as_uuid=True),
            ForeignKey(f"{settings.ACCOUNTS_SCHEMA}.user.id", ondelete="CASCADE"),
            nullable=False,
        )
    )

    # Relationships
    user: "User" = Relationship(back_populates="team_links")
    team: "Team" = Relationship(back_populates="user_links")


class LayerOrganizationLink(SQLModel, table=True):
    """
    A table representing the relation between layers and organizations.

    Attributes:
        id (int): The unique identifier for the layer organization.
        organization_id (str): The unique identifier for the organization the layer belongs to.
        layer_id (str): The unique identifier for the layer that belongs to the organization.
    """

    __tablename__ = "layer_organization"
    __table_args__ = {"schema": settings.ACCOUNTS_SCHEMA}

    id: Optional[int] = Field(
        sa_column=Column(Integer, primary_key=True, autoincrement=True)
    )
    organization_id: Optional[UUID] = Field(
        sa_column=Column(
            UUID_PG(as_uuid=True),
            ForeignKey(
                f"{settings.ACCOUNTS_SCHEMA}.organization.id", ondelete="CASCADE"
            ),
            nullable=False,
        )
    )
    layer_id: Optional[UUID] = Field(
        sa_column=Column(
            UUID_PG(as_uuid=True),
            ForeignKey(f"{settings.CUSTOMER_SCHEMA}.layer.id", ondelete="CASCADE"),
            nullable=False,
        )
    )
    role_id: UUID = Field(
        sa_column=Column(
            UUID_PG(as_uuid=True),
            ForeignKey(f"{settings.ACCOUNTS_SCHEMA}.role.id"),
            nullable=False,
        )
    )

    # Relationships
    layer: "Layer" = Relationship(back_populates="organization_links")
    organization: "Organization" = Relationship(back_populates="layer_links")


class LayerTeamLink(SQLModel, table=True):
    """
    A table representing the relation between layers and teams.

    Attributes:
        id (int): The unique identifier for the layer team.
        team_id (str): The unique identifier for the team the layer belongs to.
        layer_id (str): The unique identifier for the layer that belongs to the team.
    """

    __tablename__ = "layer_team"
    __table_args__ = {"schema": settings.ACCOUNTS_SCHEMA}

    id: Optional[int] = Field(
        sa_column=Column(Integer, primary_key=True, autoincrement=True)
    )
    team_id: Optional[UUID] = Field(
        sa_column=Column(
            UUID_PG(as_uuid=True),
            ForeignKey(f"{settings.ACCOUNTS_SCHEMA}.team.id", ondelete="CASCADE"),
            nullable=False,
        )
    )
    layer_id: Optional[UUID] = Field(
        sa_column=Column(
            UUID_PG(as_uuid=True),
            ForeignKey(f"{settings.CUSTOMER_SCHEMA}.layer.id", ondelete="CASCADE"),
            nullable=False,
        )
    )
    role_id: UUID = Field(
        sa_column=Column(
            UUID_PG(as_uuid=True),
            ForeignKey(f"{settings.ACCOUNTS_SCHEMA}.role.id"),
            nullable=False,
        )
    )

    # Relationships
    layer: "Layer" = Relationship(back_populates="team_links")
    team: "Team" = Relationship(back_populates="layer_links")


class ProjectTeamLink(SQLModel, table=True):
    """
    A table representing the relation between projects and teams.

    Attributes:
        id (int): The unique identifier for the project team.
        team_id (str): The unique identifier for the team the project belongs to.
        project_id (str): The unique identifier for the project that belongs to the team.
    """

    __tablename__ = "project_team"
    __table_args__ = {"schema": settings.ACCOUNTS_SCHEMA}

    id: Optional[int] = Field(
        sa_column=Column(Integer, primary_key=True, autoincrement=True)
    )
    team_id: Optional[UUID] = Field(
        sa_column=Column(
            UUID_PG(as_uuid=True),
            ForeignKey(f"{settings.ACCOUNTS_SCHEMA}.team.id", ondelete="CASCADE"),
            nullable=False,
        )
    )
    project_id: Optional[UUID] = Field(
        sa_column=Column(
            UUID_PG(as_uuid=True),
            ForeignKey(f"{settings.CUSTOMER_SCHEMA}.project.id", ondelete="CASCADE"),
            nullable=False,
        )
    )
    role_id: UUID = Field(
        sa_column=Column(
            UUID_PG(as_uuid=True),
            ForeignKey(f"{settings.ACCOUNTS_SCHEMA}.role.id"),
            nullable=False,
        )
    )

    # Relationships
    project: "Project" = Relationship(back_populates="team_links")
    team: "Team" = Relationship(back_populates="project_links")


class ProjectOrganizationLink(SQLModel, table=True):
    """
    A table representing the relation between projects and organizations.

    Attributes:
        id (int): The unique identifier for the project organization.
        organization_id (str): The unique identifier for the organization the project belongs to.
        project_id (str): The unique identifier for the project that belongs to the organization.
    """

    __tablename__ = "project_organization"
    __table_args__ = {"schema": settings.ACCOUNTS_SCHEMA}

    id: Optional[int] = Field(
        sa_column=Column(Integer, primary_key=True, autoincrement=True)
    )
    organization_id: Optional[UUID] = Field(
        sa_column=Column(
            UUID_PG(as_uuid=True),
            ForeignKey(
                f"{settings.ACCOUNTS_SCHEMA}.organization.id", ondelete="CASCADE"
            ),
            nullable=False,
        )
    )
    project_id: Optional[UUID] = Field(
        sa_column=Column(
            UUID_PG(as_uuid=True),
            ForeignKey(f"{settings.CUSTOMER_SCHEMA}.project.id", ondelete="CASCADE"),
            nullable=False,
        )
    )
    role_id: UUID = Field(
        sa_column=Column(
            UUID_PG(as_uuid=True),
            ForeignKey(f"{settings.ACCOUNTS_SCHEMA}.role.id"),
            nullable=False,
        )
    )

    # Relationships
    project: "Project" = Relationship(back_populates="organization_links")
    organization: "Organization" = Relationship(back_populates="project_links")
