"""Heatmap V2 tool for Windmill — on-the-fly via local C++ routing.

Supports walking, bicycle, pedelec, car, and public-transport modes. PT
uses an arrive-by reverse-RAPTOR pipeline with precomputed per-mode
access/egress lookup tables (resolved from settings). Per-opportunity
max_cost drives the routing budget; the resolver turns layer IDs into
parquet paths.
"""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta, timezone
from datetime import time as time_of_day
from enum import StrEnum
from pathlib import Path
from typing import Any, Literal, Self

from pydantic import ConfigDict, Field

from goatlib.analysis.accessibility import HeatmapV2Tool
from goatlib.analysis.schemas.catchment_area import WEEKDAY_LABELS
from goatlib.analysis.schemas.catchment_area_v2 import (
    AccessEgressMode,
    CostType,
    PTMode,
    RoutingMode,
    Weekday,
)
from goatlib.analysis.schemas.heatmap import (
    ROUTING_MODE_ICONS,
    ROUTING_MODE_LABELS,
    PotentialExpression,
    PotentialType,
    TwoSFCAType_LABELS,
)
from goatlib.analysis.schemas.heatmap_v2 import (
    N_DESTINATIONS_MAX,
    N_DESTINATIONS_MIN,
    SENSITIVITY_MAX,
    SENSITIVITY_MIN,
    GravityDecay,
    HeatmapType,
    HeatmapV2Params,
    OpportunityV2,
    TwoSFCAType,
)
from goatlib.analysis.schemas.ui import (
    UISection,
    ui_field,
    ui_sections,
)
from goatlib.models.io import DatasetMetadata
from goatlib.tools._routing_limits import (
    ACTIVE_DISTANCE_LIMIT_MSG,
    ACTIVE_TIME_LIMIT_MSG,
    CAR_DISTANCE_LIMIT_MSG,
    CAR_TIME_LIMIT_MSG,
    DEFAULT_MAX_DISTANCE_ACTIVE_M,
    DEFAULT_MAX_DISTANCE_CAR_M,
    DEFAULT_MAX_TIME_ACTIVE_MIN,
    DEFAULT_MAX_TIME_CAR_MIN,
    DEFAULT_MAX_TIME_PT_MIN,
    MAX_DISTANCE_ACTIVE_M,
    MAX_DISTANCE_CAR_M,
    MAX_TIME_ACTIVE_MIN,
    MAX_TIME_CAR_MIN,
    MAX_TIME_PT_MIN,
    PT_TIME_LIMIT_MSG,
)
from goatlib.tools.base import BaseToolRunner
from goatlib.tools.catchment_area_v2 import (
    ACCESS_EGRESS_MODE_ICONS,
    ACCESS_EGRESS_MODE_LABELS,
    COST_TYPE_ICONS,
    COST_TYPE_LABELS,
    PT_MODE_LABELS,
    SECTION_CONFIGURATION,
)
from goatlib.tools.schemas import (
    ToolInputBase,
    get_default_layer_name,
)
from goatlib.tools.style import get_heatmap_style

logger = logging.getLogger(__name__)


class HeatmapRoutingMode(StrEnum):
    """Routing modes supported by heatmap v2.

    PT uses an arrive-by reverse-RAPTOR pipeline with precomputed per-mode
    access/egress lookup tables (the access/egress mode selects which table is
    loaded; only the walk table is generated so far, others resolve once built).
    """

    walking = "walking"
    bicycle = "bicycle"
    pedelec = "pedelec"
    car = "car"
    pt = "pt"


# Routing-mode icons/labels for the heatmap form. Extends the street-mode
# maps from the heatmap schema with a PT entry (matching catchment v2). The
# base street maps (without PT) are reused directly for the connectivity tile.
HM_ROUTING_MODE_ICONS: dict[str, str] = {**ROUTING_MODE_ICONS, "pt": "bus"}
HM_ROUTING_MODE_LABELS: dict[str, str] = {
    **ROUTING_MODE_LABELS,
    "pt": "routing_modes.pt",
}


# =========================================================================
# UI Sections
# =========================================================================

SECTION_ROUTING_HM = UISection(
    id="routing",
    order=1,
    icon="route",
    label_key="routing",
)

SECTION_OPPORTUNITIES_HM = UISection(
    id="opportunities",
    order=4,
    icon="opportunity",
    label_key="opportunities",
    depends_on={"routing_mode": {"$ne": None}},
)

SECTION_RESULT_HM = UISection(
    id="result",
    order=7,
    icon="save",
    label_key="result_layer_section",
    depends_on={"routing_mode": {"$ne": None}},
)

# Connectivity only: the reference area is a required input domain, so it gets
# its own section (ordered right after configuration) rather than sharing the
# advanced-clip slot the other heatmaps use.
SECTION_REFERENCE_AREA = UISection(
    id="reference_area",
    order=3,
    icon="layers",
    label_key="reference_area",
    depends_on={"routing_mode": {"$ne": None}},
)

# =========================================================================
# Label Mappings
# =========================================================================

HEATMAP_TYPE_LABELS: dict[str, str] = {
    "gravity": "enums.heatmap_type.gravity",
    "closest_average": "enums.heatmap_type.closest_average",
}

GRAVITY_DECAY_LABELS: dict[str, str] = {
    "gaussian": "enums.gravity_decay.gaussian",
    "exponential": "enums.gravity_decay.exponential",
    "linear": "enums.gravity_decay.linear",
    "power": "enums.gravity_decay.power",
}


# =========================================================================
# Form-layer opportunity schema
#
# Adds a point / polygon geometry filter to the layer selector on top of the
# analysis-layer OpportunityV2; instances stay compatible via inheritance.
# =========================================================================


class OpportunityV2PointBase(OpportunityV2):
    """Shared form-layer base for v2 opportunity cards. Accepts point or
    polygon layers, splits the per-opportunity budget into time/distance
    variants (gated by the outer cost_type), and hides formula-specific extras;
    the gravity / closest-average subclasses re-expose what each needs."""

    input_path: str = Field(
        ...,
        description="Path to opportunity dataset (point or polygon layer).",
        json_schema_extra=ui_field(
            section="opportunities",
            field_order=1,
            label_key="input_path",
            widget="layer-selector",
            widget_options={
                "geometry_types": [
                    "Point", "MultiPoint", "Polygon", "MultiPolygon",
                ]
            },
        ),
    )

    layer_project_id: int | None = Field(
        default=None,
        description="Project-layer id of the opportunity layer (auto-populated).",
        json_schema_extra=ui_field(
            section="opportunities", field_order=1, hidden=True
        ),
    )

    # Hide the inherited analysis-layer scalar `max_cost`. The runner sets
    # it via resolve_max_cost(cost_type) before handing the opportunity to
    # the analysis layer.
    max_cost: int = Field(
        default=DEFAULT_MAX_TIME_ACTIVE_MIN,
        gt=0,
        json_schema_extra=ui_field(section="opportunities", hidden=True),
    )

    max_cost_time: int = Field(
        default=DEFAULT_MAX_TIME_ACTIVE_MIN,
        ge=1,
        description="Maximum travel time in minutes.",
        json_schema_extra=ui_field(
            section="opportunities",
            field_order=2,
            label_key="max_cost_time",
            visible_when={
                "$and": [
                    {"input_path": {"$ne": None}},
                    {"cost_type": "time"},
                ]
            },
            widget_options={
                "default_by_field": {
                    "field": "routing_mode",
                    "values": {
                        "walking": DEFAULT_MAX_TIME_ACTIVE_MIN,
                        "bicycle": DEFAULT_MAX_TIME_ACTIVE_MIN,
                        "pedelec": DEFAULT_MAX_TIME_ACTIVE_MIN,
                        "car": DEFAULT_MAX_TIME_CAR_MIN,
                        "pt": DEFAULT_MAX_TIME_PT_MIN,
                    },
                },
                "max_value_from": {
                    "fields": [
                        {
                            "value": MAX_TIME_ACTIVE_MIN,
                            "when": {"routing_mode": "walking"},
                            "message": ACTIVE_TIME_LIMIT_MSG,
                        },
                        {
                            "value": MAX_TIME_ACTIVE_MIN,
                            "when": {"routing_mode": "bicycle"},
                            "message": ACTIVE_TIME_LIMIT_MSG,
                        },
                        {
                            "value": MAX_TIME_ACTIVE_MIN,
                            "when": {"routing_mode": "pedelec"},
                            "message": ACTIVE_TIME_LIMIT_MSG,
                        },
                        {
                            "value": MAX_TIME_CAR_MIN,
                            "when": {"routing_mode": "car"},
                            "message": CAR_TIME_LIMIT_MSG,
                        },
                        {
                            "value": MAX_TIME_PT_MIN,
                            "when": {"routing_mode": "pt"},
                            "message": PT_TIME_LIMIT_MSG,
                        },
                    ],
                    "min": 1,
                    "message": ACTIVE_TIME_LIMIT_MSG,
                },
            },
        ),
    )

    max_cost_distance: int = Field(
        default=DEFAULT_MAX_DISTANCE_ACTIVE_M,
        ge=50,
        description="Maximum travel distance in meters.",
        json_schema_extra=ui_field(
            section="opportunities",
            field_order=2,
            label_key="max_cost_distance",
            visible_when={
                "$and": [
                    {"input_path": {"$ne": None}},
                    {"cost_type": "distance"},
                ]
            },
            widget_options={
                "default_by_field": {
                    "field": "routing_mode",
                    "values": {
                        "walking": DEFAULT_MAX_DISTANCE_ACTIVE_M,
                        "bicycle": DEFAULT_MAX_DISTANCE_ACTIVE_M,
                        "pedelec": DEFAULT_MAX_DISTANCE_ACTIVE_M,
                        "car": DEFAULT_MAX_DISTANCE_CAR_M,
                    },
                },
                "max_value_from": {
                    "fields": [
                        {
                            "value": MAX_DISTANCE_ACTIVE_M,
                            "when": {"routing_mode": "walking"},
                            "message": ACTIVE_DISTANCE_LIMIT_MSG,
                        },
                        {
                            "value": MAX_DISTANCE_ACTIVE_M,
                            "when": {"routing_mode": "bicycle"},
                            "message": ACTIVE_DISTANCE_LIMIT_MSG,
                        },
                        {
                            "value": MAX_DISTANCE_ACTIVE_M,
                            "when": {"routing_mode": "pedelec"},
                            "message": ACTIVE_DISTANCE_LIMIT_MSG,
                        },
                        {
                            "value": MAX_DISTANCE_CAR_M,
                            "when": {"routing_mode": "car"},
                            "message": CAR_DISTANCE_LIMIT_MSG,
                        },
                    ],
                    "min": 50,
                    "message": ACTIVE_DISTANCE_LIMIT_MSG,
                },
            },
        ),
    )

    # Hide all formula-specific extras from the base. The two formula
    # subclasses below re-declare the fields they need as visible.
    sensitivity: float = Field(
        default=300000.0,
        ge=SENSITIVITY_MIN,
        le=SENSITIVITY_MAX,
        json_schema_extra=ui_field(section="opportunities", hidden=True),
    )
    potential_type: PotentialType = Field(
        default=PotentialType.constant,
        json_schema_extra=ui_field(section="opportunities", hidden=True),
    )
    potential_field: str | None = Field(
        None,
        json_schema_extra=ui_field(section="opportunities", hidden=True),
    )
    potential_constant: float | None = Field(
        1.0,
        gt=0.0,
        json_schema_extra=ui_field(section="opportunities", hidden=True),
    )
    potential_expression: PotentialExpression | None = Field(
        None,
        json_schema_extra=ui_field(section="opportunities", hidden=True),
    )
    n_destinations: Literal[1, 2, 3, 4, 5, 6, 7, 8, 9, 10] = Field(
        default=1,
        title="Number of Destinations",
        json_schema_extra=ui_field(section="opportunities", hidden=True),
    )

    def resolve_max_cost(self: Self, cost_type: CostType) -> int:
        """Return the active per-opp budget for the outer cost_type —
        minutes when time, meters when distance."""
        return (
            self.max_cost_distance if cost_type == CostType.distance
            else self.max_cost_time
        )


class OpportunityV2PointGravity(OpportunityV2PointBase):
    """Gravity opportunity card: re-exposes sensitivity + potential_* fields."""

    sensitivity: float = Field(
        default=300000.0,
        ge=SENSITIVITY_MIN,
        le=SENSITIVITY_MAX,
        description="Sensitivity parameter for gravity decay function "
                    "(larger = slower decay / wider reach).",
        json_schema_extra=ui_field(
            section="opportunities",
            field_order=10,
            label_key="sensitivity",
            widget="number",
            widget_options={
                "min": SENSITIVITY_MIN,
                "max": SENSITIVITY_MAX,
                "step": 1000,
            },
            visible_when={"input_path": {"$ne": None}},
        ),
    )
    potential_type: PotentialType = Field(
        default=PotentialType.constant,
        description="How to determine the potential value for each opportunity.",
        json_schema_extra=ui_field(
            section="opportunities",
            field_order=4,
            visible_when={"input_path": {"$ne": None}},
            widget_options={
                "enum_geometry_filter": {
                    "source_layer": "input_path",
                    "expression": ["Polygon", "MultiPolygon"],
                }
            },
        ),
    )
    potential_field: str | None = Field(
        None,
        description="Field name to use as potential.",
        json_schema_extra=ui_field(
            section="opportunities",
            field_order=5,
            widget="field-selector",
            widget_options={
                "source_layer": "input_path",
                "field_types": ["number"],
            },
            visible_when={
                "input_path": {"$ne": None},
                "potential_type": "field",
            },
        ),
    )
    potential_constant: float | None = Field(
        1.0,
        gt=0.0,
        description="Constant potential value applied to all features.",
        json_schema_extra=ui_field(
            section="opportunities",
            field_order=6,
            widget="number",
            visible_when={
                "input_path": {"$ne": None},
                "potential_type": "constant",
            },
        ),
    )
    potential_expression: PotentialExpression | None = Field(
        None,
        description="Expression to compute potential for polygon layers.",
        json_schema_extra=ui_field(
            section="opportunities",
            field_order=7,
            visible_when={
                "input_path": {"$ne": None},
                "potential_type": "expression",
            },
        ),
    )


class OpportunityV2PointClosestAverage(OpportunityV2PointBase):
    """Closest-Average opportunity card: re-exposes n_destinations."""

    n_destinations: int = Field(
        default=1,
        title="Number of Destinations",
        description="Number of closest destinations to average",
        json_schema_extra=ui_field(
            section="opportunities",
            field_order=5,
            label_key="n_destinations",
            widget="number",
            # min/max live in widget_options (not ge/le) so the field renders
            # as a number input rather than a slider; the 1–10 bound is
            # enforced server-side by the analysis-layer schema.
            widget_options={
                "min": N_DESTINATIONS_MIN,
                "max": N_DESTINATIONS_MAX,
                "step": 1,
            },
            visible_when={"input_path": {"$ne": None}},
        ),
    )


# =========================================================================
# Windmill Params
# =========================================================================


class HeatmapV2WindmillParams(ToolInputBase):
    """Windmill-facing params for HeatmapV2.

    Mode/cost/PT fields mirror catchment_area_v2's structure exactly. The
    runner's `process()` resolves the per-mode budget fields into a single
    `max_cost`, builds the analysis-level `HeatmapV2Params`, and hands off
    to `HeatmapV2Tool`.
    """

    model_config = ConfigDict(
        json_schema_extra=ui_sections(
            SECTION_ROUTING_HM,
            SECTION_CONFIGURATION,
            SECTION_OPPORTUNITIES_HM,
            SECTION_RESULT_HM,
        )
    )

    # =========================================================================
    # Result Section
    # =========================================================================

    result_layer_name: str | None = Field(
        default=get_default_layer_name("heatmap_gravity", "en"),
        description="Name for the heatmap result layer.",
        json_schema_extra=ui_field(
            section="result",
            field_order=1,
            label_key="result_layer_name",
            widget_options={
                "default_en": get_default_layer_name("heatmap_gravity", "en"),
                "default_de": get_default_layer_name("heatmap_gravity", "de"),
            },
        ),
    )

    # =========================================================================
    # Routing Section
    # =========================================================================

    routing_mode: HeatmapRoutingMode = Field(
        ...,
        description="Transport mode for the heatmap.",
        json_schema_extra=ui_field(
            section="routing",
            field_order=1,
            label_key="routing_mode",
            enum_icons=HM_ROUTING_MODE_ICONS,
            enum_labels=HM_ROUTING_MODE_LABELS,
        ),
    )

    # PT transit-mode filter (only the listed PT classes are used). Mirrors
    # catchment v2's pt_modes. Visible only for PT.
    pt_modes: list[PTMode] | None = Field(
        default=list(PTMode),
        description="Public transport modes to include.",
        json_schema_extra=ui_field(
            section="routing",
            field_order=2,
            label_key="choose_pt_mode",
            enum_labels=PT_MODE_LABELS,
            visible_when={"routing_mode": "pt"},
        ),
    )

    # =========================================================================
    # Configuration Section — heatmap formula + measure unit
    # =========================================================================

    heatmap_type: HeatmapType = Field(
        default=HeatmapType.gravity,
        description="Formula used to score each cell from reachable opportunities.",
        json_schema_extra=ui_field(
            section="configuration",
            field_order=0,
            label_key="heatmap_type",
            enum_labels=HEATMAP_TYPE_LABELS,
        ),
    )

    # Cost type (time vs distance) — mirrors catchment_area_v2. Drives which
    # set of per-opportunity budget fields apply.
    cost_type: CostType = Field(
        default=CostType.time,
        description="Measure the heatmap by travel time or travel distance.",
        json_schema_extra=ui_field(
            section="configuration",
            field_order=2,
            label_key="measure_type",
            enum_labels=COST_TYPE_LABELS,
            enum_icons=COST_TYPE_ICONS,
            inline_group="cost_config",
            # PT is always time-based (total journey minutes); hide the
            # time/distance selector for PT.
            visible_when={
                "routing_mode": {"$in": ["walking", "bicycle", "pedelec", "car"]}
            },
        ),
    )

    # =========================================================================
    # PT (routing_mode == pt) — arrive-by reverse RAPTOR.
    #
    # Unlike catchment (departure), the PT heatmap is anchored on an ARRIVAL
    # time: every reachable cell's score reflects a journey arriving by this
    # time. Access/egress mode + time budget mirror catchment (see below);
    # the budget is capped at the lookup table's built max (20 min). The
    # per-opportunity max_cost is the total journey budget.
    # =========================================================================

    pt_day: Weekday = Field(
        default=Weekday.weekday,
        description="Day type for PT schedule.",
        json_schema_extra=ui_field(
            section="configuration",
            field_order=3,
            label_key="weekday",
            enum_labels=WEEKDAY_LABELS,
            visible_when={"routing_mode": "pt"},
        ),
    )
    pt_arrival_time: int = Field(
        default=32400,  # 09:00
        ge=0,
        le=86399,
        description="Arrive-by time of day (seconds from midnight).",
        json_schema_extra=ui_field(
            section="configuration",
            field_order=4,
            label_key="arrival_time",
            widget="time-picker",
            visible_when={"routing_mode": "pt"},
        ),
    )
    # Access & egress legs — mirrors catchment_area_v2's PT access/egress
    # (mode selector + per-leg budget, grouped, under Advanced). Unlike
    # catchment, the legs are served by precomputed per-mode lookup tables
    # (minutes, mode speed baked in), so there's no speed/distance override
    # and the budget is capped at the table's built max (20 min). The mode
    # selects which lookup table is loaded.
    # Access/egress legs are walk-only for PT heatmaps: only the walk
    # access/egress lookup table is precomputed. The mode selector stays visible
    # for consistency with the other legs/config, but is restricted to the
    # single "walk" option (== AccessEgressMode.walk) via the Literal type.
    pt_access_mode: Literal["walk"] = Field(
        default="walk",
        description="Mode to reach transit stops (walk-only for PT heatmaps).",
        # Literal keeps validation walk-only (emits `const`); the explicit
        # `enum` makes the frontend render it as a (single-option) dropdown,
        # since it derives options from schema `enum`, not `const`.
        json_schema_extra={
            **ui_field(
                section="configuration",
                field_order=20,
                label_key="access_mode",
                group_label="groups.access_leg",
                enum_icons=ACCESS_EGRESS_MODE_ICONS,
                enum_labels=ACCESS_EGRESS_MODE_LABELS,
                visible_when={
                    "$and": [
                        {"routing_mode": "pt"},
                        {"show_advanced": True},
                    ]
                },
            ),
            "enum": [AccessEgressMode.walk.value],
        },
    )
    pt_access_max_time: int = Field(
        default=DEFAULT_MAX_TIME_ACTIVE_MIN,
        # No ge/le: bounds come from widget_options.max_value_from (a plain
        # number input). Pydantic ge+le would emit schema min+max, which the
        # form renders as a slider — catchment avoids this the same way.
        description="Access leg budget in minutes (≤ the lookup table max).",
        json_schema_extra=ui_field(
            section="configuration",
            field_order=21,
            label_key="time_limit",
            inline_group="pt_access_cost",
            inline_flex="1 0 0",
            visible_when={
                "$and": [
                    {"routing_mode": "pt"},
                    {"show_advanced": True},
                ]
            },
            widget_options={
                "max_value_from": {
                    "fields": [],
                    "message": "pt_access_time_limit_message",
                    "max": 20,
                    "min": 1,
                },
            },
        ),
    )
    pt_egress_mode: Literal["walk"] = Field(
        default="walk",
        description="Mode from transit stops to the opportunity "
                    "(walk-only for PT heatmaps).",
        # See pt_access_mode: Literal for validation + explicit enum so the
        # frontend renders a (single-option) dropdown.
        json_schema_extra={
            **ui_field(
                section="configuration",
                field_order=22,
                label_key="pt_egress_mode",
                group_label="groups.egress_leg",
                enum_icons=ACCESS_EGRESS_MODE_ICONS,
                enum_labels=ACCESS_EGRESS_MODE_LABELS,
                visible_when={
                    "$and": [
                        {"routing_mode": "pt"},
                        {"show_advanced": True},
                    ]
                },
            ),
            "enum": [AccessEgressMode.walk.value],
        },
    )
    pt_egress_max_time: int = Field(
        default=DEFAULT_MAX_TIME_ACTIVE_MIN,
        # No ge/le — see pt_access_max_time (avoids the slider; number input).
        description="Egress leg budget in minutes (≤ the lookup table max).",
        json_schema_extra=ui_field(
            section="configuration",
            field_order=23,
            label_key="time_limit",
            inline_group="pt_egress_cost",
            inline_flex="1 0 0",
            visible_when={
                "$and": [
                    {"routing_mode": "pt"},
                    {"show_advanced": True},
                ]
            },
            widget_options={
                "max_value_from": {
                    "fields": [],
                    "message": "pt_egress_time_limit_message",
                    "max": 20,
                    "min": 1,
                },
            },
        ),
    )
    pt_max_transfers: int = Field(
        default=5,
        # No ge/le — see pt_access_max_time (avoids the slider; number input).
        description="Maximum number of transit transfers.",
        json_schema_extra=ui_field(
            section="configuration",
            field_order=17,
            label_key="max_transfers",
            visible_when={
                "$and": [
                    {"routing_mode": "pt"},
                    {"show_advanced": True},
                ]
            },
            widget_options={
                "max_value_from": {
                    "fields": [],
                    "message": "max_transfers_limit_message",
                    "max": 5,
                    "min": 0,
                },
            },
        ),
    )

    decay: GravityDecay = Field(
        default=GravityDecay.gaussian,
        description="Shape of the distance-decay curve applied to travel cost.",
        json_schema_extra=ui_field(
            section="configuration",
            field_order=1,
            label_key="impedance",
            enum_labels=GRAVITY_DECAY_LABELS,
            visible_when={"heatmap_type": "gravity"},
        ),
    )

    max_sensitivity: float = Field(
        default=1_000_000.0,
        gt=0.0,
        description="Gravity sensitivity normalization anchor.",
        json_schema_extra=ui_field(
            section="configuration",
            field_order=14,
            hidden=True,  # Internal normalization constant
        ),
    )

    # Mirrors catchment_area_v2.show_advanced: gates the Speed override
    # (and any other advanced-only field) behind a single toggle.
    show_advanced: bool = Field(
        default=False,
        description="Show advanced configuration options.",
        json_schema_extra=ui_field(
            section="configuration",
            field_order=15,
            label_key="advanced_options",
            widget="advanced-toggle",
        ),
    )

    h3_resolution: int | None = Field(
        default=None,
        ge=5,
        le=12,
        description="H3 resolution for origin tiling. None → per-mode default.",
        json_schema_extra=ui_field(
            section="configuration",
            field_order=16,
            label_key="h3_resolution",
            hidden=True,  # Advanced; expose later if needed
        ),
    )

    # Optional reference-area clip — when set, output cells are restricted
    # to those inside the polygon (cells outside dropped; cells inside that
    # weren't reached become NULL). Gated behind show_advanced so it shares
    # the same toggle as speed; connectivity overrides this to required +
    # always-visible.
    reference_area_layer_id: str | None = Field(
        None,
        description="Layer ID for the reference area polygon.",
        json_schema_extra=ui_field(
            section="configuration",
            # Top of the advanced options — right after the show_advanced
            # toggle (15) and before the PT access/egress groups (20-23), so
            # it isn't pulled into the access leg group.
            field_order=16,
            label_key="reference_area_path",
            widget="layer-selector",
            widget_options={"geometry_types": ["Polygon", "MultiPolygon"]},
            visible_when={"show_advanced": True},
            # Advanced-only clip: stays optional when shown so the user can
            # enable Advanced for other fields (e.g. speed) and leave this
            # blank. Connectivity overrides to required.
            optional=True,
        ),
    )
    reference_area_layer_filter: dict[str, Any] | None = Field(
        None,
        description="CQL2-JSON filter to apply to the reference area layer.",
        json_schema_extra=ui_field(
            section="configuration", field_order=16, hidden=True
        ),
    )

    # =========================================================================
    # Cost / budget / speed
    #
    # v2 mirrors the matrix-based gravity tool: per-opportunity `max_cost`
    # lives on each OpportunityGravity entry under the Opportunities section
    # (in minutes). Mode-default speeds drive routing — surfaced as advanced
    # if the user needs to override.
    # =========================================================================

    speed: float | None = Field(
        default=None,
        description=(
            "Travel speed in km/h. Leave blank to use the mode default "
            "(walking 5, bicycle 15, pedelec 23). Car uses per-road speed "
            "limits and ignores this setting."
        ),
        json_schema_extra=ui_field(
            section="configuration",
            field_order=20,
            label_key="speed",
            visible_when={
                "$and": [
                    {"routing_mode": {"$in": ["walking", "bicycle", "pedelec"]}},
                    {"cost_type": "time"},
                    {"show_advanced": True},
                ]
            },
            widget_options={
                "default_by_field": {
                    "field": "routing_mode",
                    "values": {"walking": 5, "bicycle": 15, "pedelec": 23},
                },
                "max_value_from": {
                    "fields": [
                        {"value": 30, "when": {"routing_mode": "walking"},
                         "message": "walking_speed_limit_message"},
                        {"value": 60, "when": {"routing_mode": "bicycle"},
                         "message": "bicycle_speed_limit_message"},
                        {"value": 60, "when": {"routing_mode": "pedelec"},
                         "message": "pedelec_speed_limit_message"},
                    ],
                    "min": 1,
                    "message": "walking_speed_limit_message",
                },
            },
        ),
    )

    # =========================================================================
    # Opportunity layers (Gravity / ClosestAverage — workflow-canvas
    # connectors, so hidden in the form). Up to 3 layers.
    # =========================================================================

    opportunity_layer_1_id: str | None = Field(
        None,
        description="First opportunity layer.",
        json_schema_extra=ui_field(
            section="opportunities",
            field_order=1,
            widget="layer-selector",
            label_key="opportunity_layer_1",
            hidden=True,
            visible_when={
                "heatmap_type": {"$in": ["gravity", "closest_average"]}
            },
        ),
    )
    opportunity_layer_1_filter: dict[str, Any] | None = Field(
        None,
        json_schema_extra=ui_field(section="opportunities", field_order=2, hidden=True),
    )
    opportunity_layer_2_id: str | None = Field(
        None,
        description="Second opportunity layer.",
        json_schema_extra=ui_field(
            section="opportunities",
            field_order=3,
            widget="layer-selector",
            label_key="opportunity_layer_2",
            hidden=True,
            visible_when={
                "heatmap_type": {"$in": ["gravity", "closest_average"]}
            },
        ),
    )
    opportunity_layer_2_filter: dict[str, Any] | None = Field(
        None,
        json_schema_extra=ui_field(section="opportunities", field_order=4, hidden=True),
    )
    opportunity_layer_3_id: str | None = Field(
        None,
        description="Third opportunity layer.",
        json_schema_extra=ui_field(
            section="opportunities",
            field_order=5,
            widget="layer-selector",
            label_key="opportunity_layer_3",
            hidden=True,
            visible_when={
                "heatmap_type": {"$in": ["gravity", "closest_average"]}
            },
        ),
    )
    opportunity_layer_3_filter: dict[str, Any] | None = Field(
        None,
        json_schema_extra=ui_field(section="opportunities", field_order=6, hidden=True),
    )

    # =========================================================================
    # Opportunities list (toolbox UI: repeatable layer entries with per-layer
    # weight + sensitivity controls). Workflow-canvas numbered layer-IDs above
    # take precedence when present (the runner re-packs them into this list).
    # =========================================================================

    opportunities: list[OpportunityV2] | None = Field(
        default=None,
        description="Opportunity layers to score against.",
        json_schema_extra=ui_field(
            section="opportunities",
            field_order=10,
            repeatable=True,
            min_items=1,
            visible_when={
                "heatmap_type": {"$in": ["gravity", "closest_average"]}
            },
        ),
    )

    # =========================================================================
    # Helpers
    # =========================================================================

    def aggregate_max_cost(self: Self) -> float:
        """Maximum per-opportunity budget across all layers — used so the
        loaded network buffer covers every layer's reach. Unit follows
        cost_type: minutes for time, meters for distance."""
        if not self.opportunities:
            return 30.0
        budgets = [
            o.resolve_max_cost(self.cost_type)
            if isinstance(o, OpportunityV2PointBase)
            else o.max_cost
            for o in self.opportunities
        ]
        return float(max(budgets))

    def resolved_opportunities(self: Self) -> list[OpportunityV2]:
        """Project form opportunities to analysis-layer OpportunityV2,
        collapsing max_cost_time / max_cost_distance into max_cost based on
        the form's cost_type."""
        if not self.opportunities:
            return []
        out: list[OpportunityV2] = []
        for o in self.opportunities:
            if isinstance(o, OpportunityV2PointBase):
                data = o.model_dump(
                    exclude={"max_cost_time", "max_cost_distance"}
                )
                data["max_cost"] = o.resolve_max_cost(self.cost_type)
                out.append(OpportunityV2(**data))
            else:
                out.append(o)
        return out


# =========================================================================
# Per-formula entry points
#
# The toolbox surfaces one tool per heatmap formula (Gravity / ClosestAverage).
# Each pre-binds heatmap_type and hides the selector so the formula-specific
# tile renders a focused form.
# =========================================================================


class HeatmapGravityV2WindmillParams(HeatmapV2WindmillParams):
    """Gravity-based spatial accessibility analysis."""

    heatmap_type: HeatmapType = Field(
        default=HeatmapType.gravity,
        json_schema_extra=ui_field(section="configuration", hidden=True),
    )
    # Mirrors v1 HeatmapGravityParams: opportunities required, 1-3 layers.
    opportunities: list[OpportunityV2PointGravity] = Field(
        ...,
        title="Opportunity Layers",
        min_length=1,
        max_length=3,
        description="Opportunity layers to score against.",
        json_schema_extra=ui_field(
            section="opportunities",
            field_order=10,
            repeatable=True,
            min_items=1,
            max_items=3,
        ),
    )
    result_layer_name: str | None = Field(
        default=get_default_layer_name("heatmap_gravity", "en"),
        json_schema_extra=ui_field(
            section="result",
            field_order=1,
            label_key="result_layer_name",
            widget_options={
                "default_en": get_default_layer_name("heatmap_gravity", "en"),
                "default_de": get_default_layer_name("heatmap_gravity", "de"),
            },
        ),
    )


class HeatmapClosestAverageV2WindmillParams(HeatmapV2WindmillParams):
    """Average distance/time to N closest destinations."""

    heatmap_type: HeatmapType = Field(
        default=HeatmapType.closest_average,
        json_schema_extra=ui_field(section="configuration", hidden=True),
    )
    decay: GravityDecay = Field(
        default=GravityDecay.gaussian,
        json_schema_extra=ui_field(section="configuration", hidden=True),
    )
    # Mirrors v1 HeatmapClosestAverageParams: opportunities required, 1-3 layers.
    opportunities: list[OpportunityV2PointClosestAverage] = Field(
        ...,
        title="Opportunity Layers",
        min_length=1,
        max_length=3,
        description="Opportunity layers to score against.",
        json_schema_extra=ui_field(
            section="opportunities",
            field_order=10,
            repeatable=True,
            min_items=1,
            max_items=3,
        ),
    )
    result_layer_name: str | None = Field(
        default=get_default_layer_name("heatmap_closest_average", "en"),
        json_schema_extra=ui_field(
            section="result",
            field_order=1,
            label_key="result_layer_name",
            widget_options={
                "default_en": get_default_layer_name(
                    "heatmap_closest_average", "en"
                ),
                "default_de": get_default_layer_name(
                    "heatmap_closest_average", "de"
                ),
            },
        ),
    )


class HeatmapConnectivityV2WindmillParams(HeatmapV2WindmillParams):
    """Total area reachable within max travel cost."""

    # Adds a dedicated reference-area section (its required input domain) to
    # the inherited routing → configuration → opportunities → result layout.
    model_config = ConfigDict(
        json_schema_extra=ui_sections(
            SECTION_ROUTING_HM,
            SECTION_CONFIGURATION,
            SECTION_REFERENCE_AREA,
            SECTION_OPPORTUNITIES_HM,
            SECTION_RESULT_HM,
        )
    )

    # routing_mode is inherited from the base (full mode set incl. PT). PT
    # connectivity runs through the same arrive-by reverse-RAPTOR pipeline as
    # gravity/closest-average; the inherited PT fields (arrival time,
    # access/egress, transfers) surface via their routing_mode == pt guards.

    # Hide the heatmap_type selector and pre-bind to connectivity
    heatmap_type: HeatmapType = Field(
        default=HeatmapType.connectivity,
        description="Heatmap formula (pre-bound to connectivity).",
        json_schema_extra=ui_field(
            section="configuration",
            field_order=2,
            hidden=True,
        ),
    )

    # Opportunity layers are not used for connectivity — override as optional
    # with empty default so the base-class validator doesn't demand them.
    opportunities: list[OpportunityV2] | None = Field(
        default=None,
        description="Not used for connectivity (pre-bound formula).",
        json_schema_extra=ui_field(
            section="opportunities",
            field_order=10,
            repeatable=True,
            min_items=1,
            hidden=True,
            visible_when={
                "heatmap_type": {"$in": ["gravity", "closest_average"]}
            },
        ),
    )

    # Travel budget — two fields gated by cost_type. Per-mode caps come from
    # widget_options.max_value_from (active vs. car). Same pattern as the
    # per-opportunity max_cost on OpportunityV2Point.
    max_cost_time: int = Field(
        default=DEFAULT_MAX_TIME_ACTIVE_MIN,
        ge=1,
        description="Maximum travel time in minutes.",
        json_schema_extra=ui_field(
            section="configuration",
            field_order=3,
            label_key="max_cost_time",
            visible_when={"cost_type": "time"},
            widget_options={
                "default_by_field": {
                    "field": "routing_mode",
                    "values": {
                        "walking": DEFAULT_MAX_TIME_ACTIVE_MIN,
                        "bicycle": DEFAULT_MAX_TIME_ACTIVE_MIN,
                        "pedelec": DEFAULT_MAX_TIME_ACTIVE_MIN,
                        "car": DEFAULT_MAX_TIME_CAR_MIN,
                        "pt": DEFAULT_MAX_TIME_PT_MIN,
                    },
                },
                "max_value_from": {
                    "fields": [
                        {
                            "value": MAX_TIME_ACTIVE_MIN,
                            "when": {"routing_mode": "walking"},
                            "message": ACTIVE_TIME_LIMIT_MSG,
                        },
                        {
                            "value": MAX_TIME_ACTIVE_MIN,
                            "when": {"routing_mode": "bicycle"},
                            "message": ACTIVE_TIME_LIMIT_MSG,
                        },
                        {
                            "value": MAX_TIME_ACTIVE_MIN,
                            "when": {"routing_mode": "pedelec"},
                            "message": ACTIVE_TIME_LIMIT_MSG,
                        },
                        {
                            "value": MAX_TIME_CAR_MIN,
                            "when": {"routing_mode": "car"},
                            "message": CAR_TIME_LIMIT_MSG,
                        },
                        {
                            "value": MAX_TIME_PT_MIN,
                            "when": {"routing_mode": "pt"},
                            "message": PT_TIME_LIMIT_MSG,
                        },
                    ],
                    "min": 1,
                    "message": ACTIVE_TIME_LIMIT_MSG,
                },
            },
        ),
    )

    max_cost_distance: int = Field(
        default=DEFAULT_MAX_DISTANCE_ACTIVE_M,
        ge=50,
        description="Maximum travel distance in meters.",
        json_schema_extra=ui_field(
            section="configuration",
            field_order=3,
            label_key="max_cost_distance",
            visible_when={"cost_type": "distance"},
            widget_options={
                "default_by_field": {
                    "field": "routing_mode",
                    "values": {
                        "walking": DEFAULT_MAX_DISTANCE_ACTIVE_M,
                        "bicycle": DEFAULT_MAX_DISTANCE_ACTIVE_M,
                        "pedelec": DEFAULT_MAX_DISTANCE_ACTIVE_M,
                        "car": DEFAULT_MAX_DISTANCE_CAR_M,
                    },
                },
                "max_value_from": {
                    "fields": [
                        {
                            "value": MAX_DISTANCE_ACTIVE_M,
                            "when": {"routing_mode": "walking"},
                            "message": ACTIVE_DISTANCE_LIMIT_MSG,
                        },
                        {
                            "value": MAX_DISTANCE_ACTIVE_M,
                            "when": {"routing_mode": "bicycle"},
                            "message": ACTIVE_DISTANCE_LIMIT_MSG,
                        },
                        {
                            "value": MAX_DISTANCE_ACTIVE_M,
                            "when": {"routing_mode": "pedelec"},
                            "message": ACTIVE_DISTANCE_LIMIT_MSG,
                        },
                        {
                            "value": MAX_DISTANCE_CAR_M,
                            "when": {"routing_mode": "car"},
                            "message": CAR_DISTANCE_LIMIT_MSG,
                        },
                    ],
                    "min": 50,
                    "message": ACTIVE_DISTANCE_LIMIT_MSG,
                },
            },
        ),
    )

    # Connectivity requires the reference area; promote the inherited
    # optional+advanced field to required, in its own dedicated section.
    reference_area_layer_id: str = Field(
        ...,
        description="Layer ID for the reference area polygon.",
        json_schema_extra=ui_field(
            section="reference_area",
            field_order=1,
            label_key="reference_area_path",
            widget="layer-selector",
            widget_options={"geometry_types": ["Polygon", "MultiPolygon"]},
        ),
    )

    result_layer_name: str | None = Field(
        default=get_default_layer_name("heatmap_connectivity", "en"),
        json_schema_extra=ui_field(
            section="result",
            field_order=1,
            label_key="result_layer_name",
            widget_options={
                "default_en": get_default_layer_name(
                    "heatmap_connectivity", "en"
                ),
                "default_de": get_default_layer_name(
                    "heatmap_connectivity", "de"
                ),
            },
        ),
    )

    def aggregate_max_cost(self: Self) -> float:
        """Connectivity budget — minutes (time) or meters (distance)."""
        return float(
            self.max_cost_distance if self.cost_type == CostType.distance
            else self.max_cost_time
        )


# =========================================================================
# Runner
# =========================================================================


# HeatmapRoutingMode (UI layer) → analysis-layer RoutingMode.
# Both enums have identical values for the supported modes; the map exists
# only to make the type conversion explicit.
_ROUTING_MODE_MAP: dict[HeatmapRoutingMode, RoutingMode] = {
    HeatmapRoutingMode.walking: RoutingMode.walking,
    HeatmapRoutingMode.bicycle: RoutingMode.bicycle,
    HeatmapRoutingMode.pedelec: RoutingMode.pedelec,
    HeatmapRoutingMode.car: RoutingMode.car,
    HeatmapRoutingMode.pt: RoutingMode.pt,
}

# PT access/egress mode (catchment-style "walk" naming) → analysis RoutingMode.
# The analysis layer resolves the per-mode lookup table from this.
_ACCESS_EGRESS_MODE_MAP: dict[AccessEgressMode, RoutingMode] = {
    AccessEgressMode.walk: RoutingMode.walking,
    AccessEgressMode.bicycle: RoutingMode.bicycle,
    AccessEgressMode.pedelec: RoutingMode.pedelec,
    AccessEgressMode.car: RoutingMode.car,
}

# Anchor dates per weekday type — must match catchment v2's
# `_pt_departure_unix_minutes` so PT routing resolves against the same
# representative service days.
_PT_WEEKDAY_DATES: dict[str, date] = {
    "weekday": date(2026, 6, 16),
    "saturday": date(2026, 6, 20),
    "sunday": date(2026, 6, 21),
}


def _pt_arrival_unix_minutes(pt_day: Weekday, seconds_of_day: int) -> int:
    """Convert a weekday type + time-of-day into a unix-minute arrival
    anchor (UTC), mirroring catchment v2's departure conversion."""
    day_value = pt_day.value if hasattr(pt_day, "value") else str(pt_day)
    anchor = _PT_WEEKDAY_DATES.get(day_value, _PT_WEEKDAY_DATES["weekday"])
    arrival_dt = datetime.combine(
        anchor, time_of_day.min, tzinfo=timezone.utc
    ) + timedelta(seconds=seconds_of_day)
    return int(arrival_dt.timestamp() // 60)


class Heatmap2SFCAV2WindmillParams(HeatmapV2WindmillParams):
    """Two-Step Floating Catchment Area accessibility analysis."""

    heatmap_type: HeatmapType = Field(
        default=HeatmapType.two_sfca,
        json_schema_extra=ui_field(section="configuration", hidden=True),
    )
    two_sfca_type: TwoSFCAType = Field(
        default=TwoSFCAType.twosfca,
        description="2SFCA method variant (standard / E2SFCA / M2SFCA).",
        json_schema_extra=ui_field(
            section="configuration",
            field_order=5,
            label_key="two_sfca_type",
            enum_labels=TwoSFCAType_LABELS,
        ),
    )
    # Supply layers — capacity is carried by the opportunity potential fields.
    opportunities: list[OpportunityV2PointGravity] = Field(
        ...,
        title="Supply Layers",
        min_length=1,
        max_length=3,
        description="Supply layers; each opportunity's potential is its capacity.",
        json_schema_extra=ui_field(
            section="opportunities",
            field_order=10,
            repeatable=True,
            min_items=1,
            max_items=3,
        ),
    )
    # Demand layer (population). Rasterized to cells by the analysis layer.
    demand_layer_id: str = Field(
        ...,
        description="Demand layer (e.g. population).",
        json_schema_extra=ui_field(
            section="configuration",
            field_order=6,
            label_key="demand_path",
            widget="layer-selector",
        ),
    )
    demand_layer_filter: dict[str, Any] | None = Field(
        default=None,
        json_schema_extra=ui_field(
            section="configuration", field_order=7, hidden=True
        ),
    )
    demand_field: str = Field(
        ...,
        description="Field in the demand layer holding the demand value.",
        json_schema_extra=ui_field(
            section="configuration",
            field_order=8,
            label_key="demand_field",
            widget="field-selector",
            widget_options={
                "source_layer": "demand_layer_id",
                "field_types": ["number"],
            },
            visible_when={"demand_layer_id": {"$ne": None}},
        ),
    )
    result_layer_name: str | None = Field(
        default=get_default_layer_name("heatmap_2sfca", "en"),
        json_schema_extra=ui_field(
            section="result",
            field_order=1,
            label_key="result_layer_name",
            widget_options={
                "default_en": get_default_layer_name("heatmap_2sfca", "en"),
                "default_de": get_default_layer_name("heatmap_2sfca", "de"),
            },
        ),
    )


class HeatmapV2ToolRunner(BaseToolRunner[HeatmapV2WindmillParams]):
    """Heatmap V2 tool runner for Windmill — local C++ routing backend."""

    tool_class = HeatmapV2Tool
    output_geometry_type = "polygon"  # H3 cells
    default_output_name = get_default_layer_name("heatmap_gravity", "en")

    @classmethod
    def predict_output_schema(
        cls,
        input_schemas: dict[str, dict[str, str]],
        params: dict[str, Any],
    ) -> dict[str, str]:
        return {
            "h3_index": "VARCHAR",
            "total_accessibility": "DOUBLE",
            "geometry": "GEOMETRY",
        }

    def get_layer_properties(
        self: Self,
        params: HeatmapV2WindmillParams,
        metadata: DatasetMetadata,
        table_info: dict[str, Any] | None = None,
        parquet_path: Path | str | None = None,
    ) -> dict[str, Any] | None:
        color_field = "total_accessibility"
        color_scale_breaks = None
        table_name = table_info["table_name"] if table_info else None
        if table_name or parquet_path:
            color_scale_breaks = self.compute_quantile_breaks(
                table_name=table_name,
                column_name=color_field,
                num_breaks=6,
                strip_zeros=True,
                parquet_path=parquet_path,
            )
        return get_heatmap_style(
            color_field_name=color_field,
            color_scale_breaks=color_scale_breaks,
            color_range_name="Emrld",
        )

    # --------------------------------------------------------- helpers

    def _resolve_opportunities(
        self: Self, params: HeatmapV2WindmillParams
    ) -> list[OpportunityV2]:
        """Resolve opportunity layer IDs → parquet paths.

        Two entry shapes:
          (1) Toolbox form: `params.opportunities` holds OpportunityV2
              instances where `input_path` is a layer UUID and the
              per-layer fields (potential_type / potential_field /
              potential_constant / potential_expression / sensitivity /
              input_layer_filter / name) are already populated by the UI.
              `resolve_layer_paths` swaps the UUID for an exported parquet
              path, applies the CQL filter, and preserves every other
              field on the model.
          (2) Workflow canvas: the canvas connector only supplies layer
              IDs via the numbered `opportunity_layer_{1,2,3}_id` fields;
              per-layer config is unavailable, so we construct stub
              OpportunityV2 entries with just `input_path`.
        Workflow-canvas IDs take precedence when present.
        """
        numbered_ids = [
            params.opportunity_layer_1_id,
            params.opportunity_layer_2_id,
            params.opportunity_layer_3_id,
        ]
        if any(numbered_ids):
            # Workflow-canvas path: bare layer IDs, no per-layer config —
            # take the form's resolved budget as the default for every
            # canvas opportunity.
            fallback_max_cost = int(params.aggregate_max_cost())
            opps: list[OpportunityV2] = []
            for layer_id in numbered_ids:
                if not layer_id:
                    continue
                parquet_path = str(
                    self.export_layer_to_parquet(
                        layer_id=layer_id,
                        user_id=params.user_id,
                        project_id=params.project_id,
                    )
                )
                opps.append(
                    OpportunityV2(
                        input_path=parquet_path,
                        max_cost=fallback_max_cost,
                    )
                )
            return opps

        if not params.opportunities:
            raise ValueError(
                "At least one opportunity layer is required "
                "(via opportunity_layer_{1,2,3}_id or the opportunities list)."
            )
        # Toolbox-form path: collapse OpportunityV2PointBase's per-mode budget
        # fields into the analysis-layer OpportunityV2.max_cost (resolved
        # against the form's outer routing_mode + cost_type), then swap
        # layer UUIDs for parquet paths.
        # Name the result column after the project layer. Set before
        # resolve_layer_paths, which fills the dataset name when name is unset.
        resolved = params.resolved_opportunities()
        named = []
        for opp, card in zip(resolved, params.opportunities):
            if not opp.name:
                proj_name = self.get_project_layer_name_by_id(
                    getattr(card, "layer_project_id", None)
                )
                if proj_name:
                    opp = opp.model_copy(update={"name": proj_name})
            named.append(opp)
        return self.resolve_layer_paths(named, params.user_id, "input_path")

    def _resolve_reference_area(
        self: Self, params: HeatmapV2WindmillParams
    ) -> str | None:
        """Export the reference area layer (if any) to a parquet path.
        Returns None when the user didn't supply one (gravity/closest_avg
        advanced field left blank). Connectivity's subclass marks the
        field as required, so this returns a path for that tool."""
        if not getattr(params, "reference_area_layer_id", None):
            return None
        return str(
            self.export_layer_to_parquet(
                layer_id=params.reference_area_layer_id,
                user_id=params.user_id,
                cql_filter=params.reference_area_layer_filter,
                scenario_id=params.scenario_id,
                project_id=params.project_id,
            )
        )

    def _resolve_demand(
        self: Self, params: HeatmapV2WindmillParams
    ) -> str | None:
        """Export the demand layer (2SFCA only) to a parquet path."""
        if not getattr(params, "demand_layer_id", None):
            return None
        return str(
            self.export_layer_to_parquet(
                layer_id=params.demand_layer_id,
                user_id=params.user_id,
                cql_filter=getattr(params, "demand_layer_filter", None),
                scenario_id=params.scenario_id,
                project_id=params.project_id,
            )
        )

    # --------------------------------------------------------- main

    def process(
        self: Self, params: HeatmapV2WindmillParams, temp_dir: Path
    ) -> tuple[Path, DatasetMetadata]:
        output_path = temp_dir / "output.parquet"

        # Connectivity uses the reference area as the input domain; gravity
        # / closest_avg uses it (optional, advanced) to clip the output.
        is_connectivity = params.heatmap_type == HeatmapType.connectivity
        reference_area_path = self._resolve_reference_area(params)
        resolved_opportunities = (
            [] if is_connectivity else self._resolve_opportunities(params)
        )

        # 2SFCA: resolve the demand layer + method variant.
        is_two_sfca = params.heatmap_type == HeatmapType.two_sfca
        demand_path = self._resolve_demand(params) if is_two_sfca else None
        demand_field = getattr(params, "demand_field", None)
        two_sfca_type = getattr(params, "two_sfca_type", TwoSFCAType.twosfca)

        # routing_mode is HeatmapRoutingMode across all heatmap types; normalise
        # via value to be robust to a raw string coming from Windmill.
        mode = HeatmapRoutingMode(
            params.routing_mode.value
            if hasattr(params.routing_mode, "value")
            else params.routing_mode
        )
        is_pt = mode == HeatmapRoutingMode.pt

        analysis_params = HeatmapV2Params(
            # Study area
            h3_resolution=params.h3_resolution,
            # Routing
            routing_mode=_ROUTING_MODE_MAP[mode],
            cost_type=params.cost_type,
            max_cost=params.aggregate_max_cost(),
            speed=params.speed,
            # Formula
            heatmap_type=params.heatmap_type,
            decay=params.decay,
            max_sensitivity=params.max_sensitivity,
            # Opportunities + optional reference-area clip
            opportunities=resolved_opportunities,
            reference_area_path=reference_area_path,
            # 2SFCA supply-vs-demand
            two_sfca_type=two_sfca_type,
            demand_path=demand_path,
            demand_field=demand_field,
            # PT (arrive-by reverse RAPTOR). access/egress modes select the
            # per-mode lookup table (walk/bicycle/pedelec/car); the analysis
            # layer resolves the table path and errors if it isn't built yet.
            arrival_time=(
                _pt_arrival_unix_minutes(params.pt_day, params.pt_arrival_time)
                if is_pt
                else None
            ),
            transit_modes=(
                [m.value for m in params.pt_modes]
                if is_pt and params.pt_modes
                else None
            ),
            max_transfers=params.pt_max_transfers,
            access_mode=_ACCESS_EGRESS_MODE_MAP[params.pt_access_mode],
            egress_mode=_ACCESS_EGRESS_MODE_MAP[params.pt_egress_mode],
            access_max_time=params.pt_access_max_time,
            egress_max_time=params.pt_egress_max_time,
            # Output
            output_path=str(output_path),
        )

        tool = self.tool_class()
        try:
            results = tool.run(analysis_params)
            result_path, metadata = results[0]
            return Path(result_path), metadata
        finally:
            tool.cleanup()


class HeatmapGravityV2ToolRunner(HeatmapV2ToolRunner):
    """Per-formula entry point: pre-binds heatmap_type=gravity in the UI."""

    default_output_name = get_default_layer_name("heatmap_gravity", "en")


class HeatmapClosestAverageV2ToolRunner(HeatmapV2ToolRunner):
    """Per-formula entry point: pre-binds heatmap_type=closest_average."""

    default_output_name = get_default_layer_name("heatmap_closest_average", "en")


class HeatmapConnectivityV2ToolRunner(HeatmapV2ToolRunner):
    """Per-formula entry point: pre-binds heatmap_type=connectivity in the UI.
    The base runner handles reference-area export + dispatch."""

    default_output_name = get_default_layer_name("heatmap_connectivity", "en")


class Heatmap2SFCAV2ToolRunner(HeatmapV2ToolRunner):
    """Per-formula entry point: pre-binds heatmap_type=two_sfca in the UI.
    The base runner handles demand + supply export + dispatch."""

    default_output_name = get_default_layer_name("heatmap_2sfca", "en")


def main(params: HeatmapV2WindmillParams) -> dict:
    """Formula-agnostic Windmill entry point — kept for programmatic callers.

    Toolbox tiles use the per-formula shim modules
    (`heatmap_gravity_v2`, `heatmap_closest_average_v2`) so each tile
    pre-binds heatmap_type and hides the selector.
    """
    runner = HeatmapV2ToolRunner()
    runner.init_from_env()
    try:
        return runner.run(params)
    finally:
        runner.cleanup()
