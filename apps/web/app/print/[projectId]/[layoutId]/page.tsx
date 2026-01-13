"use client";

import { Box, CircularProgress, Typography } from "@mui/material";
import { useParams, useSearchParams } from "next/navigation";
import React, { useCallback, useEffect, useMemo, useState } from "react";

import ThemeProvider from "@p4b/ui/theme/ThemeProvider";

import { useProject } from "@/lib/api/projects";
import { useReportLayout } from "@/lib/api/reportLayouts";
import type { AtlasPage } from "@/lib/print/atlas-utils";
import { PAGE_SIZES, mmToPx } from "@/lib/print/units";
import type { ProjectLayer } from "@/lib/validations/project";
import type { ReportLayoutConfig } from "@/lib/validations/reportLayout";

import { useFilteredProjectLayers } from "@/hooks/map/LayerPanelHooks";
import { useBasemap } from "@/hooks/map/MapHooks";
import { useAtlasFeatures } from "@/hooks/reports/useAtlasFeatures";

import { ElementContentRenderer } from "@/components/reports/elements/renderers/ElementRenderers";

// Print DPI - higher quality for PDF output (used when generating the actual PDF)
// const PRINT_DPI = 300;
// Screen DPI for preview (Playwright captures at screen resolution)
const SCREEN_DPI = 96;

// Light theme settings for print preview (paper is always white)
const LIGHT_THEME_SETTINGS = {
  mode: "light" as const,
};

/**
 * Print-ready page that renders a report layout for Playwright PDF capture.
 * This page is designed to be rendered without any UI chrome - just the paper content.
 *
 * Playwright will navigate to this page and use page.pdf() to generate the PDF.
 *
 * Query params:
 * - page: Atlas page index (0-based). If not provided and atlas is enabled, renders page 0.
 */
export default function PrintPage() {
  const params = useParams();
  const searchParams = useSearchParams();
  const projectId = params.projectId as string;
  const layoutId = params.layoutId as string;

  // Get atlas page index from query params (0-based)
  const atlasPageIndex = searchParams.get("page") ? parseInt(searchParams.get("page")!, 10) : 0;

  const { reportLayout, isLoading, isError } = useReportLayout(projectId, layoutId);
  const { project, isLoading: isProjectLoading } = useProject(projectId);
  const { layers: projectLayers, isLoading: isLayersLoading } = useFilteredProjectLayers(
    projectId,
    ["table"],
    []
  );
  const { activeBasemap } = useBasemap(project);
  const [isReady, setIsReady] = useState(false);

  // Atlas support - fetch features and generate pages
  const {
    atlasResult,
    currentPage: currentAtlasPage,
    isLoading: isAtlasLoading,
    totalPages: atlasTotalPages,
  } = useAtlasFeatures({
    atlasConfig: reportLayout?.config?.atlas,
    projectLayers,
    currentPageIndex: atlasPageIndex,
  });

  // Check if atlas is enabled
  const isAtlasEnabled = reportLayout?.config?.atlas?.enabled === true;

  // Track map loading state
  const [mapsLoadedCount, setMapsLoadedCount] = useState(0);

  // Count how many map elements there are
  const mapElementCount = useMemo(() => {
    if (!reportLayout?.config?.elements) return 0;
    return reportLayout.config.elements.filter((el) => el.type === "map").length;
  }, [reportLayout]);

  // Callback for when a map finishes loading
  const handleMapLoaded = useCallback(() => {
    setMapsLoadedCount((prev) => prev + 1);
  }, []);

  // Check if all maps are loaded
  const allMapsLoaded = mapElementCount === 0 || mapsLoadedCount >= mapElementCount;

  // Check if atlas data is ready (if atlas is enabled)
  const atlasReady = !isAtlasEnabled || (!isAtlasLoading && (atlasResult !== null || atlasTotalPages === 0));

  // Signal to Playwright that the page is ready for printing
  // Wait for data to load AND all maps to be loaded AND atlas data (if enabled)
  useEffect(() => {
    if (reportLayout && !isLoading && !isProjectLoading && !isLayersLoading && allMapsLoaded && atlasReady) {
      // Give additional delay for map tiles to fully render
      // Keep this short since Playwright also waits for networkidle
      const timer = setTimeout(() => {
        setIsReady(true);
        // Add a data attribute that Playwright can check
        document.body.setAttribute("data-print-ready", "true");
      }, 1000); // 1 second delay to allow map tiles to render
      return () => clearTimeout(timer);
    }
  }, [reportLayout, isLoading, isProjectLoading, isLayersLoading, allMapsLoaded, atlasReady]);

  // Set document title based on layout name (used as PDF filename)
  useEffect(() => {
    if (reportLayout?.name) {
      document.title = reportLayout.name;
    }
  }, [reportLayout?.name]);

  // Extract page config
  const pageConfig = useMemo(() => {
    return (
      reportLayout?.config?.page ?? {
        size: "A4" as const,
        orientation: "portrait" as const,
        margins: { top: 10, right: 10, bottom: 10, left: 10 },
      }
    );
  }, [reportLayout]);

  // Calculate paper dimensions in pixels at screen DPI
  const paperDimensions = useMemo(() => {
    const sizeKey = pageConfig.size === "Custom" ? "A4" : pageConfig.size;
    const size = PAGE_SIZES[sizeKey] || PAGE_SIZES.A4;

    const widthMm = pageConfig.orientation === "landscape" ? size.height : size.width;
    const heightMm = pageConfig.orientation === "landscape" ? size.width : size.height;

    return {
      widthMm,
      heightMm,
      widthPx: mmToPx(widthMm, SCREEN_DPI),
      heightPx: mmToPx(heightMm, SCREEN_DPI),
    };
  }, [pageConfig.size, pageConfig.orientation]);

  if (isLoading || isProjectLoading || isLayersLoading || (isAtlasEnabled && isAtlasLoading)) {
    return (
      <Box
        sx={{
          width: "100vw",
          height: "100vh",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          backgroundColor: "#fff",
        }}>
        <CircularProgress />
      </Box>
    );
  }

  if (isError || !reportLayout) {
    return (
      <Box
        sx={{
          width: "100vw",
          height: "100vh",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          backgroundColor: "#fff",
        }}>
        <Typography color="error">Failed to load report layout</Typography>
      </Box>
    );
  }

  return (
    <Box
      sx={{
        width: paperDimensions.widthPx,
        height: paperDimensions.heightPx,
        backgroundColor: "#fff",
        padding: 0,
        margin: 0,
        // Hide scrollbars for print
        overflow: "hidden",
        "@media print": {
          backgroundColor: "transparent",
        },
      }}>
      {/* Paper */}
      <Box
        id="print-paper"
        sx={{
          width: paperDimensions.widthPx,
          height: paperDimensions.heightPx,
          backgroundColor: "#ffffff",
          position: "relative",
          boxSizing: "border-box",
          // For print, no shadow
          "@media print": {
            boxShadow: "none",
            margin: 0,
          },
        }}>
        {/* Report elements - positioned relative to the paper, not the margins */}
        {/* Wrap with light theme since paper is always white */}
        <ThemeProvider settings={LIGHT_THEME_SETTINGS}>
          <ReportElements
            config={reportLayout.config}
            basemapUrl={activeBasemap?.url}
            projectLayers={projectLayers}
            atlasPage={currentAtlasPage}
            onMapLoaded={handleMapLoaded}
          />
        </ThemeProvider>
      </Box>

      {/* Hidden metadata for Playwright */}
      <div
        id="print-metadata"
        data-ready={isReady}
        data-width-mm={paperDimensions.widthMm}
        data-height-mm={paperDimensions.heightMm}
        data-orientation={pageConfig.orientation}
        data-atlas-enabled={isAtlasEnabled}
        data-atlas-total-pages={atlasTotalPages}
        data-atlas-current-page={atlasPageIndex}
        style={{ display: "none" }}
      />
    </Box>
  );
}

/**
 * Renders the report elements on the page
 */
interface ReportElementsProps {
  config: ReportLayoutConfig;
  basemapUrl?: string;
  projectLayers?: ProjectLayer[];
  atlasPage?: AtlasPage | null;
  onMapLoaded?: () => void;
}

const ReportElements: React.FC<ReportElementsProps> = ({
  config,
  basemapUrl,
  projectLayers,
  atlasPage,
  onMapLoaded,
}) => {
  const elements = config.elements || [];

  if (elements.length === 0) {
    // Show placeholder for empty reports
    return (
      <Box
        sx={{
          width: "100%",
          height: "100%",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          color: "#ccc",
          fontSize: "14px",
        }}>
        No elements in this report
      </Box>
    );
  }

  // Render elements - positions are stored in mm, need to convert to px
  return (
    <>
      {elements.map((element) => {
        const widthPx = mmToPx(element.position.width, SCREEN_DPI);
        const heightPx = mmToPx(element.position.height, SCREEN_DPI);

        // Extract border style (width is in mm, needs conversion to px)
        const borderStyle = (element.style?.border ?? {}) as {
          enabled?: boolean;
          color?: string;
          width?: number;
        };
        const borderEnabled = borderStyle.enabled ?? false;
        const borderColor = borderStyle.color ?? "#000000";
        const borderWidthPx = borderEnabled ? mmToPx(borderStyle.width ?? 0.5, SCREEN_DPI) : 0;

        // Extract background style
        const backgroundStyle = (element.style?.background ?? {}) as {
          enabled?: boolean;
          color?: string;
          opacity?: number;
        };
        const backgroundEnabled = backgroundStyle.enabled ?? false;
        const backgroundColor = backgroundStyle.color ?? "#ffffff";
        const backgroundOpacity = backgroundStyle.opacity ?? 1;

        // Create rgba background color
        const backgroundRgba = backgroundEnabled
          ? `rgba(${parseInt(backgroundColor.slice(1, 3), 16)}, ${parseInt(backgroundColor.slice(3, 5), 16)}, ${parseInt(backgroundColor.slice(5, 7), 16)}, ${backgroundOpacity})`
          : "transparent";

        return (
          <Box
            key={element.id}
            sx={{
              position: "absolute",
              // Convert mm positions to pixels at SCREEN_DPI (96)
              left: mmToPx(element.position.x, SCREEN_DPI),
              top: mmToPx(element.position.y, SCREEN_DPI),
              width: widthPx,
              height: heightPx,
              zIndex: element.position.z_index,
              backgroundColor: backgroundRgba,
              opacity: element.style?.opacity ?? 1,
              // No rounded borders in print view
              borderRadius: 0,
              borderWidth: borderEnabled ? borderWidthPx : 0,
              borderColor: borderEnabled ? borderColor : "transparent",
              borderStyle: borderEnabled ? "solid" : "none",
              overflow: "hidden",
              // Ensure backgrounds print correctly
              WebkitPrintColorAdjust: "exact",
              printColorAdjust: "exact",
            }}>
            {/* Element content using shared renderer */}
            <ElementContentRenderer
              element={element}
              allElements={elements}
              width={widthPx}
              height={heightPx}
              basemapUrl={basemapUrl}
              projectLayers={projectLayers}
              atlasPage={atlasPage}
              viewOnly
              onMapLoaded={onMapLoaded}
            />
          </Box>
        );
      })}
    </>
  );
};
