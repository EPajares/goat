# ADR-002: Tool Metadata & Dynamic UI Rendering

**Status:** Completed  
**Date:** 2026-01-01  
**Authors:** @eliasjp

## Context

Currently, the web client has hardcoded tool interfaces for each analysis tool. A colleague has implemented dynamic rendering from the OGC Processes API, but the backend needs to provide richer metadata to support:

- **Field grouping/sections** - Organize fields into logical UI sections
- **Conditional visibility** - Show/hide fields based on other field values
- **Mutual exclusivity** - Only one option in a group active at a time
- **i18n translations** - Labels and descriptions in multiple languages
- **Field ordering** - Control display order within sections

## Current State

### Tools in goatlib
| Category | Tools |
|----------|-------|
| Geoprocessing | buffer, clip, centroid |
| Data Management | layerimport, layerexport, layerdelete |
| Heatmaps | (schemas defined, tools planned) |
| Statistics | feature-count, unique-values, class-breaks, area-statistics |

### Architecture
```
goatlib.tools.registry (TOOL_REGISTRY)
    └─> goatlib.tools.*.ToolParams (Pydantic models)
           └─> geoapi.services.tool_registry (OGC process descriptions)
                  └─> OGC Processes API → Frontend
```

## Decision

Embed UI metadata directly in Pydantic schemas using `json_schema_extra`, which:
- Keeps metadata next to field definitions (no duplication)
- Auto-propagates via `model_json_schema()`
- Type-safe via helper functions
- Works with existing OGC Processes infrastructure

---

## Implementation Phases

### Phase 1: Core Infrastructure (goatlib) ✅ COMPLETED

**Goal:** Create the `ui_field()` helper and supporting types.

**Files created:**
- `packages/python/goatlib/src/goatlib/analysis/schemas/ui.py` ✅

**Deliverables:**
1. ✅ `UISection` dataclass for section definitions
2. ✅ `ui_field()` helper function that returns `json_schema_extra` dict
3. ✅ `ui_sections()` model config helper for `x-ui-sections`
4. ✅ Predefined sections (SECTION_ROUTING, SECTION_CONFIGURATION, etc.)
5. ✅ `layer_selector_field()` and `scenario_selector_field()` convenience helpers

**Helper Function Signature:**
```python
def ui_field(
    section: str,                          # Section ID (e.g., "routing")
    field_order: int = 0,                  # Order within section
    label_key: str | None = None,          # i18n key for label
    description_key: str | None = None,    # i18n key for description
    hidden: bool = False,                  # Never show in UI
    visible_when: dict | None = None,      # Show when condition met
    hidden_when: dict | None = None,       # Hide when condition met
    mutually_exclusive_group: str | None = None,  # Only one in group shown
    priority: int = 0,                     # Priority within exclusive group
    repeatable: bool = False,              # For list fields
    min_items: int | None = None,          # Minimum items for repeatable
    max_items: int | None = None,          # Maximum items for repeatable
) -> dict:
    """Generate json_schema_extra dict for UI configuration."""
```

### Phase 2: i18n Infrastructure (goatlib) ✅ COMPLETED

**Goal:** Create translation system for tool metadata.

**Files created:**
- `packages/python/goatlib/src/goatlib/i18n/__init__.py` ✅
- `packages/python/goatlib/src/goatlib/i18n/translations/en.json` ✅
- `packages/python/goatlib/src/goatlib/i18n/translations/de.json` ✅

**Features:**
- ✅ `Translator` class for loading translations
- ✅ `get_translator()` cached factory
- ✅ `resolve_schema_translations()` to resolve keys in JSON schemas
- ✅ Translations for sections, fields, enums, and tools

**Translation File Structure:**
```json
{
  "sections": {
    "routing": { "label": "Routing" },
    "configuration": { "label": "Configuration" },
    "opportunities": { "label": "Opportunities" },
    "scenario": { "label": "Scenario" },
    "input": { "label": "Input" },
    "output": { "label": "Output" },
    "options": { "label": "Options" }
  },
  "fields": {
    "routing_mode": {
      "label": "Transport Mode",
      "description": "Select the transport mode for accessibility analysis"
    },
    "sensitivity": {
      "label": "Sensitivity",
      "description": "Decay sensitivity parameter for gravity model"
    }
  }
}
```

**Translation Resolver:**
```python
class TranslationResolver:
    def resolve_schema(
        self,
        schema: dict,
        language: str = "en"
    ) -> dict:
        """Replace label_key/description_key with translated strings."""
```

### Phase 3: Heatmap Schema Migration ✅ COMPLETED

**Goal:** Apply UI metadata to all heatmap schemas as reference implementation.

**Files modified:**
- `packages/python/goatlib/src/goatlib/analysis/schemas/heatmap.py` ✅

**Completed:**
- ✅ `HeatmapCommon` with sections (routing, configuration, opportunities)
- ✅ `HeatmapGravityParams` with all UI metadata
- ✅ `OpportunityGravity` with mutually exclusive potential fields
- ✅ `HeatmapClosestAverageParams` and `HeatmapConnectivityParams`
- ✅ Hidden internal fields (od_matrix_path, output_path)

**Target UI Structure (Heatmap Gravity):**
```
┌─ Routing (section_order=1, icon="route")
│  └─ Transport Mode (routing_mode)
│
├─ Configuration (section_order=2, icon="settings")
│  └─ Impedance Function (impedance)
│
├─ Opportunities (section_order=3, icon="location-marker", repeatable)
│  ├─ Opportunity Layer (input_path)
│  ├─ Traveltime Limit (max_cost)
│  ├─ Destination Potential [mutually exclusive group: potential_source]
│  │  ├─ Field (potential_field, priority=1)
│  │  ├─ Constant (potential_constant, priority=2)
│  │  └─ Expression (potential_expression, priority=3)
│  └─ Sensitivity (sensitivity)
│
└─ Scenario (section_order=4, icon="scenario")
   └─ Scenario (scenario_id)
```

### Phase 4: GeoAPI Schema Enhancement ✅ COMPLETED

**Goal:** Extend OGC process descriptions with UI metadata and translations.

**Files modified:**
- `apps/geoapi/src/geoapi/services/tool_registry.py` ✅
- `apps/geoapi/src/geoapi/routers/processes.py` ✅
- `apps/geoapi/src/geoapi/models/processes.py` ✅

**Completed:**
- ✅ `get_full_json_schema()` method returns schema with x-ui metadata
- ✅ `get_process_description()` includes translations based on `Accept-Language`
- ✅ `ProcessDescription` model extended with `x_ui_sections` field
- ✅ Hidden fields filtered from inputs
- ✅ `get_language_from_request()` helper in router

### Phase 5: Geoprocessing Tool Migration ✅ COMPLETED

**Goal:** Apply UI metadata to all geoprocessing schemas.

**Files modified:**
- `packages/python/goatlib/src/goatlib/analysis/schemas/geoprocessing.py` ✅

**Completed:**
- ✅ `BufferParams` with sections (input, buffer, options, output)
- ✅ `ClipParams` with sections (input, overlay, output)
- ✅ `IntersectionParams` with sections (input, overlay, field_selection, output)
- ✅ `UnionParams` with sections (input, overlay, output)
- ✅ `DifferenceParams` with sections (input, overlay, output)
- ✅ `CentroidParams` with sections (input, output)
- ✅ `OriginDestinationParams` with sections (input, matrix, columns, output)
- ✅ Mutually exclusive group for buffer distance/field
- ✅ Conditional visibility for mitre_limit (only with JOIN_MITRE)
- ✅ Hidden output fields (output_path, output_crs)
- ✅ Widget hints for layer selectors and field selectors

### Phase 6: Data Management Tool Migration ✅ COMPLETED

**Goal:** Apply UI metadata to data management schemas.

**Files modified:**
- `packages/python/goatlib/src/goatlib/tools/layer_import.py` ✅
- `packages/python/goatlib/src/goatlib/tools/layer_export.py` ✅
- `packages/python/goatlib/src/goatlib/tools/layer_delete.py` ✅
- `packages/python/goatlib/src/goatlib/tools/schemas.py` ✅

**Completed:**
- ✅ `LayerImportParams` with sections (source, wfs_options, metadata, output)
- ✅ `LayerExportParams` with sections (input, output, options)
- ✅ `LayerDeleteParams` with section (input)
- ✅ `ToolInputBase` base class with hidden system fields
- ✅ `LayerInputMixin` and `TwoLayerInputMixin` with layer-selector widgets
- ✅ Mutually exclusive import sources (s3_key vs wfs_url)
- ✅ Conditional visibility for WFS options
- ✅ Widget hints for format select, tags, CRS selector, SQL editor

---

## Open Questions for Discussion

### 1. Condition Syntax for `visible_when` / `hidden_when`

**Proposed:** MongoDB-like syntax for familiarity and expressiveness:

```python
# Simple equality
visible_when={"routing_mode": "public_transport"}

# Comparison operators
visible_when={"max_cost": {"$gte": 30}}

# Not equal (check if set)
hidden_when={"potential_field": {"$ne": None}}

# One of multiple values
visible_when={"routing_mode": {"$in": ["walking", "bicycle"]}}
```

**Alternatives considered:**
- A) JSON Logic (`{"==": [{"var": "routing_mode"}, "public_transport"]}`)
- B) Simple string expressions (`"routing_mode == 'public_transport'"`)
- C) Custom DSL

**Question for frontend:** Is MongoDB-like syntax OK to parse? Already have a library for it?

---

### 2. Nested Models in Repeatable Sections

When we have:
```python
opportunities: list[OpportunityGravity] = Field(
    ...,
    json_schema_extra=ui_field(section="opportunities", repeatable=True),
)

class OpportunityGravity(BaseModel):
    input_path: str = Field(...)
    sensitivity: float = Field(...)
```

**Options:**
- **A) Inherit parent section** - Nested fields become part of "opportunities" section, just define `field_order`
- **B) Define own sections** - Nested model has sub-sections (complex)
- **C) No section** - Render as grouped block within repeatable item

**Recommendation:** Option A - simpler, nested fields just need `field_order` for ordering within the repeatable block.

**Question for frontend:** How do you want to render nested models within repeatable sections?

---

### 3. Frontend Rendering of Mutually Exclusive Fields

For fields like `potential_field`, `potential_constant`, `potential_expression` where only one should be active:

**Options:**
- **A) Dropdown selector** - "Potential source: [Field ▼]" then show selected field
- **B) Radio buttons + field** - Three radio options, each with its input
- **C) Tabs within section** - Tab UI for switching
- **D) Priority default** - Show highest priority by default, link to switch

**Question for frontend:** Which UX pattern fits best?

---

### 4. Hidden Fields Management

Some fields should never show in UI: `user_id`, `project_id`, `output_path`, `input_path`.

**Options:**
- **A) Schema with `hidden=True`** - Explicit in each schema
- **B) Exclusion list in geoapi** - Central list of fields to exclude (current approach)
- **C) Combination** - Default exclusion list + schema override capability

**Current state:** GeoAPI has `EXCLUDED_FIELDS = {"input_path", "output_path", "overlay_path", "output_crs"}`.

**Recommendation:** Keep exclusion list in geoapi, add `hidden=True` for tool-specific hidden fields.

---

### 5. Section Icon Mapping

Icons reference the `@p4b/ui/components/Icon` component.

| Section | Icon String | Use Case |
|---------|-------------|----------|
| routing | `"route"` | Transport mode selection |
| configuration | `"settings"` | General settings |
| opportunities | `"location-marker"` | POI/destination layers |
| scenario | `"scenario"` | Scenario selection |
| input | `"layers"` | Input layer selection |
| output | `"table"` | Output configuration |
| options | `"settings"` | Advanced options |
| statistics | `"chart"` | Stats configuration |
| time | `"clock"` | Time/duration settings |
| area | `"hexagon"` | Area/zone settings |

**Question for frontend:** 
- Are these icon names correct for `@p4b/ui/components/Icon`?
- Need different icons or additional mappings?

---

### 6. Layer Selection Widget

Fields ending in `_layer_id` should render as layer selector dropdowns.

**Current:** GeoAPI detects `*_layer_id` pattern and adds `"format": "layer-uuid"`.

**Proposed enhancement:** Add explicit UI type:
```python
input_layer_id: str = Field(
    ...,
    json_schema_extra=ui_field(
        section="input",
        widget="layer-selector",
        layer_geometry_types=["Polygon", "MultiPolygon"],  # Filter layers
    ),
)
```

**Question for frontend:** What metadata do you need for the layer selector?

---

## Output JSON Schema Example

What the API would return for Heatmap Gravity:

```json
{
  "id": "heatmap-gravity",
  "title": "Heatmap Gravity",
  "description": "Compute gravity-based accessibility heatmaps",
  "x-ui-sections": [
    {"id": "routing", "order": 1, "label": "Routing", "icon": "route"},
    {"id": "configuration", "order": 2, "label": "Configuration", "icon": "settings"},
    {"id": "opportunities", "order": 3, "label": "Opportunities", "icon": "location-marker"},
    {"id": "scenario", "order": 4, "label": "Scenario", "icon": "scenario"}
  ],
  "inputs": {
    "routing_mode": {
      "title": "Transport Mode",
      "description": "Select transport mode for accessibility analysis",
      "schema": {
        "type": "string",
        "enum": ["walking", "bicycle", "pedelec", "public_transport", "car"],
        "x-ui": {
          "section": "routing",
          "field_order": 1,
          "label": "Transport Mode",
          "description": "Select transport mode for accessibility analysis"
        }
      }
    },
    "impedance": {
      "title": "Impedance Function",
      "description": "Distance decay function",
      "schema": {
        "type": "string",
        "enum": ["gaussian", "linear", "exponential", "power"],
        "x-ui": {
          "section": "configuration",
          "field_order": 1,
          "label": "Impedance Function",
          "description": "Distance decay function for gravity calculation"
        }
      }
    },
    "opportunities": {
      "title": "Opportunities",
      "description": "List of opportunity datasets with gravity parameters",
      "schema": {
        "type": "array",
        "items": {"$ref": "#/$defs/OpportunityGravity"},
        "x-ui": {
          "section": "opportunities",
          "repeatable": true,
          "min_items": 1
        }
      }
    }
  },
  "$defs": {
    "OpportunityGravity": {
      "type": "object",
      "properties": {
        "input_path": {
          "type": "string",
          "x-ui": {
            "section": "opportunities",
            "field_order": 1,
            "widget": "layer-selector"
          }
        },
        "potential_field": {
          "type": "string",
          "x-ui": {
            "section": "opportunities",
            "field_order": 2,
            "mutually_exclusive_group": "potential_source",
            "priority": 1
          }
        },
        "potential_constant": {
          "type": "number",
          "x-ui": {
            "section": "opportunities",
            "field_order": 2,
            "mutually_exclusive_group": "potential_source",
            "priority": 2
          }
        },
        "sensitivity": {
          "type": "number",
          "x-ui": {
            "section": "opportunities",
            "field_order": 3
          }
        }
      }
    }
  }
}
```

---

## Migration Checklist

For each tool migration, ensure:

- [ ] Add `model_config` with `x-ui-sections`
- [ ] Add `json_schema_extra=ui_field(...)` to each field
- [ ] Add translation keys to `en.json` and `de.json`
- [ ] Add tests for schema generation
- [ ] Verify OGC process description output
- [ ] Frontend renders correctly

---

## References

- [Pydantic JSON Schema Customization](https://docs.pydantic.dev/latest/concepts/json_schema/)
- [OGC API Processes Specification](https://docs.ogc.org/is/18-062r2/18-062r2.html)
- Current implementation: [tool_registry.py](../apps/geoapi/src/geoapi/services/tool_registry.py)
