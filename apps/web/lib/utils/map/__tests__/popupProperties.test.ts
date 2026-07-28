import { describe, expect, it } from "vitest";

import {
  buildPopupFieldConfig,
  getEffectivePopupTrigger,
  popupFieldInfo,
  selectPopupProperties,
  splitPopupProperties,
  type PopupConfigLayerLike,
} from "@/lib/utils/map/popupProperties";

const makeLayer = (properties: unknown): PopupConfigLayerLike => ({ properties });

describe("getEffectivePopupTrigger", () => {
  it("returns undefined when popup.enabled is false, regardless of trigger", () => {
    expect(
      getEffectivePopupTrigger(makeLayer({ popup: { enabled: false, trigger: "click" } }))
    ).toBeUndefined();
  });

  it("returns the configured trigger when popup is enabled with a valid trigger", () => {
    expect(
      getEffectivePopupTrigger(makeLayer({ popup: { enabled: true, trigger: "hover" } }))
    ).toBe("hover");
    expect(
      getEffectivePopupTrigger(makeLayer({ popup: { enabled: true, trigger: "click_and_hover" } }))
    ).toBe("click_and_hover");
  });

  it("falls back to default 'click' when popup.trigger is invalid/unrecognized", () => {
    expect(
      getEffectivePopupTrigger(
        makeLayer({ popup: { enabled: true, trigger: "bogus" as unknown as string } })
      )
    ).toBe("click");
  });

  it("falls back to legacy interaction.type when there is no popup block", () => {
    expect(getEffectivePopupTrigger(makeLayer({ interaction: { type: "none" } }))).toBeUndefined();
    expect(getEffectivePopupTrigger(makeLayer({ interaction: { type: "hover" } }))).toBe("hover");
    expect(getEffectivePopupTrigger(makeLayer({ interaction: { type: "click" } }))).toBe("click");
  });

  it("defaults to 'click' when there is no popup and no interaction config at all", () => {
    expect(getEffectivePopupTrigger(makeLayer({}))).toBe("click");
    expect(getEffectivePopupTrigger(makeLayer(undefined))).toBe("click");
  });

  it("handles null/undefined layer or properties without throwing", () => {
    expect(getEffectivePopupTrigger(null)).toBe("click");
    expect(getEffectivePopupTrigger(undefined)).toBe("click");
    expect(getEffectivePopupTrigger({ properties: null } as unknown as PopupConfigLayerLike)).toBe(
      "click"
    );
  });
});

describe("buildPopupFieldConfig", () => {
  it("returns hasFieldList: false and empty maps when there is no field_list content", () => {
    const result = buildPopupFieldConfig(makeLayer({}));
    expect(result).toEqual({
      fieldOrder: [],
      fieldLabels: {},
      fieldDecorators: {},
      hasFieldList: false,
    });

    // Non field_list content (e.g. image) is also filtered out.
    const withImageOnly = buildPopupFieldConfig(
      makeLayer({ interaction: { content: [{ type: "image", url: "x" }] } })
    );
    expect(withImageOnly.hasFieldList).toBe(false);
  });

  it("builds fieldOrder/fieldLabels from field_list attributes, falling back label to name", () => {
    const layer = makeLayer({
      interaction: {
        content: [
          {
            type: "field_list",
            attributes: [
              { name: "population", label: "Population", type: "number" },
              { name: "area_ha", type: "number" }, // no label -> falls back to name
            ],
          },
        ],
      },
    });
    const result = buildPopupFieldConfig(layer);
    expect(result.hasFieldList).toBe(true);
    expect(result.fieldOrder).toEqual(["population", "area_ha"]);
    expect(result.fieldLabels).toEqual({
      population: "Population",
      area_ha: "area_ha",
    });
  });

  it("keeps only the first definition when a field name is duplicated across field_list contents", () => {
    const layer = makeLayer({
      interaction: {
        content: [
          {
            type: "field_list",
            attributes: [{ name: "population", label: "First", type: "number" }],
          },
          {
            type: "field_list",
            attributes: [{ name: "population", label: "Second", type: "number" }],
          },
        ],
      },
    });
    const result = buildPopupFieldConfig(layer);
    expect(result.fieldOrder).toEqual(["population"]);
    expect(result.fieldLabels.population).toBe("First");
  });

  it("only sets a decorator entry when format, prefix, or suffix is present", () => {
    const layer = makeLayer({
      interaction: {
        content: [
          {
            type: "field_list",
            attributes: [
              { name: "plain", label: "Plain", type: "string" },
              { name: "with_format", label: "Fmt", type: "number", format: "AREA" },
              { name: "with_prefix", label: "Pre", type: "number", prefix: "$" },
              { name: "with_suffix", label: "Suf", type: "number", suffix: "m²" },
            ],
          },
        ],
      },
    });
    const result = buildPopupFieldConfig(layer);
    expect(result.fieldDecorators.plain).toBeUndefined();
    expect(result.fieldDecorators.with_format).toEqual({
      format: "AREA",
      prefix: undefined,
      suffix: undefined,
    });
    expect(result.fieldDecorators.with_prefix).toEqual({
      format: undefined,
      prefix: "$",
      suffix: undefined,
    });
    expect(result.fieldDecorators.with_suffix).toEqual({
      format: undefined,
      prefix: undefined,
      suffix: "m²",
    });
  });
});

describe("selectPopupProperties", () => {
  it("passes raw properties through unchanged when there is no field list", () => {
    const fieldConfig = buildPopupFieldConfig(makeLayer({}));
    const raw = { name: "Berlin", population: 3700000 };
    expect(selectPopupProperties(fieldConfig, raw)).toBe(raw);
  });

  it("narrows to fieldOrder when a field list is configured", () => {
    const layer = makeLayer({
      interaction: {
        content: [
          {
            type: "field_list",
            attributes: [
              { name: "name", label: "Name", type: "string" },
              { name: "population", label: "Population", type: "number" },
            ],
          },
        ],
      },
    });
    const fieldConfig = buildPopupFieldConfig(layer);
    const raw = { name: "Berlin", population: 3700000, extra_secret: "should not leak" };
    expect(selectPopupProperties(fieldConfig, raw)).toEqual({
      name: "Berlin",
      population: 3700000,
    });
  });

  it("skips a field-list entry whose name is a system property key, even though the raw key would be excluded anyway", () => {
    // This documents actual behavior: selectPopupProperties re-checks
    // isSystemPropertyKey per fieldOrder entry, so a field list that
    // (incorrectly) references a system key like "id" is dropped rather
    // than leaking the raw system value into the popup.
    const layer = makeLayer({
      interaction: {
        content: [
          {
            type: "field_list",
            attributes: [
              { name: "name", label: "Name", type: "string" },
              { name: "id", label: "Id", type: "string" },
            ],
          },
        ],
      },
    });
    const fieldConfig = buildPopupFieldConfig(layer);
    const raw = { name: "Berlin", id: "abc-123" };
    expect(selectPopupProperties(fieldConfig, raw)).toEqual({ name: "Berlin" });
  });

  it("sets undefined for a fieldOrder entry missing from raw properties", () => {
    const layer = makeLayer({
      interaction: {
        content: [{ type: "field_list", attributes: [{ name: "missing", type: "string" }] }],
      },
    });
    const fieldConfig = buildPopupFieldConfig(layer);
    const result = selectPopupProperties(fieldConfig, { other: "value" });
    expect(result).toEqual({ missing: undefined });
  });
});

describe("popupFieldInfo", () => {
  it("returns {} when there is no field list", () => {
    const fieldConfig = buildPopupFieldConfig(makeLayer({}));
    expect(popupFieldInfo(fieldConfig)).toEqual({});
  });

  it("always includes fieldLabels/fieldOrder when a field list exists", () => {
    const layer = makeLayer({
      interaction: {
        content: [
          { type: "field_list", attributes: [{ name: "name", label: "Name", type: "string" }] },
        ],
      },
    });
    const fieldConfig = buildPopupFieldConfig(layer);
    const info = popupFieldInfo(fieldConfig);
    expect(info.fieldOrder).toEqual(["name"]);
    expect(info.fieldLabels).toEqual({ name: "Name" });
    expect(info.fieldDecorators).toBeUndefined();
  });

  it("includes fieldDecorators only when non-empty", () => {
    const layer = makeLayer({
      interaction: {
        content: [
          {
            type: "field_list",
            attributes: [{ name: "area", label: "Area", type: "number", suffix: "ha" }],
          },
        ],
      },
    });
    const fieldConfig = buildPopupFieldConfig(layer);
    const info = popupFieldInfo(fieldConfig);
    expect(info.fieldDecorators).toEqual({ area: { format: undefined, prefix: undefined, suffix: "ha" } });
  });
});

describe("splitPopupProperties", () => {
  it("returns empty buckets for undefined raw input", () => {
    expect(splitPopupProperties(undefined)).toEqual({ properties: {}, jsonProperties: {} });
  });

  it("routes JSON-object/array-parseable string values to jsonProperties", () => {
    const raw = {
      tags: '{"a":1,"b":2}',
      list: "[1,2,3]",
      name: "Berlin",
    };
    const result = splitPopupProperties(raw);
    expect(result.jsonProperties).toEqual({ tags: { a: 1, b: 2 }, list: [1, 2, 3] });
    expect(result.properties).toEqual({ name: "Berlin" });
  });

  it("keeps primitive/non-JSON-parseable values in properties, including numbers and null", () => {
    const raw = { population: 3700000, active: true, note: "hello world", nothing: null };
    const result = splitPopupProperties(raw);
    // JSON.parse(null) coerces to JSON.parse("null") -> null; the `parsedValue !== null`
    // guard rejects it, so it falls through to `properties` rather than `jsonProperties`.
    expect(result.jsonProperties).toEqual({});
    expect(result.properties).toEqual({
      population: 3700000,
      active: true,
      note: "hello world",
      nothing: null,
    });
  });

  it("excludes system property keys from both buckets", () => {
    const raw = {
      layer_id: 1,
      id: 2,
      _rowid: 3,
      feature_id: 4,
      h3_3: "x",
      h3_6: "y",
      cluster: true,
      clustered: true,
      point_count: 5,
      point_count_abbreviated: "5",
      sqrt_point_count: 2.2,
      ags_gemeinde: "0001",
      ags_landkreis: "01",
      name: "kept",
    };
    const result = splitPopupProperties(raw);
    expect(result.properties).toEqual({ name: "kept" });
    expect(result.jsonProperties).toEqual({});
  });
});
