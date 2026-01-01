"""Analytics process registry.

Auto-generates OGC Process descriptions from goatlib statistics schemas.
"""

from typing import Any

from goatlib.analysis.statistics import (
    AreaStatisticsInput,
    AreaStatisticsResult,
    ClassBreaksInput,
    ClassBreaksResult,
    FeatureCountInput,
    FeatureCountResult,
    UniqueValuesInput,
    UniqueValuesResult,
)
from pydantic import BaseModel, Field

from geoapi.models.processes import (
    InputDescription,
    JobControlOptions,
    Link,
    OutputDescription,
    ProcessDescription,
    ProcessSummary,
    TransmissionMode,
)

# Extended input models that add 'collection' field
# (goatlib inputs work on table names, we need layer IDs)


class FeatureCountProcessInput(FeatureCountInput):
    """Feature count input with collection (layer ID)."""

    collection: str = Field(description="Layer ID (UUID)")


class UniqueValuesProcessInput(UniqueValuesInput):
    """Unique values input with collection (layer ID)."""

    collection: str = Field(description="Layer ID (UUID)")


class ClassBreaksProcessInput(ClassBreaksInput):
    """Class breaks input with collection (layer ID)."""

    collection: str = Field(description="Layer ID (UUID)")


class AreaStatisticsProcessInput(AreaStatisticsInput):
    """Area statistics input with collection (layer ID)."""

    collection: str = Field(description="Layer ID (UUID)")


# Analytics process definitions
ANALYTICS_DEFINITIONS: dict[str, dict[str, Any]] = {
    "feature-count": {
        "title": "Feature Count",
        "description": "Count features in a collection with optional filtering",
        "input_model": FeatureCountProcessInput,
        "output_model": FeatureCountResult,
        "keywords": ["analytics", "statistics", "count"],
    },
    "unique-values": {
        "title": "Unique Values",
        "description": "Get unique values for an attribute with occurrence counts",
        "input_model": UniqueValuesProcessInput,
        "output_model": UniqueValuesResult,
        "keywords": ["analytics", "statistics", "unique", "values"],
    },
    "class-breaks": {
        "title": "Class Breaks",
        "description": "Calculate classification breaks for a numeric attribute",
        "input_model": ClassBreaksProcessInput,
        "output_model": ClassBreaksResult,
        "keywords": ["analytics", "statistics", "classification", "breaks"],
    },
    "area-statistics": {
        "title": "Area Statistics",
        "description": "Calculate area statistics for polygon features",
        "input_model": AreaStatisticsProcessInput,
        "output_model": AreaStatisticsResult,
        "keywords": ["analytics", "statistics", "area", "polygon"],
    },
}


def _pydantic_to_ogc_inputs(model: type[BaseModel]) -> dict[str, InputDescription]:
    """Convert Pydantic model to OGC input descriptions.

    Args:
        model: Pydantic model class

    Returns:
        Dict of field name to InputDescription
    """
    schema = model.model_json_schema()
    properties = schema.get("properties", {})
    required = set(schema.get("required", []))
    defs = schema.get("$defs", {})

    inputs = {}
    for field_name, field_schema in properties.items():
        # Resolve $ref if present
        if "$ref" in field_schema:
            ref_name = field_schema["$ref"].split("/")[-1]
            field_schema = defs.get(ref_name, field_schema)

        # Determine if required
        is_required = field_name in required
        has_default = "default" in field_schema

        # Build keywords based on field name
        keywords = []
        if field_name == "collection":
            keywords = ["layer"]
        elif field_name == "attribute":
            keywords = ["field"]

        inputs[field_name] = InputDescription(
            title=field_schema.get("title", field_name.replace("_", " ").title()),
            description=field_schema.get("description"),
            schema=field_schema,
            minOccurs=1 if is_required and not has_default else 0,
            maxOccurs=1,
            keywords=keywords,
        )

    return inputs


def _pydantic_to_ogc_output(model: type[BaseModel]) -> dict[str, OutputDescription]:
    """Convert Pydantic model to OGC output description.

    Args:
        model: Pydantic model class

    Returns:
        Dict with single 'result' output
    """
    schema = model.model_json_schema()

    return {
        "result": OutputDescription(
            title="Result",
            description=model.__doc__ or "Process result",
            schema=schema,
        )
    }


class AnalyticsRegistry:
    """Registry for analytics processes.

    Auto-generates OGC process descriptions from goatlib Pydantic schemas.
    """

    def __init__(self) -> None:
        self._definitions = ANALYTICS_DEFINITIONS

    def get_process_ids(self) -> list[str]:
        """Get list of all analytics process IDs."""
        return list(self._definitions.keys())

    def is_analytics_process(self, process_id: str) -> bool:
        """Check if a process ID is an analytics process."""
        return process_id in self._definitions

    def get_process_summary(
        self, process_id: str, base_url: str
    ) -> ProcessSummary | None:
        """Get process summary for an analytics process.

        Args:
            process_id: Analytics process ID
            base_url: Base URL for links

        Returns:
            ProcessSummary or None if not found
        """
        if process_id not in self._definitions:
            return None

        defn = self._definitions[process_id]
        return ProcessSummary(
            id=process_id,
            title=defn["title"],
            description=defn["description"],
            version="1.0.0",
            keywords=defn.get("keywords", ["analytics"]),
            jobControlOptions=[JobControlOptions.sync_execute],
            outputTransmission=[TransmissionMode.value],
            links=[
                Link(
                    href=f"{base_url}/processes/{process_id}",
                    rel="self",
                    type="application/json",
                    title=defn["title"],
                ),
            ],
        )

    def get_process_description(
        self, process_id: str, base_url: str
    ) -> ProcessDescription | None:
        """Get full process description for an analytics process.

        Args:
            process_id: Analytics process ID
            base_url: Base URL for links

        Returns:
            ProcessDescription or None if not found
        """
        if process_id not in self._definitions:
            return None

        defn = self._definitions[process_id]
        input_model = defn["input_model"]
        output_model = defn["output_model"]

        return ProcessDescription(
            id=process_id,
            title=defn["title"],
            description=defn["description"],
            version="1.0.0",
            keywords=defn.get("keywords", ["analytics"]),
            jobControlOptions=[JobControlOptions.sync_execute],
            outputTransmission=[TransmissionMode.value],
            inputs=_pydantic_to_ogc_inputs(input_model),
            outputs=_pydantic_to_ogc_output(output_model),
            links=[
                Link(
                    href=f"{base_url}/processes/{process_id}",
                    rel="self",
                    type="application/json",
                    title=defn["title"],
                ),
                Link(
                    href=f"{base_url}/processes/{process_id}/execution",
                    rel="http://www.opengis.net/def/rel/ogc/1.0/execute",
                    type="application/json",
                    title="Execute process",
                ),
            ],
        )

    def get_all_summaries(self, base_url: str) -> list[ProcessSummary]:
        """Get summaries for all analytics processes.

        Args:
            base_url: Base URL for links

        Returns:
            List of ProcessSummary
        """
        summaries = []
        for process_id in self._definitions:
            summary = self.get_process_summary(process_id, base_url)
            if summary:
                summaries.append(summary)
        return summaries


# Singleton instance
analytics_registry = AnalyticsRegistry()
