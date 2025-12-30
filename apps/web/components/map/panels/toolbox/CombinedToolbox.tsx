/**
 * Combined Toolbox Component
 *
 * Shows both:
 * 1. Existing custom tools (for complex UIs like catchment area, heatmaps)
 * 2. Generic tools from OGC API Processes (for simple geoprocessing tools)
 *
 * Uses a tab-based UI to separate them, or can be configured to merge them.
 */
import {
  Box,
  CircularProgress,
  List,
  ListItemButton,
  ListItemSecondaryAction,
  ListItemText,
  Typography,
  useTheme,
} from "@mui/material";
import React, { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";

import { ICON_NAME, Icon } from "@p4b/ui/components/Icon";

import {
  setActiveRightPanel,
  setIsMapGetInfoActive,
  setMapCursor,
  setMaskLayer,
  setToolboxStartingPoints,
} from "@/lib/store/map/slice";

import type { ToolCategory } from "@/types/map/ogc-processes";

import { useCategorizedProcesses } from "@/hooks/map/useOgcProcesses";
import { useAppDispatch } from "@/hooks/store/ContextHooks";

import AccordionWrapper from "@/components/common/AccordionWrapper";
import Container from "@/components/map/panels/Container";
import GenericTool from "@/components/map/panels/toolbox/generic/GenericTool";
// Existing custom tool components
import Aggregate from "@/components/map/panels/toolbox/tools/aggregate/Aggregate";
import CatchmentArea from "@/components/map/panels/toolbox/tools/catchment-area/CatchmentArea";
import HeatmapClosestAverage from "@/components/map/panels/toolbox/tools/heatmap-closest-average/HeatmapClosestAverage";
import HeatmapConnectivity from "@/components/map/panels/toolbox/tools/heatmap-connectivity/HeatmapConnectivity";
import HeatmapGravity from "@/components/map/panels/toolbox/tools/heatmap-gravity/HeatmapGravity";
import NearbyStations from "@/components/map/panels/toolbox/tools/nearby-stations/NearbyStations";
import OevGueteklassen from "@/components/map/panels/toolbox/tools/oev-gueteklassen/OevGueteklassen";
import TripCount from "@/components/map/panels/toolbox/tools/trip-count/TripCount";

/**
 * Tools that should use custom components instead of generic form
 * These are complex tools that need special UI handling
 */
const CUSTOM_TOOL_IDS = new Set([
  // Accessibility indicators - complex UI with map interactions
  "catchment_area",
  "heatmap_connectivity",
  "heatmap_closest_average",
  "heatmap_gravity",
  "oev_guteklassen",
  "trip_count",
  "nearby_stations",
  // These have custom implementations
  "aggregate",
  "aggregate_polygon",
  // Keep existing join/buffer for now since they work
  // "join", // Can switch to generic
  // "buffer", // Can switch to generic
]);

/**
 * Category display configuration
 */
const CATEGORY_CONFIG: Record<ToolCategory, { name: string; icon: ICON_NAME; order: number }> = {
  accessibility_indicators: {
    name: "accessibility_indicators",
    icon: ICON_NAME.BULLSEYE,
    order: 1,
  },
  geoprocessing: {
    name: "geoprocessing",
    icon: ICON_NAME.SETTINGS,
    order: 2,
  },
  geoanalysis: {
    name: "geoanalysis",
    icon: ICON_NAME.CHART,
    order: 3,
  },
  data_management: {
    name: "data_management",
    icon: ICON_NAME.TABLE,
    order: 4,
  },
  other: {
    name: "other",
    icon: ICON_NAME.CIRCLEINFO,
    order: 5,
  },
};

/**
 * Custom tools configuration (kept for complex tools)
 */
interface CustomToolConfig {
  id: string;
  category: ToolCategory;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  component: React.ComponentType<any>;
  props?: Record<string, unknown>;
}

const CUSTOM_TOOLS: CustomToolConfig[] = [
  // Accessibility indicators
  { id: "catchment_area", category: "accessibility_indicators", component: CatchmentArea },
  { id: "heatmap_connectivity", category: "accessibility_indicators", component: HeatmapConnectivity },
  { id: "heatmap_closest_average", category: "accessibility_indicators", component: HeatmapClosestAverage },
  { id: "heatmap_gravity", category: "accessibility_indicators", component: HeatmapGravity },
  { id: "oev_guteklassen", category: "accessibility_indicators", component: OevGueteklassen },
  { id: "trip_count", category: "accessibility_indicators", component: TripCount },
  { id: "nearby_stations", category: "accessibility_indicators", component: NearbyStations },
  // Geoanalysis
  { id: "aggregate", category: "geoanalysis", component: Aggregate, props: { type: "point" } },
  { id: "aggregate_polygon", category: "geoanalysis", component: Aggregate, props: { type: "polygon" } },
];

interface ToolItem {
  id: string;
  title: string;
  description?: string;
  isGeneric: boolean;
}

interface ToolListProps {
  tools: ToolItem[];
  onSelectTool: (toolId: string, isGeneric: boolean) => void;
}

function ToolList({ tools, onSelectTool }: ToolListProps) {
  const { t } = useTranslation("common");

  return (
    <List dense sx={{ pt: 0 }}>
      {tools.map((tool) => (
        <ListItemButton key={tool.id} onClick={() => onSelectTool(tool.id, tool.isGeneric)}>
          <ListItemText
            primary={t(tool.id, { defaultValue: tool.title })}
            secondary={
              tool.description && tool.description.length > 60
                ? `${tool.description.substring(0, 60)}...`
                : tool.description
            }
            secondaryTypographyProps={{
              variant: "caption",
              sx: { opacity: 0.7 },
            }}
          />
          <ListItemSecondaryAction>
            <Icon iconName={ICON_NAME.CHEVRON_RIGHT} sx={{ fontSize: "12px" }} />
          </ListItemSecondaryAction>
        </ListItemButton>
      ))}
    </List>
  );
}

export default function CombinedToolbox() {
  const { t } = useTranslation("common");
  const theme = useTheme();
  const dispatch = useAppDispatch();

  const [selectedTool, setSelectedTool] = useState<
    | {
        id: string;
        isGeneric: boolean;
      }
    | undefined
  >(undefined);

  // Fetch generic processes from OGC API
  const { processes: ogcProcesses, isLoading, error } = useCategorizedProcesses();

  // Combine custom tools and generic tools by category
  const toolsByCategory = useMemo(() => {
    const categories: Record<ToolCategory, ToolItem[]> = {
      accessibility_indicators: [],
      geoprocessing: [],
      geoanalysis: [],
      data_management: [],
      other: [],
    };

    // Add custom tools first
    for (const customTool of CUSTOM_TOOLS) {
      categories[customTool.category].push({
        id: customTool.id,
        title: customTool.id.replace(/_/g, " "),
        isGeneric: false,
      });
    }

    // Add generic tools from OGC API (exclude those that have custom implementations)
    for (const process of ogcProcesses) {
      if (!CUSTOM_TOOL_IDS.has(process.id)) {
        const category = process.category || "other";
        categories[category].push({
          id: process.id,
          title: process.title,
          description: process.description,
          isGeneric: true,
        });
      }
    }

    return categories;
  }, [ogcProcesses]);

  // Sort categories and filter empty ones
  const sortedCategories = useMemo(() => {
    return Object.entries(toolsByCategory)
      .filter(([_, tools]) => tools.length > 0)
      .sort(([a], [b]) => {
        const orderA = CATEGORY_CONFIG[a as ToolCategory]?.order ?? 99;
        const orderB = CATEGORY_CONFIG[b as ToolCategory]?.order ?? 99;
        return orderA - orderB;
      });
  }, [toolsByCategory]);

  const handleSelectTool = (toolId: string, isGeneric: boolean) => {
    setSelectedTool({ id: toolId, isGeneric });
  };

  const handleBack = () => {
    setSelectedTool(undefined);
    dispatch(setMaskLayer(undefined));
    dispatch(setToolboxStartingPoints(undefined));
    dispatch(setIsMapGetInfoActive(true));
    dispatch(setMapCursor(undefined));
  };

  const handleClose = () => {
    setSelectedTool(undefined);
    dispatch(setActiveRightPanel(undefined));
  };

  // Render selected tool
  if (selectedTool) {
    // Check if it's a generic tool
    if (selectedTool.isGeneric) {
      return <GenericTool processId={selectedTool.id} onBack={handleBack} onClose={handleClose} />;
    }

    // Find custom tool config
    const customTool = CUSTOM_TOOLS.find((t) => t.id === selectedTool.id);
    if (customTool) {
      const ToolComponent = customTool.component;
      return <ToolComponent onBack={handleBack} onClose={handleClose} {...(customTool.props || {})} />;
    }
  }

  // Loading state
  if (isLoading) {
    return (
      <Container
        title={t("tools")}
        disablePadding={true}
        close={handleClose}
        body={
          <Box sx={{ display: "flex", justifyContent: "center", py: 4 }}>
            <CircularProgress />
          </Box>
        }
      />
    );
  }

  // Main toolbox view
  return (
    <Container
      title={t("tools")}
      disablePadding={true}
      close={handleClose}
      body={
        <>
          {error && (
            <Typography color="warning.main" variant="caption" sx={{ p: 1, display: "block" }}>
              {t("some_tools_unavailable")}
            </Typography>
          )}

          {sortedCategories.map(([category, tools]) => {
            const config = CATEGORY_CONFIG[category as ToolCategory];

            return (
              <AccordionWrapper
                key={category}
                boxShadow="none"
                backgroundColor="transparent"
                header={
                  <Typography
                    variant="body2"
                    fontWeight="bold"
                    sx={{
                      flexShrink: 0,
                      display: "flex",
                      gap: theme.spacing(2),
                      alignItems: "center",
                    }}>
                    <Icon
                      iconName={config?.icon ?? ICON_NAME.CIRCLEINFO}
                      sx={{ fontSize: "16px" }}
                      htmlColor="inherit"
                    />
                    {t(config?.name ?? category)}
                  </Typography>
                }
                body={<ToolList tools={tools} onSelectTool={handleSelectTool} />}
              />
            );
          })}

          {sortedCategories.length === 0 && (
            <Box sx={{ p: 2 }}>
              <Typography variant="body2" color="text.secondary">
                {t("no_tools_available")}
              </Typography>
            </Box>
          )}
        </>
      }
    />
  );
}
