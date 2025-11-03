from uuid import UUID

from pydantic import BaseModel

from core.db.models.scenario_feature import (
    ScenarioFeatureEditType,
)


class IScenarioCreate(BaseModel):
    name: str


class IScenarioUpdate(BaseModel):
    name: str


class IScenarioFeatureCreate(BaseModel):
    layer_project_id: int
    edit_type: ScenarioFeatureEditType
    geom: str

    class Config:
        model_config = {"extra": "allow"}


class IScenarioFeatureUpdate(BaseModel):
    id: UUID
    feature_id: UUID | None = None
    edit_type: ScenarioFeatureEditType
    layer_project_id: int
    h3_3: int | None = None
    geom: str | None = None

    class Config:
        model_config = {"extra": "allow"}


request_examples = {
    "create": {
        "name": "Scenario test",
    },
    "update": {
        "name": "Scenario test updated",
    },
    "create_scenario_features": [
        {
            "geom": "POINT (35.5 47.8)",
            "id": 127,
            "edit_type": "n",
        }
    ],
}
