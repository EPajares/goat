import { act, renderHook } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { FilterType, type Expression } from "@/lib/validations/filter";

import { combineCqlFilters, useTableViewFilterController } from "@/hooks/useTableViewFilterController";

const FIELDS = [
  { name: "status", type: "string" },
  { name: "height", type: "number" },
];

const expression = (partial: Partial<Expression>): Expression => ({
  id: "e1",
  attribute: "status",
  expression: "is",
  value: "open",
  type: FilterType.Logical,
  ...partial,
});

describe("useTableViewFilterController", () => {
  it("starts with nothing filtered and no query filter", () => {
    const { result } = renderHook(() => useTableViewFilterController(FIELDS));
    expect(result.current.controller.expressions).toEqual([]);
    expect(result.current.cqlFilter).toBeUndefined();
  });

  it("adds an expression and compiles it to CQL for the query", () => {
    const { result } = renderHook(() => useTableViewFilterController(FIELDS));
    act(() => result.current.controller.upsert(expression({})));

    expect(result.current.controller.expressions).toHaveLength(1);
    const cql = JSON.parse(result.current.cqlFilter!);
    expect(cql).toMatchObject({ op: "and" });
    expect(JSON.stringify(cql)).toContain("status");
  });

  it("replaces by id rather than accumulating duplicates", () => {
    const { result } = renderHook(() => useTableViewFilterController(FIELDS));
    act(() => result.current.controller.upsert(expression({ id: "e1", value: "open" })));
    act(() => result.current.controller.upsert(expression({ id: "e1", value: "closed" })));

    expect(result.current.controller.expressions).toHaveLength(1);
    expect(result.current.controller.expressions[0].value).toBe("closed");
  });

  it("keeps filters on different columns side by side", () => {
    const { result } = renderHook(() => useTableViewFilterController(FIELDS));
    act(() => result.current.controller.upsert(expression({ id: "e1" })));
    act(() =>
      result.current.controller.upsert(
        expression({ id: "e2", attribute: "height", expression: "is_at_least", value: 5 })
      )
    );
    expect(result.current.controller.expressions.map((e) => e.attribute)).toEqual(["status", "height"]);
  });

  it("removes one and clears all", () => {
    const { result } = renderHook(() => useTableViewFilterController(FIELDS));
    act(() => result.current.controller.upsert(expression({ id: "e1" })));
    act(() => result.current.controller.upsert(expression({ id: "e2", attribute: "height" })));

    act(() => result.current.controller.remove("e1"));
    expect(result.current.controller.expressions.map((e) => e.id)).toEqual(["e2"]);

    act(() => result.current.clear());
    expect(result.current.controller.expressions).toEqual([]);
    expect(result.current.cqlFilter).toBeUndefined();
  });

  it("reports itself as an and-controller, matching how it compiles", () => {
    const { result } = renderHook(() => useTableViewFilterController(FIELDS));
    expect(result.current.controller.logicalOperator).toBe("and");
  });

  it("can be marked read-only for viewers who may not filter", () => {
    const { result } = renderHook(() => useTableViewFilterController(FIELDS, { canEdit: false }));
    expect(result.current.controller.canEdit).toBe(false);
  });
});

describe("combineCqlFilters", () => {
  const author = JSON.stringify({ op: "=", args: [{ property: "city" }, "Hamburg"] });
  const viewer = JSON.stringify({ op: "=", args: [{ property: "status" }, "open"] });

  it("returns undefined when there is nothing to apply", () => {
    expect(combineCqlFilters(undefined, undefined)).toBeUndefined();
  });

  it("passes a single filter through untouched", () => {
    expect(combineCqlFilters(author, undefined)).toBe(author);
    expect(combineCqlFilters(undefined, viewer)).toBe(viewer);
  });

  it("ANDs the author's filter with the viewer's, narrowing rather than replacing", () => {
    const combined = JSON.parse(combineCqlFilters(author, viewer)!);
    expect(combined.op).toBe("and");
    expect(combined.args).toHaveLength(2);
    expect(combined.args[0]).toEqual(JSON.parse(author));
    expect(combined.args[1]).toEqual(JSON.parse(viewer));
  });
});
