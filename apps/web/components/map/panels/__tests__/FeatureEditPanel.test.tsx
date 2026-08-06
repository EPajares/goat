/**
 * Regression tests for the boolean value dropdown in the feature attribute
 * panel: the first selection must take effect immediately (single click),
 * including when the undo-snapshot capture (drawControl.getAll) misbehaves.
 */
import { configureStore } from "@reduxjs/toolkit";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import React from "react";
import { Provider } from "react-redux";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { featureEditorReducer } from "@/lib/store/featureEditor/slice";

const mockUseDraw = vi.fn();
vi.mock("@/lib/providers/DrawProvider", () => ({
  useDraw: () => mockUseDraw(),
}));

vi.mock("@/hooks/map/CommonHooks", () => ({
  default: () => ({
    layerFields: [
      { name: "flag", type: "boolean", kind: "boolean", is_computed: false, display_config: {} },
    ],
    isLoading: false,
    isError: false,
  }),
}));

vi.mock("react-i18next", () => ({
  useTranslation: () => ({ t: (k: string) => k }),
}));

import FeatureEditPanel from "@/components/map/panels/FeatureEditPanel";

const makeStore = () =>
  configureStore({
    reducer: { featureEditor: featureEditorReducer },
    preloadedState: {
      featureEditor: {
        activeLayerId: "layer-1",
        geometryType: "point",
        mode: "select" as const,
        activeFeatureId: "feat-1",
        isSaving: false,
        undoStack: [],
        redoStack: [],
        pendingFeatures: {
          "feat-1": {
            id: "feat-1",
            drawFeatureId: null,
            geometry: { type: "Point" as const, coordinates: [0, 0] },
            properties: {},
            committed: false,
            action: "update" as const,
            originalGeometry: { type: "Point" as const, coordinates: [0, 0] },
            originalProperties: {},
          },
        },
      },
    },
  });

const selectOption = async (user: ReturnType<typeof userEvent.setup>, label: string) => {
  // MUI Select renders as a combobox button; open it and click the option
  const combo = screen.getByRole("combobox");
  await user.click(combo);
  const listbox = await screen.findByRole("listbox");
  await user.click(within(listbox).getByText(label));
};

const selectTrue = (user: ReturnType<typeof userEvent.setup>) => selectOption(user, "True");

describe("FeatureEditPanel boolean field", () => {
  beforeEach(() => {
    mockUseDraw.mockReset();
  });

  it("stores true on the FIRST selection (drawControl present)", async () => {
    mockUseDraw.mockReturnValue({
      drawControl: { getAll: () => ({ type: "FeatureCollection", features: [] }) },
    });
    const store = makeStore();
    const user = userEvent.setup();
    render(
      <Provider store={store}>
        <FeatureEditPanel />
      </Provider>
    );

    await selectTrue(user);

    expect(store.getState().featureEditor.pendingFeatures["feat-1"].properties.flag).toBe(true);
  });

  it("CHANGING an already-set value takes effect on the first selection", async () => {
    mockUseDraw.mockReturnValue({
      drawControl: { getAll: () => ({ type: "FeatureCollection", features: [] }) },
    });
    const store = makeStore();
    const user = userEvent.setup();
    render(
      <Provider store={store}>
        <FeatureEditPanel />
      </Provider>
    );

    await selectOption(user, "True");
    expect(store.getState().featureEditor.pendingFeatures["feat-1"].properties.flag).toBe(true);

    await selectOption(user, "False");
    expect(store.getState().featureEditor.pendingFeatures["feat-1"].properties.flag).toBe(false);

    await selectOption(user, "—");
    expect(store.getState().featureEditor.pendingFeatures["feat-1"].properties.flag).toBeNull();
  });

  it("stores true on the FIRST selection even when the snapshot capture throws", async () => {
    mockUseDraw.mockReturnValue({
      drawControl: {
        getAll: () => {
          throw new Error("draw control not added to map");
        },
      },
    });
    const store = makeStore();
    const user = userEvent.setup();
    render(
      <Provider store={store}>
        <FeatureEditPanel />
      </Provider>
    );

    await selectTrue(user);

    expect(store.getState().featureEditor.pendingFeatures["feat-1"].properties.flag).toBe(true);
  });
});
