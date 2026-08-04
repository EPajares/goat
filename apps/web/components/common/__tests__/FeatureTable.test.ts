import { describe, expect, it } from "vitest";

import { formatFeatureValue, isArrayOfRecords } from "@/components/common/FeatureTable";

describe("formatFeatureValue", () => {
  it("renders empty for absent values rather than 'null'", () => {
    expect(formatFeatureValue(null)).toBe("");
    expect(formatFeatureValue(undefined)).toBe("");
    expect(formatFeatureValue(null, { name: "a", type: "string" })).toBe("");
  });

  it("passes strings and numbers through when the field is plain text", () => {
    expect(formatFeatureValue("abc", { name: "a", type: "string" })).toBe("abc");
    expect(formatFeatureValue(42, { name: "a", type: "number" })).toBe("42");
  });

  it("formats by the field's display kind, not its raw type", () => {
    const asBoolean = formatFeatureValue(true, { name: "verified", type: "boolean", kind: "boolean" });
    expect(asBoolean).not.toBe("true");
    expect(asBoolean.length).toBeGreaterThan(0);
  });

  it("serialises objects so a cell never renders [object Object]", () => {
    expect(formatFeatureValue({ a: 1 })).toBe('{"a":1}');
    expect(formatFeatureValue([1, 2])).toBe("[1,2]");
  });

  it("survives a field with no kind information", () => {
    expect(formatFeatureValue("x", { name: "a", type: "VARCHAR" })).toBe("x");
  });
});

describe("isArrayOfRecords", () => {
  it("accepts a non-empty list of plain objects", () => {
    expect(isArrayOfRecords([{ a: 1 }, { a: 2 }])).toBe(true);
  });

  it("rejects anything that cannot render as a nested table", () => {
    expect(isArrayOfRecords([])).toBe(false);
    expect(isArrayOfRecords([1, 2, 3])).toBe(false);
    expect(isArrayOfRecords([["a"], ["b"]])).toBe(false);
    expect(isArrayOfRecords([null])).toBe(false);
    expect(isArrayOfRecords({ a: 1 })).toBe(false);
    expect(isArrayOfRecords(undefined)).toBe(false);
    expect(isArrayOfRecords("[]")).toBe(false);
  });
});
