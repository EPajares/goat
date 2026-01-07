import { describe, expect, it } from "vitest";

import {
  mapElementConfigSchema,
  reportElementSchema,
  reportLayoutSchema,
} from "@/lib/validations/reportLayout";

describe("Print Template Schemas", () => {
  describe("reportLayoutSchema", () => {
    it("should validate a minimal valid template", () => {
      const template = {
        id: "123e4567-e89b-12d3-a456-426614174000",
        project_id: "123e4567-e89b-12d3-a456-426614174001",
        name: "Test Template",
        config: {
          page: {
            size: "A4",
            orientation: "portrait",
            margins: { top: 10, right: 10, bottom: 10, left: 10 },
          },
          layout: {
            type: "grid",
            columns: 12,
            rows: 12,
          },
          elements: [],
        },
      };

      const result = reportLayoutSchema.safeParse(template);
      expect(result.success).toBe(true);
    });

    it("should apply default values", () => {
      const template = {
        id: "123e4567-e89b-12d3-a456-426614174000",
        project_id: "123e4567-e89b-12d3-a456-426614174001",
        name: "Test Template",
        config: {
          page: {
            size: "A4",
            orientation: "portrait",
          },
          elements: [],
        },
      };

      const result = reportLayoutSchema.safeParse(template);
      expect(result.success).toBe(true);

      if (result.success) {
        expect(result.data.is_predefined).toBe(false);
        expect(result.data.config.page.margins.top).toBe(10);
        expect(result.data.config.layout?.type).toBe("grid");
      }
    });

    it("should reject invalid page size", () => {
      const template = {
        id: "123e4567-e89b-12d3-a456-426614174000",
        project_id: "123e4567-e89b-12d3-a456-426614174001",
        name: "Test Template",
        config: {
          page: {
            size: "INVALID",
            orientation: "portrait",
          },
          elements: [],
        },
      };

      const result = reportLayoutSchema.safeParse(template);
      expect(result.success).toBe(false);
    });

    it("should accept custom page size", () => {
      const template = {
        id: "123e4567-e89b-12d3-a456-426614174000",
        project_id: "123e4567-e89b-12d3-a456-426614174001",
        name: "Test Template",
        config: {
          page: {
            size: "Custom",
            orientation: "portrait",
            width: 200,
            height: 300,
          },
          elements: [],
        },
      };

      const result = reportLayoutSchema.safeParse(template);
      expect(result.success).toBe(true);
    });
  });

  describe("reportElementSchema", () => {
    it("should validate a map element", () => {
      const element = {
        id: "123e4567-e89b-12d3-a456-426614174001",
        type: "map",
        position: { x: 10, y: 10, width: 180, height: 200, z_index: 0 },
        config: {},
        map_config: {
          layers: [1, 2, 3],
          basemap: "mapbox://styles/mapbox/streets-v11",
          show_labels: true,
          atlas_control: { enabled: false },
          snapshot: {
            center: [13.405, 52.52],
            zoom: 12,
            bearing: 0,
            pitch: 0,
          },
        },
      };

      const result = reportElementSchema.safeParse(element);
      expect(result.success).toBe(true);
    });

    it("should validate a text element", () => {
      const element = {
        id: "123e4567-e89b-12d3-a456-426614174002",
        type: "text",
        position: { x: 10, y: 10, width: 100, height: 50 },
        config: {
          content: "Hello World",
          fontSize: 14,
          fontWeight: "bold",
        },
      };

      const result = reportElementSchema.safeParse(element);
      expect(result.success).toBe(true);
    });

    it("should apply default z_index", () => {
      const element = {
        id: "123e4567-e89b-12d3-a456-426614174003",
        type: "text",
        position: { x: 10, y: 10, width: 100, height: 30 },
        config: {},
      };

      const result = reportElementSchema.safeParse(element);
      expect(result.success).toBe(true);

      if (result.success) {
        expect(result.data.position.z_index).toBe(0);
      }
    });

    it("should reject invalid element type", () => {
      const element = {
        id: "123e4567-e89b-12d3-a456-426614174004",
        type: "invalid_type",
        position: { x: 10, y: 10, width: 100, height: 100 },
        config: {},
      };

      const result = reportElementSchema.safeParse(element);
      expect(result.success).toBe(false);
    });
  });

  describe("mapElementConfigSchema", () => {
    it("should validate minimal map config", () => {
      const config = {
        layers: [1, 2, 3],
        basemap: "mapbox://styles/mapbox/streets-v11",
      };

      const result = mapElementConfigSchema.safeParse(config);
      expect(result.success).toBe(true);
    });

    it("should apply default values for atlas_control", () => {
      const config = {
        layers: [1, 2, 3],
        basemap: "mapbox://styles/mapbox/streets-v11",
      };

      const result = mapElementConfigSchema.safeParse(config);
      expect(result.success).toBe(true);

      if (result.success) {
        expect(result.data.show_labels).toBe(true);
        expect(result.data.atlas_control.enabled).toBe(false);
        expect(result.data.atlas_control.mode).toBe("best_fit");
        expect(result.data.atlas_control.margin_percent).toBe(10);
      }
    });

    it("should validate atlas_control with fixed_scale mode", () => {
      const config = {
        layers: [1, 2, 3],
        basemap: "mapbox://styles/mapbox/streets-v11",
        atlas_control: {
          enabled: true,
          mode: "fixed_scale",
          margin_percent: 5,
          fixed_scale: 10000,
        },
      };

      const result = mapElementConfigSchema.safeParse(config);
      expect(result.success).toBe(true);

      if (result.success) {
        expect(result.data.atlas_control.mode).toBe("fixed_scale");
        expect(result.data.atlas_control.fixed_scale).toBe(10000);
      }
    });

    it("should validate snapshot viewport", () => {
      const config = {
        layers: [],
        snapshot: {
          center: [13.405, 52.52],
          zoom: 12,
          bearing: 45,
          pitch: 30,
        },
      };

      const result = mapElementConfigSchema.safeParse(config);
      expect(result.success).toBe(true);

      if (result.success) {
        expect(result.data.snapshot?.center).toEqual([13.405, 52.52]);
        expect(result.data.snapshot?.bearing).toBe(45);
      }
    });
  });
});
