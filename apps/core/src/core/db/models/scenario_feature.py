from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, List
from uuid import UUID

from geoalchemy2 import Geometry
from pydantic import create_model
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as UUID_PG
from sqlmodel import (
    ARRAY,
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Field,
    Float,
    ForeignKey,
    Index,
    Integer,
    Relationship,
    SQLModel,
    Text,
    text,
)

from core.core.config import settings

from ._base_class import DateTimeBase

if TYPE_CHECKING:
    from ._link_model import LayerProjectLink, ScenarioScenarioFeatureLink


class ScenarioFeatureEditType(str, Enum):
    """Edit types."""

    new = "n"
    modified = "m"
    deleted = "d"


def generate_field_definitions() -> Dict[str, Any]:
    field_definitions: Dict[str, Any] = {
        "geom": (
            str,
            Field(
                sa_column=Column(
                    Geometry(srid="4326", spatial_index=False),
                ),
            ),
        ),
    }

    for i in range(1, 26):
        field_definitions[f"integer_attr{i}"] = (
            int | None,
            Field(default=None, sa_column=Column(Integer)),
        )
        field_definitions[f"float_attr{i}"] = (
            float | None,
            Field(default=None, sa_column=Column(Float)),
        )
        field_definitions[f"text_attr{i}"] = (
            str | None,
            Field(default=None, sa_column=Column(Text)),
        )

    for i in range(1, 6):
        field_definitions[f"bigint_attr{i}"] = (
            int | None,
            Field(default=None, sa_column=Column(BigInteger)),
        )

    for i in range(1, 11):
        field_definitions[f"jsonb_attr{i}"] = (
            dict | None,
            Field(default=None, sa_column=Column(JSONB)),
        )
        field_definitions[f"boolean_attr{i}"] = (
            bool | None,
            Field(default=None, sa_column=Column(Boolean)),
        )

    for i in range(1, 4):
        field_definitions[f"arrint_attr{i}"] = (
            List[int] | None,
            Field(default=None, sa_column=Column(ARRAY(Integer))),
        )
        field_definitions[f"arrfloat_attr{i}"] = (
            List[float] | None,
            Field(default=None, sa_column=Column(ARRAY(Float))),
        )
        field_definitions[f"arrtext_attr{i}"] = (
            List[str] | None,
            Field(default=None, sa_column=Column(ARRAY(Text))),
        )
        field_definitions[f"timestamp_attr{i}"] = (
            datetime | None,
            Field(default=None, sa_column=Column(DateTime(timezone=False))),
        )

    return field_definitions


UserData = create_model("UserData", __base__=SQLModel, **generate_field_definitions())


class ScenarioFeature(DateTimeBase, UserData, table=True):
    """Layer model."""

    __tablename__ = "scenario_feature"
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
    feature_id: UUID | None = Field(
        default=None,
        sa_column=Column(UUID_PG(as_uuid=True), nullable=True),
        description="Feature ID of the modified feature",
    )
    layer_project_id: int | None = Field(
        default=None,
        sa_column=Column(
            Integer,
            ForeignKey(
                f"{settings.CUSTOMER_SCHEMA}.layer_project.id", ondelete="CASCADE"
            ),
            nullable=False,
        ),
        description="Project layer ID",
    )

    h3_3: int | None = Field(
        default=None,
        sa_column=Column(Integer, nullable=True),
        description="H3 resolution 3",
    )

    h3_6: int | None = Field(
        default=None,
        sa_column=Column(Integer, nullable=True),
        description="H3 resolution 6",
    )

    edit_type: ScenarioFeatureEditType = Field(
        sa_column=Column(Text, nullable=False), description="Type of the edit"
    )

    # Relationships
    layer_project: "LayerProjectLink" = Relationship(back_populates="scenario_features")

    scenarios_links: List["ScenarioScenarioFeatureLink"] = Relationship(
        back_populates="scenario_feature",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )


Index(
    "scenario_feature_geom_idx",
    ScenarioFeature.__table__.c.geom,
    postgresql_using="gist",
)
