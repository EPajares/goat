from typing import Any, Dict, List
from uuid import UUID

from geojson import FeatureCollection
from sqlalchemy import RowMapping, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, load_only

from core.core.layer import get_user_table
from core.crud.base import CRUDBase
from core.db.models._link_model import LayerProjectLink, ScenarioScenarioFeatureLink
from core.db.models.layer import Layer
from core.db.models.scenario import Scenario
from core.db.models.scenario_feature import ScenarioFeature, ScenarioFeatureEditType
from core.schemas.scenario import (
    IScenarioCreate,
    IScenarioFeatureCreate,
    IScenarioFeatureUpdate,
    IScenarioUpdate,
)
from core.utils import to_feature_collection


class CRUDScenario(CRUDBase[Scenario, IScenarioCreate, IScenarioUpdate]):
    async def _get_origin_features(
        self,
        async_session: AsyncSession,
        layer_project: LayerProjectLink,
        feature_id: UUID,
        h3_3: int,
    ) -> RowMapping | None:
        """Get all features from the origin table."""

        user_table = get_user_table(layer_project.layer.model_dump())
        origin_feature_result = await async_session.execute(
            text(f"""SELECT * FROM {user_table} WHERE id = :id AND h3_3 = :h3_3"""),
            {"id": feature_id, "h3_3": h3_3},
        )
        origin_feature_obj = origin_feature_result.mappings().fetchone()
        return origin_feature_obj

    def _get_rev_attr_mapping(self, layer_project: LayerProjectLink) -> Dict[str, Any]:
        """Get attribute mapping for a project layer."""

        attribute_mapping = layer_project.layer.attribute_mapping
        if attribute_mapping:
            reversed_attribute_mapping = {v: k for k, v in attribute_mapping.items()}
            attribute_mapping = reversed_attribute_mapping

        if attribute_mapping is None:
            raise ValueError("Attribute mapping unavailable for layer")

        return attribute_mapping

    async def get_features(
        self, async_session: AsyncSession, scenario_id: UUID
    ) -> List[Dict[str, Any]]:
        """Get all features of a scenario."""

        query = (
            select(ScenarioFeature)
            .where(
                ScenarioScenarioFeatureLink.scenario_id == scenario_id,
                ScenarioFeature.id == ScenarioScenarioFeatureLink.scenario_feature_id,
            )
            .options(
                joinedload(ScenarioFeature.layer_project).options(
                    load_only(LayerProjectLink.id),
                    joinedload(LayerProjectLink.layer).options(
                        load_only(Layer.attribute_mapping, Layer.id)
                    ),
                )
            )
        )

        result = await async_session.execute(query)
        features = result.scalars().all()

        transformed_features = []
        for feature in features:
            attribute_mapping = feature.layer_project.layer.attribute_mapping
            transformed_feature = {
                "id": feature.id,
                "geom": feature.geom,
                "feature_id": feature.feature_id,
                "layer_project_id": feature.layer_project_id,
                "edit_type": feature.edit_type,
                "updated_at": feature.updated_at,
                "created_at": feature.created_at,
            }
            for key, value in feature.dict().items():
                if attribute_mapping is not None and key in attribute_mapping:
                    transformed_feature[attribute_mapping[key]] = value

            transformed_features.append(transformed_feature)

        return transformed_features

    async def create_features(
        self,
        async_session: AsyncSession,
        user_id: UUID,
        scenario: Scenario,
        features: List[IScenarioFeatureCreate],
    ) -> FeatureCollection:
        """Create a feature in a scenario."""

        scenario_features = []
        for feature in features:
            scenario_feature = ScenarioFeature.model_validate(feature)
            scenario_scenario_feature_link = ScenarioScenarioFeatureLink(
                scenario=scenario, scenario_feature=scenario_feature
            )
            async_session.add(scenario_feature)
            async_session.add(scenario_scenario_feature_link)
            scenario_features.append(scenario_feature)

        await async_session.commit()

        for scenario_feature in scenario_features:
            await async_session.refresh(scenario_feature)

        fc = to_feature_collection(scenario_features)

        return fc

    async def update_feature(
        self,
        async_session: AsyncSession,
        user_id: UUID,
        layer_project: LayerProjectLink,
        scenario: Scenario,
        feature: IScenarioFeatureUpdate,
    ) -> ScenarioFeature:
        """Update a feature in a scenario."""

        attribute_mapping = self._get_rev_attr_mapping(layer_project)

        # Check if feature exists in the scenario_feature table
        feature_db = feature_db = await CRUDBase(ScenarioFeature).get(
            db=async_session, id=feature.id
        )
        if feature_db:
            for key, value in feature.dict().items():
                if value is not None and key in attribute_mapping:
                    setattr(feature_db, attribute_mapping[key], value)
                if key == "geom" and value is not None:
                    setattr(feature_db, key, value)
            async_session.add(feature_db)
            await async_session.commit()
            return feature_db

        if feature.h3_3 is None:
            raise ValueError("h3_3 is required to modify a scenario from user table")

        # New modified feature. Create a new feature in the scenario_feature table
        origin_feature_obj = await self._get_origin_features(
            async_session, layer_project, feature.id, feature.h3_3
        )
        if origin_feature_obj:
            scenario_feature_dict = {
                **origin_feature_obj,
                "id": None,
                "feature_id": feature.id,
                "layer_project_id": layer_project.id,
                "edit_type": ScenarioFeatureEditType.modified,
            }
            for key, value in feature.dict().items():
                if value is not None and key in attribute_mapping:
                    scenario_feature_dict[attribute_mapping[key]] = value

            scenario_feature_obj = ScenarioFeature(**scenario_feature_dict)
            scenario_scenario_feature_link = ScenarioScenarioFeatureLink(
                scenario=scenario, scenario_feature=scenario_feature_obj
            )
            async_session.add(scenario_scenario_feature_link)
            await async_session.commit()
            return scenario_feature_obj

        raise ValueError("Cannot update feature")

    async def delete_feature(
        self,
        async_session: AsyncSession,
        user_id: UUID,
        layer_project: LayerProjectLink,
        scenario: Scenario,
        feature_id: UUID,
        h3_3: int | None = None,
    ) -> ScenarioFeature:
        """Delete a feature from a scenario."""

        # Check if feature exists in the scenario_feature table
        feature_db = await CRUDBase(ScenarioFeature).get(
            db=async_session, id=feature_id
        )
        if feature_db:
            return await CRUDBase(ScenarioFeature).remove(
                db=async_session, id=feature_db.id
            )

        # New deleted feature. Create a new feature in the scenario_feature table
        if h3_3 is None:
            raise ValueError(
                "h3_3 is required to delete a scenario feature which is derived from user table"
            )

        origin_feature_obj = await self._get_origin_features(
            async_session, layer_project, feature_id, h3_3
        )
        if origin_feature_obj:
            scenario_feature_dict = {
                **origin_feature_obj,
                "id": None,
                "feature_id": feature_id,
                "layer_project_id": layer_project.id,
                "edit_type": ScenarioFeatureEditType.deleted,
            }
            scenario_feature_obj = ScenarioFeature(**scenario_feature_dict)
            scenario_scenario_feature_link = ScenarioScenarioFeatureLink(
                scenario=scenario, scenario_feature=scenario_feature_obj
            )
            async_session.add(scenario_scenario_feature_link)
            await async_session.commit()
            return scenario_feature_obj

        # Throw error if feature does not exist
        raise ValueError("Feature does not exist")


scenario = CRUDScenario(Scenario)
