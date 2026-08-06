import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import type { DatasetCollectionItems } from "@/lib/validations/layer";

import FeatureTable from "@/components/common/FeatureTable";
import { COLUMN_MENU_PAPER_SX } from "@/components/common/columnMenuStyles";

vi.mock("react-i18next", () => ({
  useTranslation: () => ({ t: (key: string) => key }),
}));

const FIELDS = [
  { name: "name", type: "string" },
  { name: "height", type: "number" },
];

const data = (properties: Record<string, unknown>[], ids?: number[]): DatasetCollectionItems =>
  ({
    features: properties.map((props, index) => ({ id: ids?.[index] ?? index, properties: props })),
    numberMatched: properties.length,
    numberReturned: properties.length,
  }) as unknown as DatasetCollectionItems;

describe("FeatureTable", () => {
  it("renders a header per non-object field and a cell per row", () => {
    render(<FeatureTable fields={FIELDS} data={data([{ name: "Alpha", height: 12 }])} />);

    expect(screen.getByText("name")).toBeInTheDocument();
    expect(screen.getByText("height")).toBeInTheDocument();
    expect(screen.getByText("Alpha")).toBeInTheDocument();
    expect(screen.getByText("12")).toBeInTheDocument();
  });

  it("prefers a header label override, then the label map, then the field name", () => {
    const { rerender } = render(
      <FeatureTable fields={FIELDS} data={data([{ name: "Alpha" }])} headerLabelMap={{ name: "Standort" }} />
    );
    expect(screen.getByText("Standort")).toBeInTheDocument();
    expect(screen.queryByText("name")).not.toBeInTheDocument();

    rerender(
      <FeatureTable
        fields={FIELDS}
        data={data([{ name: "Alpha" }])}
        headerLabelMap={{ name: "Standort" }}
        renderHeaderLabel={(fieldName, label) => <span>{`${fieldName}:${label}`}</span>}
      />
    );
    expect(screen.getByText("name:Standort")).toBeInTheDocument();
  });

  it("lets a caller take over cell rendering — the widget formats numbers its own way", () => {
    render(
      <FeatureTable
        fields={FIELDS}
        data={data([{ name: "Alpha", height: 1234 }])}
        formatCellValue={(fieldName, value) => (fieldName === "height" ? `${value} m` : String(value))}
      />
    );
    expect(screen.getByText("1234 m")).toBeInTheDocument();
  });

  it("keys rows uniquely when the caller repeats a feature id", () => {
    // A paged list that accumulates can hand the same feature over twice. Keying
    // on the id alone made React log "two children with the same key".
    const errors: string[] = [];
    const spy = vi.spyOn(console, "error").mockImplementation((...args) => {
      errors.push(args.map(String).join(" "));
    });

    const { container } = render(
      <FeatureTable
        fields={FIELDS}
        data={data([{ name: "Alpha" }, { name: "Beta" }, { name: "Gamma" }], [291865, 291865, 7])}
      />
    );
    spy.mockRestore();

    expect(errors.join("\n")).not.toMatch(/same key/i);
    expect(container.querySelectorAll("tbody tr")).toHaveLength(3);
  });

  it("renders nothing rather than 'null' for absent values", () => {
    render(<FeatureTable fields={FIELDS} data={data([{ name: null, height: undefined }])} />);
    expect(screen.queryByText("null")).not.toBeInTheDocument();
    expect(screen.queryByText("undefined")).not.toBeInTheDocument();
  });

  it("offers an expander only when the layer has an object field", () => {
    const { rerender } = render(<FeatureTable fields={FIELDS} data={data([{ name: "Alpha" }])} />);
    expect(screen.queryByLabelText("expand row")).not.toBeInTheDocument();

    rerender(
      <FeatureTable
        fields={[...FIELDS, { name: "details", type: "object" }]}
        data={data([{ name: "Alpha", details: { a: 1 } }])}
      />
    );
    const expander = screen.getByLabelText("expand row");
    expect(expander).toBeInTheDocument();
    // The object column is not a data column of its own.
    expect(screen.queryByText("details")).not.toBeInTheDocument();

    fireEvent.click(expander);
    expect(screen.getByText("details")).toBeInTheDocument();
  });

  it("shows the empty state, and a caller's message when given one", () => {
    const { rerender } = render(<FeatureTable fields={FIELDS} data={data([])} />);
    expect(screen.getByText("no_values_found")).toBeInTheDocument();

    rerender(<FeatureTable fields={FIELDS} data={data([])} emptyMessage={<span>Nothing matches</span>} />);
    expect(screen.getByText("Nothing matches")).toBeInTheDocument();
  });

  it("shows skeletons while loading and nothing at all without data", () => {
    const { container, rerender } = render(<FeatureTable fields={FIELDS} isLoading />);
    expect(container.querySelectorAll(".MuiSkeleton-root").length).toBeGreaterThan(0);

    rerender(<FeatureTable fields={FIELDS} />);
    expect(container.querySelector("table")).toBeNull();
  });

  it("only renders interaction affordances the caller opted into", () => {
    const { container, rerender } = render(<FeatureTable fields={FIELDS} data={data([{ name: "A" }])} />);
    expect(container.querySelector("[data-resize-handle='true']")).toBeNull();
    expect(container.querySelector(".col-sort-arrow")).toBeNull();
    expect(container.querySelector("th[draggable='true']")).toBeNull();

    rerender(
      <FeatureTable
        fields={FIELDS}
        data={data([{ name: "A" }])}
        onHeaderResizeStart={() => undefined}
        columnMenuItems={() => []}
        onReorderColumns={() => undefined}
        sortColumn="name"
        sortDirection="asc"
      />
    );
    expect(container.querySelector("[data-resize-handle='true']")).not.toBeNull();
    expect(container.querySelector("th[draggable='true']")).not.toBeNull();
  });

  it("marks only the sorted column, and only while something is sorted", () => {
    const { container, rerender } = render(
      <FeatureTable fields={FIELDS} data={data([{ name: "A" }])} columnMenuItems={() => []} />
    );
    // Sorting lives in the menu now, so an unsorted table shows no arrows at all.
    expect(container.querySelectorAll(".col-sort-arrow")).toHaveLength(0);

    rerender(
      <FeatureTable
        fields={FIELDS}
        data={data([{ name: "A" }])}
        columnMenuItems={() => []}
        sortColumn="name"
        sortDirection="asc"
      />
    );
    // One arrow, on the sorted column — not a faint one in every header.
    expect(container.querySelectorAll(".col-sort-arrow")).toHaveLength(1);
    const sortedHeader = [...container.querySelectorAll("th")].find((th) =>
      th.textContent?.includes("name")
    );
    expect(sortedHeader?.querySelector(".col-sort-arrow")).not.toBeNull();

    rerender(
      <FeatureTable
        fields={FIELDS}
        data={data([{ name: "A" }])}
        columnMenuItems={() => []}
        sortColumn="height"
        sortDirection="desc"
      />
    );
    const heightHeader = [...container.querySelectorAll("th")].find((th) =>
      th.textContent?.includes("height")
    );
    expect(heightHeader?.querySelector(".col-sort-arrow")).not.toBeNull();
    expect(container.querySelectorAll(".col-sort-arrow")).toHaveLength(1);
  });

  it("opens a column menu on header click and hands the host the header cell", () => {
    const onSelect = vi.fn();
    const columnMenuItems = vi.fn((fieldName: string) => [
      { key: "sort", label: `sort ${fieldName}`, onSelect },
    ]);

    render(
      <FeatureTable fields={FIELDS} data={data([{ name: "A" }])} columnMenuItems={columnMenuItems} />
    );

    fireEvent.click(screen.getByText("height"));
    expect(columnMenuItems).toHaveBeenCalledWith("height");

    fireEvent.click(screen.getByText("sort height"));
    // The host anchors its own popover to the cell the menu came from.
    expect(onSelect).toHaveBeenCalledTimes(1);
    expect(onSelect.mock.calls[0][0]).toBeInstanceOf(HTMLElement);
  });

  it("styles the column menu exactly as the map table's, via the shared constants", () => {
    render(
      <FeatureTable
        fields={FIELDS}
        data={data([{ name: "A" }])}
        columnMenuItems={() => [
          { key: "sort", label: "sort", onSelect: vi.fn() },
          { key: "filter", label: "filter", onSelect: vi.fn(), dividerBefore: true },
        ]}
      />
    );
    fireEvent.click(screen.getByText("height"));

    // Both menus read their look from COLUMN_MENU_PAPER_SX; asserting the
    // structure it targets keeps the two from drifting apart again.
    const paper = document.querySelector(".MuiMenu-paper") as HTMLElement;
    expect(paper.querySelectorAll(".MuiListItemText-root")).toHaveLength(2);
    expect(paper.querySelector("hr")).not.toBeNull();
    expect(COLUMN_MENU_PAPER_SX["& .MuiListItemText-root .MuiTypography-root"].fontSize).toBe("0.8rem");
    expect(COLUMN_MENU_PAPER_SX["& .MuiListItemIcon-root"].minWidth).toBe(28);
  });

  it("does not open the column menu when the click lands on the resize handle", () => {
    const columnMenuItems = vi.fn(() => [{ key: "sort", label: "sort", onSelect: vi.fn() }]);
    const { container } = render(
      <FeatureTable
        fields={FIELDS}
        data={data([{ name: "A" }])}
        columnMenuItems={columnMenuItems}
        onHeaderResizeStart={() => undefined}
      />
    );

    fireEvent.click(container.querySelector("[data-resize-handle='true']")!);
    expect(columnMenuItems).not.toHaveBeenCalled();
  });

  it("renders no menu at all when the host offers no column actions", () => {
    const { container } = render(<FeatureTable fields={FIELDS} data={data([{ name: "A" }])} />);
    fireEvent.click(screen.getByText("height"));
    expect(document.querySelector(".MuiMenu-paper")).toBeNull();
    expect(container.querySelector("th")?.getAttribute("draggable")).not.toBe("true");
  });
});
