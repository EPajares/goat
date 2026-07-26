import { describe, expect, it } from "vitest";

import { builderConfigSchema } from "@/lib/validations/project";

describe("builder_config settings.search", () => {
  it("defaults to places on with no searchable layers", () => {
    const parsed = builderConfigSchema.parse({});
    expect(parsed.settings.search).toEqual({ places: true, layers: [] });
  });

  it("round-trips a configured search block", () => {
    const parsed = builderConfigSchema.parse({
      settings: {
        search: {
          places: false,
          layers: [{ layer_project_id: 7, columns: ["name", "street"], label_column: "name" }],
        },
      },
    });
    expect(parsed.settings.search.places).toBe(false);
    expect(parsed.settings.search.layers[0].columns).toEqual(["name", "street"]);
  });

  it("rejects more than 3 columns", () => {
    const result = builderConfigSchema.safeParse({
      settings: {
        search: { layers: [{ layer_project_id: 7, columns: ["a", "b", "c", "d"] }] },
      },
    });
    expect(result.success).toBe(false);
  });
});
