import LayersIcon from "@mui/icons-material/Layers";
import { Box, Stack, Tab, Tabs, Typography } from "@mui/material";
import React, { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";

import { setSelectedLayers } from "@/lib/store/layer/slice";
import { setActiveRightPanel } from "@/lib/store/map/slice";
import type { ProjectLayer } from "@/lib/validations/project";

import { MapSidebarItemID } from "@/types/map/common";

import { useAppDispatch, useAppSelector } from "@/hooks/store/ContextHooks";

import Container from "@/components/map/panels/Container";
import Filter from "@/components/map/panels/filter/Filter";
import PropertiesPanel from "@/components/map/panels/properties/Properties";
import LayerStyle from "@/components/map/panels/style/LayerStyle";

interface LayerSettingsPanelProps {
  projectId: string;
  projectLayers?: ProjectLayer[];
}

// Helper function to get max tab index for layer type
const getMaxTabIndex = (layerType: string | undefined): number => {
  if (layerType === "raster" || layerType === "table") return 1; // 0, 1
  return 2; // 0, 1, 2
};

// Helper function to clamp tab value
const clampTabValue = (value: number, layerType: string | undefined): number => {
  const max = getMaxTabIndex(layerType);
  return Math.max(0, Math.min(value, max));
};

// 1. Helper function to map Redux ID to Tab Index
const getTabFromPanelId = (panelId: string | undefined, layerType: string | undefined): number => {
  if (layerType === "raster") {
    // Only Style (0) and Metadata (1)
    if (panelId === MapSidebarItemID.PROPERTIES) return 1;
    if (panelId === MapSidebarItemID.STYLE) return 0;
    return 0; // Default to Style for raster
  }
  if (layerType === "table") {
    // Only Filter (0) and Metadata (1)
    if (panelId === MapSidebarItemID.PROPERTIES) return 1;
    if (panelId === MapSidebarItemID.FILTER) return 0;
    return 0; // Default to Filter for table
  }
  // Default: vector (Style, Filter, Metadata)
  if (panelId === MapSidebarItemID.FILTER) return 1;
  if (panelId === MapSidebarItemID.PROPERTIES) return 2;
  if (panelId === MapSidebarItemID.STYLE) return 0;
  return 0; // Default to Style for vector
};

const LayerSettingsPanel = ({ projectId, projectLayers = [] }: LayerSettingsPanelProps) => {
  const { t } = useTranslation("common");
  const dispatch = useAppDispatch();

  const activeRightPanel = useAppSelector((state) => state.map.activeRightPanel);
  const selectedLayerIds = useAppSelector((state) => state.layers.selectedLayerIds || []);

  const activeLayer = useMemo(() => {
    if (selectedLayerIds.length === 1) {
      return projectLayers.find((l) => l.id === selectedLayerIds[0]);
    }
    return null;
  }, [selectedLayerIds, projectLayers]);

  const layerType = activeLayer?.type;

  const [activeTab, setActiveTab] = useState(() =>
    clampTabValue(getTabFromPanelId(activeRightPanel, layerType), layerType)
  );

  // 3. Keep syncing if Redux changes while panel is open
  useEffect(() => {
    const newTab = clampTabValue(getTabFromPanelId(activeRightPanel, layerType), layerType);
    setActiveTab(newTab);
  }, [activeRightPanel, layerType]);

  const handleClose = () => {
    dispatch(setSelectedLayers([]));
    dispatch(setActiveRightPanel(undefined));
  };

  // Manual Tab Click Logic
  const handleTabChange = (newValue: number) => {
    setActiveTab(newValue);
    if (layerType === "raster") {
      // 0: Style, 1: Metadata
      if (newValue === 0) dispatch(setActiveRightPanel(MapSidebarItemID.STYLE));
      if (newValue === 1) dispatch(setActiveRightPanel(MapSidebarItemID.PROPERTIES));
    } else if (layerType === "table") {
      // 0: Filter, 1: Metadata
      if (newValue === 0) dispatch(setActiveRightPanel(MapSidebarItemID.FILTER));
      if (newValue === 1) dispatch(setActiveRightPanel(MapSidebarItemID.PROPERTIES));
    } else {
      // vector: 0: Style, 1: Filter, 2: Metadata
      if (newValue === 0) dispatch(setActiveRightPanel(MapSidebarItemID.STYLE));
      if (newValue === 1) dispatch(setActiveRightPanel(MapSidebarItemID.FILTER));
      if (newValue === 2) dispatch(setActiveRightPanel(MapSidebarItemID.PROPERTIES));
    }
  };

  const renderContent = () => {
    // ... (Multi selection logic same as before)
    if (selectedLayerIds.length > 1) {
      return (
        <Stack
          alignItems="center"
          justifyContent="center"
          spacing={2}
          sx={{ height: "100%", p: 4, textAlign: "center", color: "text.secondary" }}>
          <LayersIcon sx={{ fontSize: 48, color: "action.active" }} />
          <Typography variant="h6">
            {selectedLayerIds.length} {t("layers_selected")}
          </Typography>
          <Typography variant="body2">
            {t("bulk_actions_description", { defaultValue: "Select a single layer to edit styles." })}
          </Typography>
        </Stack>
      );
    }

    // ... (Single selection logic)
    if (selectedLayerIds.length === 1 && activeLayer) {
      return (
        <Box sx={{ height: "100%", display: "flex", flexDirection: "column" }}>
          <Box sx={{ borderBottom: 1, borderColor: "divider" }}>
            <Tabs
              value={activeTab}
              onChange={(_, v) => handleTabChange(v)}
              variant="fullWidth"
              aria-label="Layer Settings Tabs">
              {layerType === "raster" && <Tab label={t("style")} />}
              {layerType === "table" && <Tab label={t("filter")} />}
              {layerType !== "raster" && layerType !== "table" && <Tab label={t("style")} />}
              {layerType !== "raster" && layerType !== "table" && <Tab label={t("filter")} />}
              <Tab label={t("metadata.title")} />
            </Tabs>
          </Box>
          <Box sx={{ flexGrow: 1, overflowY: "auto", p: 0 }}>
            {/* Raster: Style (0), Metadata (1) */}
            {layerType === "raster" && (
              <>
                <Box role="tabpanel" hidden={activeTab !== 0} sx={{ height: "100%" }}>
                  {activeTab === 0 && <LayerStyle projectId={projectId} />}
                </Box>
                <Box role="tabpanel" hidden={activeTab !== 1} sx={{ height: "100%" }}>
                  {activeTab === 1 && <PropertiesPanel activeLayer={activeLayer} />}
                </Box>
              </>
            )}
            {/* Table: Filter (0), Metadata (1) */}
            {layerType === "table" && (
              <>
                <Box role="tabpanel" hidden={activeTab !== 0} sx={{ height: "100%" }}>
                  {activeTab === 0 && <Filter activeLayer={activeLayer} projectId={projectId} />}
                </Box>
                <Box role="tabpanel" hidden={activeTab !== 1} sx={{ height: "100%" }}>
                  {activeTab === 1 && <PropertiesPanel activeLayer={activeLayer} />}
                </Box>
              </>
            )}
            {/* Vector: Style (0), Filter (1), Metadata (2) */}
            {layerType !== "raster" && layerType !== "table" && (
              <>
                <Box role="tabpanel" hidden={activeTab !== 0} sx={{ height: "100%" }}>
                  {activeTab === 0 && <LayerStyle projectId={projectId} />}
                </Box>
                <Box role="tabpanel" hidden={activeTab !== 1} sx={{ height: "100%" }}>
                  {activeTab === 1 && <Filter activeLayer={activeLayer} projectId={projectId} />}
                </Box>
                <Box role="tabpanel" hidden={activeTab !== 2} sx={{ height: "100%" }}>
                  {activeTab === 2 && <PropertiesPanel activeLayer={activeLayer} />}
                </Box>
              </>
            )}
          </Box>
        </Box>
      );
    }
    return null;
  };

  const title = activeLayer ? activeLayer.name : t("layer_settings");
  return (
    <Box sx={{ height: "100%" }}>
      <Container title={title} disablePadding={true} close={handleClose} body={renderContent()} />
    </Box>
  );
};
export default LayerSettingsPanel;
