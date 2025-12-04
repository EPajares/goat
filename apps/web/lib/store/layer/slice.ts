import { createSlice } from "@reduxjs/toolkit";
import type { PayloadAction } from "@reduxjs/toolkit";

import type { ProjectLayer, ProjectLayerGroup } from "@/lib/validations/project";

export interface LayerState {
  activeLayerId: number | null;
  selectedLayerIds: number[];
  projectLayers: ProjectLayer[];
  projectLayerGroups: ProjectLayerGroup[];
}

const initialState = {
  activeLayerId: -1,
  selectedLayerIds: [],
  projectLayers: [],
  projectLayerGroups: [],
} as LayerState;

const layerSlice = createSlice({
  name: "layer",
  initialState: initialState,
  reducers: {
    setActiveLayer: (state, action: PayloadAction<number | null>) => {
      if (action.payload === state.activeLayerId) {
        state.activeLayerId = null;
      } else {
        state.activeLayerId = action.payload;
      }
    },
    setSelectedLayers: (state, action: PayloadAction<number[]>) => {
      state.selectedLayerIds = action.payload;

      // Sync the primary active ID:
      // If exactly one item is selected, it becomes the "Active" layer.
      // If 0 or >1 items selected, activeLayerId is null (Properties panel handles bulk/empty state).
      if (action.payload.length === 1) {
        state.activeLayerId = action.payload[0];
      } else {
        state.activeLayerId = null;
      }
    },
    setProjectLayers: (state, action: PayloadAction<ProjectLayer[]>) => {
      state.projectLayers = action.payload;
    },
    updateProjectLayer: (state, action: PayloadAction<{ id: number; changes: Partial<ProjectLayer> }>) => {
      const { id, changes } = action.payload;
      state.projectLayers = state.projectLayers.map((layer) =>
        layer.id === id ? { ...layer, ...changes } : layer
      );
    },
    addProjectLayer: (state, action: PayloadAction<ProjectLayer>) => {
      state.projectLayers.push(action.payload);
    },
    removeProjectLayer: (state, action: PayloadAction<number>) => {
      state.projectLayers = state.projectLayers.filter((layer) => layer.id !== action.payload);
    },
    setProjectLayerGroups: (state, action: PayloadAction<ProjectLayerGroup[]>) => {
      state.projectLayerGroups = action.payload;
    },
    updateProjectLayerGroup: (
      state,
      action: PayloadAction<{ id: number; changes: Partial<ProjectLayerGroup> }>
    ) => {
      const { id, changes } = action.payload;
      state.projectLayerGroups = state.projectLayerGroups.map((group) =>
        group.id === id ? { ...group, ...changes } : group
      );
    },
    addProjectLayerGroup: (state, action: PayloadAction<ProjectLayerGroup>) => {
      state.projectLayerGroups.push(action.payload);
    },
    removeProjectLayerGroup: (state, action: PayloadAction<number>) => {
      state.projectLayerGroups = state.projectLayerGroups.filter((group) => group.id !== action.payload);
    },
  },
});

export const {
  setActiveLayer,
  setSelectedLayers,
  setProjectLayers,
  updateProjectLayer,
  addProjectLayer,
  removeProjectLayer,
  setProjectLayerGroups,
  updateProjectLayerGroup,
  addProjectLayerGroup,
  removeProjectLayerGroup,
} = layerSlice.actions;

export const layerReducer = layerSlice.reducer;
