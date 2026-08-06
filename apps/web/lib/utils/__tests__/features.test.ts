import { describe, expect, it } from "vitest";

import { appendUniqueFeatures } from "@/lib/utils/features";

const feature = (id: number) => ({ id, properties: { name: `f${id}` } });

describe("appendUniqueFeatures", () => {
  it("appends a genuinely new page", () => {
    const result = appendUniqueFeatures([feature(1), feature(2)], [feature(3), feature(4)]);
    expect(result.map((f) => f.id)).toEqual([1, 2, 3, 4]);
  });

  it("drops a page that is already accumulated", () => {
    // The cursor advances before SWR has the next payload, so the effect can
    // re-append the page it already holds.
    const previous = [feature(1), feature(2)];
    const result = appendUniqueFeatures(previous, [feature(1), feature(2)]);
    expect(result.map((f) => f.id)).toEqual([1, 2]);
  });

  it("keeps the new half of a partially overlapping page", () => {
    const result = appendUniqueFeatures([feature(1), feature(2)], [feature(2), feature(3)]);
    expect(result.map((f) => f.id)).toEqual([1, 2, 3]);
  });

  it("returns the same array when nothing is new, so React can skip the update", () => {
    const previous = [feature(1)];
    expect(appendUniqueFeatures(previous, [feature(1)])).toBe(previous);
  });

  it("handles empty inputs", () => {
    expect(appendUniqueFeatures([], [feature(1)]).map((f) => f.id)).toEqual([1]);
    const previous = [feature(1)];
    expect(appendUniqueFeatures(previous, [])).toBe(previous);
  });

  it("appends features that carry no id, having nothing to compare", () => {
    type Unidentified = { id?: number; properties: Record<string, unknown> };
    const previous: Unidentified[] = [{ properties: {} }, { properties: {} }];
    const result = appendUniqueFeatures(previous, [{ properties: {} }]);
    expect(result).toHaveLength(3);
  });
});
