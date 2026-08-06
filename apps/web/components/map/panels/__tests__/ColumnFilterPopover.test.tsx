import { fireEvent, render, screen, within } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { FilterType, type Expression } from "@/lib/validations/filter";

import type { TableFilterController } from "@/types/map/tableFilter";

import ColumnFilterPopover from "@/components/map/panels/ColumnFilterPopover";

vi.mock("react-i18next", () => ({
  useTranslation: () => ({ t: (key: string) => key }),
}));

vi.mock("@/hooks/map/CommonHooks", () => ({
  default: () => ({ layerFields: [{ name: "status", type: "string" }], isLoading: false }),
}));

vi.mock("@/hooks/map/DatasetHooks", () => ({
  useDatasetValueSelectorMethods: () => ({
    data: {
      items: [
        { value: "open", count: 3675 },
        { value: "closed", count: 296 },
      ],
    },
    isLoading: false,
    searchText: "",
    setSearchText: vi.fn(),
    debouncedSetSearchText: vi.fn(),
  }),
}));

const controllerWith = (expressions: Expression[] = []): TableFilterController => ({
  expressions,
  logicalOperator: "and",
  upsert: vi.fn(),
  remove: vi.fn(),
  canEdit: true,
});

const renderPopover = (controller: TableFilterController) => {
  const anchor = document.createElement("th");
  document.body.appendChild(anchor);
  const onClose = vi.fn();
  render(
    <ColumnFilterPopover
      anchorEl={anchor}
      columnName="status"
      columnType="string"
      iconKind="string"
      layerId="layer-1"
      controller={controller}
      onClose={onClose}
    />
  );
  return { onClose };
};

const valueRow = (label: string) => screen.getByText(label).closest("li")!;

const button = (label: string) =>
  screen.getByText(label).closest("button") as HTMLButtonElement;

const checkboxOf = (label: string) => valueRow(label).querySelector("input") as HTMLInputElement;

describe("ColumnFilterPopover", () => {
  it("shows the column, its operator and the distinct values with counts", () => {
    renderPopover(controllerWith());

    expect(screen.getByText("status")).toBeInTheDocument();
    expect(screen.getByText("filter_expressions.is")).toBeInTheDocument();
    expect(screen.getByText("open")).toBeInTheDocument();
    expect(screen.getByText("3,675")).toBeInTheDocument();
    expect(screen.getByText("closed")).toBeInTheDocument();
    expect(screen.getByText("296")).toBeInTheDocument();
  });

  it("offers no select-all — ticking every value is the same as no filter", () => {
    renderPopover(controllerWith());
    expect(screen.queryByText("select_all")).not.toBeInTheDocument();
    expect(screen.queryByText(/select all/i)).not.toBeInTheDocument();
  });

  it("keeps Done disabled until something is chosen", () => {
    renderPopover(controllerWith());
    expect(button("done").disabled).toBe(true);

    fireEvent.click(valueRow("open"));
    expect(button("done").disabled).toBe(false);
  });

  it("compiles a single choice to is", () => {
    const controller = controllerWith();
    renderPopover(controller);

    fireEvent.click(valueRow("open"));
    fireEvent.click(screen.getByText("done"));
    expect(controller.upsert).toHaveBeenCalledWith(
      expect.objectContaining({ attribute: "status", expression: "is", value: "open" })
    );
  });

  it("compiles several choices to includes", () => {
    const controller = controllerWith();
    renderPopover(controller);

    fireEvent.click(valueRow("open"));
    fireEvent.click(valueRow("closed"));
    fireEvent.click(screen.getByText("done"));
    expect(controller.upsert).toHaveBeenCalledWith(
      expect.objectContaining({ expression: "includes", value: ["open", "closed"] })
    );
  });

  it("ignores a second Done — applying closes the popover", () => {
    const controller = controllerWith();
    renderPopover(controller);

    fireEvent.click(valueRow("open"));
    fireEvent.click(screen.getByText("done"));
    fireEvent.click(screen.getByText("done"));
    expect(controller.upsert).toHaveBeenCalledTimes(1);
  });

  it("reopens on the column's existing filter and can remove it", () => {
    const existing: Expression = {
      id: "cql-0",
      attribute: "status",
      expression: "includes",
      value: ["open", "closed"],
      type: FilterType.Logical,
    };
    const controller = controllerWith([existing]);
    renderPopover(controller);

    // Both values arrive pre-ticked.
    expect(checkboxOf("open").checked).toBe(true);
    expect(checkboxOf("closed").checked).toBe(true);

    fireEvent.click(screen.getByText("remove"));
    expect(controller.remove).toHaveBeenCalledWith("cql-0");
  });

  it("replaces the existing expression instead of adding a second", () => {
    const controller = controllerWith([
      {
        id: "cql-0",
        attribute: "status",
        expression: "is",
        value: "open",
        type: FilterType.Logical,
      },
    ]);
    renderPopover(controller);

    fireEvent.click(valueRow("closed"));
    fireEvent.click(screen.getByText("done"));
    expect(controller.upsert).toHaveBeenCalledWith(expect.objectContaining({ id: "cql-0" }));
  });

  it("offers no Remove when the column has no filter yet", () => {
    renderPopover(controllerWith());
    expect(screen.queryByText("remove")).not.toBeInTheDocument();
  });

  it("opens the operator list from the header, grouped by dividers", () => {
    renderPopover(controllerWith());
    fireEvent.click(button("filter_expressions.is"));

    const menu = document.querySelector(".MuiMenu-paper") as HTMLElement;
    expect(menu).not.toBeNull();

    // Text columns group as: value matching / text matching / no value needed.
    expect(menu.querySelectorAll("hr").length).toBe(2);
    expect(within(menu).getByText("filter_expressions.is_not")).toBeInTheDocument();
    expect(within(menu).getByText("filter_expressions.contains_the_text")).toBeInTheDocument();
    expect(within(menu).getByText("filter_expressions.is_blank")).toBeInTheDocument();
    // includes/excludes are implementation detail, never offered.
    expect(within(menu).queryByText("filter_expressions.includes")).not.toBeInTheDocument();
  });

  it("swaps the value editor when the operator needs a different one", () => {
    renderPopover(controllerWith());
    expect(screen.getByText("open")).toBeInTheDocument();

    fireEvent.click(button("filter_expressions.is"));
    const menu = document.querySelector(".MuiMenu-paper") as HTMLElement;
    fireEvent.click(within(menu).getByText("filter_expressions.contains_the_text"));

    // Value list gone, free-text input in its place.
    expect(screen.queryByText("open")).not.toBeInTheDocument();
    expect(screen.getByPlaceholderText("filter_expressions.enter_value")).toBeInTheDocument();
  });

  it("keeps ticked values when swapping is for is not", () => {
    renderPopover(controllerWith());
    fireEvent.click(valueRow("open"));

    fireEvent.click(button("filter_expressions.is"));
    const menu = document.querySelector(".MuiMenu-paper") as HTMLElement;
    fireEvent.click(within(menu).getByText("filter_expressions.is_not"));

    expect(checkboxOf("open").checked).toBe(true);
  });

  it("needs no value editor for an operator that takes no value", () => {
    renderPopover(controllerWith());
    fireEvent.click(button("filter_expressions.is"));
    const menu = document.querySelector(".MuiMenu-paper") as HTMLElement;
    fireEvent.click(within(menu).getByText("filter_expressions.is_blank"));

    expect(screen.getByText("operator_needs_no_value")).toBeInTheDocument();
    expect(button("done").disabled).toBe(false);
  });

  it("claims a fixed height for a value list, so loading values cannot shift it", () => {
    renderPopover(controllerWith());
    const paper = document.querySelector(".MuiPopover-paper") as HTMLElement;
    // Without this, the paper grows when the values arrive; an upward-opening
    // popover is bottom-anchored, so growing moves its top edge.
    expect(getComputedStyle(paper).height).not.toBe("");
    expect(getComputedStyle(paper).height).not.toBe("auto");
  });

  it("lets a short editor size itself — no 460px panel around one text field", () => {
    renderPopover(controllerWith());
    fireEvent.click(button("filter_expressions.is"));
    const menu = document.querySelector(".MuiMenu-paper") as HTMLElement;
    fireEvent.click(within(menu).getByText("filter_expressions.contains_the_text"));

    const paper = document.querySelector(".MuiPopover-paper") as HTMLElement;
    expect(["", "auto"]).toContain(getComputedStyle(paper).height);
  });

  it("rules off each section of the panel", () => {
    renderPopover(controllerWith());
    const popover = document.querySelector(".MuiPopover-paper") as HTMLElement;
    // Under the field + operator row, under the search field, above Cancel/Done.
    expect(popover.querySelectorAll("hr").length).toBe(3);
  });

  it("keeps every section on one gutter, so labels line up down the panel", () => {
    renderPopover(controllerWith());
    const popover = document.querySelector(".MuiPopover-paper") as HTMLElement;
    const gutters = [
      // field + operator row
      popover.querySelector("p")?.parentElement,
      // a value row
      valueRow("open"),
      // the actions row
      button("done").parentElement,
    ].map((element) => element && getComputedStyle(element).paddingLeft);

    expect(new Set(gutters.filter(Boolean)).size).toBe(1);
  });

  it("says so when the column carries filters it does not own", () => {
    const controller = controllerWith([
      { id: "cql-0", attribute: "status", expression: "is", value: "open", type: FilterType.Logical },
      {
        id: "cql-1",
        attribute: "status",
        expression: "is_empty_string",
        value: "",
        type: FilterType.Logical,
      },
    ]);
    renderPopover(controller);
    expect(screen.getByText("column_has_other_filters")).toBeInTheDocument();
  });
});
