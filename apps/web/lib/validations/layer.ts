import { v4 } from "uuid";
import * as z from "zod";

import { DEFAULT_WKT_EXTENT } from "@/lib/constants";
import { DEFAULT_COLOR, DEFAULT_COLOR_RANGE } from "@/lib/constants/color";
import { formatNumberTypes } from "@/lib/validations/common";
import {
  contentMetadataSchema,
  dataCategory,
  dataLicense,
  dataType,
  featureDataExchangeType,
  featureLayerGeometryType,
  featureLayerType,
  layerType,
  paginatedSchema,
} from "@/lib/validations/common";
import { responseSchema } from "@/lib/validations/response";
import { publicUserSchema } from "@/lib/validations/user";

export const layerRoleEnums = z.enum(["layer-owner", "layer-viewer", "layer-editor"]);

export const layerRoles = {
  OWNER: "layer-owner",
  VIEWER: "layer-viewer",
  EDITOR: "layer-editor",
} as const;

export const layerShareRoleEnum = z.enum(["layer-viewer", "layer-editor"]);

export const shareLayerWithTeamOrOrganizationSchema = z.object({
  id: z.string(),
  name: z.string().optional(),
  avatar: z.string().optional(),
  role: layerShareRoleEnum,
});

export const shareLayerSchema = z.object({
  teams: z.array(shareLayerWithTeamOrOrganizationSchema).optional(),
  organizations: z.array(shareLayerWithTeamOrOrganizationSchema).optional(),
});

const HexColor = z.string();
const ColorMap = z.array(z.tuple([z.union([z.array(z.string()), z.null()]), HexColor]));

export const sizeOrdinalMap = z.array(z.tuple([z.string(), z.number()]));

export const classBreaks = z.enum([
  "quantile",
  "standard_deviation",
  "equal_interval",
  "heads_and_tails",
  "ordinal",
  "custom_breaks",
]);

export const sizeScale = z.enum(["linear", "logarithmic", "exponential"]);
const layerFieldType = z.object({
  $ref: z.string().optional(),
  name: z.string(),
  type: z.string(),
  format: z.string().optional(),
  // D2: computed-field metadata exposed by the queryables endpoint
  kind: z.string().optional(),
  is_computed: z.boolean().optional(),
  display_config: z.record(z.string(), z.unknown()).optional(),
});

export const layerClassBreaks = z.object({
  min: z.number(),
  max: z.number(),
  mean: z.number(),
  breaks: z.array(z.number()),
});

const ColorLegends = z.record(z.string());
const sanitizeColorRangeInput = (input: unknown): unknown => {
  if (!input || typeof input !== "object") {
    return input;
  }

  const colorRangeInput = { ...(input as Record<string, unknown>) };
  const rawColorMap = colorRangeInput.color_map;

  if (Array.isArray(rawColorMap)) {
    colorRangeInput.color_map = rawColorMap.filter((entry) => {
      if (!Array.isArray(entry) || entry.length < 2) {
        return false;
      }

      const color = entry[1];
      return typeof color === "string" && color.length > 0;
    });
  }

  return colorRangeInput;
};

const colorRangeSchema = z.object({
  name: z.string().optional(),
  type: z.string().optional(),
  category: z.string().optional(),
  colors: z.array(HexColor),
  reversed: z.boolean().optional(),
  color_map: ColorMap.optional(),
  color_legends: ColorLegends.optional(),
});

export const colorRange = z.preprocess(sanitizeColorRangeInput, colorRangeSchema);

export const SymbolPlacementAnchor = z.enum([
  "center",
  "left",
  "right",
  "top",
  "bottom",
  "top-left",
  "top-right",
  "bottom-left",
  "bottom-right",
]);
export const TextLabelSchema = z.object({
  size: z.number().min(1).max(100).default(14),
  color: z.array(z.number().min(0).max(255)).optional().default([0, 0, 0]),
  field: z.string().optional(),
  offset: z.array(z.number().min(-5).max(5)).optional().default([0, 0]),
  anchor: SymbolPlacementAnchor.default("bottom"),
  alignment: z.enum(["center", "left", "right"]).optional().default("center"),
  background: z.boolean().optional().default(false),
  allow_overlap: z.boolean().optional().default(false),
  font_family: z.array(z.string()).optional().default(["Open Sans Regular", "Arial Unicode MS Regular"]),
  background_color: z.array(z.number().min(0).max(255)).optional().default([0, 0, 0, 0]),
  outline_color: z.array(z.number().min(0).max(255)).optional().default([255, 255, 255]),
  outline_width: z.number().min(0).max(10).optional().default(0),
});

export const layerPropertiesBaseSchema = z.object({
  opacity: z.number().min(0).max(1).default(0.8),
  visibility: z.boolean(),
  min_zoom: z.number().min(0).max(23).default(0),
  max_zoom: z.number().min(0).max(23).default(21),
});

export const colorSchema = z.object({
  color: z.array(z.number().min(0).max(255)).optional().default(DEFAULT_COLOR),
  color_range: colorRange.optional().default(DEFAULT_COLOR_RANGE),
  color_field: layerFieldType.optional(),
  color_scale: classBreaks.optional().default("quantile"),
  color_scale_breaks: layerClassBreaks.optional(),
  color_no_data: z.string().optional(),
});

export const strokeColorSchema = z.object({
  stroke_color: z.array(z.number().min(0).max(255)).optional().default(DEFAULT_COLOR),
  stroke_color_range: colorRange.optional().default(DEFAULT_COLOR_RANGE),
  stroke_color_field: layerFieldType.optional(),
  stroke_color_scale: classBreaks.optional().default("quantile"),
  stroke_color_scale_breaks: layerClassBreaks.optional(),
  stroke_color_no_data: z.string().optional(),
});

export const strokeWidthSchema = z.object({
  stroke_width: z.number().min(0).max(200).default(2),
  stroke_width_range: z.array(z.number().min(0).max(200)).default([0, 10]),
  stroke_width_field: layerFieldType.optional(),
  stroke_width_scale: classBreaks.catch("quantile").optional().default("quantile"),
  stroke_width_num_steps: z.number().min(2).max(10).default(5),
  stroke_width_scale_breaks: layerClassBreaks.optional(),
  stroke_width_ordinal_map: sizeOrdinalMap.optional(),
});

export const lineStyleSchema = z.object({
  stroke_pattern: z.enum(["solid", "dashed", "dotted", "dash_dot"]).default("solid"),
  stroke_dash_density: z.enum(["tight", "normal", "loose"]).default("normal"),
  stroke_cap: z.enum(["butt", "round", "square"]).default("butt"),
  stroke_join: z.enum(["bevel", "round", "miter"]).default("miter"),
  // Perpendicular pixel offset from the line geometry; positive shifts to
  // the right of the line direction, negative to the left. Purely visual —
  // hit-testing/snapping still uses the unshifted geometry.
  stroke_offset: z.number().min(-50).max(50).catch(0).default(0),
  // "decoration" is the cartography term for repeating symbols along a line.
  // Generic so v2 can add "chevron" / "dot" / "tick" without a migration.
  decoration_type: z.enum(["none", "arrow"]).default("none"),
  decoration_direction: z.enum(["forward", "backward", "both"]).default("forward"),
  decoration_placement: z
    .enum(["repeat", "start", "end", "start_and_end", "center"])
    .default("repeat"),
  decoration_spacing: z.number().min(50).max(800).default(200),
  // Target arrow size in screen pixels (matches the visible arrow extent
  // because the source SVG fills its 32x32 viewBox). `.catch(32)` ensures
  // out-of-range legacy values (e.g. the pre-pixel-scale fractional sizes)
  // silently fall back to the default instead of throwing at parse time.
  decoration_size: z.number().min(8).max(64).catch(32).default(32),
  // When true, arrows render even where they'd collide with other symbols
  // (and don't block other symbols from rendering near them). When false,
  // MapLibre's collision detector culls overlapping arrows — arrows can
  // disappear at low zoom or in dense areas.
  decoration_allow_overlap: z.boolean().default(true),
});

export const radiusSchema = z.object({
  radius: z.number().min(0).max(100).default(10),
  radius_range: z.array(z.number().min(0).max(500)).default([0, 10]),
  fixed_radius: z.boolean().default(false),
  radius_field: layerFieldType.optional(),
  radius_scale: classBreaks.catch("quantile").optional().default("quantile"),
  radius_num_steps: z.number().min(2).max(10).default(5),
  radius_scale_breaks: layerClassBreaks.optional(),
  radius_ordinal_map: sizeOrdinalMap.optional(),
});

export const marker = z.object({
  id: z.string().optional(),
  name: z.string(),
  url: z.string(),
  category: z.string().optional(),
  source: z.enum(["library", "custom"]).optional().default("library"),
});

const MarkerMap = z.array(z.tuple([z.union([z.array(z.string()), z.null()]), marker]));

export const markerBackgroundType = z.enum(["circle", "marker"]);

export const markerSchema = z.object({
  custom_marker: z.boolean().default(false),
  marker: marker.optional(),
  marker_field: layerFieldType.optional(),
  marker_mapping: MarkerMap.optional(),
  marker_size: z.number().min(0).max(100).default(10),
  marker_size_range: z.array(z.number().min(0).max(500)).default([0, 10]),
  marker_size_field: layerFieldType.optional(),
  marker_size_scale: classBreaks.catch("quantile").optional().default("quantile"),
  marker_size_num_steps: z.number().min(2).max(10).default(5),
  marker_size_scale_breaks: layerClassBreaks.optional(),
  marker_size_ordinal_map: sizeOrdinalMap.optional(),
  marker_background_type: markerBackgroundType.optional().default("marker"),
  marker_allow_overlap: z.boolean().optional().default(false),
  marker_anchor: SymbolPlacementAnchor.optional().default("center"),
  marker_offset: z.array(z.number().min(-5).max(5)).optional().default([0, 0]),
});

export const clusterSchema = z.object({
  enabled: z.boolean().default(false),
  radius: z.number().min(1).max(100).default(50),
  min_points: z.number().min(2).max(20).default(3),
  max_zoom: z.number().min(0).max(20).default(14),
  color: z.array(z.number().min(0).max(255)).length(3).default([40, 56, 178]),
  text_color: z.array(z.number().min(0).max(255)).length(3).default([255, 255, 255]),
});

export const layerInteractionContentType = z.enum(["field_list", "image"]);

// Composable number formatting — mirrors the `display_config` shape used by
// FieldEditor for layer schema fields, so the popup editor can speak the
// same vocabulary. Added alongside the legacy `format` preset enum (which
// the original interaction popup still uses); the popup-v2 renderer prefers
// `format_config` when present and falls back to `format`.
export const attributeFormatConfig = z.object({
  decimals: z.union([z.literal("auto"), z.number().int().min(0).max(10)]).optional(),
  thousands_separator: z.boolean().optional(),
  abbreviate: z.boolean().optional(),
  always_show_sign: z.boolean().optional(),
});

export const attributeSchema = z.object({
  name: z.string(),
  label: z.string().optional(),
  type: z.enum(["string", "number", "boolean"]),
  format: formatNumberTypes.optional(),
  format_config: attributeFormatConfig.optional(),
  prefix: z.string().optional(),
  suffix: z.string().optional(),
});

export const interactionFieldListContent = z.object({
  id: z
    .string()
    .uuid()
    .default(() => v4()),
  type: z.literal(layerInteractionContentType.Enum.field_list).default("field_list"),
  title: z.string().optional(),
  attributes: z.array(attributeSchema).optional().default([]),
});

export const interactionImageContent = z.object({
  id: z
    .string()
    .uuid()
    .default(() => v4()),
  type: z.literal(layerInteractionContentType.Enum.image).default("image"),
  title: z.string().optional(),
  url: z.string().optional().default(""),
});

export const layerInteractionContent = z.union([interactionFieldListContent, interactionImageContent]);

export const layerInteractionType = z.enum(["click", "hover", "none"]);

export const interactionProperties = z.object({
  type: layerInteractionType.optional().default("click"),
  content: z.array(interactionFieldListContent.or(interactionImageContent)).default([]),
});

export const layerLegend = z.object({
  show: z.boolean().default(true),
  caption: z.string().optional(),
  collapsed: z.boolean().optional().default(false),
});

// Popup v2 — new customizable popup schema. Lives alongside `interaction`
// for back-compat; renderer prefers `popup` when present.
export const popupTextBlock = z.object({
  id: z
    .string()
    .uuid()
    .default(() => v4()),
  type: z.literal("text"),
  html: z.string().default(""),
});

export const popupFieldListBlock = z.object({
  id: z
    .string()
    .uuid()
    .default(() => v4()),
  type: z.literal("fieldList"),
  layout: z.enum(["table", "list"]).default("table"),
  attributes: z.array(attributeSchema).default([]),
  collapse_after: z.number().int().min(1).max(50).nullable().default(null),
});

export const popupImageBlock = z.object({
  id: z
    .string()
    .uuid()
    .default(() => v4()),
  type: z.literal("image"),
  source: z.enum(["field", "static"]).default("field"),
  field: z.string().optional(),
  url: z.string().optional(),
  sizing: z.enum(["fit", "fixed", "aspect"]).default("fixed"),
  height: z.number().min(40).max(400).default(140),
  aspect: z.enum(["16/9", "4/3", "3/2", "1/1", "2/3"]).default("16/9"),
});

export const popupButtonBlock = z.object({
  id: z
    .string()
    .uuid()
    .default(() => v4()),
  type: z.literal("button"),
  label: z.string().default("Open"),
  url_template: z.string().default(""),
  style: z.enum(["link", "outlined", "filled"]).default("link"),
  color: z.string().optional(),
});

export const popupBadgeBlock = z.object({
  id: z
    .string()
    .uuid()
    .default(() => v4()),
  type: z.literal("badge"),
  field: z.string().min(1),
  // "single" → one color for every value (read from `color`).
  // "per_value" → colors derived from `palette` (value → hex).
  mode: z.enum(["single", "per_value"]).default("single"),
  color: z.string().optional(),
  palette: z.record(z.string()).default({}),
  labels: z.record(z.string()).optional(),
  full_width: z.boolean().default(false),
});

export const popupDividerBlock = z.object({
  id: z
    .string()
    .uuid()
    .default(() => v4()),
  type: z.literal("divider"),
  thickness: z.number().int().min(1).max(8).default(1),
  color: z.string().optional(),
});

export const popupBlock = z.discriminatedUnion("type", [
  popupTextBlock,
  popupFieldListBlock,
  popupImageBlock,
  popupButtonBlock,
  popupBadgeBlock,
  popupDividerBlock,
]);

export const popupAnchor = z.enum(["top_left", "top_right", "bottom_left", "bottom_right"]);

export const popupLayout = z.enum([
  "popup",
  "pinned",
  "modal",
  "left_sidebar",
  "right_sidebar",
]);

export const popupHeader = z.enum(["standard", "compact", "none"]);

export const popupProperties = z.object({
  enabled: z.boolean().default(true),
  // "click_and_hover" opens the popup on hover (transient) AND on click
  // (pinned). Once a popup is active on any layer, triggers from OTHER
  // layers are suppressed by the runtime until the popup closes.
  trigger: z.enum(["click", "hover", "click_and_hover"]).default("click"),
  mode: z.enum(["simple", "html"]).default("simple"),
  blocks: z.array(popupBlock).default([]),
  html: z.string().default(""),
  // Unified, mode-agnostic appearance ("Desktop layout").
  layout: popupLayout.default("popup"),
  anchor: popupAnchor.optional(), // only meaningful when layout === "pinned"
  width: z.number().int().positive().optional(), // px; undefined = auto
  max_height: z.number().int().positive().optional(), // px; undefined = auto
  header: popupHeader.default("standard"),
  highlight_active_feature: z.boolean().default(true),
  // DEPRECATED — kept optional so legacy stored popups survive parsing
  // and can be mapped forward by normalizePopup(). Never written by new code.
  position: z.enum(["in_place", "fixed"]).optional(),
  show_layer_header: z.boolean().optional(),
});

export type PopupBlock = z.infer<typeof popupBlock>;
export type PopupTextBlock = z.infer<typeof popupTextBlock>;
export type PopupFieldListBlock = z.infer<typeof popupFieldListBlock>;
export type AttributeFormatConfig = z.infer<typeof attributeFormatConfig>;
export type Attribute = z.infer<typeof attributeSchema>;
export type PopupImageBlock = z.infer<typeof popupImageBlock>;
export type PopupButtonBlock = z.infer<typeof popupButtonBlock>;
export type PopupBadgeBlock = z.infer<typeof popupBadgeBlock>;
export type PopupDividerBlock = z.infer<typeof popupDividerBlock>;
export type PopupProperties = z.infer<typeof popupProperties>;
export type PopupLayout = z.infer<typeof popupLayout>;
export type PopupHeader = z.infer<typeof popupHeader>;
export type PopupAnchor = z.infer<typeof popupAnchor>;

export const featureLayerBasePropertiesSchema = z
  .object({
    filled: z.boolean().default(true),
    stroked: z.boolean().default(true),
    text_label: TextLabelSchema.optional(),
    interaction: interactionProperties.optional().default({}),
    popup: popupProperties.optional(), // NEW: undefined = legacy renderer
    legend: layerLegend.optional().default({}),
  })
  .merge(layerPropertiesBaseSchema)
  .merge(colorSchema)
  .merge(strokeColorSchema)
  .merge(strokeWidthSchema);

export const featureLayerPointPropertiesSchema = featureLayerBasePropertiesSchema
  .merge(strokeColorSchema)
  .merge(radiusSchema)
  .merge(markerSchema)
  .extend({
    cluster: clusterSchema.optional(),
  });

export const featureLayerLinePropertiesSchema =
  featureLayerBasePropertiesSchema.merge(lineStyleSchema);

export const featureLayerPolygonPropertiesSchema = featureLayerBasePropertiesSchema.merge(strokeColorSchema);

export const featureLayerProperties = featureLayerPointPropertiesSchema
  .or(featureLayerLinePropertiesSchema)
  .or(featureLayerPolygonPropertiesSchema);

export const featureLabelProperties = z.object({});

// lineage, positional_accuracy, attribute_accuracy, completeness
export const layerMetadataSchema = contentMetadataSchema.extend({
  lineage: z.string().optional(),
  positional_accuracy: z.string().optional(),
  attribute_accuracy: z.string().optional(),
  completeness: z.string().optional(),
  upload_reference_system: z.number().optional(),
  upload_file_type: featureDataExchangeType.optional(),
  geographical_code: z.string().length(2).optional(),
  language_code: z.string().optional(),
  data_reference_year: z.coerce.number().optional(),
  distributor_name: z.string().optional(),
  distributor_email: z.string().email().optional(),
  distribution_url: z.string().url().optional(),
  license: dataLicense.optional(),
  attribution: z.string().optional(),
  data_category: dataCategory.optional(),
  in_catalog: z.boolean().optional().default(false),
});

export const tableConfigSchema = z.object({
  // Columns pinned to the left of the data table, in pin order
  frozen_columns: z.array(z.string()).optional(),
  // Column widths in px — required for stable sticky offsets across reloads
  column_widths: z.record(z.string(), z.number()).optional(),
});

export const otherPropertiesSchmea = z.object({
  url: z.string().optional(),
  layers: z.array(z.string()).optional(),
  srs: z.string().optional(),
  width: z.number().optional(), // width of the image (only for external imagery)
  height: z.number().optional(), // height of the image (only for external imagery)
  legend_urls: z.array(z.string()).optional(),
  version: z.string().optional(),
  dpi: z.number().optional(),
  tile_size: z.number().optional(),
  // Per-project-layer data table preferences
  table_config: tableConfigSchema.optional(),
});

// Raster styling schemas
export const rasterStyleType = z.enum(["image", "color_range", "categories", "hillshade"]);

export const rasterResampling = z.enum(["linear", "nearest"]);

export const rasterStyleImageProperties = z.object({
  style_type: z.literal("image").default("image"),
  opacity: z.number().min(0).max(1).default(1.0),
  brightness_min: z.number().min(0).max(1).optional().default(0.0),
  brightness_max: z.number().min(0).max(1).optional().default(1.0),
  contrast: z.number().min(-1).max(1).optional().default(0.0),
  saturation: z.number().min(-1).max(1).optional().default(0.0),
  gamma: z.number().min(0.1).max(3).optional().default(1.0),
});

export const rasterStyleColorRangeProperties = z.object({
  style_type: z.literal("color_range").default("color_range"),
  band: z.number().min(1).default(1),
  min_value: z.number().optional(),
  max_value: z.number().optional(),
  min_label: z.string().optional(),
  max_label: z.string().optional(),
  color_map: z.array(z.tuple([z.number(), z.string()])).default([]),
  no_data_color: z.string().optional().default("transparent"),
  interpolate: z.boolean().default(true),
});

export const rasterStyleCategoriesProperties = z.object({
  style_type: z.literal("categories").default("categories"),
  band: z.number().min(1).default(1),
  categories: z
    .array(
      z.object({
        value: z.number(),
        color: z.string(),
        label: z.string().optional(),
      })
    )
    .default([]),
  default_color: z.string().default("#cccccc"),
  no_data_color: z.string().optional().default("transparent"),
});

export const rasterStyleHillshadeProperties = z.object({
  style_type: z.literal("hillshade").default("hillshade"),
  band: z.number().min(1).default(1),
  azimuth: z.number().min(0).max(360).default(315.0),
  altitude: z.number().min(0).max(90).default(45.0),
  z_factor: z.number().min(0.01).default(1.0),
  opacity: z.number().min(0).max(1).default(1.0),
});

export const rasterStyleProperties = z.discriminatedUnion("style_type", [
  rasterStyleImageProperties,
  rasterStyleColorRangeProperties,
  rasterStyleCategoriesProperties,
  rasterStyleHillshadeProperties,
]);

export const rasterLayerPropertiesSchema = layerPropertiesBaseSchema.extend({
  text_label: TextLabelSchema.optional(),
  interaction: interactionProperties.optional().default({}),
  legend: layerLegend.optional().default({}),
  resampling: rasterResampling.optional().default("nearest"),
  style: rasterStyleProperties
    .optional()
    .default({ style_type: "image", opacity: 1.0 } as z.infer<typeof rasterStyleImageProperties>),
});

export const layerSchema = layerMetadataSchema.extend({
  id: z.string(),
  properties: featureLayerProperties.or(rasterLayerPropertiesSchema).or(z.record(z.any())).default({}),
  total_count: z.number().optional(),
  extent: z.string().default(DEFAULT_WKT_EXTENT),
  folder_id: z.string(),
  user_id: z.string().uuid(),
  type: layerType,
  size: z.number().optional(),
  other_properties: otherPropertiesSchmea.optional(),
  url: z.string().optional(),
  feature_layer_type: featureLayerType.optional(),
  feature_layer_geometry_type: featureLayerGeometryType.optional(),
  tool_type: z.string().optional(),
  job_id: z.string().optional(),
  data_type: dataType.optional(),
  legend_urls: z.array(z.string()).optional(),
  attribute_mapping: z.object({}).optional(),
  shared_with: shareLayerSchema.optional(),
  owned_by: publicUserSchema.optional(),
  updated_at: z.string(),
  created_at: z.string(),
});

export const postDatasetSchema = layerSchema.partial();

export const getLayerUniqueValuesQueryParamsSchema = paginatedSchema.extend({
  query: z.string().optional(),
});

export const createLayerBaseSchema = layerMetadataSchema.extend({
  folder_id: z.string().uuid(),
});

export const externalDatasetFeatureUrlSchema = z.object({
  data_type: dataType,
  other_properties: otherPropertiesSchmea,
});

export const createLayerFromDatasetSchema = createLayerBaseSchema.extend({
  s3_key: z.string().optional(),
  dataset_id: z.string().optional(),
  project_id: z.string().uuid().optional(),
  data_type: dataType.optional(),
  other_properties: otherPropertiesSchmea.optional(),
  has_header: z.boolean().optional(),
  sheet_name: z.string().optional(),
});

export const createRasterLayerSchema = createLayerBaseSchema.extend({
  type: z.literal("raster"),
  url: z.string().url(),
  data_type: dataType,
  extent: z.string().optional(),
  properties: rasterLayerPropertiesSchema.optional(),
  other_properties: otherPropertiesSchmea,
});

export const layerQueryables = z.object({
  title: z.string(),
  properties: z.record(layerFieldType),
  type: z.string(),
  $schema: z.string(),
  $id: z.string(),
});

export const uniqueValuesSchema = z.object({
  value: z.string(),
  count: z.number(),
});
export const uniqueValuesResponseSchema = responseSchema(uniqueValuesSchema);

export const datasetDownloadRequestSchema = z.object({
  id: z.string().uuid(),
  file_type: featureDataExchangeType.optional(),
  file_name: z.string().optional(),
  crs: z.string().optional(),
  query: z.string().optional(),
});

export const datasetCollectionItems = z.object({
  description: z.string().optional(),
  features: z.array(
    z.object({
      geometry: z
        .object({
          coordinates: z.array(z.number()),
          type: z.string(),
        })
        .optional(),
      id: z.number(),
      properties: z.object({}),
      type: z.string(),
    })
  ),
  id: z.string().optional(),
  links: z.array(
    z.object({
      href: z.string(),
      rel: z.string(),
      type: z.string(),
      title: z.string(),
    })
  ),
  numberMatched: z.number(),
  numberReturned: z.number(),
  title: z.string(),
  type: z.string(),
});

export const datasetCollectionItemsQueryParams = z.object({
  "geom-column": z.string().optional(),
  "datetime-column": z.string().optional(),
  limit: z.number().min(0).max(10000).optional().default(10),
  offset: z.number().min(0).optional(),
  "bbox-only": z.boolean().optional(),
  simplify: z.boolean().optional(),
  ids: z.string().optional(),
  bbox: z.string().optional(),
  datetime: z.string().optional(),
  properties: z.string().optional(),
  filter: z.string().optional(),
  sortby: z.string().optional(),
  f: z.string().optional(),
});

export const getDatasetSchema = z.object({
  folder_id: z.string().uuid().optional(),
  search: z.string().optional(),
  type: layerType.array().optional(),
  feature_layer_type: featureLayerType.optional(),
  license: z.array(dataLicense).optional(),
  data_category: z.array(dataCategory).optional(),
  geographical_code: z.array(z.string().length(2)).optional(),
  language_code: z.array(z.string()).optional(),
  distributor_name: z.array(z.string()).optional(),
  in_catalog: z.boolean().optional(),
  spatial_search: z.string().optional(),
});

export const datasetMetadataValue = z.object({
  value: z.string(),
  count: z.number(),
});
export const datasetMetadataAggregated = z.object({
  type: z.array(datasetMetadataValue),
  data_category: z.array(datasetMetadataValue),
  geographical_code: z.array(datasetMetadataValue),
  language_code: z.array(datasetMetadataValue),
  distributor_name: z.array(datasetMetadataValue),
  license: z.array(datasetMetadataValue),
});

export type DatasetCollectionItems = z.infer<typeof datasetCollectionItems>;
export type GetCollectionItemsQueryParams = z.infer<typeof datasetCollectionItemsQueryParams>;
export type GetDatasetSchema = z.infer<typeof getDatasetSchema>;
export type DatasetMetadataValue = z.infer<typeof datasetMetadataValue>;
export type DatasetMetadataAggregated = z.infer<typeof datasetMetadataAggregated>;

export type DatasetDownloadRequest = z.infer<typeof datasetDownloadRequestSchema>;

export const layerResponseSchema = responseSchema(layerSchema);
export const layerTypesArray = Object.values(layerType.Values);
export const featureLayerTypesArray = Object.values(featureLayerType.Values);

export type ColorRange = z.infer<typeof colorRange>;
export type ColorMap = z.infer<typeof ColorMap>;
export type Layer = z.infer<typeof layerSchema>;
export type PostDataset = z.infer<typeof postDatasetSchema>;
export type FeatureLayerProperties = z.infer<typeof featureLayerProperties>;
export type FeatureLayerPointProperties = z.infer<typeof featureLayerPointPropertiesSchema>;
export type FeatureLayerLineProperties = z.infer<typeof featureLayerLinePropertiesSchema>;
export type FeatureLayerPolygonProperties = z.infer<typeof featureLayerPolygonPropertiesSchema>;
export type LayerPaginated = z.infer<typeof layerResponseSchema>;
export type LayerUniqueValues = z.infer<typeof uniqueValuesSchema>;
export type LayerUniqueValuesPaginated = z.infer<typeof uniqueValuesResponseSchema>;
export type Marker = z.infer<typeof marker>;
export type MarkerMap = z.infer<typeof MarkerMap>;
export type LayerType = z.infer<typeof layerType>;
export type LayerQueryables = z.infer<typeof layerQueryables>;
export type ClassBreaks = z.infer<typeof classBreaks>;
export type LayerClassBreaks = z.infer<typeof layerClassBreaks>;
export type LayerFieldType = z.infer<typeof layerFieldType>;
export type LayerMetadata = z.infer<typeof layerMetadataSchema>;
export type FeatureLayerType = z.infer<typeof featureLayerType>;
export type GetLayerUniqueValuesQueryParams = z.infer<typeof getLayerUniqueValuesQueryParamsSchema>;
export type ExternalDatasetFeatureUrl = z.infer<typeof externalDatasetFeatureUrlSchema>;
export type CreateLayerFromDataset = z.infer<typeof createLayerFromDatasetSchema>;
export type CreateRasterLayer = z.infer<typeof createRasterLayerSchema>;
export type LayerSharedWith = z.infer<typeof shareLayerSchema>;
export type TextLabelSchemaData = z.infer<typeof TextLabelSchema>;
export type LayerInteractionContentType = z.infer<typeof layerInteractionContentType>;
export type LayerInteractionContent = z.infer<typeof layerInteractionContent>;
export type LayerInteractionFieldListContent = z.infer<typeof interactionFieldListContent>;
export type SizeOrdinalMap = z.infer<typeof sizeOrdinalMap>;

// Raster styling types
export type RasterStyleType = z.infer<typeof rasterStyleType>;
export type RasterResampling = z.infer<typeof rasterResampling>;
export type RasterStyleImageProperties = z.infer<typeof rasterStyleImageProperties>;
export type RasterStyleColorRangeProperties = z.infer<typeof rasterStyleColorRangeProperties>;
export type RasterStyleCategoriesProperties = z.infer<typeof rasterStyleCategoriesProperties>;
export type RasterStyleHillshadeProperties = z.infer<typeof rasterStyleHillshadeProperties>;
export type RasterStyleProperties = z.infer<typeof rasterStyleProperties>;
export type RasterLayerProperties = z.infer<typeof rasterLayerPropertiesSchema>;

// Union type for all layer properties
export type LayerProperties = FeatureLayerProperties | RasterLayerProperties;

// --- Field definitions ---

export const fieldKindSchema = z.enum([
  "string",
  "number",
  "area",
  "perimeter",
  "length",
  "datetime",
  "boolean",
  "formula",
]);
export type FieldKind = z.infer<typeof fieldKindSchema>;

/** The kind used to FORMAT a field's values: formula fields format as their
 * inferred result kind (number/string/boolean/datetime). */
export const resolveDisplayKind = (field: {
  kind?: string;
  output_kind?: string;
}): string | undefined =>
  field.kind === "formula" ? (field.output_kind ?? "string") : field.kind;

const numericFormatSchema = z.object({
  decimals: z.union([z.literal("auto"), z.number().int().min(0).max(10)])
    .default("auto"),
  thousands_separator: z.boolean().default(false),
  abbreviate: z.boolean().default(false),
  always_show_sign: z.boolean().default(false),
});

export const stringDisplayConfigSchema = z.object({}).strict();
export const numberDisplayConfigSchema = numericFormatSchema.strict();
export const areaDisplayConfigSchema = numericFormatSchema.extend({
  unit: z.enum(["auto", "mm²", "cm²", "m²", "ha", "km²"]).default("auto"),
}).strict();
export const lengthLikeUnitSchema = z.enum(["auto", "mm", "cm", "m", "km"]);
export const perimeterDisplayConfigSchema = numericFormatSchema.extend({
  unit: lengthLikeUnitSchema.default("auto"),
}).strict();
export const lengthDisplayConfigSchema = numericFormatSchema.extend({
  unit: lengthLikeUnitSchema.default("auto"),
}).strict();
export const datetimeDisplayConfigSchema = z.object({
  tz: z.string().default("UTC"),
  format: z.string().nullish(),
}).strict();

export const displayConfigSchema = z.discriminatedUnion("kind", [
  z.object({ kind: z.literal("string"), config: stringDisplayConfigSchema }),
  z.object({ kind: z.literal("number"), config: numberDisplayConfigSchema }),
  z.object({ kind: z.literal("area"), config: areaDisplayConfigSchema }),
  z.object({ kind: z.literal("perimeter"), config: perimeterDisplayConfigSchema }),
  z.object({ kind: z.literal("length"), config: lengthDisplayConfigSchema }),
  z.object({ kind: z.literal("datetime"), config: datetimeDisplayConfigSchema }),
]);

export const fieldDefinitionSchema = z.object({
  id: z.string(),
  name: z.string().min(1, "Field name is required").max(255, "Field name too long"),
  kind: fieldKindSchema,
  is_computed: z.boolean().default(false),
  display_config: z.record(z.string(), z.unknown()).default({}),
  // Formula fields only: the SQL expression and its inferred result kind
  formula: z.string().optional(),
  output_kind: z.string().optional(),
});

export const RESERVED_FIELD_NAMES = ["id", "geometry", "geom", "__duckdb_row_id"];

export const createEmptyLayerSchema = z.object({
  name: z.string().min(1, "Layer name is required"),
  geometryType: z.enum(["point", "line", "polygon"]).nullable(),
  fields: z
    .array(fieldDefinitionSchema)
    .refine(
      (fields) => {
        const names = fields.map((f) => f.name.toLowerCase());
        return new Set(names).size === names.length;
      },
      { message: "Field names must be unique" }
    )
    .refine(
      (fields) =>
        fields.every((f) => !RESERVED_FIELD_NAMES.includes(f.name.toLowerCase())),
      { message: "Field name conflicts with a reserved system column" }
    ),
});

export type FieldDefinition = z.infer<typeof fieldDefinitionSchema>;
export type CreateEmptyLayerInput = z.infer<typeof createEmptyLayerSchema>;

// Map of geometry types to allowed kinds for the Add-Field dropdown
export const ALLOWED_KINDS_BY_GEOM_TYPE: Record<string, FieldKind[]> = {
  point: ["string", "number", "datetime", "boolean", "formula"],
  multipoint: ["string", "number", "datetime", "boolean", "formula"],
  line: ["string", "number", "length", "datetime", "boolean", "formula"],
  multiline: ["string", "number", "length", "datetime", "boolean", "formula"],
  polygon: ["string", "number", "area", "perimeter", "datetime", "boolean", "formula"],
  multipolygon: ["string", "number", "area", "perimeter", "datetime", "boolean", "formula"],
};

// Kinds whose VALUES are computed by the backend (read-only in editors).
// Formula belongs here: its values are derived, only its expression is edited.
export const COMPUTED_KINDS: ReadonlySet<FieldKind> = new Set([
  "area",
  "perimeter",
  "length",
  "formula",
]);
