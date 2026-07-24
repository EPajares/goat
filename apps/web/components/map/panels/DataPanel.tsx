import { Box, useTheme } from "@mui/material";
import React, { useCallback, useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";

import { stopEditing } from "@/lib/store/featureEditor/slice";
import { setDataPanelHeight, setDataPanelLayerId, setIsDataPanelOpen } from "@/lib/store/map/slice";
import type { ProjectLayer } from "@/lib/validations/project";

import { useAppDispatch, useAppSelector } from "@/hooks/store/ContextHooks";

import ConfirmModal from "@/components/modals/Confirm";
import DatasetDownloadModal from "@/components/modals/DatasetDownload";
import EditableDataTable from "@/components/map/panels/EditableDataTable";

const MIN_PANEL_HEIGHT = 150;
const DEFAULT_PANEL_HEIGHT = 350;
const MAX_PANEL_HEIGHT_RATIO = 0.8; // Max 80% of container
const RESIZE_HANDLE_HEIGHT = 12;

/** CSS custom property name used to communicate panel height to sibling layout components */
export const DATA_PANEL_HEIGHT_VAR = "--data-panel-height";

interface DataPanelProps {
  projectLayers: ProjectLayer[];
  isEditor?: boolean;
}

const DataPanel: React.FC<DataPanelProps> = ({ projectLayers, isEditor = true }) => {
  const theme = useTheme();
  const dispatch = useAppDispatch();
  const [isDragging, setIsDragging] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);
  const dragStartRef = useRef<{ y: number; height: number } | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const heightRef = useRef(DEFAULT_PANEL_HEIGHT);

  const [isDownloadOpen, setIsDownloadOpen] = useState(false);
  const isDataPanelOpen = useAppSelector((state) => state.map.isDataPanelOpen);
  const dataPanelLayerId = useAppSelector((state) => state.map.dataPanelLayerId);
  const mapMode = useAppSelector((state) => state.map.mapMode);

  // Find the data panel's project layer (independent of layer tree selection)
  const activeProjectLayer = dataPanelLayerId
    ? projectLayers.find((l) => l.id === dataPanelLayerId)
    : undefined;

  // An edit session is bound to ONE layer. If the panel switches to a
  // different layer, the floating edit toolbar and the table would silently
  // target different layers — end the session instead (with a confirmation
  // when unsaved edits would be discarded).
  const { t } = useTranslation("common");
  const editingLayerId = useAppSelector((state) => state.featureEditor.activeLayerId);
  const hasPendingEdits = useAppSelector(
    (state) => Object.keys(state.featureEditor.pendingFeatures).length > 0
  );
  const [layerSwitchConfirmOpen, setLayerSwitchConfirmOpen] = useState(false);
  useEffect(() => {
    if (!editingLayerId || !activeProjectLayer) return;
    if (activeProjectLayer.layer_id === editingLayerId) {
      setLayerSwitchConfirmOpen(false);
      return;
    }
    if (hasPendingEdits) {
      setLayerSwitchConfirmOpen(true);
    } else {
      dispatch(stopEditing());
    }
  }, [activeProjectLayer, editingLayerId, hasPendingEdits, dispatch]);

  const handleLayerSwitchConfirm = useCallback(() => {
    dispatch(stopEditing());
    setLayerSwitchConfirmOpen(false);
  }, [dispatch]);

  const handleLayerSwitchCancel = useCallback(() => {
    // Return the panel to the layer being edited; if that layer is no longer
    // in the project, the session has nothing to return to — end it.
    const editingProjectLayer = projectLayers.find((l) => l.layer_id === editingLayerId);
    if (editingProjectLayer) {
      dispatch(setDataPanelLayerId(editingProjectLayer.id));
    } else {
      dispatch(stopEditing());
    }
    setLayerSwitchConfirmOpen(false);
  }, [projectLayers, editingLayerId, dispatch]);

  // Single source of truth: set the CSS variable on :root.
  // Both the panel itself and sibling layout components read from this variable.
  const syncHeight = useCallback((height: number) => {
    heightRef.current = height;
    document.documentElement.style.setProperty(DATA_PANEL_HEIGHT_VAR, `${height}px`);
  }, []);

  // Document-level drag handlers — only touch the CSS variable, no React state
  const handleDragMove = useCallback(
    (event: MouseEvent) => {
      if (!dragStartRef.current) return;
      const parentHeight = containerRef.current?.parentElement?.clientHeight ?? 800;
      const maxHeight = parentHeight * MAX_PANEL_HEIGHT_RATIO;
      const deltaY = dragStartRef.current.y - event.clientY;
      const newHeight = Math.min(maxHeight, Math.max(MIN_PANEL_HEIGHT, dragStartRef.current.height + deltaY));
      syncHeight(newHeight);
    },
    [syncHeight]
  );

  const handleDragEnd = useCallback(() => {
    setIsDragging(false);
    dragStartRef.current = null;
    dispatch(setDataPanelHeight(heightRef.current));
  }, [dispatch]);

  useEffect(() => {
    if (isDragging) {
      document.body.style.userSelect = "none";
      document.body.style.cursor = "ns-resize";
      window.addEventListener("mousemove", handleDragMove);
      window.addEventListener("mouseup", handleDragEnd);
      return () => {
        document.body.style.userSelect = "";
        document.body.style.cursor = "";
        window.removeEventListener("mousemove", handleDragMove);
        window.removeEventListener("mouseup", handleDragEnd);
      };
    }
  }, [isDragging, handleDragMove, handleDragEnd]);

  // Sync CSS var when panel visibility changes
  const isVisible = mapMode === "data" && isDataPanelOpen && !!activeProjectLayer;
  useEffect(() => {
    if (isVisible) {
      syncHeight(heightRef.current);
      dispatch(setDataPanelHeight(heightRef.current));
    } else {
      document.documentElement.style.setProperty(DATA_PANEL_HEIGHT_VAR, "0px");
    }
  }, [isVisible, syncHeight, dispatch]);

  // Also clean up on unmount
  useEffect(() => {
    return () => {
      document.documentElement.style.setProperty(DATA_PANEL_HEIGHT_VAR, "0px");
    };
  }, []);

  // Only render in data mode when panel is open with an active layer
  if (mapMode !== "data" || !isDataPanelOpen || !activeProjectLayer) {
    return null;
  }

  const handleDragStart = (event: React.MouseEvent) => {
    if (isExpanded) return; // No drag resize when expanded
    event.preventDefault();
    setIsDragging(true);
    dragStartRef.current = { y: event.clientY, height: heightRef.current };
  };

  const handleClose = () => {
    setIsExpanded(false);
    dispatch(setIsDataPanelOpen(false));
    // Reset CSS var to 0 but keep heightRef at the stored height so reopening works
    document.documentElement.style.setProperty(DATA_PANEL_HEIGHT_VAR, "0px");
  };

  const handleToggleExpand = () => {
    if (isExpanded) {
      // Collapse back to previous height — restore CSS var so overlays adjust
      setIsExpanded(false);
      syncHeight(heightRef.current);
    } else {
      // Expand to fill container — keep CSS var at current height so overlays stay in place
      setIsExpanded(true);
    }
  };

  return (
    <Box
      ref={containerRef}
      sx={{
        position: isExpanded ? "fixed" : "absolute",
        bottom: 0,
        left: 0,
        right: 0,
        ...(isExpanded ? { top: 0 } : {}),
        height: isExpanded ? "100vh" : `var(${DATA_PANEL_HEIGHT_VAR}, ${DEFAULT_PANEL_HEIGHT}px)`,
        display: "flex",
        flexDirection: "column",
        zIndex: isExpanded ? 1300 : 10,
        transition: isDragging ? "none" : "height 0.15s ease-out",
        pointerEvents: "auto",
      }}>
      {/* Resize handle — full width top edge (hidden when expanded) */}
      {!isExpanded && (
        <Box
          onMouseDown={handleDragStart}
          sx={{
            position: "absolute",
            top: -2,
            left: 0,
            right: 0,
            height: RESIZE_HANDLE_HEIGHT,
            cursor: "ns-resize",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 1,
            borderTop: isDragging ? `4px solid ${theme.palette.primary.main}` : "2px solid transparent",
            "&:hover .drag-pill": {
              backgroundColor: theme.palette.text.secondary,
            },
          }}>
          {/* Visual drag indicator pill */}
          <Box
            className="drag-pill"
            sx={{
              width: 32,
              height: 4,
              borderRadius: 2,
              backgroundColor: isDragging
                ? theme.palette.primary.main
                : theme.palette.action.disabled,
              transition: "background-color 0.15s ease",
            }}
          />
        </Box>
      )}

      {/* Table content — includes its own toolbar/header */}
      <Box
        sx={{
          flex: 1,
          minHeight: 0,
          overflow: "hidden",
          display: "flex",
          flexDirection: "column",
          backgroundColor: theme.palette.background.paper,
          transition: "background-color 0.15s ease-out",
        }}>
        <EditableDataTable
          layerId={activeProjectLayer.layer_id}
          projectLayer={activeProjectLayer}
          layerName={activeProjectLayer.name}
          isExpanded={isExpanded}
          isEditor={isEditor}
          onToggleExpand={handleToggleExpand}
          onClose={handleClose}
          onDownload={() => setIsDownloadOpen(true)}
        />
        <DatasetDownloadModal
          open={isDownloadOpen}
          onClose={() => setIsDownloadOpen(false)}
          dataset={activeProjectLayer}
        />
        <ConfirmModal
          open={layerSwitchConfirmOpen}
          title={t("stop_editing")}
          body={t("discard_edits_confirmation")}
          closeText={t("cancel")}
          confirmText={t("stop_editing")}
          onClose={handleLayerSwitchCancel}
          onConfirm={handleLayerSwitchConfirm}
        />
      </Box>
    </Box>
  );
};

export default DataPanel;
