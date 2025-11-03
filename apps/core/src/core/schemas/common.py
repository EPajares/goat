from enum import Enum
from typing import Any, Dict, List

from pydantic import UUID4, BaseModel, Field, field_validator
from pygeofilter.parsers.cql2_json import parse as cql2_json_parser


class OrderEnum(str, Enum):
    ascendent = "ascendent"
    descendent = "descendent"


class ContentIdList(BaseModel):
    ids: List[UUID4]


class IntersectionGeomType(str, Enum):
    bbox = "bbox"
    draw = "draw"
    boundary = "boundary"


class IntersectionQueryMetadata(BaseModel):
    label: str | None = Field(None, description="Name of the bounday")
    geom_type: str = Field(..., description="Value of the metadata")
    buffer_size: float | None = Field(None, description="Buffer size for the boundary")


class MetaDataQuery(BaseModel):
    intersection: IntersectionQueryMetadata | None = Field(
        None, description="Intersection query"
    )


class CQLQueryObject(BaseModel):
    metadata: MetaDataQuery | None = Field(None, description="Metadata query")
    cql: Dict[str, Any] | None = Field(None, description="CQL query")

    # Validate using cql2_json_parser(query)
    @field_validator("cql")
    @classmethod
    def validate_query(
        cls: type["CQLQueryObject"], value: Dict[str, Any] | None
    ) -> Dict[str, Any] | None:
        if value is None:
            return value
        try:
            cql2_json_parser(value)
        except Exception as e:
            raise ValueError(f"Invalid CQL query: {e}")
        return value


class CQLQuery(BaseModel):
    """Model for CQL query."""

    query: CQLQueryObject | None = Field(None, description="CQL query")


# test = CQLQueryObject(
#     cql={
#         "op": "=",
#         "args": [{"property": "category"}, "second_category"],
#     }
# )
# print(test)

# x={'query': {'cql': {'op': '=', 'args': [{'property': 'category'}, 'second_category']}}}
# CQLQuery(**x)
