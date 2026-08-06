import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import WidgetAggregateTable from "@/components/builder/widgets/data/WidgetAggregateTable";

vi.mock("react-i18next", () => ({
  useTranslation: () => ({ t: (key: string) => key }),
}));

/** Columns as Table.tsx builds them for grouped mode. */
const GROUPED_COLUMNS = [
  { key: "grouped_value", label: "display_status", align: "left" as const },
  { key: "metric_0", label: "COUNT", align: "right" as const },
];

/** Flat grouped rows, shaped like the aggregation-stats response is mapped. */
const FLAT_ROWS = [
  { grouped_value: "AVAILABLE", metric_0: 6745 },
  { grouped_value: "OCCUPIED", metric_0: 493 },
  { grouped_value: "-", metric_0: 12715 },
];

/**
 * Collapsible grouped rows: a parent carrying subtotals, the sub-header naming
 * the secondary column, then its children. The `_`-prefixed flags are how
 * Table.tsx marks them.
 */
const COLLAPSIBLE_ROWS = [
  { grouped_value: "Hamburg", _isParent: true, _isExpanded: true, _childCount: 2, metric_0: 30 },
  { grouped_value: "operator", _isSubHeader: true, metric_0: "COUNT" },
  { grouped_value: "Alpha", _isChild: true, metric_0: 18 },
  { grouped_value: "Beta", _isChild: true, metric_0: 12 },
  { grouped_value: "Bremen", _isParent: true, _isExpanded: false, _childCount: 1, metric_0: 7 },
];

const cellsOf = (row: HTMLElement) => [...row.querySelectorAll("td")].map((td) => td.textContent?.trim());
const bodyRows = (container: HTMLElement) =>
  [...container.querySelectorAll<HTMLElement>("tbody tr")];

describe("WidgetAggregateTable", () => {
  it("renders grouped columns and rows", () => {
    const { container } = render(
      <WidgetAggregateTable tableColumns={GROUPED_COLUMNS} tableRows={FLAT_ROWS} />
    );

    expect(screen.getByText("display_status")).toBeInTheDocument();
    expect(screen.getByText("COUNT")).toBeInTheDocument();
    expect(bodyRows(container)).toHaveLength(3);
    expect(cellsOf(bodyRows(container)[0])).toEqual(["AVAILABLE", "6745"]);
    // A null group arrives already mapped to "-" by the widget.
    expect(cellsOf(bodyRows(container)[2])).toEqual(["-", "12715"]);
  });

  it("right-aligns metric columns and left-aligns the group", () => {
    const { container } = render(
      <WidgetAggregateTable tableColumns={GROUPED_COLUMNS} tableRows={FLAT_ROWS} />
    );
    const headers = [...container.querySelectorAll("thead th")];
    expect(headers[0].getAttribute("class")).toContain("alignLeft");
    expect(headers[1].getAttribute("class")).toContain("alignRight");
  });

  it("renders a totals row after the data", () => {
    const { container } = render(
      <WidgetAggregateTable
        tableColumns={GROUPED_COLUMNS}
        tableRows={FLAT_ROWS}
        totalsRow={{ grouped_value: "total", metric_0: 19953 }}
      />
    );
    const rows = bodyRows(container);
    expect(rows).toHaveLength(4);
    expect(cellsOf(rows[3])).toEqual(["total", "19953"]);
  });

  it("hands the whole row to the cell formatter, which collapsible modes depend on", () => {
    // Table.tsx reads row._isParent / _isChild / _isSubHeader to draw the
    // expander arrow, the child indentation and the sub-header. Dropping the
    // third argument would silently flatten all of that.
    const formatCellValueForColumn = vi.fn(
      (_columnKey: string, value: unknown, _row?: Record<string, unknown>) => String(value ?? "")
    );
    render(
      <WidgetAggregateTable
        tableColumns={GROUPED_COLUMNS}
        tableRows={COLLAPSIBLE_ROWS}
        formatCellValueForColumn={formatCellValueForColumn}
      />
    );

    const parentCall = formatCellValueForColumn.mock.calls.find(
      (call) => call[0] === "grouped_value" && call[1] === "Hamburg"
    );
    expect(parentCall?.[2]).toMatchObject({ _isParent: true, _isExpanded: true, _childCount: 2 });

    const childCall = formatCellValueForColumn.mock.calls.find(
      (call) => call[0] === "grouped_value" && call[1] === "Alpha"
    );
    expect(childCall?.[2]).toMatchObject({ _isChild: true });

    const subHeaderCall = formatCellValueForColumn.mock.calls.find(
      (call) => call[0] === "grouped_value" && call[1] === "operator"
    );
    expect(subHeaderCall?.[2]).toMatchObject({ _isSubHeader: true });
  });

  it("reports a clicked row so a parent can be expanded", () => {
    const onRowClick = vi.fn();
    const { container } = render(
      <WidgetAggregateTable
        tableColumns={GROUPED_COLUMNS}
        tableRows={COLLAPSIBLE_ROWS}
        onRowClick={onRowClick}
      />
    );

    fireEvent.click(bodyRows(container)[0]);
    expect(onRowClick).toHaveBeenCalledWith(expect.objectContaining({ grouped_value: "Hamburg" }), 0);
  });

  it("lets the host style parent and sub-header rows differently", () => {
    const getRowSx = vi.fn((row: Record<string, unknown>) =>
      row._isParent || row._isSubHeader ? { backgroundColor: "action.hover" } : undefined
    );
    render(
      <WidgetAggregateTable
        tableColumns={GROUPED_COLUMNS}
        tableRows={COLLAPSIBLE_ROWS}
        getRowSx={getRowSx}
      />
    );
    expect(getRowSx).toHaveBeenCalledWith(expect.objectContaining({ _isParent: true }));
    expect(getRowSx).toHaveBeenCalledWith(expect.objectContaining({ _isSubHeader: true }));
  });

  it("respects the configured column order and labels", () => {
    const { container } = render(
      <WidgetAggregateTable
        tableColumns={[GROUPED_COLUMNS[1], GROUPED_COLUMNS[0]]}
        tableRows={FLAT_ROWS}
      />
    );
    const headers = [...container.querySelectorAll("thead th")].map((th) => th.textContent?.trim());
    expect(headers).toEqual(["COUNT", "display_status"]);
    expect(cellsOf(bodyRows(container)[0])).toEqual(["6745", "AVAILABLE"]);
  });

  it("shows the host's empty message when a query returns nothing", () => {
    render(
      <WidgetAggregateTable
        tableColumns={GROUPED_COLUMNS}
        tableRows={[]}
        emptyMessage={<span>no_data_for_current_filters</span>}
      />
    );
    expect(screen.getByText("no_data_for_current_filters")).toBeInTheDocument();
  });

  it("falls back to its own empty state with no message given", () => {
    render(<WidgetAggregateTable tableColumns={GROUPED_COLUMNS} tableRows={[]} />);
    expect(screen.getByText("no_values_found")).toBeInTheDocument();
  });

  it("renders dashes for absent cells rather than blanks", () => {
    const { container } = render(
      <WidgetAggregateTable tableColumns={GROUPED_COLUMNS} tableRows={[{ grouped_value: "Hamburg" }]} />
    );
    expect(cellsOf(bodyRows(container)[0])).toEqual(["Hamburg", "-"]);
  });

  it("only renders resize, reorder and sort affordances the host opted into", () => {
    const { container, rerender } = render(
      <WidgetAggregateTable tableColumns={GROUPED_COLUMNS} tableRows={FLAT_ROWS} />
    );
    expect(container.querySelector("[data-resize-handle='true']")).toBeNull();
    expect(container.querySelector("th[draggable='true']")).toBeNull();
    expect(container.querySelector(".col-sort-arrow")).toBeNull();

    rerender(
      <WidgetAggregateTable
        tableColumns={GROUPED_COLUMNS}
        tableRows={FLAT_ROWS}
        onHeaderResizeStart={() => undefined}
        onReorderColumns={() => undefined}
        onColumnSortClick={() => undefined}
        sortColumn="metric_0"
        sortDirection="desc"
      />
    );
    expect(container.querySelector("[data-resize-handle='true']")).not.toBeNull();
    expect(container.querySelector("th[draggable='true']")).not.toBeNull();
    expect(container.querySelector(".col-sort-arrow")).not.toBeNull();
  });

  it("sorts on a header click, but not when the resize handle is hit", () => {
    const onColumnSortClick = vi.fn();
    const { container } = render(
      <WidgetAggregateTable
        tableColumns={GROUPED_COLUMNS}
        tableRows={FLAT_ROWS}
        onColumnSortClick={onColumnSortClick}
        onHeaderResizeStart={() => undefined}
      />
    );

    fireEvent.click(screen.getByText("COUNT"));
    expect(onColumnSortClick).toHaveBeenCalledWith("metric_0");

    onColumnSortClick.mockClear();
    fireEvent.click(container.querySelector("[data-resize-handle='true']")!);
    expect(onColumnSortClick).not.toHaveBeenCalled();
  });
});
