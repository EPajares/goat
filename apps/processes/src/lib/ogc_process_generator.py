"""
OGC Process Description Generator.

Generates OGC API Processes compliant process descriptions from ToolInfo.
Reads geometry constraints from goatlib params_class properties and exposes
them via metadata with role="constraint".

Also includes static process definitions for layer operations (LayerImport,
LayerExport, LayerUpdate).
"""

from typing import Any, Dict, List, Optional

from lib.ogc_schemas import (
    InputDescription,
    JobControlOptions,
    Link,
    Metadata,
    OutputDescription,
    ProcessDescription,
    ProcessSummary,
    TransmissionMode,
)
from lib.tool_registry import ToolInfo, get_all_tools, get_tool


# =============================================================================
# Static Layer Process Definitions
# =============================================================================

LAYER_PROCESSES: Dict[str, Dict[str, Any]] = {
    "LayerImport": {
        "title": "Layer Import",
        "description": "Import geospatial data from S3 file or WFS service into DuckLake storage. "
        "Supports GeoJSON, GPKG, Shapefile (ZIP), KML, CSV, XLSX, and WFS.",
        "version": "1.0.0",
        "keywords": ["data_management"],
        "jobControlOptions": [JobControlOptions.async_execute],
        "inputs": {
            "layer_id": {
                "title": "Layer ID",
                "description": "UUID for the new layer",
                "schema": {"type": "string", "format": "uuid"},
                "minOccurs": 1,
            },
            "folder_id": {
                "title": "Folder ID",
                "description": "UUID of folder to place layer in",
                "schema": {"type": "string", "format": "uuid"},
                "minOccurs": 1,
            },
            "name": {
                "title": "Layer Name",
                "description": "Name for the new layer",
                "schema": {"type": "string"},
                "minOccurs": 1,
            },
            "s3_key": {
                "title": "S3 Key",
                "description": "S3 key of the file to import (for S3 import)",
                "schema": {"type": "string"},
                "minOccurs": 0,
            },
            "wfs_url": {
                "title": "WFS URL",
                "description": "WFS service URL (for WFS import)",
                "schema": {"type": "string", "format": "uri"},
                "minOccurs": 0,
            },
            "wfs_layer_name": {
                "title": "WFS Layer Name",
                "description": "Specific layer to import from WFS (optional)",
                "schema": {"type": "string"},
                "minOccurs": 0,
            },
            "description": {
                "title": "Description",
                "description": "Layer description",
                "schema": {"type": "string"},
                "minOccurs": 0,
            },
            "project_id": {
                "title": "Project ID",
                "description": "Project UUID to link layer to (optional)",
                "schema": {"type": "string", "format": "uuid"},
                "minOccurs": 0,
            },
        },
        "outputs": {
            "layer_id": {
                "title": "Layer ID",
                "description": "UUID of the created layer",
                "schema": {"type": "string", "format": "uuid"},
            },
            "feature_count": {
                "title": "Feature Count",
                "description": "Number of features imported",
                "schema": {"type": "integer"},
            },
            "geometry_type": {
                "title": "Geometry Type",
                "description": "Type of geometry (point, line, polygon, or null for tables)",
                "schema": {"type": "string"},
            },
        },
    },
    "LayerExport": {
        "title": "Layer Export",
        "description": "Export a layer from DuckLake to various file formats. "
        "Uploads result to S3 and returns presigned download URL.",
        "version": "1.0.0",
        "keywords": ["data_management"],
        "jobControlOptions": [JobControlOptions.async_execute],
        "inputs": {
            "layer_id": {
                "title": "Layer ID",
                "description": "UUID of the layer to export",
                "schema": {"type": "string", "format": "uuid"},
                "minOccurs": 1,
            },
            "file_type": {
                "title": "File Type",
                "description": "Output format (gpkg, geojson, csv, xlsx, kml, shp)",
                "schema": {
                    "type": "string",
                    "enum": ["gpkg", "geojson", "csv", "xlsx", "kml", "shp"],
                },
                "minOccurs": 1,
            },
            "file_name": {
                "title": "File Name",
                "description": "Output file name (without extension)",
                "schema": {"type": "string"},
                "minOccurs": 1,
            },
            "crs": {
                "title": "Target CRS",
                "description": "Target coordinate reference system (e.g., EPSG:4326)",
                "schema": {"type": "string"},
                "minOccurs": 0,
            },
            "query": {
                "title": "Filter Query",
                "description": "SQL WHERE clause to filter features",
                "schema": {"type": "string"},
                "minOccurs": 0,
            },
        },
        "outputs": {
            "download_url": {
                "title": "Download URL",
                "description": "Presigned URL to download the exported file",
                "schema": {"type": "string", "format": "uri"},
            },
            "s3_key": {
                "title": "S3 Key",
                "description": "S3 key of the exported file",
                "schema": {"type": "string"},
            },
            "file_size_bytes": {
                "title": "File Size",
                "description": "Size of the exported file in bytes",
                "schema": {"type": "integer"},
            },
        },
    },
    "LayerUpdate": {
        "title": "Layer Update",
        "description": "Update existing layer data from S3 file or refresh from WFS source. "
        "Replaces existing data with new data.",
        "version": "1.0.0",
        "keywords": ["data_management"],
        "jobControlOptions": [JobControlOptions.async_execute],
        "inputs": {
            "layer_id": {
                "title": "Layer ID",
                "description": "UUID of the layer to update",
                "schema": {"type": "string", "format": "uuid"},
                "minOccurs": 1,
            },
            "s3_key": {
                "title": "S3 Key",
                "description": "S3 key of the new file (for file update)",
                "schema": {"type": "string"},
                "minOccurs": 0,
            },
            "refresh_wfs": {
                "title": "Refresh WFS",
                "description": "Set to true to refresh from original WFS source",
                "schema": {"type": "boolean"},
                "minOccurs": 0,
            },
        },
        "outputs": {
            "feature_count": {
                "title": "Feature Count",
                "description": "Number of features after update",
                "schema": {"type": "integer"},
            },
            "geometry_type": {
                "title": "Geometry Type",
                "description": "Type of geometry after update",
                "schema": {"type": "string"},
            },
        },
    },
    "LayerDelete": {
        "title": "Layer Delete",
        "description": "Delete a layer and its data from DuckLake storage. "
        "Removes both the data table and layer metadata.",
        "version": "1.0.0",
        "keywords": ["data_management"],
        "jobControlOptions": [JobControlOptions.async_execute],
        "inputs": {
            "layer_id": {
                "title": "Layer ID",
                "description": "UUID of the layer to delete",
                "schema": {"type": "string", "format": "uuid"},
                "minOccurs": 1,
            },
        },
        "outputs": {
            "ducklake_deleted": {
                "title": "DuckLake Data Deleted",
                "description": "Whether DuckLake table was deleted",
                "schema": {"type": "boolean"},
            },
            "metadata_deleted": {
                "title": "Metadata Deleted",
                "description": "Whether PostgreSQL metadata was deleted",
                "schema": {"type": "boolean"},
            },
        },
    },
}


def _generate_layer_process_summary(
    process_id: str,
    process_def: Dict[str, Any],
    base_url: str = "",
) -> ProcessSummary:
    """Generate ProcessSummary for a layer process."""
    links = [
        Link(
            href=f"{base_url}/processes/{process_id}",
            rel="self",
            type="application/json",
            title=process_def["title"],
        )
    ]

    return ProcessSummary(
        id=process_id,
        title=process_def["title"],
        description=process_def["description"],
        version=process_def["version"],
        keywords=process_def.get("keywords", []),
        jobControlOptions=process_def["jobControlOptions"],
        outputTransmission=[TransmissionMode.value, TransmissionMode.reference],
        links=links,
    )


def _generate_layer_process_description(
    process_id: str,
    process_def: Dict[str, Any],
    base_url: str = "",
) -> ProcessDescription:
    """Generate ProcessDescription for a layer process."""
    # Build inputs
    inputs = {}
    for input_id, input_def in process_def["inputs"].items():
        inputs[input_id] = InputDescription(
            title=input_def["title"],
            description=input_def.get("description"),
            schema=input_def["schema"],
            minOccurs=input_def.get("minOccurs", 1),
            maxOccurs=1,
        )

    # Build outputs
    outputs = {}
    for output_id, output_def in process_def["outputs"].items():
        outputs[output_id] = OutputDescription(
            title=output_def["title"],
            description=output_def.get("description"),
            schema=output_def["schema"],
        )

    # Links
    links = [
        Link(
            href=f"{base_url}/processes/{process_id}",
            rel="self",
            type="application/json",
            title=f"{process_def['title']} process description",
        ),
        Link(
            href=f"{base_url}/processes/{process_id}/execution",
            rel="execute",
            type="application/json",
            title=f"Execute {process_def['title']}",
        ),
    ]

    return ProcessDescription(
        id=process_id,
        title=process_def["title"],
        description=process_def["description"],
        version=process_def["version"],
        keywords=process_def.get("keywords", []),
        jobControlOptions=process_def["jobControlOptions"],
        outputTransmission=[TransmissionMode.value, TransmissionMode.reference],
        inputs=inputs,
        outputs=outputs,
        links=links,
    )


# =============================================================================
# Geometry Constraint Extraction
# =============================================================================


def _get_geometry_constraints(params_class: type) -> Dict[str, List[str]]:
    """Extract geometry type constraints from a params_class.

    Looks for properties like:
    - accepted_input_geometry_types
    - accepted_overlay_geometry_types
    - accepted_target_geometry_types
    - etc.

    Returns:
        Dict mapping field prefix to list of accepted geometry types.
        E.g., {"input": ["Polygon", "MultiPolygon"], "overlay": ["Polygon"]}
    """
    constraints = {}

    # Find all accepted_*_geometry_types attributes
    constraint_attrs = [
        attr_name
        for attr_name in dir(params_class)
        if attr_name.startswith("accepted_") and attr_name.endswith("_geometry_types")
    ]

    if not constraint_attrs:
        return constraints

    # Create a dummy instance to access property values
    # goatlib params use @property decorators that require an instance
    try:
        # Get required fields from Pydantic model
        model_fields = getattr(params_class, "model_fields", {})
        dummy_args = {}
        for field_name, field_info in model_fields.items():
            # Provide dummy values for required fields
            if field_info.is_required():
                annotation = field_info.annotation
                if annotation == str or (
                    hasattr(annotation, "__origin__") and annotation.__origin__ is str
                ):
                    dummy_args[field_name] = "/tmp/dummy"
                elif annotation == int:
                    dummy_args[field_name] = 0
                elif annotation == float:
                    dummy_args[field_name] = 0.0
                elif annotation == bool:
                    dummy_args[field_name] = False

        # Create instance with dummy values
        dummy_instance = params_class(**dummy_args)

        # Extract geometry constraints from instance properties
        for attr_name in constraint_attrs:
            try:
                value = getattr(dummy_instance, attr_name)
                if isinstance(value, (list, tuple)) and len(value) > 0:
                    prefix = attr_name.replace("accepted_", "").replace(
                        "_geometry_types", ""
                    )
                    # Convert enum values to strings (e.g., GeometryType.polygon -> "Polygon")
                    geometry_types = []
                    for geom in value:
                        if hasattr(geom, "value"):
                            # It's an enum, get the value and format it
                            geometry_types.append(geom.value.title())
                        elif hasattr(geom, "name"):
                            geometry_types.append(geom.name.title())
                        else:
                            geometry_types.append(str(geom).title())
                    constraints[prefix] = geometry_types
            except Exception:
                pass

    except Exception:
        # If we can't create a dummy instance, constraints will be empty
        pass

    return constraints


def _generate_input_description(
    field_name: str,
    field_info: Any,
    schema: Dict[str, Any],
    geometry_constraints: Dict[str, List[str]],
) -> InputDescription:
    """Generate OGC InputDescription for a single field.

    Args:
        field_name: Name of the field (e.g., "input_layer_id")
        field_info: Pydantic field info
        schema: JSON schema for the field
        geometry_constraints: Dict of geometry constraints by prefix

    Returns:
        InputDescription with metadata for geometry constraints if applicable
    """
    # Determine title from field name
    title = field_name.replace("_", " ").title()

    # Get description from field info or schema
    description = None
    if hasattr(field_info, "description") and field_info.description:
        description = field_info.description
    elif "description" in schema:
        description = schema["description"]

    # Determine if field is required
    is_required = (
        field_info.is_required() if hasattr(field_info, "is_required") else True
    )
    min_occurs = 1 if is_required else 0

    # Build field schema
    field_schema = schema.copy()
    field_schema.pop(
        "description", None
    )  # Remove description from schema, it's in InputDescription

    # Check for geometry constraints
    metadata: List[Metadata] = []
    keywords: List[str] = []

    # Check if this is a layer_id field that might have geometry constraints
    if field_name.endswith("_layer_id"):
        keywords.append("layer")
        prefix = field_name.replace("_layer_id", "")

        # Look for matching geometry constraint
        if prefix in geometry_constraints:
            metadata.append(
                Metadata(
                    title="Accepted Geometry Types",
                    role="constraint",
                    value=geometry_constraints[prefix],
                )
            )
            keywords.append("geometry")

    return InputDescription(
        title=title,
        description=description,
        schema=field_schema,
        minOccurs=min_occurs,
        maxOccurs=1,
        keywords=keywords,
        metadata=metadata,
    )


def generate_process_description(
    tool_info: ToolInfo,
    base_url: str = "",
) -> ProcessDescription:
    """Generate OGC ProcessDescription from ToolInfo.

    Args:
        tool_info: ToolInfo from tool registry
        base_url: Base URL for generating links

    Returns:
        ProcessDescription with inputs, outputs, and geometry constraints in metadata
    """
    # Get geometry constraints from the original params_class
    geometry_constraints = _get_geometry_constraints(tool_info.params_class)

    # Get JSON schema from layer_params_class
    layer_schema = tool_info.layer_params_class.model_json_schema()
    properties = layer_schema.get("properties", {})
    set(layer_schema.get("required", []))

    # Build inputs dict
    inputs: Dict[str, InputDescription] = {}

    for field_name, field_schema in properties.items():
        # Skip output_layer_id - it's an output, not an input
        if field_name == "output_layer_id":
            continue

        # Get field info from model
        field_info = tool_info.layer_params_class.model_fields.get(field_name)

        inputs[field_name] = _generate_input_description(
            field_name=field_name,
            field_info=field_info,
            schema=field_schema,
            geometry_constraints=geometry_constraints,
        )

    # Build outputs dict - different for statistics vs vector tools
    outputs: Dict[str, OutputDescription] = {}

    if tool_info.category == "statistics":
        # Statistics tools return results directly, not a layer reference
        # Get result schema based on tool name
        if tool_info.name == "feature_count":
            outputs["count"] = OutputDescription(
                title="Feature Count",
                description="Number of features matching the criteria",
                schema={"type": "integer"},
            )
        elif tool_info.name == "unique_values":
            outputs["attribute"] = OutputDescription(
                title="Attribute",
                description="The attribute/column analyzed",
                schema={"type": "string"},
            )
            outputs["total"] = OutputDescription(
                title="Total",
                description="Total number of unique values",
                schema={"type": "integer"},
            )
            outputs["values"] = OutputDescription(
                title="Values",
                description="List of unique values with counts",
                schema={
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "value": {"type": "string"},
                            "count": {"type": "integer"},
                        },
                    },
                },
            )
        elif tool_info.name == "class_breaks":
            outputs["attribute"] = OutputDescription(
                title="Attribute",
                description="The attribute/column analyzed",
                schema={"type": "string"},
            )
            outputs["method"] = OutputDescription(
                title="Method",
                description="Classification method used",
                schema={"type": "string"},
            )
            outputs["breaks"] = OutputDescription(
                title="Breaks",
                description="Classification break values",
                schema={"type": "array", "items": {"type": "number"}},
            )
            outputs["min"] = OutputDescription(
                title="Minimum",
                description="Minimum value",
                schema={"type": "number"},
            )
            outputs["max"] = OutputDescription(
                title="Maximum",
                description="Maximum value",
                schema={"type": "number"},
            )
            outputs["mean"] = OutputDescription(
                title="Mean",
                description="Mean value",
                schema={"type": "number"},
            )
            outputs["std_dev"] = OutputDescription(
                title="Standard Deviation",
                description="Standard deviation",
                schema={"type": "number"},
            )
        elif tool_info.name == "area_statistics":
            outputs["result"] = OutputDescription(
                title="Result",
                description="Result of the statistical operation",
                schema={"type": "number"},
            )
            outputs["total_area"] = OutputDescription(
                title="Total Area",
                description="Total area of all features",
                schema={"type": "number"},
            )
            outputs["feature_count"] = OutputDescription(
                title="Feature Count",
                description="Number of features",
                schema={"type": "integer"},
            )
            outputs["unit"] = OutputDescription(
                title="Unit",
                description="Unit of area measurement",
                schema={"type": "string"},
            )
        else:
            # Fallback generic result output
            outputs["result"] = OutputDescription(
                title="Result",
                description="Analysis result",
                schema={"type": "object"},
            )
    else:
        # Vector tools output a layer reference
        outputs["result"] = OutputDescription(
            title="Result Layer",
            description="UUID of the output layer containing the analysis results",
            schema={"type": "string", "format": "uuid"},
        )

    # Build links
    links: List[Link] = []
    if base_url:
        links = [
            Link(
                href=f"{base_url}/processes/{tool_info.name}",
                rel="self",
                type="application/json",
            ),
            Link(
                href=f"{base_url}/processes/{tool_info.name}/execution",
                rel="http://www.opengis.net/def/rel/ogc/1.0/execute",
                type="application/json",
                title="Execute process",
            ),
        ]

    # Map tool's job_control_options to OGC enum values
    job_control = []
    for opt in tool_info.job_control_options:
        if opt == "sync-execute":
            job_control.append(JobControlOptions.sync_execute)
        elif opt == "async-execute":
            job_control.append(JobControlOptions.async_execute)

    return ProcessDescription(
        id=tool_info.name,
        title=tool_info.display_name,
        description=tool_info.description,
        version="1.0.0",
        keywords=[tool_info.category] if tool_info.category else [],
        jobControlOptions=job_control,
        outputTransmission=[TransmissionMode.value, TransmissionMode.reference],
        links=links,
        inputs=inputs,
        outputs=outputs,
    )


def generate_process_summary(
    tool_info: ToolInfo,
    base_url: str = "",
) -> ProcessSummary:
    """Generate OGC ProcessSummary from ToolInfo.

    Args:
        tool_info: ToolInfo from tool registry
        base_url: Base URL for generating links

    Returns:
        ProcessSummary for process list
    """
    links: List[Link] = []
    if base_url:
        links = [
            Link(
                href=f"{base_url}/processes/{tool_info.name}",
                rel="self",
                type="application/json",
                title=f"Process: {tool_info.display_name}",
            ),
        ]

    # Map tool's job_control_options to OGC enum values
    job_control = []
    for opt in tool_info.job_control_options:
        if opt == "sync-execute":
            job_control.append(JobControlOptions.sync_execute)
        elif opt == "async-execute":
            job_control.append(JobControlOptions.async_execute)

    return ProcessSummary(
        id=tool_info.name,
        title=tool_info.display_name,
        description=tool_info.description,
        version="1.0.0",
        keywords=[tool_info.category] if tool_info.category else [],
        jobControlOptions=job_control,
        outputTransmission=[TransmissionMode.value, TransmissionMode.reference],
        links=links,
    )


def get_process_list(base_url: str = "") -> List[ProcessSummary]:
    """Get list of all processes as OGC ProcessSummary objects.

    Includes both analysis tools and layer processes.

    Args:
        base_url: Base URL for generating links

    Returns:
        List of ProcessSummary for all registered tools and layer processes
    """
    processes = []

    # Add analysis tools from tool registry
    tools = get_all_tools()
    for tool_info in tools.values():
        processes.append(generate_process_summary(tool_info, base_url))

    # Add layer processes
    for process_id, process_def in LAYER_PROCESSES.items():
        processes.append(
            _generate_layer_process_summary(process_id, process_def, base_url)
        )

    return processes


def get_process(process_id: str, base_url: str = "") -> Optional[ProcessDescription]:
    """Get OGC ProcessDescription for a specific process.

    Checks both analysis tools and layer processes.

    Args:
        process_id: Process/tool name
        base_url: Base URL for generating links

    Returns:
        ProcessDescription or None if not found
    """
    # Check layer processes first
    if process_id in LAYER_PROCESSES:
        return _generate_layer_process_description(
            process_id, LAYER_PROCESSES[process_id], base_url
        )

    # Check analysis tools
    tool_info = get_tool(process_id)
    if not tool_info:
        return None
    return generate_process_description(tool_info, base_url)
