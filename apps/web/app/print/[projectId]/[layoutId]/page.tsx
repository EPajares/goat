"use client";

import { Box, CircularProgress, Typography } from "@mui/material";
import { useParams } from "next/navigation";
import React, { useEffect, useMemo, useState } from "react";

import ThemeProvider from "@p4b/ui/theme/ThemeProvider";

import { useProject } from "@/lib/api/projects";
import { useReportLayout } from "@/lib/api/reportLayouts";
import { PAGE_SIZES, mmToPx } from "@/lib/print/units";
import type { ProjectLayer } from "@/lib/validations/project";
import type { ReportLayoutConfig } from "@/lib/validations/reportLayout";

import { useFilteredProjectLayers } from "@/hooks/map/LayerPanelHooks";
import { useBasemap } from "@/hooks/map/MapHooks";

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
 */
export default function PrintPage() {
  const params = useParams();
  const projectId = params.projectId as string;
  const layoutId = params.layoutId as string;

  const { reportLayout, isLoading, isError } = useReportLayout(projectId, layoutId);
  const { project, isLoading: isProjectLoading } = useProject(projectId);
  const { layers: projectLayers, isLoading: isLayersLoading } = useFilteredProjectLayers(
    projectId,
    ["table"],
    []
  );
  const { activeBasemap } = useBasemap(project);
  const [isReady, setIsReady] = useState(false);

  // Signal to Playwright that the page is ready for printing
  useEffect(() => {
    if (reportLayout && !isLoading && !isProjectLoading && !isLayersLoading) {
      // Give a small delay for any async rendering to complete
      const timer = setTimeout(() => {
        setIsReady(true);
        // Add a data attribute that Playwright can check
        document.body.setAttribute("data-print-ready", "true");
      }, 500);
      return () => clearTimeout(timer);
    }
  }, [reportLayout, isLoading, isProjectLoading, isLayersLoading]);

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

  if (isLoading || isProjectLoading || isLayersLoading) {
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
        width: "100vw",
        minHeight: "100vh",
        backgroundColor: "#fff",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
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
          // For screen preview, add shadow
          "@media screen": {
            boxShadow: "0 0 10px rgba(0,0,0,0.1)",
          },
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
}

const ReportElements: React.FC<ReportElementsProps> = ({ config, basemapUrl, projectLayers }) => {
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
              backgroundColor: element.style?.background || "transparent",
              opacity: element.style?.opacity ?? 1,
              // No rounded borders in print view
              borderRadius: 0,
              borderWidth: element.style?.border?.width || 0,
              borderColor: element.style?.border?.color || "transparent",
              borderStyle: element.style?.border?.width ? "solid" : "none",
              overflow: "hidden",
            }}>
            {/* Element content using shared renderer */}
            <ElementContentRenderer
              element={element}
              width={widthPx}
              height={heightPx}
              basemapUrl={basemapUrl}
              projectLayers={projectLayers}
              viewOnly
            />
          </Box>
        );
      })}
    </>
  );
};
