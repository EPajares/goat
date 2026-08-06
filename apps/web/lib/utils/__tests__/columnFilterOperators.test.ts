import { describe, expect, it } from "vitest";

import {
  BLANK_VALUE,
  compileOperator,
  decompileOperator,
  draftFromExpression,
  draftToExpression,
  emptyDraft,
  filterColumnType,
  filterValueLabel,
  isDraftComplete,
  isQuickFilterOperator,
  operatorBody,
  quickFilterOperators,
  toggleDraftValue,
} from "@/lib/utils/columnFilterOperators";
import { FilterType, type Expression } from "@/lib/validations/filter";

const expression = (partial: Partial<Expression>): Expression => ({
  id: "e1",
  attribute: "status",
  expression: "is",
  value: "",
  type: FilterType.Logical,
  ...partial,
});

const newId = () => "generated";

describe("filterColumnType", () => {
  it("collapses field kinds to the four filter domains", () => {
    expect(filterColumnType({ kind: "datetime", type: "TIMESTAMP" })).toBe("date");
    expect(filterColumnType({ kind: "area", type: "number" })).toBe("number");
    expect(filterColumnType({ kind: "boolean" })).toBe("boolean");
    expect(filterColumnType({ kind: "formula", type: "string" })).toBe("string");
  });

  it("falls back to raw database types when no kind is declared", () => {
    expect(filterColumnType({ type: "BIGINT" })).toBe("number");
    expect(filterColumnType({ type: "DOUBLE" })).toBe("number");
    expect(filterColumnType({ type: "TIMESTAMP WITH TIME ZONE" })).toBe("date");
    expect(filterColumnType({ type: "BOOLEAN" })).toBe("boolean");
    expect(filterColumnType({ type: "VARCHAR" })).toBe("string");
    expect(filterColumnType({})).toBe("string");
  });
});

describe("operator vocabulary", () => {
  it("hides includes and excludes — they are what is / is not compile to", () => {
    for (const columnType of ["string", "number", "date", "boolean"] as const) {
      const values = quickFilterOperators(columnType).map((o) => o.value);
      expect(values).not.toContain("includes");
      expect(values).not.toContain("excludes");
    }
  });

  it("keeps the two empty-string operators out of the quick popover", () => {
    const values = quickFilterOperators("string").map((o) => o.value);
    expect(values).not.toContain("is_empty_string");
    expect(values).not.toContain("is_not_empty_string");
    expect(values).toContain("is_blank");
  });

  it("offers value lists for text and numbers but not dates or booleans", () => {
    expect(operatorBody("string", "is")).toBe("values");
    expect(operatorBody("number", "is")).toBe("values");
    expect(quickFilterOperators("date").map((o) => o.value)).not.toContain("is");
    expect(quickFilterOperators("boolean").map((o) => o.value)).not.toContain("is");
  });

  it("recognises a stored includes as an operator it owns", () => {
    expect(isQuickFilterOperator("string", "includes")).toBe(true);
    expect(isQuickFilterOperator("string", "excludes")).toBe(true);
    // Left to the Filter panel — the popover must not overwrite these.
    expect(isQuickFilterOperator("string", "is_empty_string")).toBe(false);
    expect(isQuickFilterOperator("string", "s_intersects")).toBe(false);
  });
});

describe("compile / decompile", () => {
  it("promotes is to includes only once a second value is ticked", () => {
    expect(compileOperator("is", 1)).toBe("is");
    expect(compileOperator("is", 2)).toBe("includes");
    expect(compileOperator("is_not", 1)).toBe("is_not");
    expect(compileOperator("is_not", 2)).toBe("excludes");
  });

  it("leaves other operators alone", () => {
    expect(compileOperator("contains_the_text", 3)).toBe("contains_the_text");
    expect(decompileOperator("contains_the_text")).toBe("contains_the_text");
  });

  it("maps a stored list operator back to the one the popover shows", () => {
    expect(decompileOperator("includes")).toBe("is");
    expect(decompileOperator("excludes")).toBe("is_not");
  });
});

describe("draftFromExpression", () => {
  it("pre-checks the values of a stored includes", () => {
    const draft = draftFromExpression(
      "string",
      expression({ expression: "includes", value: ["a", "b"] })
    );
    expect(draft.operator).toBe("is");
    expect(draft.values).toEqual(["a", "b"]);
    expect(draft.editingId).toBe("e1");
  });

  it("distinguishes excludes from includes", () => {
    const draft = draftFromExpression("string", expression({ expression: "excludes", value: ["a"] }));
    expect(draft.operator).toBe("is_not");
    expect(draft.values).toEqual(["a"]);
  });

  it("reads a single-value is back into the value list", () => {
    const draft = draftFromExpression("string", expression({ expression: "is", value: "a" }));
    expect(draft.values).toEqual(["a"]);
  });

  it("reads text, number and range operators", () => {
    expect(
      draftFromExpression("string", expression({ expression: "contains_the_text", value: "school" })).text
    ).toBe("school");
    expect(draftFromExpression("number", expression({ expression: "is_at_least", value: 5 })).first).toBe("5");

    const range = draftFromExpression("number", expression({ expression: "is_between", value: [5, 40] }));
    expect([range.first, range.second]).toEqual(["5", "40"]);
  });

  it("still reads the legacy numeric range string", () => {
    const draft = draftFromExpression("number", expression({ expression: "is_between", value: "35-45" }));
    expect([draft.first, draft.second]).toEqual(["35", "45"]);
  });

  it("reads a date range", () => {
    const draft = draftFromExpression(
      "date",
      expression({ expression: "is_between", value: ["2024-01-01", "2024-03-01"] })
    );
    expect([draft.first, draft.second]).toEqual(["2024-01-01", "2024-03-01"]);
  });
});

describe("toggleDraftValue", () => {
  it("adds and removes concrete values", () => {
    let draft = emptyDraft("string");
    draft = toggleDraftValue(draft, "a");
    draft = toggleDraftValue(draft, "b");
    expect(draft.values).toEqual(["a", "b"]);
    draft = toggleDraftValue(draft, "a");
    expect(draft.values).toEqual(["b"]);
  });

  it("keeps (empty) exclusive — one column's expressions are ANDed, so the mix can never match", () => {
    let draft = { ...emptyDraft("string"), values: ["a", "b"] };
    draft = toggleDraftValue(draft, BLANK_VALUE);
    expect(draft.values).toEqual([BLANK_VALUE]);

    draft = toggleDraftValue(draft, "c");
    expect(draft.values).toEqual(["c"]);
  });
});

describe("draftToExpression", () => {
  it("emits is for one value and includes for several", () => {
    const one = draftToExpression("string", "status", { ...emptyDraft("string"), values: ["a"] }, newId);
    expect(one).toMatchObject({ expression: "is", value: "a" });

    const many = draftToExpression(
      "string",
      "status",
      { ...emptyDraft("string"), values: ["a", "b"] },
      newId
    );
    expect(many).toMatchObject({ expression: "includes", value: ["a", "b"] });
  });

  it("turns the (empty) row into a blank check", () => {
    expect(
      draftToExpression("string", "status", { ...emptyDraft("string"), values: [BLANK_VALUE] }, newId)
    ).toMatchObject({ expression: "is_blank" });

    expect(
      draftToExpression(
        "string",
        "status",
        { ...emptyDraft("string"), operator: "is_not", values: [BLANK_VALUE] },
        newId
      )
    ).toMatchObject({ expression: "is_not_blank" });
  });

  it("emits numeric bounds as a pair, not a hyphenated string", () => {
    expect(
      draftToExpression(
        "number",
        "groundelev",
        { ...emptyDraft("number"), operator: "is_between", first: "5", second: "40" },
        newId
      )
    ).toMatchObject({ expression: "is_between", value: [5, 40] });
  });

  it("reuses the edited expression id so applying replaces instead of appending", () => {
    const draft = { ...emptyDraft("string"), values: ["a"], editingId: "cql-0" };
    expect(draftToExpression("string", "status", draft, newId).id).toBe("cql-0");
    expect(draftToExpression("string", "status", { ...draft, editingId: null }, newId).id).toBe("generated");
  });
});

describe("filterValueLabel", () => {
  it("shows a single value", () => {
    expect(filterValueLabel("string", { expression: "is", value: "open" })).toBe("open");
  });

  it("lists every ticked value, leaving truncation to the caller", () => {
    expect(filterValueLabel("string", { expression: "includes", value: ["open", "closed"] })).toBe(
      "open, closed"
    );
  });

  it("reads a range as a span", () => {
    expect(filterValueLabel("number", { expression: "is_between", value: [5, 40] })).toBe("5 – 40");
    expect(
      filterValueLabel("date", { expression: "is_between", value: ["2024-01-01", "2024-03-01"] })
    ).toBe("2024-01-01 – 2024-03-01");
  });

  it("says nothing for operators that carry no value", () => {
    // "status is empty" needs no value appended to read correctly.
    expect(filterValueLabel("string", { expression: "is_blank", value: "" })).toBe("");
    expect(filterValueLabel("boolean", { expression: "is_true", value: "" })).toBe("");
    expect(filterValueLabel("string", { expression: "is_not_blank", value: "" })).toBe("");
  });

  it("shows text, numbers and dates as given", () => {
    expect(filterValueLabel("string", { expression: "contains_the_text", value: "school" })).toBe("school");
    expect(filterValueLabel("number", { expression: "is_at_least", value: 5 })).toBe("5");
    expect(filterValueLabel("date", { expression: "is_before", value: "2024-01-01" })).toBe("2024-01-01");
    expect(filterValueLabel("date", { expression: "in_the_last", value: 30 })).toBe("30");
  });

  it("shows nothing rather than 'null' for a missing value", () => {
    expect(filterValueLabel("string", { expression: "is", value: null as unknown as string })).toBe("");
  });
});

describe("isDraftComplete", () => {
  it("requires whatever the operator's editor collects", () => {
    expect(isDraftComplete("string", emptyDraft("string"))).toBe(false);
    expect(isDraftComplete("string", { ...emptyDraft("string"), values: ["a"] })).toBe(true);

    const text = { ...emptyDraft("string"), operator: "contains_the_text" };
    expect(isDraftComplete("string", text)).toBe(false);
    expect(isDraftComplete("string", { ...text, text: "  " })).toBe(false);
    expect(isDraftComplete("string", { ...text, text: "school" })).toBe(true);

    const range = { ...emptyDraft("number"), operator: "is_between", first: "5" };
    expect(isDraftComplete("number", range)).toBe(false);
    expect(isDraftComplete("number", { ...range, second: "40" })).toBe(true);
  });

  it("treats value-free operators as ready immediately", () => {
    expect(isDraftComplete("boolean", { ...emptyDraft("boolean"), operator: "is_true" })).toBe(true);
    expect(isDraftComplete("string", { ...emptyDraft("string"), operator: "is_blank" })).toBe(true);
  });
});
