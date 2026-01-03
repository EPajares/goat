/**
 * Combined Toolbox Component
 *
 * Displays all tools from OGC API Processes, organized by category.
 * All tools use the generic form renderer based on their JSON schema.
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
import { useMemo, useState } from "react";
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

interface ToolItem {
  id: string;
  title: string;
  description?: string;
}

interface ToolListProps {
  tools: ToolItem[];
  onSelectTool: (toolId: string) => void;
}

function ToolList({ tools, onSelectTool }: ToolListProps) {
  const { t } = useTranslation("common");

  return (
    <List dense sx={{ pt: 0 }}>
      {tools.map((tool) => (
        <ListItemButton key={tool.id} onClick={() => onSelectTool(tool.id)}>
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

  const [selectedToolId, setSelectedToolId] = useState<string | undefined>(undefined);

  // Fetch all processes from OGC API
  const { processes: ogcProcesses, isLoading, error } = useCategorizedProcesses();

  // Organize tools by category
  const toolsByCategory = useMemo(() => {
    const categories: Record<ToolCategory, ToolItem[]> = {
      accessibility_indicators: [],
      geoprocessing: [],
      geoanalysis: [],
      data_management: [],
      other: [],
    };

    // Add all tools from OGC API
    for (const process of ogcProcesses) {
      const category = process.category || "other";
      categories[category].push({
        id: process.id,
        title: process.title,
        description: process.description,
      });
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

  const handleSelectTool = (toolId: string) => {
    setSelectedToolId(toolId);
  };

  const handleBack = () => {
    setSelectedToolId(undefined);
    dispatch(setMaskLayer(undefined));
    dispatch(setToolboxStartingPoints(undefined));
    dispatch(setIsMapGetInfoActive(true));
    dispatch(setMapCursor(undefined));
  };

  const handleClose = () => {
    setSelectedToolId(undefined);
    dispatch(setActiveRightPanel(undefined));
  };

  // Render selected tool
  if (selectedToolId) {
    return <GenericTool processId={selectedToolId} onBack={handleBack} onClose={handleClose} />;
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
