import { createSlice } from "@reduxjs/toolkit";
import type { PayloadAction } from "@reduxjs/toolkit";
import type { MapGeoJSONFeature } from "react-map-gl/maplibre";

import { MAPTILER_KEY } from "@/lib/constants";
import type { BuilderPanelSchema, BuilderWidgetSchema, Project } from "@/lib/validations/project";
import type { Scenario } from "@/lib/validations/scenario";

import type { Basemap, SelectorItem } from "@/types/map/common";
import { MapSidebarItemID } from "@/types/map/common";
import type { MapPopoverEditorProps, MapPopoverInfoProps } from "@/types/map/popover";
import type { Result } from "@/types/map/controllers";

export type TemporaryFilter = {
  id: string; // unique identifier
  layer_id: number; // layer id
  filter: object;
  spatial_cross_filter?: object | undefined;
};

export type MapMode = "data" | "builder" | "public";

export interface MapState {
  project: Project | undefined;
  basemaps: Basemap[];
  activeBasemap: Basemap | undefined;
  maskLayer: string | undefined; // Toolbox mask layer
  toolboxStartingPoints: [number, number][] | undefined;
  activeLeftPanel: MapSidebarItemID | undefined;
  activeRightPanel: MapSidebarItemID | undefined;
  isMapGetInfoActive: boolean;
  mapCursor: string | undefined; // Toolbox features will override this. If undefined, the map will use the default cursor with pointer on hover
  editingScenario: Scenario | undefined;
  selectedScenarioLayer: SelectorItem | undefined;
  highlightedFeature: MapGeoJSONFeature | undefined;
  popupInfo: MapPopoverInfoProps | undefined;
  popupEditor: MapPopoverEditorProps | undefined;
  mapMode: MapMode;
  userLocation:
  | {
    active: boolean;
    position: GeolocationPosition | undefined;
  }
  | undefined;
  geocoderResult: Result | null;
  selectedBuilderItem: BuilderPanelSchema | BuilderWidgetSchema | undefined;
  currentZoom: number | undefined;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  temporaryFilters: TemporaryFilter[]; // Temporary filters for the map,
}

const initialState = {
  project: undefined,
  basemaps: [
    {
      value: "streets",
      url: `https://api.maptiler.com/maps/streets-v2/style.json?key=${MAPTILER_KEY}`,
      title: "High Fidelity",
      subtitle: "Great for public presentations",
      thumbnail: `https://cloud.maptiler.com/static/img/maps/streets-v2.png`,
    },
    {
      value: "satellite",
      url: `https://api.maptiler.com/maps/hybrid/style.json?key=${MAPTILER_KEY}`,
      title: "Satellite",
      subtitle: "As seen from space",
      thumbnail: "https://cloud.maptiler.com/static/img/maps/satellite.png",
    },
    {
      value: "light",
      url: `https://api.maptiler.com/maps/dataviz-light/style.json?key=${MAPTILER_KEY}`,
      title: "Light",
      subtitle: "For highlighting data overlays",
      thumbnail: "https://media.maptiler.com/old/img/cloud/slider/streets-v2-light.png",
    },
    {
      value: "dark",
      url: `https://api.maptiler.com/maps/dataviz-dark/style.json?key=${MAPTILER_KEY}`,
      title: "Dark",
      subtitle: "For highlighting data overlays",
      thumbnail: "https://media.maptiler.com/old/img/cloud/slider/streets-v2-dark.png",
    },
    {
      value: "basemap_de_col",
      url: `https://sgx.geodatenzentrum.de/gdz_basemapde_vektor/styles/bm_web_col.json`,
      title: "BKG Basemap",
      subtitle: "Colored",
      thumbnail: "https://basemap.de/viewer/assets/basemap_colour.png",
    },
    {
      value: "basemap_de_gry",
      url: `https://sgx.geodatenzentrum.de/gdz_basemapde_vektor/styles/bm_web_gry.json`,
      title: "BKG Basemap",
      subtitle: "Grayscale",
      thumbnail: "https://basemap.de/viewer/assets/basemap_greyscale.png",
    },
    {
      value: "basemap_de_top",
      url: `https://sgx.geodatenzentrum.de/gdz_basemapde_vektor/styles/bm_web_top.json`,
      title: "BKG Basemap",
      subtitle: "Topographic",
      thumbnail: "https://basemap.de/viewer/assets/basemap_hillshade.png",
    },
  ],
  maskLayer: undefined,
  activeBasemap: undefined,
  activeLeftPanel: MapSidebarItemID.LAYERS,
  toolboxStartingPoints: undefined,
  activeRightPanel: undefined,
  isMapGetInfoActive: true,
  mapCursor: undefined,
  editingScenario: undefined,
  selectedScenarioLayer: undefined,
  popupInfo: undefined,
  popupEditor: undefined,
  highlightedFeature: undefined,
  mapMode: "data",
  userLocation: undefined,
  geocoderResult: null,
  selectedBuilderItem: undefined,
  temporaryFilters: [] as TemporaryFilter[],
} as MapState;

const mapSlice = createSlice({
  name: "map",
  initialState: initialState,
  reducers: {
    setProject: (state, action: PayloadAction<Project | undefined>) => {
      state.project = action.payload;
    },
    updateProject: (state, action: PayloadAction<Project>) => {
      if (state.project) {
        state.project = { ...state.project, ...action.payload };
      }
    },
    setActiveBasemap: (state, action: PayloadAction<Basemap>) => {
      state.activeBasemap = action.payload;
    },
    setActiveLeftPanel: (state, action: PayloadAction<MapSidebarItemID | undefined>) => {
      state.activeLeftPanel = action.payload;
    },
    setActiveRightPanel: (state, action: PayloadAction<MapSidebarItemID | undefined>) => {
      if (state.activeRightPanel === MapSidebarItemID.TOOLBOX) {
        state.maskLayer = undefined;
        state.toolboxStartingPoints = undefined;
        state.mapCursor = undefined;
      }
      if (state.activeRightPanel === MapSidebarItemID.SCENARIO) {
        state.editingScenario = undefined;
        state.selectedScenarioLayer = undefined;
      }
      state.activeRightPanel = action.payload;
    },
    setMaskLayer: (state, action: PayloadAction<string | undefined>) => {
      state.maskLayer = action.payload;
    },
    setToolboxStartingPoints: (state, action: PayloadAction<[number, number][] | undefined>) => {
      if (state.toolboxStartingPoints === undefined) {
        state.toolboxStartingPoints = action.payload;
      } else {
        if (action.payload === undefined) {
          state.toolboxStartingPoints = undefined;
        } else {
          state.toolboxStartingPoints = [...state.toolboxStartingPoints, ...action.payload];
        }
      }
    },
    setIsMapGetInfoActive: (state, action: PayloadAction<boolean>) => {
      state.isMapGetInfoActive = action.payload;
      if (action.payload === false) {
        state.popupInfo = undefined;
        state.highlightedFeature = undefined;
      }
    },
    setMapCursor: (state, action: PayloadAction<string | undefined>) => {
      state.mapCursor = action.payload;
    },
    setEditingScenario: (state, action: PayloadAction<Scenario | undefined>) => {
      state.editingScenario = action.payload;
      if (action.payload === undefined) {
        state.selectedScenarioLayer = undefined;
      }
    },
    setSelectedScenarioLayer: (state, action: PayloadAction<SelectorItem | undefined>) => {
      state.selectedScenarioLayer = action.payload;
    },
    setPopupInfo: (state, action: PayloadAction<MapPopoverInfoProps | undefined>) => {
      state.popupInfo = action.payload;
    },
    setPopupEditor: (state, action) => {
      state.popupEditor = action.payload;
    },
    setHighlightedFeature: (state, action) => {
      state.highlightedFeature = action.payload;
    },
    setMapMode: (state, action: PayloadAction<MapMode>) => {
      state.mapMode = action.payload;
      if (action.payload === "data") {
        state.selectedBuilderItem = undefined;
      }
    },
    setUserLocation: (state, action: PayloadAction<MapState["userLocation"]>) => {
      state.userLocation = action.payload;
    },
    setGeocoderResult: (state, action: PayloadAction<MapState["geocoderResult"]>) => {
      state.geocoderResult = action.payload;
    },
    setSelectedBuilderItem: (state, action: PayloadAction<MapState["selectedBuilderItem"]>) => {
      state.selectedBuilderItem = action.payload;
    },
    setCurrentZoom: (state, action: PayloadAction<number | undefined>) => {
      state.currentZoom = action.payload;
    },
    // Temporary filters for the map
    addTemporaryFilter: (state, action: PayloadAction<TemporaryFilter>) => {
      state.temporaryFilters.push(action.payload);
    },
    updateTemporaryFilter: (state, action: PayloadAction<TemporaryFilter>) => {
      const index = state.temporaryFilters.findIndex((f) => f.id === action.payload.id);
      if (index !== -1) {
        state.temporaryFilters[index] = action.payload;
      }
    },
    removeTemporaryFilter: (state, action: PayloadAction<string>) => {
      state.temporaryFilters = state.temporaryFilters.filter((f) => f.id !== action.payload);
    },
  },
});

export const {
  setProject,
  updateProject,
  setActiveBasemap,
  setActiveLeftPanel,
  setActiveRightPanel,
  setMaskLayer,
  setToolboxStartingPoints,
  setIsMapGetInfoActive,
  setMapCursor,
  setEditingScenario,
  setSelectedScenarioLayer,
  setPopupInfo,
  setPopupEditor,
  setHighlightedFeature,
  setMapMode,
  setUserLocation,
  setGeocoderResult,
  setSelectedBuilderItem,
  setCurrentZoom,
  addTemporaryFilter,
  updateTemporaryFilter,
  removeTemporaryFilter,
} = mapSlice.actions;

export const mapReducer = mapSlice.reducer;
