import { describe, expect, it } from "vitest";

import { createTheCQLBasedOnExpression, parseCQLQueryToObject } from "@/lib/transformers/filter";
import { FilterType, type Expression } from "@/lib/validations/filter";

const FIELDS = [
  { name: "status", type: "string" },
  { name: "groundelev", type: "number" },
  { name: "lstmoddate", type: "date" },
];

const expression = (partial: Partial<Expression>): Expression => ({
  id: "e1",
  attribute: "status",
  expression: "is",
  value: "",
  type: FilterType.Logical,
  ...partial,
});

/** Write one expression to CQL and read it back, as reopening a filter does. */
const roundTrip = (input: Expression) => {
  const cql = createTheCQLBasedOnExpression([input], FIELDS, "and");
  return parseCQLQueryToObject(cql as { op: string; args: unknown[] })[0];
};

describe("parseCQLQueryToObject", () => {
  it("keeps excludes distinct from includes", () => {
    // Both are and/or wrappers; reading the wrapper alone silently inverted
    // every excludes filter into an includes on reload.
    expect(roundTrip(expression({ expression: "excludes", value: ["a", "b"] }))).toMatchObject({
      attribute: "status",
      expression: "excludes",
      value: ["a", "b"],
    });

    expect(roundTrip(expression({ expression: "includes", value: ["a", "b"] }))).toMatchObject({
      attribute: "status",
      expression: "includes",
      value: ["a", "b"],
    });
  });

  it("reads back a negated text match", () => {
    expect(
      roundTrip(expression({ expression: "does_not_contains_the_text", value: "school" }))
    ).toMatchObject({
      attribute: "status",
      expression: "does_not_contains_the_text",
      value: "school",
    });
  });

  it("reads a numeric range as a range, not a value list", () => {
    expect(
      roundTrip(expression({ attribute: "groundelev", expression: "is_between", value: [5, 40] }))
    ).toMatchObject({
      attribute: "groundelev",
      expression: "is_between",
      value: [5, 40],
    });
  });

  it("reads a date range in the order it was written", () => {
    const parsed = roundTrip(
      expression({
        attribute: "lstmoddate",
        expression: "is_not_between",
        value: ["2024-01-01", "2024-03-01"],
      })
    );
    expect(parsed.expression).toBe("is_not_between");
    expect(parsed.attribute).toBe("lstmoddate");
    const [from, to] = parsed.value as string[];
    expect(new Date(from).getTime()).toBeLessThan(new Date(to).getTime());
  });

  it("still reads the operators it always handled", () => {
    expect(roundTrip(expression({ expression: "is", value: "a" }))).toMatchObject({
      expression: "is",
      value: "a",
    });
    expect(roundTrip(expression({ expression: "is_not", value: "a" }))).toMatchObject({
      expression: "is_not",
    });
    expect(roundTrip(expression({ expression: "contains_the_text", value: "abc" }))).toMatchObject({
      expression: "contains_the_text",
      value: "abc",
    });
    expect(roundTrip(expression({ expression: "starts_with", value: "abc" }))).toMatchObject({
      expression: "starts_with",
      value: "abc",
    });
    expect(roundTrip(expression({ expression: "is_blank" }))).toMatchObject({
      expression: "is_blank",
      attribute: "status",
    });
    expect(roundTrip(expression({ expression: "is_not_blank" }))).toMatchObject({
      expression: "is_not_blank",
      attribute: "status",
    });
    expect(
      roundTrip(expression({ attribute: "groundelev", expression: "is_at_least", value: 5 }))
    ).toMatchObject({ expression: "is_at_least", value: 5 });
  });

  it("returns nothing for an absent filter", () => {
    expect(parseCQLQueryToObject(undefined)).toEqual([]);
  });
});

describe("createTheCQLBasedOnExpression", () => {
  it("accepts numeric bounds as a pair and as the legacy string", () => {
    const fromPair = createTheCQLBasedOnExpression(
      [expression({ attribute: "groundelev", expression: "is_between", value: [5, 40] })],
      FIELDS,
      "and"
    );
    const fromString = createTheCQLBasedOnExpression(
      [expression({ attribute: "groundelev", expression: "is_between", value: "5-40" })],
      FIELDS,
      "and"
    );
    expect(fromPair).toEqual(fromString);
  });

  it("keeps several expressions under the chosen logical operator", () => {
    const cql = createTheCQLBasedOnExpression(
      [
        expression({ expression: "is", value: "a" }),
        expression({ id: "e2", attribute: "groundelev", expression: "is_at_least", value: 5 }),
      ],
      FIELDS,
      "or"
    ) as { op: string; args: unknown[] };

    expect(cql.op).toBe("or");
    expect(cql.args).toHaveLength(2);
    expect(parseCQLQueryToObject(cql).map((e) => e.expression)).toEqual(["is", "is_at_least"]);
  });
});
