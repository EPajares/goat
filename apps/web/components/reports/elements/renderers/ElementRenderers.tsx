import { Box, Typography } from "@mui/material";
import React from "react";

import type { AtlasPage } from "@/lib/print/atlas-utils";
import type { ProjectLayer } from "@/lib/validations/project";
import type { ReportElement, ReportElementType } from "@/lib/validations/reportLayout";
import type { WidgetChartConfig, WidgetElementConfig } from "@/lib/validations/widget";
import type { chartTypes } from "@/lib/validations/widget";
import { elementTypes } from "@/lib/validations/widget";

import WidgetChart from "@/components/builder/widgets/chart/WidgetChart";
import WidgetElement from "@/components/builder/widgets/elements/WidgetElement";
import MapElementRenderer from "@/components/reports/elements/renderers/MapElementRenderer";

// Types that are rendered as chart widgets (same as dashboard)
const chartElementTypes: ReportElementType[] = ["histogram_chart", "categories_chart", "pie_chart"];

// Types that are rendered as element widgets (text, image, divider)
const elementElementTypes: ReportElementType[] = ["text", "image", "divider"];

export const isChartElementType = (type: ReportElementType): boolean => {
  return chartElementTypes.includes(type);
};

export const isElementElementType = (type: ReportElementType): boolean => {
  return elementElementTypes.includes(type);
};

interface ElementRendererProps {
  element: ReportElement;
  viewOnly?: boolean;
  onElementUpdate?: (elementId: string, config: Record<string, unknown>) => void;
}

interface ElementContentRendererProps {
  element: ReportElement;
  width: number;
  height: number;
  zoom?: number;
  basemapUrl?: string;
  projectLayers?: ProjectLayer[];
  atlasPage?: AtlasPage | null;
  viewOnly?: boolean;
  onElementUpdate?: (elementId: string, config: Record<string, unknown>) => void;
  onNavigationModeChange?: (isNavigating: boolean) => void;
}

/**
 * Convert report chart element to WidgetChartConfig
 * Chart configs have: type, setup (title, layer_project_id, ...), options (...)
 * We use type assertion since report element config is stored as Record<string, any>
 */
const toChartConfig = (element: ReportElement): WidgetChartConfig => {
  const chartType = element.type as (typeof chartTypes.Values)[keyof typeof chartTypes.Values];

  // If config is already in the correct format (has setup and options), use it directly
  if (element.config.setup && element.config.options) {
    return {
      type: chartType,
      setup: element.config.setup,
      options: element.config.options,
    } as WidgetChartConfig;
  }

  // Return default config with proper type
  return {
    type: chartType,
    setup: { title: "Chart" },
    options: {},
  } as WidgetChartConfig;
};

/**
 * Convert report element to WidgetElementConfig
 * Element configs vary by type:
 * - text: { type, setup: { text } }
 * - divider: { type, setup: { size } }
 * - image: { type, setup: { url, alt }, options: { has_padding, description } }
 * We use type assertion since report element config is stored as Record<string, any>
 */
const toElementConfig = (element: ReportElement): WidgetElementConfig => {
  const elemType = element.type as (typeof elementTypes.Values)[keyof typeof elementTypes.Values];

  if (elemType === elementTypes.Values.text) {
    return {
      type: elementTypes.Values.text,
      setup: {
        text: element.config.setup?.text ?? element.config.text ?? element.config.content ?? "Text",
      },
    };
  }

  if (elemType === elementTypes.Values.image) {
    return {
      type: elementTypes.Values.image,
      setup: {
        url: element.config.setup?.url ?? element.config.url ?? "",
        alt: element.config.setup?.alt ?? element.config.alt ?? "",
      },
      options: {
        has_padding: element.config.options?.has_padding ?? false,
        description: element.config.options?.description,
      },
    };
  }

  if (elemType === elementTypes.Values.divider) {
    return {
      type: elementTypes.Values.divider,
      setup: {
        size: element.config.setup?.size ?? element.config.size ?? 1,
      },
    };
  }

  // Fallback
  return {
    type: elementTypes.Values.text,
    setup: { text: "Text" },
  };
};

/**
 * Renders chart elements (histogram, categories, pie) using WidgetChart from builder
 */
export const ChartElementRenderer: React.FC<ElementRendererProps> = ({ element, viewOnly = true }) => {
  if (!isChartElementType(element.type)) {
    return null;
  }

  const chartConfig = toChartConfig(element);

  return <WidgetChart config={chartConfig} viewOnly={viewOnly} />;
};

/**
 * Renders element widgets (text, image, divider) using WidgetElement from builder
 */
export const ElementRenderer: React.FC<ElementRendererProps> = ({
  element,
  viewOnly = true,
  onElementUpdate,
}) => {
  if (!isElementElementType(element.type)) {
    return null;
  }

  const elementConfig = toElementConfig(element);

  const handleWidgetUpdate = (newData: WidgetElementConfig) => {
    if (onElementUpdate) {
      onElementUpdate(element.id, newData as unknown as Record<string, unknown>);
    }
  };

  return (
    <WidgetElement
      config={elementConfig}
      viewOnly={viewOnly}
      onWidgetUpdate={handleWidgetUpdate}
      fitMode="contain"
    />
  );
};

/**
 * Generic renderer that dispatches to the appropriate renderer based on element type
 */
export const ReportElementRenderer: React.FC<ElementRendererProps> = (props) => {
  const { element } = props;

  if (isChartElementType(element.type)) {
    return <ChartElementRenderer {...props} />;
  }

  if (isElementElementType(element.type)) {
    return <ElementRenderer {...props} />;
  }

  // For other types (map, legend, etc.) - placeholder for now
  return null;
};

/**
 * Content renderer used by the canvas - wraps ReportElementRenderer with proper sizing
 */
export const ElementContentRenderer: React.FC<ElementContentRendererProps> = ({
  element,
  width: _width,
  height: _height,
  zoom = 1,
  basemapUrl,
  projectLayers,
  atlasPage,
  viewOnly = true,
  onElementUpdate,
  onNavigationModeChange,
}) => {
  // For chart and element types, use the widget renderers
  if (isChartElementType(element.type) || isElementElementType(element.type)) {
    return (
      <Box
        sx={{
          width: "100%",
          height: "100%",
          overflow: "hidden",
          pointerEvents: viewOnly ? "none" : "all",
        }}>
        <ReportElementRenderer element={element} viewOnly={viewOnly} onElementUpdate={onElementUpdate} />
      </Box>
    );
  }

  // For map elements - use MapElementRenderer (reads snapshot from element.config)
  if (element.type === "map") {
    return (
      <Box
        sx={{
          width: "100%",
          height: "100%",
          overflow: "hidden",
        }}>
        <MapElementRenderer
          element={element}
          basemapUrl={basemapUrl}
          layers={projectLayers}
          zoom={zoom}
          atlasPage={atlasPage}
          viewOnly={viewOnly}
          onElementUpdate={onElementUpdate}
          onNavigationModeChange={onNavigationModeChange}
        />
      </Box>
    );
  }

  // For legend elements - placeholder
  if (element.type === "legend") {
    return (
      <Box
        sx={{
          width: "100%",
          height: "100%",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          backgroundColor: "#f5f5f5",
        }}>
        <Typography variant="caption" color="text.secondary">
          Legend
        </Typography>
      </Box>
    );
  }

  // For scalebar elements - placeholder
  if (element.type === "scalebar") {
    return (
      <Box
        sx={{
          width: "100%",
          height: "100%",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}>
        <Box
          sx={{
            width: "80%",
            height: 8,
            display: "flex",
          }}>
          <Box sx={{ flex: 1, backgroundColor: "#333" }} />
          <Box sx={{ flex: 1, backgroundColor: "#fff", border: "1px solid #333" }} />
          <Box sx={{ flex: 1, backgroundColor: "#333" }} />
        </Box>
      </Box>
    );
  }

  // For north arrow elements - placeholder
  if (element.type === "north_arrow") {
    return (
      <Box
        sx={{
          width: "100%",
          height: "100%",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}>
        <Typography variant="h4" fontWeight="bold">
          ⬆
        </Typography>
      </Box>
    );
  }

  // Default placeholder for unknown types
  return (
    <Box
      sx={{
        width: "100%",
        height: "100%",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        backgroundColor: "rgba(200, 220, 255, 0.3)",
        p: 1,
      }}>
      <Typography variant="caption" color="text.secondary" noWrap>
        {element.type}
      </Typography>
    </Box>
  );
};

export default ReportElementRenderer;
