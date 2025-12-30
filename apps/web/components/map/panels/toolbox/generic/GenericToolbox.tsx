/**
 * Generic Toolbox Component
 *
 * Displays tools fetched from OGC API Processes, organized by category.
 * Can be used alongside the existing toolbox or as a replacement.
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

import type { CategorizedTool, ToolCategory } from "@/types/map/ogc-processes";

import { useCategorizedProcesses } from "@/hooks/map/useOgcProcesses";
import { useAppDispatch } from "@/hooks/store/ContextHooks";

import AccordionWrapper from "@/components/common/AccordionWrapper";
import Container from "@/components/map/panels/Container";
import GenericTool from "@/components/map/panels/toolbox/generic/GenericTool";

/**
 * Category display configuration
 */
const CATEGORY_CONFIG: Record<ToolCategory, { name: string; icon: ICON_NAME; order: number }> = {
  geoprocessing: {
    name: "geoprocessing",
    icon: ICON_NAME.SETTINGS,
    order: 1,
  },
  geoanalysis: {
    name: "geoanalysis",
    icon: ICON_NAME.CHART,
    order: 2,
  },
  data_management: {
    name: "data_management",
    icon: ICON_NAME.TABLE,
    order: 3,
  },
  accessibility_indicators: {
    name: "accessibility_indicators",
    icon: ICON_NAME.BULLSEYE,
    order: 4,
  },
  other: {
    name: "other",
    icon: ICON_NAME.CIRCLEINFO,
    order: 5,
  },
};

interface ToolListProps {
  tools: CategorizedTool[];
  onSelectTool: (toolId: string) => void;
}

function ToolList({ tools, onSelectTool }: ToolListProps) {
  return (
    <List dense sx={{ pt: 0 }}>
      {tools.map((tool) => (
        <ListItemButton key={tool.id} onClick={() => onSelectTool(tool.id)}>
          <ListItemText
            primary={tool.title}
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

export default function GenericToolbox() {
  const { t } = useTranslation("common");
  const theme = useTheme();
  const dispatch = useAppDispatch();

  const [selectedTool, setSelectedTool] = useState<string | undefined>(undefined);

  // Fetch processes from OGC API
  const { byCategory, isLoading, error } = useCategorizedProcesses();

  // Sort categories by order
  const sortedCategories = useMemo(() => {
    return Object.entries(byCategory)
      .filter(([_, tools]) => tools.length > 0)
      .sort(([a], [b]) => {
        const orderA = CATEGORY_CONFIG[a as ToolCategory]?.order ?? 99;
        const orderB = CATEGORY_CONFIG[b as ToolCategory]?.order ?? 99;
        return orderA - orderB;
      });
  }, [byCategory]);

  const handleSelectTool = (toolId: string) => {
    setSelectedTool(toolId);
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

  // Show selected tool form
  if (selectedTool) {
    return <GenericTool processId={selectedTool} onBack={handleBack} onClose={handleClose} />;
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

  // Error state
  if (error) {
    return (
      <Container
        title={t("tools")}
        disablePadding={true}
        close={handleClose}
        body={
          <Box sx={{ p: 2 }}>
            <Typography color="error" variant="body2">
              {t("error_loading_tools")}
            </Typography>
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
