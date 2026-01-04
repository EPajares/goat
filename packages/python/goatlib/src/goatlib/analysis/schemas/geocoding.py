"""
Geocoding schemas for goatlib analysis.

This module provides schemas for batch geocoding operations using Pelias.
Supports both structured (separate address columns) and full address (single column)
input modes. Internally, all requests are sent as free-text queries to leverage
libpostal's language-agnostic address parsing.
"""

from enum import StrEnum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from goatlib.analysis.schemas.ui import (
    SECTION_INPUT,
    SECTION_OUTPUT,
    UISection,
    ui_field,
    ui_sections,
)


# =============================================================================
# Sections
# =============================================================================

SECTION_GEOCODING = UISection(
    id="geocoding",
    order=2,
    icon="location-marker",
)


# =============================================================================
# Enums
# =============================================================================


class GeocodingInputMode(StrEnum):
    """Input mode for geocoding."""

    full_address = "full_address"  # Single column with complete address
    structured = "structured"  # Separate address component columns


class FieldSourceType(StrEnum):
    """Source type for a field value - from column or constant."""

    field = "field"  # Value comes from a column in the input data
    constant = "constant"  # Value is a constant applied to all rows


# =============================================================================
# Tool Parameters Schema
# =============================================================================


class GeocodingParams(BaseModel):
    """
    Parameters for GeocodingTool.

    Supports two input modes:
    1. Full address mode: Single column containing the complete address
    2. Structured mode: Separate columns for address components

    For structured mode, locality and country can be:
    - From a column (field mode)
    - A constant value applied to all rows (constant mode)

    In both modes, the tool internally concatenates fields and uses
    Pelias free-text search for best language/alias resolution.
    """

    model_config = ConfigDict(
        json_schema_extra=ui_sections(
            SECTION_INPUT,
            SECTION_GEOCODING,
            SECTION_OUTPUT,
        )
    )

    # === Input Source ===
    input_path: str = Field(
        ...,
        description="Path to input parquet file for batch geocoding",
        json_schema_extra=ui_field(
            section="input",
            field_order=1,
            widget="file",
            widget_options={"accept": [".parquet"]},
        ),
    )

    # === Input Mode Selection ===
    input_mode: GeocodingInputMode = Field(
        default=GeocodingInputMode.full_address,
        description="How address input is provided",
        json_schema_extra=ui_field(
            section="geocoding",
            field_order=1,
            widget="radio",
            enum_icons={
                "full_address": "text",
                "structured": "table",
            },
        ),
    )

    # === Full Address Mode ===
    full_address_field: str | None = Field(
        default=None,
        description="Column containing complete address (e.g., 'Marienplatz 1, Munich, Germany')",
        json_schema_extra=ui_field(
            section="geocoding",
            field_order=2,
            widget="field-selector",
            widget_options={"source_layer": "input_path", "field_types": ["string"]},
            visible_when={"input_mode": "full_address"},
        ),
    )

    # === Structured Mode: Address Field (always from column) ===
    address_field: str | None = Field(
        default=None,
        description="Column for street address (e.g., 'Marienplatz 1')",
        json_schema_extra=ui_field(
            section="geocoding",
            field_order=10,
            widget="field-selector",
            widget_options={"source_layer": "input_path", "field_types": ["string"]},
            visible_when={"input_mode": "structured"},
        ),
    )

    # === Structured Mode: Locality (city) - field or constant ===
    locality_source_type: FieldSourceType = Field(
        default=FieldSourceType.field,
        description="How to get the city/locality value",
        json_schema_extra=ui_field(
            section="geocoding",
            field_order=20,
            widget="radio",
            visible_when={"input_mode": "structured"},
        ),
    )
    locality_field: str | None = Field(
        default=None,
        description="Column for city/town",
        json_schema_extra=ui_field(
            section="geocoding",
            field_order=21,
            widget="field-selector",
            widget_options={"source_layer": "input_path", "field_types": ["string"]},
            visible_when={
                "input_mode": "structured",
                "locality_source_type": "field",
            },
        ),
    )
    locality_constant: str | None = Field(
        default=None,
        description="Constant city/locality applied to all addresses",
        json_schema_extra=ui_field(
            section="geocoding",
            field_order=22,
            widget="text",
            visible_when={
                "input_mode": "structured",
                "locality_source_type": "constant",
            },
        ),
    )

    # === Structured Mode: Region (state/province) - field or constant ===
    region_source_type: FieldSourceType = Field(
        default=FieldSourceType.field,
        description="How to get the state/province value",
        json_schema_extra=ui_field(
            section="geocoding",
            field_order=25,
            widget="radio",
            visible_when={"input_mode": "structured"},
        ),
    )
    region_field: str | None = Field(
        default=None,
        description="Column for state/province/region",
        json_schema_extra=ui_field(
            section="geocoding",
            field_order=26,
            widget="field-selector",
            widget_options={"source_layer": "input_path", "field_types": ["string"]},
            visible_when={
                "input_mode": "structured",
                "region_source_type": "field",
            },
        ),
    )
    region_constant: str | None = Field(
        default=None,
        description="Constant state/province/region applied to all addresses",
        json_schema_extra=ui_field(
            section="geocoding",
            field_order=27,
            widget="text",
            visible_when={
                "input_mode": "structured",
                "region_source_type": "constant",
            },
        ),
    )

    # === Structured Mode: Postal code (always from column) ===
    postalcode_field: str | None = Field(
        default=None,
        description="Column for postal/ZIP code",
        json_schema_extra=ui_field(
            section="geocoding",
            field_order=30,
            widget="field-selector",
            widget_options={
                "source_layer": "input_path",
                "field_types": ["string", "number"],
            },
            visible_when={"input_mode": "structured"},
        ),
    )

    # === Structured Mode: Country - field or constant ===
    country_source_type: FieldSourceType = Field(
        default=FieldSourceType.constant,
        description="How to get the country value",
        json_schema_extra=ui_field(
            section="geocoding",
            field_order=35,
            widget="radio",
            visible_when={"input_mode": "structured"},
        ),
    )
    country_field: str | None = Field(
        default=None,
        description="Column for country (name or ISO code)",
        json_schema_extra=ui_field(
            section="geocoding",
            field_order=36,
            widget="field-selector",
            widget_options={"source_layer": "input_path", "field_types": ["string"]},
            visible_when={
                "input_mode": "structured",
                "country_source_type": "field",
            },
        ),
    )
    country_constant: str | None = Field(
        default="Germany",
        description="Constant country applied to all addresses (name or ISO code)",
        json_schema_extra=ui_field(
            section="geocoding",
            field_order=37,
            widget="text",
            visible_when={
                "input_mode": "structured",
                "country_source_type": "constant",
            },
        ),
    )

    # === Output Configuration ===
    output_path: str = Field(
        ...,
        description="Path for output parquet file with geocoding results",
        json_schema_extra=ui_field(
            section="output",
            field_order=1,
            widget="file",
            widget_options={"accept": [".parquet"]},
        ),
    )
    output_crs: Optional[str] = Field(
        "EPSG:4326",
        description="Target coordinate reference system for the output geometry.",
        json_schema_extra=ui_field(section="output", field_order=2, hidden=True),
    )

    # === Service Configuration ===
    geocoder_url: str = Field(
        ...,
        description="Pelias geocoder service URL",
        json_schema_extra=ui_field(
            section="geocoding",
            field_order=80,
            hidden=True,
        ),
    )
    geocoder_username: str = Field(
        ...,
        description="Pelias geocoder username for Basic auth",
        json_schema_extra=ui_field(
            section="geocoding",
            field_order=81,
            hidden=True,
        ),
    )
    geocoder_password: str = Field(
        ...,
        description="Pelias geocoder password for Basic auth",
        json_schema_extra=ui_field(
            section="geocoding",
            field_order=82,
            hidden=True,
        ),
    )

    def _get_locality(self, row: dict) -> str | None:
        """Get locality value from field or constant."""
        if self.locality_source_type == FieldSourceType.field and self.locality_field:
            return str(row.get(self.locality_field, "")).strip() or None
        return self.locality_constant

    def _get_region(self, row: dict) -> str | None:
        """Get region value from field or constant."""
        if self.region_source_type == FieldSourceType.field and self.region_field:
            return str(row.get(self.region_field, "")).strip() or None
        return self.region_constant

    def _get_country(self, row: dict) -> str | None:
        """Get country value from field or constant."""
        if self.country_source_type == FieldSourceType.field and self.country_field:
            return str(row.get(self.country_field, "")).strip() or None
        return self.country_constant

    def build_query_text(self, row: dict) -> str:
        """
        Build the free-text query string from a row of data.

        For full_address mode, returns the full address column value.
        For structured mode, concatenates address components with commas.

        Args:
            row: Dictionary of column values from the input data.

        Returns:
            Query string for Pelias free-text search.
        """
        if self.input_mode == GeocodingInputMode.full_address:
            return str(row.get(self.full_address_field, "")).strip()

        # Structured mode: concatenate components
        components: list[str] = []

        if self.address_field and row.get(self.address_field):
            components.append(str(row[self.address_field]).strip())

        locality = self._get_locality(row)
        if locality:
            components.append(locality)

        if self.postalcode_field and row.get(self.postalcode_field):
            components.append(str(row[self.postalcode_field]).strip())

        region = self._get_region(row)
        if region:
            components.append(region)

        country = self._get_country(row)
        if country:
            components.append(country)

        return ", ".join(components)


# =============================================================================
# Result Schema
# =============================================================================


class GeocodingResult(BaseModel):
    """Result from a single geocoding operation."""

    input_text: str = Field(description="Original input query text")
    latitude: float | None = Field(default=None, description="Geocoded latitude")
    longitude: float | None = Field(default=None, description="Geocoded longitude")
    confidence: float | None = Field(default=None, description="Match confidence (0-1)")
    match_type: str | None = Field(
        default=None, description="Match type (exact, fallback, etc.)"
    )
