/**
 * Tests for Atlas/Series Print Utilities
 */
import { describe, expect, it } from "vitest";

import type {
  AtlasFeatureCoverage,
  AtlasGridCoverage,
  MapAtlasControl,
} from "@/lib/validations/reportLayout";

import {
  calculateMapViewport,
  generateFeaturePages,
  generateGridPages,
  getAdjacentGridPages,
  getFeatureBounds,
  resolvePageLabel,
  scaleToZoom,
  zoomToScale,
} from "../atlas-utils";

describe("generateGridPages", () => {
  it("should calculate 2x2 manual grid", () => {
    const coverage: AtlasGridCoverage = {
      type: "grid",
      bounds: [-10, -10, 10, 10],
      rows: 2,
      columns: 2,
      overlap_percent: 0,
    };

    const result = generateGridPages(coverage);

    expect(result.totalPages).toBe(4);
    expect(result.pages).toHaveLength(4);
    expect(result.coverageType).toBe("grid");
  });

  it("should calculate auto grid for wide extent", () => {
    const coverage: AtlasGridCoverage = {
      type: "grid",
      bounds: [-20, -5, 20, 5], // Wide extent (40x10)
      overlap_percent: 0,
    };

    const result = generateGridPages(coverage, "Page {page_number}", 1.414);

    expect(result.totalPages).toBeGreaterThan(0);
  });

  it("should apply overlap percentage correctly", () => {
    const coverage: AtlasGridCoverage = {
      type: "grid",
      bounds: [0, 0, 100, 100],
      rows: 2,
      columns: 2,
      overlap_percent: 10,
    };

    const result = generateGridPages(coverage);

    // With 10% overlap, tiles should extend beyond simple division
    const firstPage = result.pages[0];
    const secondPage = result.pages[1];

    expect(firstPage.bounds[2]).toBeGreaterThan(50); // East edge > 50
    expect(secondPage.bounds[0]).toBeLessThan(50); // West edge < 50
  });

  it("should generate correct page labels from template", () => {
    const coverage: AtlasGridCoverage = {
      type: "grid",
      bounds: [0, 0, 100, 100],
      rows: 2,
      columns: 2,
      overlap_percent: 0,
    };

    const result = generateGridPages(coverage, "Page {page_number} of {total_pages}");

    expect(result.pages[0].label).toBe("Page 1 of 4");
    expect(result.pages[1].label).toBe("Page 2 of 4");
    expect(result.pages[2].label).toBe("Page 3 of 4");
    expect(result.pages[3].label).toBe("Page 4 of 4");
  });

  it("should calculate page centers correctly", () => {
    const coverage: AtlasGridCoverage = {
      type: "grid",
      bounds: [0, 0, 100, 100],
      rows: 2,
      columns: 2,
      overlap_percent: 0,
    };

    const result = generateGridPages(coverage);

    // First page (top-left) center should be around [25, 75]
    expect(result.pages[0].center[0]).toBeCloseTo(25, 0);
    expect(result.pages[0].center[1]).toBeCloseTo(75, 0);

    // Last page (bottom-right) center should be around [75, 25]
    expect(result.pages[3].center[0]).toBeCloseTo(75, 0);
    expect(result.pages[3].center[1]).toBeCloseTo(25, 0);
  });

  it("should include grid position in pages", () => {
    const coverage: AtlasGridCoverage = {
      type: "grid",
      bounds: [0, 0, 100, 100],
      rows: 2,
      columns: 2,
      overlap_percent: 0,
    };

    const result = generateGridPages(coverage);

    expect(result.pages[0].grid).toEqual({ row: 0, column: 0 });
    expect(result.pages[1].grid).toEqual({ row: 0, column: 1 });
    expect(result.pages[2].grid).toEqual({ row: 1, column: 0 });
    expect(result.pages[3].grid).toEqual({ row: 1, column: 1 });
  });
});

describe("generateFeaturePages", () => {
  const mockFeatures: GeoJSON.Feature[] = [
    {
      type: "Feature",
      id: "1",
      geometry: { type: "Point", coordinates: [10, 20] },
      properties: { name: "Feature A", value: 100 },
    },
    {
      type: "Feature",
      id: "2",
      geometry: { type: "Point", coordinates: [30, 40] },
      properties: { name: "Feature B", value: 200 },
    },
    {
      type: "Feature",
      id: "3",
      geometry: { type: "Point", coordinates: [50, 60] },
      properties: { name: "Feature C", value: 50 },
    },
  ];

  it("should create one page per feature", () => {
    const coverage: AtlasFeatureCoverage = {
      type: "feature",
      layer_project_id: 42,
      sort_order: "asc",
    };

    const result = generateFeaturePages(coverage, mockFeatures);

    expect(result.totalPages).toBe(3);
    expect(result.pages).toHaveLength(3);
    expect(result.coverageType).toBe("feature");
  });

  it("should sort features by attribute", () => {
    const coverage: AtlasFeatureCoverage = {
      type: "feature",
      layer_project_id: 42,
      sort_by: "name",
      sort_order: "asc",
    };

    const result = generateFeaturePages(coverage, mockFeatures);

    expect(result.pages[0].feature?.properties.name).toBe("Feature A");
    expect(result.pages[1].feature?.properties.name).toBe("Feature B");
    expect(result.pages[2].feature?.properties.name).toBe("Feature C");
  });

  it("should sort features descending", () => {
    const coverage: AtlasFeatureCoverage = {
      type: "feature",
      layer_project_id: 42,
      sort_by: "value",
      sort_order: "desc",
    };

    const result = generateFeaturePages(coverage, mockFeatures);

    expect(result.pages[0].feature?.properties.value).toBe(200);
    expect(result.pages[1].feature?.properties.value).toBe(100);
    expect(result.pages[2].feature?.properties.value).toBe(50);
  });

  it("should resolve feature attributes in labels", () => {
    const coverage: AtlasFeatureCoverage = {
      type: "feature",
      layer_project_id: 42,
      sort_order: "asc",
    };

    const result = generateFeaturePages(
      coverage,
      mockFeatures,
      "{feature.name} - Page {page_number}/{total_pages}"
    );

    expect(result.pages[0].label).toBe("Feature A - Page 1/3");
    expect(result.pages[1].label).toBe("Feature B - Page 2/3");
  });

  it("should calculate overview bounds from all features", () => {
    const coverage: AtlasFeatureCoverage = {
      type: "feature",
      layer_project_id: 42,
      sort_order: "asc",
    };

    const result = generateFeaturePages(coverage, mockFeatures);

    // Overview should encompass all features
    expect(result.overviewBounds[0]).toBeLessThanOrEqual(10); // west
    expect(result.overviewBounds[1]).toBeLessThanOrEqual(20); // south
    expect(result.overviewBounds[2]).toBeGreaterThanOrEqual(50); // east
    expect(result.overviewBounds[3]).toBeGreaterThanOrEqual(60); // north
  });
});

describe("calculateMapViewport", () => {
  it("should calculate best_fit viewport", () => {
    const page = {
      index: 0,
      pageNumber: 1,
      totalPages: 1,
      label: "Page 1",
      bounds: [0, 0, 10, 10] as [number, number, number, number],
      center: [5, 5] as [number, number],
    };

    const atlasControl: MapAtlasControl = {
      enabled: true,
      mode: "best_fit",
      margin_percent: 10,
    };

    const viewport = calculateMapViewport(page, atlasControl, 800, 600);

    expect(viewport.center).toEqual([5, 5]);
    expect(viewport.zoom).toBeGreaterThan(0);
    // Bounds should be expanded by margin
    expect(viewport.bounds[0]).toBeLessThan(0);
    expect(viewport.bounds[2]).toBeGreaterThan(10);
  });

  it("should calculate fixed_scale viewport", () => {
    const page = {
      index: 0,
      pageNumber: 1,
      totalPages: 1,
      label: "Page 1",
      bounds: [0, 0, 10, 10] as [number, number, number, number],
      center: [5, 5] as [number, number],
    };

    const atlasControl: MapAtlasControl = {
      enabled: true,
      mode: "fixed_scale",
      margin_percent: 0,
      fixed_scale: 10000, // 1:10000
    };

    const viewport = calculateMapViewport(page, atlasControl, 800, 600);

    expect(viewport.center).toEqual([5, 5]);
    expect(viewport.zoom).toBeGreaterThan(0);
  });

  it("should throw if atlas control not enabled", () => {
    const page = {
      index: 0,
      pageNumber: 1,
      totalPages: 1,
      label: "Page 1",
      bounds: [0, 0, 10, 10] as [number, number, number, number],
      center: [5, 5] as [number, number],
    };

    const atlasControl: MapAtlasControl = {
      enabled: false,
      mode: "best_fit",
      margin_percent: 10,
    };

    expect(() => calculateMapViewport(page, atlasControl, 800, 600)).toThrow();
  });
});

describe("resolvePageLabel", () => {
  it("should replace page_number and total_pages", () => {
    const result = resolvePageLabel("Page {page_number} of {total_pages}", {
      page_number: 5,
      total_pages: 10,
    });

    expect(result).toBe("Page 5 of 10");
  });

  it("should replace feature attributes", () => {
    const result = resolvePageLabel("District: {feature.name} ({feature.code})", {
      page_number: 1,
      total_pages: 1,
      feature: { name: "Munich", code: "MUC" },
    });

    expect(result).toBe("District: Munich (MUC)");
  });

  it("should handle missing feature attributes gracefully", () => {
    const result = resolvePageLabel("{feature.missing}", {
      page_number: 1,
      total_pages: 1,
      feature: { name: "Test" },
    });

    expect(result).toBe("");
  });
});

describe("getFeatureBounds", () => {
  it("should get bounds for Point", () => {
    const geometry: GeoJSON.Point = { type: "Point", coordinates: [10, 20] };
    const bounds = getFeatureBounds(geometry);

    expect(bounds[0]).toBeLessThan(10);
    expect(bounds[1]).toBeLessThan(20);
    expect(bounds[2]).toBeGreaterThan(10);
    expect(bounds[3]).toBeGreaterThan(20);
  });

  it("should get bounds for LineString", () => {
    const geometry: GeoJSON.LineString = {
      type: "LineString",
      coordinates: [
        [0, 0],
        [10, 10],
        [20, 5],
      ],
    };
    const bounds = getFeatureBounds(geometry);

    expect(bounds).toEqual([0, 0, 20, 10]);
  });

  it("should get bounds for Polygon", () => {
    const geometry: GeoJSON.Polygon = {
      type: "Polygon",
      coordinates: [
        [
          [0, 0],
          [10, 0],
          [10, 10],
          [0, 10],
          [0, 0],
        ],
      ],
    };
    const bounds = getFeatureBounds(geometry);

    expect(bounds).toEqual([0, 0, 10, 10]);
  });
});

describe("getAdjacentGridPages", () => {
  it("should find all adjacent pages for middle page", () => {
    const coverage: AtlasGridCoverage = {
      type: "grid",
      bounds: [0, 0, 100, 100],
      rows: 3,
      columns: 3,
      overlap_percent: 0,
    };

    const result = generateGridPages(coverage);
    const middlePage = result.pages[4]; // Center page (row 1, col 1)

    const adjacent = getAdjacentGridPages(middlePage, result.pages);

    expect(adjacent.north).toBeDefined();
    expect(adjacent.south).toBeDefined();
    expect(adjacent.east).toBeDefined();
    expect(adjacent.west).toBeDefined();

    expect(adjacent.north?.grid?.row).toBe(0);
    expect(adjacent.south?.grid?.row).toBe(2);
    expect(adjacent.east?.grid?.column).toBe(2);
    expect(adjacent.west?.grid?.column).toBe(0);
  });

  it("should have no north/west for top-left corner", () => {
    const coverage: AtlasGridCoverage = {
      type: "grid",
      bounds: [0, 0, 100, 100],
      rows: 3,
      columns: 3,
      overlap_percent: 0,
    };

    const result = generateGridPages(coverage);
    const topLeft = result.pages[0];

    const adjacent = getAdjacentGridPages(topLeft, result.pages);

    expect(adjacent.north).toBeUndefined();
    expect(adjacent.west).toBeUndefined();
    expect(adjacent.south).toBeDefined();
    expect(adjacent.east).toBeDefined();
  });
});

describe("scale/zoom conversion", () => {
  it("should convert scale to zoom", () => {
    // At equator, 1:10000 should be roughly zoom 14-15
    const zoom = scaleToZoom(10000, 0);
    expect(zoom).toBeGreaterThan(13);
    expect(zoom).toBeLessThan(16);
  });

  it("should convert zoom to scale", () => {
    const scale = zoomToScale(14, 0);
    // At zoom 14, scale is roughly 1:30000-40000 at equator
    expect(scale).toBeGreaterThan(20000);
    expect(scale).toBeLessThan(50000);
  });

  it("should be approximately reversible", () => {
    const originalScale = 5000;
    const zoom = scaleToZoom(originalScale, 48); // Munich latitude
    const convertedScale = zoomToScale(zoom, 48);

    // Should be within 10% of original
    expect(convertedScale).toBeCloseTo(originalScale, -2);
  });
});
