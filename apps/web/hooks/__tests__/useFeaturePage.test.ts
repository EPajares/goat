import { act, renderHook } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { GetCollectionItemsQueryParams } from "@/lib/validations/layer";

const collectionItemsCalls: Array<{ datasetId: string; params?: GetCollectionItemsQueryParams }> = [];

// SWR hands back a referentially stable `data` between renders; the mock has to
// as well, or the hook's "keep the last page visible" effect never settles.
const PAGE = { features: [], numberMatched: 640, numberReturned: 0 };

vi.mock("@/lib/api/layers", () => ({
  useDatasetCollectionItems: (datasetId: string, params?: GetCollectionItemsQueryParams) => {
    collectionItemsCalls.push({ datasetId, params });
    return { data: PAGE, isLoading: false };
  },
}));

vi.mock("@/hooks/map/CommonHooks", () => ({
  default: () => ({ layerFields: [{ name: "uid", type: "string" }], isLoading: false }),
}));

// vi.mock is hoisted above imports, so a static import already sees the mocks.
import { useFeaturePage } from "@/hooks/useFeaturePage";

/** Query params of the most recent fetch. */
const lastParams = () => collectionItemsCalls[collectionItemsCalls.length - 1].params;

const changeRowsPerPage = (value: number) =>
  ({ target: { value: String(value) } }) as unknown as React.ChangeEvent<HTMLInputElement>;

beforeEach(() => {
  collectionItemsCalls.length = 0;
});

describe("useFeaturePage", () => {
  it("requests the first page at the requested size", () => {
    renderHook(() => useFeaturePage("layer-1", { limit: 25 }));
    expect(lastParams()).toMatchObject({ limit: 25, offset: 0 });
    expect(collectionItemsCalls[0].datasetId).toBe("layer-1");
  });

  it("defaults to 50 rows when no limit is given", () => {
    renderHook(() => useFeaturePage("layer-1"));
    expect(lastParams()).toMatchObject({ limit: 50 });
  });

  it("passes a CQL filter through — the view-data modal narrows a layer's preview with it", () => {
    const filter = { op: "=", args: [{ property: "status" }, "open"] };
    renderHook(() => useFeaturePage("layer-1", { limit: 50, filter }));
    expect(lastParams()?.filter).toBe(JSON.stringify(filter));
  });

  it("omits the filter key entirely when there is no filter", () => {
    renderHook(() => useFeaturePage("layer-1", { limit: 50 }));
    expect(lastParams()).not.toHaveProperty("filter");
  });

  it("turns a page change into an offset", () => {
    const { result } = renderHook(() => useFeaturePage("layer-1", { limit: 25 }));
    act(() => result.current.onPageChange(null, 3));
    expect(lastParams()).toMatchObject({ limit: 25, offset: 75 });
    expect(result.current.page).toBe(3);
  });

  it("returns to the first page when the page size changes", () => {
    const { result } = renderHook(() => useFeaturePage("layer-1", { limit: 25 }));
    act(() => result.current.onPageChange(null, 3));
    act(() => result.current.onRowsPerPageChange(changeRowsPerPage(10)));
    expect(lastParams()).toMatchObject({ limit: 10, offset: 0 });
    expect(result.current.page).toBe(0);
    expect(result.current.rowsPerPage).toBe(10);
  });

  it("returns to the first page when the filter changes", () => {
    const first = { op: "=", args: [{ property: "status" }, "open"] };
    const second = { op: "=", args: [{ property: "status" }, "closed"] };
    const { result, rerender } = renderHook(
      ({ filter }) => useFeaturePage("layer-1", { limit: 25, filter }),
      { initialProps: { filter: first } }
    );

    act(() => result.current.onPageChange(null, 2));
    expect(lastParams()).toMatchObject({ offset: 50 });

    rerender({ filter: second });
    expect(lastParams()).toMatchObject({ offset: 0, filter: JSON.stringify(second) });
  });

  it("does not reset the page when an equivalent filter object is re-created", () => {
    // Callers rebuild the filter literal on render; only a real change should
    // send the reader back to page one.
    const { result, rerender } = renderHook(
      ({ filter }) => useFeaturePage("layer-1", { limit: 25, filter }),
      { initialProps: { filter: { op: "=", args: ["a"] } } }
    );
    act(() => result.current.onPageChange(null, 2));
    rerender({ filter: { op: "=", args: ["a"] } });
    expect(result.current.page).toBe(2);
    expect(lastParams()).toMatchObject({ offset: 50 });
  });

  it("exposes the total row count for the pagination label", () => {
    const { result } = renderHook(() => useFeaturePage("layer-1", { limit: 25 }));
    expect(result.current.totalCount).toBe(640);
  });

  it("passes the layer's fields through", () => {
    const { result } = renderHook(() => useFeaturePage("layer-1"));
    expect(result.current.fields).toEqual([{ name: "uid", type: "string" }]);
    expect(result.current.areFieldsLoading).toBe(false);
  });
});
