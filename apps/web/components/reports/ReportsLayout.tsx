"use client";

import type { DragEndEvent, DragStartEvent, UniqueIdentifier } from "@dnd-kit/core";
import { DndContext, DragOverlay, pointerWithin } from "@dnd-kit/core";
import { Box, Card, CardHeader, Stack, Typography, useTheme } from "@mui/material";
import React, { useCallback, useState } from "react";
import { useTranslation } from "react-i18next";
import { v4 as uuidv4 } from "uuid";

import { Icon } from "@p4b/ui/components/Icon";

import { useProjectInitialViewState } from "@/lib/api/projects";
import { updateReportLayout } from "@/lib/api/reportLayouts";
import type { Project, ProjectLayer } from "@/lib/validations/project";
import type {
  ReportElement,
  ReportElementType,
  ReportLayout,
  ReportLayoutConfig,
} from "@/lib/validations/reportLayout";

import ReportsCanvas from "./canvas/ReportsCanvas";
import { reportElementIconMap } from "./elements/ReportElementIconMap";
import ReportsConfigPanel from "./panels/ReportsConfigPanel";
import ReportsElementsPanel from "./panels/ReportsElementsPanel";

export interface ReportsLayoutProps {
  project?: Project;
  projectLayers?: ProjectLayer[];
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  onProjectUpdate?: (key: string, value: any, refresh?: boolean) => void;
}

// Dragging element preview (shown during drag)
interface DragPreviewProps {
  elementType: ReportElementType;
}

const DragPreview: React.FC<DragPreviewProps> = ({ elementType }) => {
  const { t } = useTranslation("common");
  const theme = useTheme();
  return (
    <Card
      sx={{
        cursor: "grabbing",
        maxWidth: "130px",
        borderRadius: "6px",
        opacity: 0.9,
        transform: "scale(1.05)",
        boxShadow: theme.shadows[8],
      }}>
      <CardHeader
        sx={{
          px: 2,
          py: 4,
          ".MuiCardHeader-content": {
            width: "100%",
            color: theme.palette.primary.main,
          },
        }}
        title={
          <Stack
            direction="row"
            alignItems="center"
            justifyContent="space-between"
            spacing={2}
            style={{
              color: theme.palette.primary.main,
            }}>
            <Typography variant="body2" fontWeight="bold" noWrap color="inherit">
              {t(elementType)}
            </Typography>
            <Icon
              iconName={reportElementIconMap[elementType]}
              style={{
                fontSize: "1.2rem",
                color: "inherit",
              }}
            />
          </Stack>
        }
      />
    </Card>
  );
};

const ReportsLayout: React.FC<ReportsLayoutProps> = ({
  project,
  projectLayers = [],
  onProjectUpdate: _onProjectUpdate,
}) => {
  // Shared state for the selected report layout
  const [selectedReport, setSelectedReport] = useState<ReportLayout | null>(null);
  const [selectedElementId, setSelectedElementId] = useState<string | null>(null);
  const [activeId, setActiveId] = useState<UniqueIdentifier | null>(null);
  const [activeElementType, setActiveElementType] = useState<ReportElementType | null>(null);

  // Get project's initial view state for creating map element snapshots
  const { initialView } = useProjectInitialViewState(project?.id ?? "");

  // Handle drag start
  const handleDragStart = useCallback((event: DragStartEvent) => {
    const { active } = event;
    setActiveId(active.id);

    // Get the element type from the dragged item
    const data = active.data.current;
    if (data?.type === "report-element" && data?.elementType) {
      setActiveElementType(data.elementType as ReportElementType);
    }
  }, []);

  // Handle drag end
  const handleDragEnd = useCallback(
    async (event: DragEndEvent) => {
      const { active, over } = event;

      setActiveId(null);
      setActiveElementType(null);

      // If dropped over the canvas and we have a valid element type
      if (over?.id === "report-canvas" && selectedReport) {
        const data = active.data.current;
        if (data?.type === "report-element" && data?.elementType) {
          const elementType = data.elementType as ReportElementType;

          // Get the canvas/paper element to calculate relative position
          const paperElement = document.querySelector('[data-paper="true"]');
          const paperRect = paperElement?.getBoundingClientRect();

          // Default sizes based on element type (in mm)
          const defaultWidth = elementType === "map" ? 180 : elementType === "legend" ? 40 : 60;
          const defaultHeight = elementType === "map" ? 120 : elementType === "legend" ? 80 : 30;

          // Calculate stacking offset based on existing elements (so new elements don't overlap perfectly)
          const existingCount = selectedReport.config.elements?.length ?? 0;
          const stackOffset = existingCount * 5; // 5mm offset per existing element

          // Calculate position - center the element at 20% from top-left as default
          // This gives a better initial placement
          let posX = 20 + stackOffset; // mm from left
          let posY = 20 + stackOffset; // mm from top

          // If we have paper rect and the event has coordinates, try to calculate relative position
          if (paperRect && over.rect) {
            // Get the drop point relative to the paper
            // Use the center of the droppable rect as reference
            const dropX = over.rect.left + over.rect.width / 2 - paperRect.left;
            const dropY = over.rect.top + over.rect.height / 2 - paperRect.top;

            // Get zoom level from the paper's data attribute or calculate from width
            const zoomAttr = paperElement?.getAttribute("data-zoom");
            const currentZoom = zoomAttr ? parseFloat(zoomAttr) : paperRect.width / (210 * (96 / 25.4));

            // Convert to mm (96 DPI standard)
            const pxPerMm = 96 / 25.4;
            posX = Math.max(5, dropX / currentZoom / pxPerMm - defaultWidth / 2);
            posY = Math.max(5, dropY / currentZoom / pxPerMm - defaultHeight / 2);
          }

          // Create a new element
          const newElement: ReportElement = {
            id: uuidv4(),
            type: elementType,
            position: {
              x: Math.round(posX),
              y: Math.round(posY),
              width: defaultWidth,
              height: defaultHeight,
              z_index: (selectedReport.config.elements?.length ?? 0) + 1,
            },
            // For map elements, capture a snapshot of the view state only
            // (basemap and layers will be synced live from the project)
            config:
              elementType === "map"
                ? {
                    // Snapshot of view state - this is NOT synced with project
                    viewState: {
                      latitude: initialView?.latitude ?? 48.13,
                      longitude: initialView?.longitude ?? 11.57,
                      zoom: initialView?.zoom ?? 10,
                      bearing: initialView?.bearing ?? 0,
                      pitch: initialView?.pitch ?? 0,
                    },
                  }
                : {},
            style: {
              padding: 0,
              opacity: 1,
            },
          };

          // Update the report config with the new element
          const updatedConfig: ReportLayoutConfig = {
            ...selectedReport.config,
            elements: [...(selectedReport.config.elements ?? []), newElement],
          };

          // Update local state
          const updatedReport = {
            ...selectedReport,
            config: updatedConfig,
          };
          setSelectedReport(updatedReport);

          // Select the newly added element
          setSelectedElementId(newElement.id);

          // Persist to API
          try {
            await updateReportLayout(selectedReport.project_id, selectedReport.id, {
              config: updatedConfig,
            });
          } catch (error) {
            console.error("Failed to update report layout:", error);
          }
        }
      }
    },
    [selectedReport, initialView]
  );

  // Handle element selection on canvas
  const handleElementSelect = useCallback((elementId: string | null) => {
    setSelectedElementId(elementId);
  }, []);

  // Handle element update (position, size, config changes)
  const handleElementUpdate = useCallback(
    async (elementId: string, updates: Partial<ReportElement>) => {
      if (!selectedReport) return;

      const updatedElements = selectedReport.config.elements?.map((el) =>
        el.id === elementId ? { ...el, ...updates } : el
      );

      const updatedConfig: ReportLayoutConfig = {
        ...selectedReport.config,
        elements: updatedElements ?? [],
      };

      // Update local state
      const updatedReport = {
        ...selectedReport,
        config: updatedConfig,
      };
      setSelectedReport(updatedReport);

      // Persist to API
      try {
        await updateReportLayout(selectedReport.project_id, selectedReport.id, {
          config: updatedConfig,
        });
      } catch (error) {
        console.error("Failed to update report layout:", error);
      }
    },
    [selectedReport]
  );

  // Handle element delete
  const handleElementDelete = useCallback(
    async (elementId: string) => {
      if (!selectedReport) return;

      const updatedElements = selectedReport.config.elements?.filter((el) => el.id !== elementId);

      const updatedConfig: ReportLayoutConfig = {
        ...selectedReport.config,
        elements: updatedElements ?? [],
      };

      // Update local state
      const updatedReport = {
        ...selectedReport,
        config: updatedConfig,
      };
      setSelectedReport(updatedReport);

      // Clear selection if deleted element was selected
      if (selectedElementId === elementId) {
        setSelectedElementId(null);
      }

      // Persist to API
      try {
        await updateReportLayout(selectedReport.project_id, selectedReport.id, {
          config: updatedConfig,
        });
      } catch (error) {
        console.error("Failed to update report layout:", error);
      }
    },
    [selectedReport, selectedElementId]
  );

  return (
    <DndContext onDragStart={handleDragStart} onDragEnd={handleDragEnd} collisionDetection={pointerWithin}>
      <Box
        sx={{
          position: "relative",
          width: "100%",
          height: "100%",
          display: "flex",
          overflow: "hidden",
          backgroundColor: "background.default",
        }}>
        {/* Left Panel - Report Settings */}
        <ReportsConfigPanel
          project={project}
          projectLayers={projectLayers}
          selectedReport={selectedReport}
          onSelectReport={setSelectedReport}
        />

        {/* Middle Section - Canvas */}
        <ReportsCanvas
          project={project}
          projectLayers={projectLayers}
          reportConfig={selectedReport?.config}
          selectedElementId={selectedElementId}
          onElementSelect={handleElementSelect}
          onElementUpdate={handleElementUpdate}
          onElementDelete={handleElementDelete}
        />

        {/* Right Panel - Elements & History */}
        <ReportsElementsPanel
          project={project}
          projectLayers={projectLayers}
          selectedReport={selectedReport}
          selectedElementId={selectedElementId}
          onElementSelect={handleElementSelect}
          onElementUpdate={handleElementUpdate}
          onElementDelete={handleElementDelete}
        />
      </Box>

      {/* Drag Overlay */}
      <DragOverlay dropAnimation={null}>
        {activeId && activeElementType ? <DragPreview elementType={activeElementType} /> : null}
      </DragOverlay>
    </DndContext>
  );
};

export default ReportsLayout;
