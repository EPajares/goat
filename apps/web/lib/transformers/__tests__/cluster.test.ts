import { describe, expect, it } from "vitest";

import {
  buildClusterBadgeSpec,
  buildClusterCirclePaint,
  buildClusterCountTextSpec,
  buildClusterMarkerIconColor,
  buildClusterMarkerIconExpression,
  buildClusterSourceProps,
  getClusterGeoJsonUrl,
} from "../cluster";

const fixedColorLayer = {
  id: "abc-123",
  properties: {
    cluster: {
      enabled: true,
      radius: 30,
      min_points: 5,
      max_zoom: 12,
      color: [10, 20, 30],
      text_color: [200, 210, 220],
    },
  },
} as unknown as Parameters<typeof buildClusterSourceProps>[0];

const fixedIconLayer = {
  id: "abc-123",
  properties: {
    custom_marker: true,
    marker: { name: "bus", source: "library", url: "" },
    cluster: { enabled: true, radius: 50, min_points: 3, max_zoom: 14, color: [0, 0, 0], text_color: [255, 255, 255] },
  },
} as unknown as Parameters<typeof buildClusterSourceProps>[0];

const byAttrCustomUploadedMarkerLayer = {
  id: "abc-123",
  properties: {
    custom_marker: true,
    marker_field: { name: "mode" },
    marker_mapping: [
      [["bus"], { name: "bus-icon", source: "custom", url: "" }],
      [["tram", "lrt"], { name: "tram-icon", source: "custom", url: "" }],
      [["ubahn"], { name: "ubahn-icon", source: "custom", url: "" }],
    ],
    cluster: { enabled: true, radius: 50, min_points: 3, max_zoom: 14, color: [0, 0, 0], text_color: [255, 255, 255] },
  },
} as unknown as Parameters<typeof buildClusterSourceProps>[0];

const byAttrBuiltinMarkerLayer = {
  id: "abc-123",
  properties: {
    custom_marker: true,
    marker_field: { name: "mode" },
    marker_mapping: [
      [["bus"], { name: "bus-icon", source: "library", url: "" }],
      [["tram"], { name: "tram-icon", source: "library", url: "" }],
    ],
    cluster: { enabled: true, radius: 50, min_points: 3, max_zoom: 14, color: [0, 0, 0], text_color: [255, 255, 255] },
  },
} as unknown as Parameters<typeof buildClusterSourceProps>[0];

describe("getClusterGeoJsonUrl", () => {
  it("builds the OGC items URL with limit=100000", () => {
    const url = getClusterGeoJsonUrl("http://geoapi", "layer-1");
    expect(url).toBe("http://geoapi/collections/layer-1/items?limit=100000&f=json");
  });

  it("appends a filter param when given", () => {
    const url = getClusterGeoJsonUrl("http://geoapi", "layer-1", '{"op":"="}');
    expect(url).toContain("filter=");
    expect(url).toContain(encodeURIComponent('{"op":"="}'));
  });
});

describe("buildClusterSourceProps", () => {
  it("returns cluster source props from the layer's cluster config", () => {
    const props = buildClusterSourceProps(fixedColorLayer);
    expect(props.cluster).toBe(true);
    expect(props.clusterRadius).toBe(30);
    expect(props.clusterMinPoints).toBe(5);
    expect(props.clusterMaxZoom).toBe(12);
  });

  it("emits clusterProperties when the layer has marker_mapping", () => {
    const props = buildClusterSourceProps(byAttrCustomUploadedMarkerLayer);
    expect(Object.keys(props.clusterProperties ?? {})).toEqual(["cat_0", "cat_1", "cat_2"]);
    expect((props.clusterProperties?.cat_0 as unknown[])[0]).toBe("+");
  });

  it("omits clusterProperties when the layer has no marker_mapping", () => {
    expect(buildClusterSourceProps(fixedColorLayer).clusterProperties).toBeUndefined();
    expect(buildClusterSourceProps(fixedIconLayer).clusterProperties).toBeUndefined();
  });
});

describe("buildClusterCirclePaint (circle-point cluster bubble)", () => {
  it("emits step expression for radius and uses cluster.color/text_color", () => {
    const paint = buildClusterCirclePaint(fixedColorLayer);
    expect(paint["circle-color"]).toBe("rgb(10, 20, 30)");
    expect(paint["circle-radius"]).toEqual(["step", ["get", "point_count"], 16, 10, 22, 50, 28]);
  });
});

describe("buildClusterCountTextSpec (text label over circle bubble)", () => {
  it("uses point_count and the configured text color", () => {
    const spec = buildClusterCountTextSpec(fixedColorLayer);
    expect(spec.layout["text-field"]).toEqual(["to-string", ["get", "point_count"]]);
    expect(spec.paint["text-color"]).toBe("rgb(200, 210, 220)");
  });
});

describe("buildClusterMarkerIconExpression (icon image for marker clusters)", () => {
  it("wraps the fixed marker image in coalesce(image, image(badge-sdf))", () => {
    // Wrapping prevents addBucket crashes when the marker preload loses the
    // race against MapLibre's bucket creation.
    expect(buildClusterMarkerIconExpression(fixedIconLayer)).toEqual([
      "coalesce",
      ["image", "abc-123-bus"],
      ["image", "badge-sdf"],
    ]);
  });

  it("returns an argmax case expression when marker_mapping is set", () => {
    const expr = buildClusterMarkerIconExpression(byAttrCustomUploadedMarkerLayer);
    expect(Array.isArray(expr)).toBe(true);
    expect((expr as unknown[])[0]).toBe("let");
    expect((expr as unknown[])[1]).toBe("m");
    const maxExpr = (expr as unknown[])[2] as unknown[];
    expect(maxExpr[0]).toBe("max");
    expect(maxExpr.slice(1)).toEqual([
      ["get", "cat_0"],
      ["get", "cat_1"],
      ["get", "cat_2"],
    ]);
    const caseExpr = (expr as unknown[])[3] as unknown[];
    expect(caseExpr[0]).toBe("case");
    // Each per-category branch now resolves to a coalesce(image, image)
    expect(caseExpr).toContainEqual([
      "coalesce",
      ["image", "abc-123-bus-icon"],
      ["image", "badge-sdf"],
    ]);
    expect(caseExpr).toContainEqual([
      "coalesce",
      ["image", "abc-123-tram-icon"],
      ["image", "badge-sdf"],
    ]);
    expect(caseExpr).toContainEqual([
      "coalesce",
      ["image", "abc-123-ubahn-icon"],
      ["image", "badge-sdf"],
    ]);
  });

  it("prefers the base marker over the dominant-category expression when one is set", () => {
    // A cluster mixes statuses, so a layer that has a neutral base marker
    // shows it instead of the majority value's icon.
    const layer = {
      ...byAttrCustomUploadedMarkerLayer,
      properties: {
        ...(byAttrCustomUploadedMarkerLayer as { properties: object }).properties,
        marker: { name: "base-sign", source: "custom", url: "" },
      },
    } as typeof byAttrCustomUploadedMarkerLayer;
    expect(buildClusterMarkerIconExpression(layer)).toEqual([
      "coalesce",
      ["image", "abc-123-base-sign"],
      ["image", "badge-sdf"],
    ]);
  });

  it("keeps the dominant-category expression when the base marker name is empty", () => {
    const layer = {
      ...byAttrCustomUploadedMarkerLayer,
      properties: {
        ...(byAttrCustomUploadedMarkerLayer as { properties: object }).properties,
        marker: { name: "", source: "custom", url: "" },
      },
    } as typeof byAttrCustomUploadedMarkerLayer;
    const expr = buildClusterMarkerIconExpression(layer);
    expect((expr as unknown[])[0]).toBe("let");
  });
});

describe("buildClusterMarkerIconColor (gray override for built-in markers)", () => {
  it("returns gray for a library (built-in SDF) marker layer", () => {
    // Library markers are SDF and need tinting; spec forces gray on clusters.
    expect(buildClusterMarkerIconColor(fixedIconLayer)).toBe("rgb(128, 128, 128)");
    expect(buildClusterMarkerIconColor(byAttrBuiltinMarkerLayer)).toBe("rgb(128, 128, 128)");
  });

  it("returns undefined for a custom (user-uploaded raster) marker layer", () => {
    // Raster markers ignore icon-color; spec keeps native colors.
    expect(buildClusterMarkerIconColor(byAttrCustomUploadedMarkerLayer)).toBeUndefined();
  });
});

describe("buildClusterBadgeSpec", () => {
  it("uses badge-sdf icon tinted by cluster.color with point_count text", () => {
    const spec = buildClusterBadgeSpec(fixedIconLayer);
    expect(spec.layout["icon-image"]).toBe("badge-sdf");
    expect(spec.layout["text-field"]).toEqual(["to-string", ["get", "point_count"]]);
    expect(spec.paint["icon-color"]).toBe("rgb(0, 0, 0)");
    expect(spec.paint["text-color"]).toBe("rgb(255, 255, 255)");
    // Badge uses icon-translate (paint, pixels) rather than icon-offset.
    // marker_size default 10 → offset = round(10/2)=5, clamped to BADGE_MIN_OFFSET_PX (10).
    expect(spec.paint["icon-translate"]).toEqual([10, -10]);
    expect(spec.paint["text-translate"]).toEqual([10, -10]);
  });

  it("scales the badge offset with the marker size", () => {
    const layerWithLargeMarker = {
      id: "abc-123",
      properties: {
        custom_marker: true,
        marker: { name: "bus", source: "library", url: "" },
        marker_size: 60,
        cluster: { enabled: true, radius: 50, min_points: 3, max_zoom: 14, color: [0, 0, 0], text_color: [255, 255, 255] },
      },
    } as unknown as Parameters<typeof buildClusterBadgeSpec>[0];
    const spec = buildClusterBadgeSpec(layerWithLargeMarker);
    // marker_size 60 → offset = round(60/2) = 30 (places badge at upper-right corner)
    expect(spec.paint["icon-translate"]).toEqual([30, -30]);
    expect(spec.paint["text-translate"]).toEqual([30, -30]);
  });
});
