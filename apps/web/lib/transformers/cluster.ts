import type { FeatureLayerPointProperties, Layer } from "@/lib/validations/layer";
import type { ProjectLayer } from "@/lib/validations/project";

type LayerLike = ProjectLayer | Layer;

const rgb = ([r, g, b]: number[]): string => `rgb(${r}, ${g}, ${b})`;

const getCluster = (layer: LayerLike): NonNullable<FeatureLayerPointProperties["cluster"]> | undefined => {
  return (layer.properties as FeatureLayerPointProperties | undefined)?.cluster;
};

export const isClusteringEnabled = (layer: LayerLike): boolean => {
  return !!getCluster(layer)?.enabled;
};

export const getClusterGeoJsonUrl = (
  geoapiBaseUrl: string,
  layerId: string,
  filter?: string,
): string => {
  const params = new URLSearchParams({ limit: "100000", f: "json" });
  if (filter) params.set("filter", filter);
  return `${geoapiBaseUrl}/collections/${layerId}/items?${params.toString()}`;
};

const buildClusterPropertiesFromMapping = (
  markerField: string,
  marker_mapping: NonNullable<FeatureLayerPointProperties["marker_mapping"]>,
): Record<string, unknown> | undefined => {
  if (!marker_mapping.length) return undefined;
  const props: Record<string, unknown> = {};
  marker_mapping.forEach((entry, i) => {
    const values = entry[0];
    if (!values || values.length === 0) return;
    props[`cat_${i}`] = [
      "+",
      ["case", ["in", ["get", markerField], ["literal", values]], 1, 0],
    ];
  });
  return Object.keys(props).length > 0 ? props : undefined;
};

export const buildClusterSourceProps = (layer: LayerLike) => {
  const cluster = getCluster(layer);
  const props = layer.properties as FeatureLayerPointProperties;
  const markerField = props?.marker_field?.name;
  const markerMapping = props?.marker_mapping;

  let clusterProperties: Record<string, unknown> | undefined;
  if (props?.custom_marker && markerField && markerMapping?.length) {
    clusterProperties = buildClusterPropertiesFromMapping(markerField, markerMapping);
  }

  return {
    cluster: true,
    clusterRadius: cluster?.radius ?? 50,
    clusterMinPoints: cluster?.min_points ?? 3,
    clusterMaxZoom: cluster?.max_zoom ?? 14,
    // Source maxzoom must be greater than clusterMaxZoom. Cluster schema caps
    // max_zoom at 20, so we set source maxzoom to 22 to give it headroom.
    maxzoom: 22,
    ...(clusterProperties ? { clusterProperties } : {}),
  };
};

// MapLibre fades symbol/circle opacity over ~300ms when supercluster
// regenerates clusters on zoom/data change. Setting each *-transition
// duration to 0 removes the fade for cluster layers only.
const NO_FADE = { duration: 0, delay: 0 };

export const buildClusterCirclePaint = (layer: LayerLike) => {
  const cluster = getCluster(layer)!;
  return {
    "circle-color": rgb(cluster.color),
    "circle-radius": ["step", ["get", "point_count"], 16, 10, 22, 50, 28] as unknown,
    "circle-stroke-width": 0,
    "circle-opacity-transition": NO_FADE,
  };
};

export const buildClusterCountTextSpec = (layer: LayerLike) => {
  const cluster = getCluster(layer)!;
  return {
    type: "symbol" as const,
    layout: {
      // to-string so MapLibre's strict text-field type check is happy
      "text-field": ["to-string", ["get", "point_count"]] as unknown,
      // Match the badge text style for visual consistency between
      // circle-point clusters and marker-cluster badges.
      "text-font": ["Roboto Bold", "Roboto Regular"],
      "text-size": 12,
      "text-allow-overlap": true,
      "text-ignore-placement": true,
    },
    paint: {
      "text-color": rgb(cluster.text_color),
      "text-opacity-transition": NO_FADE,
      // Thin same-color halo thickens the digit strokes for crisp rendering
      // against the bubble fill at small sizes.
      "text-halo-color": rgb(cluster.color),
      "text-halo-width": 1,
      "text-halo-blur": 0,
    },
  };
};

/**
 * Wrap an `icon-image` lookup in coalesce(image(name), image(fallback)) so the
 * cluster symbol bucket never sees a missing icon. The async marker preload
 * (addOrUpdateMarkerImages → loadImage → addImage) can lose the race against
 * MapLibre's bucket creation; if the lookup resolves to null, addBucket reads
 * undefined.length and crashes. `badge-sdf` is registered up-front in
 * registerSpriteImages, so it's always available as the fallback. Once the
 * real marker image loads, MapLibre re-evaluates the expression.
 */
const safeIconImage = (imageName: string): unknown => [
  "coalesce",
  ["image", imageName],
  ["image", "badge-sdf"],
];

/**
 * Returns the `icon-image` for cluster symbols. A layer's base marker takes
 * precedence when set — a cluster mixes categories, so the neutral base icon
 * is more honest than any single value's icon. Layers with `marker_field` +
 * `marker_mapping` but no base marker fall back to the icon of the dominant
 * category via clusterProperties counters (cat_0, cat_1, …); ties resolve to
 * the first matching position from `marker_mapping`.
 */
export const buildClusterMarkerIconExpression = (layer: LayerLike): unknown => {
  const props = layer.properties as FeatureLayerPointProperties;
  const layerId = String(layer.id);

  if (props?.marker?.name) {
    return safeIconImage(`${layerId}-${props.marker.name}`);
  }

  if (props?.marker_field?.name && props?.marker_mapping?.length) {
    const mapping = props.marker_mapping;
    const counts = mapping.map((_, i) => ["get", `cat_${i}`]);
    const maxExpr = ["max", ...counts];
    const caseExpr: unknown[] = ["case"];
    mapping.forEach((entry, i) => {
      const marker = entry[1];
      if (!marker) return;
      if (i < mapping.length - 1) {
        caseExpr.push(
          ["==", ["var", "m"], ["get", `cat_${i}`]],
          safeIconImage(`${layerId}-${marker.name}`),
        );
      }
    });
    const lastMarker = mapping[mapping.length - 1]?.[1];
    caseExpr.push(lastMarker ? safeIconImage(`${layerId}-${lastMarker.name}`) : "");
    return ["let", "m", maxExpr, caseExpr];
  }

  return "";
};

/**
 * GOAT's built-in markers (source: "library") are SDF and must be tinted —
 * without an explicit icon-color they render as black. Spec: built-in markers
 * always render gray at the clustered level. Returns undefined for custom
 * (raster, source: "custom") markers — icon-color has no effect on raster
 * anyway and they keep their native colors.
 */
export const buildClusterMarkerIconColor = (layer: LayerLike): string | undefined => {
  const props = layer.properties as FeatureLayerPointProperties;
  const sources = new Set<string>();
  if (props?.marker?.source) sources.add(props.marker.source);
  props?.marker_mapping?.forEach((entry) => {
    if (entry[1]?.source) sources.add(entry[1].source);
  });
  return sources.has("library") ? "rgb(128, 128, 128)" : undefined;
};

const BADGE_MIN_OFFSET_PX = 10;
const BADGE_ICON_SIZE = 0.3; // 64px SDF × 0.3 ≈ 19px on screen

/**
 * Badge is a small circle tucked into the upper-right corner of the marker
 * icon, with the count number inside. The marker renders at `marker_size/200`
 * scale on a 200×200 source image, so the rendered half-width is ~marker_size/2
 * pixels. Placing the badge at (+half-marker, -half-marker) puts it right at
 * the marker's corner, overlapping slightly with the icon for a polished look.
 *
 * Positioning uses paint-level `icon-translate` and `text-translate` (both in
 * pixels) rather than layout-level `icon-offset` / `text-offset` (icon px,
 * text em — the unit mismatch was misaligning the count from the badge).
 */
export const buildClusterBadgeSpec = (layer: LayerLike) => {
  const cluster = getCluster(layer)!;
  const props = layer.properties as FeatureLayerPointProperties;
  const markerSize = props?.marker_size ?? 10;
  const offset = Math.max(BADGE_MIN_OFFSET_PX, Math.round(markerSize / 2));
  return {
    type: "symbol" as const,
    layout: {
      "icon-image": "badge-sdf",
      // Step icon-size up for higher counts so 3+ digit numbers fit
      // comfortably with breathing room from the badge edge. Single & double
      // digits stay at the base size (sized just right for "5" / "13").
      // Each additional digit bumps the badge by +0.1 of source size (~6.4px
      // of diameter), giving roughly constant ~5px padding around the text.
      // Source is 64px, so 0.3 → ~19px, 0.5 → ~32px, ... 0.8 → ~51px.
      "icon-size": [
        "step",
        ["get", "point_count"],
        BADGE_ICON_SIZE,            // < 100   (1–2 digits)
        100,
        BADGE_ICON_SIZE + 0.2,      // 100..999    (3 digits)
        1000,
        BADGE_ICON_SIZE + 0.3,      // 1k..9.9k    (4 digits)
        10000,
        BADGE_ICON_SIZE + 0.4,      // 10k..99.9k  (5 digits)
        100000,
        BADGE_ICON_SIZE + 0.5,      // 100k+       (6+ digits)
      ] as unknown,
      "icon-allow-overlap": true,
      "icon-ignore-placement": true,
      "text-field": ["to-string", ["get", "point_count"]] as unknown,
      // Bold first for crisper digits at the badge's small size; Roboto
      // Regular is the GOAT-wide fallback (see getSymbolStyleSpec in
      // transformers/layer.ts) in case Bold glyphs aren't in the style.
      "text-font": ["Roboto Bold", "Roboto Regular"],
      "text-size": 12,
      "text-allow-overlap": true,
      "text-ignore-placement": true,
    },
    paint: {
      "icon-color": rgb(cluster.color),
      "icon-translate": [offset, -offset],
      "icon-opacity-transition": NO_FADE,
      "text-color": rgb(cluster.text_color),
      "text-translate": [offset, -offset],
      "text-opacity-transition": NO_FADE,
      // Thin same-color halo improves legibility of the count against the
      // badge fill at small text sizes. text-halo-blur 0 keeps the edge sharp.
      "text-halo-color": rgb(cluster.color),
      "text-halo-width": 1,
      "text-halo-blur": 0,
    },
  };
};
