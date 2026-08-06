import { describe, expect, it } from "vitest";

import { tableDataConfigSchema } from "@/lib/validations/widget";

const parse = (options: Record<string, unknown> = {}) =>
  tableDataConfigSchema.parse({ type: "table", setup: {}, options });

describe("table widget column actions", () => {
  it("allows sorting and filtering unless an author turns them off", () => {
    // Dashboards published before these options existed carry neither key, and
    // must keep behaving as they were published.
    const parsed = parse();
    expect(parsed.options.show_sort_action).toBe(true);
    expect(parsed.options.show_filter_action).toBe(true);
  });

  it("round-trips an author disabling each one", () => {
    expect(parse({ show_sort_action: false }).options.show_sort_action).toBe(false);
    expect(parse({ show_filter_action: false }).options.show_filter_action).toBe(false);

    const both = parse({ show_sort_action: false, show_filter_action: false }).options;
    expect([both.show_sort_action, both.show_filter_action]).toEqual([false, false]);
  });

  it("leaves the other layout options untouched", () => {
    const parsed = parse({ show_sort_action: false }).options;
    expect(parsed.sticky_header).toBe(true);
    expect(parsed.show_totals).toBe(true);
  });

  it("rejects a non-boolean rather than coercing it", () => {
    expect(() => parse({ show_sort_action: "no" })).toThrow();
  });
});
