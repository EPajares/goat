import { describe, expect, it } from "vitest";

import { DEFAULT_ROWS_PER_PAGE_OPTIONS, offsetToPage } from "@/lib/utils/pagination";

describe("offsetToPage", () => {
  it("derives the page from offset and limit", () => {
    expect(offsetToPage(0, 25)).toBe(0);
    expect(offsetToPage(25, 25)).toBe(1);
    expect(offsetToPage(100, 50)).toBe(2);
  });

  it("treats a missing offset as the first page", () => {
    // The old call sites used `offset ? offset / limit : 0`, so offset 0 and
    // undefined both had to mean page 0.
    expect(offsetToPage(undefined, 25)).toBe(0);
  });

  it("floors a partial page instead of returning a fraction", () => {
    // One call site divided without flooring, which handed TablePagination a
    // non-integer page after a rows-per-page change.
    expect(offsetToPage(30, 25)).toBe(1);
    expect(offsetToPage(49, 25)).toBe(1);
  });

  it("does not divide by zero", () => {
    expect(offsetToPage(10, 0)).toBe(0);
  });
});

describe("DEFAULT_ROWS_PER_PAGE_OPTIONS", () => {
  it("matches what the feature views offered before", () => {
    expect(DEFAULT_ROWS_PER_PAGE_OPTIONS).toEqual([10, 25, 50]);
  });
});
