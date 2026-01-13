import { Box, Tabs as MuiTabs, Stack, Tab, Typography, useTheme } from "@mui/material";
import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";

import { setSelectedBuilderItem } from "@/lib/store/map/slice";
import type { BuilderWidgetSchema, ProjectLayer, ProjectLayerGroup } from "@/lib/validations/project";
import type { TabItemSchema, TabsContainerSchema, WidgetConfigSchema } from "@/lib/validations/widget";
import {
  type WidgetChartConfig,
  type WidgetDataConfig,
  type WidgetElementConfig,
  type WidgetInformationConfig,
  chartTypes,
  dataTypes,
  elementTypes,
  informationTypes,
} from "@/lib/validations/widget";

import { useAppDispatch, useAppSelector } from "@/hooks/store/ContextHooks";

import WidgetChart from "@/components/builder/widgets/chart/WidgetChart";
import { WidgetStatusContainer } from "@/components/builder/widgets/common/WidgetStatusContainer";
import WidgetData from "@/components/builder/widgets/data/WidgetData";
import WidgetElement from "@/components/builder/widgets/elements/WidgetElement";
import WidgetInformation from "@/components/builder/widgets/information/WidgetInformation";

interface TabsWidgetProps {
  widget: BuilderWidgetSchema;
  config: TabsContainerSchema;
  projectLayers: ProjectLayer[];
  projectLayerGroups: ProjectLayerGroup[];
  viewOnly?: boolean;
  panelWidgets?: BuilderWidgetSchema[];
  onWidgetUpdate?: (updatedWidget: BuilderWidgetSchema) => void;
}

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`tabs-widget-tabpanel-${index}`}
      aria-labelledby={`tabs-widget-tab-${index}`}
      {...other}>
      {value === index && <Box sx={{ pt: 2 }}>{children}</Box>}
    </div>
  );
}

function a11yProps(index: number) {
  return {
    id: `tabs-widget-tab-${index}`,
    "aria-controls": `tabs-widget-tabpanel-${index}`,
  };
}

// Render a single child widget inside a tab
const TabChildWidget: React.FC<{
  childWidget: BuilderWidgetSchema;
  projectLayers: ProjectLayer[];
  projectLayerGroups: ProjectLayerGroup[];
  viewOnly?: boolean;
  isSelected?: boolean;
  onSelect?: () => void;
}> = ({ childWidget, projectLayers, projectLayerGroups, viewOnly, isSelected, onSelect }) => {
  const theme = useTheme();
  const config = childWidget.config as WidgetConfigSchema;

  if (!config) return null;

  // Render the appropriate widget based on type
  const renderWidget = () => {
    if ((informationTypes.options as readonly string[]).includes(config.type)) {
      return (
        <WidgetInformation
          config={config as WidgetInformationConfig}
          projectLayers={projectLayers}
          projectLayerGroups={projectLayerGroups}
          viewOnly={viewOnly}
        />
      );
    }
    if ((dataTypes.options as readonly string[]).includes(config.type)) {
      return (
        <WidgetData
          id={childWidget.id}
          config={config as WidgetDataConfig}
          projectLayers={projectLayers}
          viewOnly={viewOnly}
        />
      );
    }
    if ((chartTypes.options as readonly string[]).includes(config.type)) {
      return <WidgetChart config={config as WidgetChartConfig} viewOnly={viewOnly} />;
    }
    // Exclude tabs from being rendered inside tabs (prevent recursive tabs)
    if ((elementTypes.options as readonly string[]).includes(config.type) && config.type !== "tabs") {
      return <WidgetElement config={config as WidgetElementConfig} viewOnly={viewOnly} />;
    }
    return null;
  };

  return (
    <Box
      onClick={(e) => {
        if (!viewOnly) {
          e.stopPropagation();
          onSelect?.();
        }
      }}
      sx={{
        cursor: viewOnly ? "default" : "pointer",
        borderRadius: 1,
        border: isSelected ? `2px solid ${theme.palette.primary.main}` : "2px solid transparent",
        transition: "border-color 0.2s ease-in-out",
        "&:hover": !viewOnly
          ? {
              borderColor: theme.palette.primary.light,
            }
          : {},
      }}>
      {renderWidget()}
    </Box>
  );
};

const TabsWidget: React.FC<TabsWidgetProps> = ({
  widget,
  config,
  projectLayers,
  projectLayerGroups,
  viewOnly,
  panelWidgets = [],
}) => {
  const { t } = useTranslation("common");
  const dispatch = useAppDispatch();
  const selectedBuilderItem = useAppSelector((state) => state.map.selectedBuilderItem);
  const [activeTab, setActiveTab] = useState(0);

  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  const tabs = config.tabs || [];

  // Get widgets assigned to a tab (from tab.widgetIds)
  const getWidgetsForTab = useMemo(() => {
    return (tab: TabItemSchema): BuilderWidgetSchema[] => {
      const widgetIds = tab.widgetIds || [];
      if (widgetIds.length === 0) return [];

      return widgetIds
        .map((id) => panelWidgets.find((w) => w.id === id))
        .filter(
          (w): w is BuilderWidgetSchema =>
            w !== undefined &&
            w.id !== widget.id && // Exclude self
            w.config?.type !== "tabs" // Prevent tabs inside tabs
        );
    };
  }, [panelWidgets, widget.id]);

  return (
    <Box sx={{ width: "100%" }}>
      {/* Show title if it has a value */}
      {config.setup?.title && (
        <Typography variant="body1" fontWeight="bold" sx={{ mb: 1 }}>
          {config.setup.title}
        </Typography>
      )}

      {/* Tabs header */}
      <Box
        sx={{
          borderBottom: 1,
          borderColor: "divider",
          position: "relative",
          "& .MuiTabs-scrollButtons.Mui-disabled": {
            display: "none",
          },
          "& .MuiTabs-scrollButtons": {
            position: "absolute",
            top: 0,
            bottom: 0,
            zIndex: 1,
            opacity: 0,
            transition: "opacity 0.2s",
            width: 40,
            "&:first-of-type": {
              left: 0,
              background: (theme) =>
                `linear-gradient(to right, ${theme.palette.background.paper} 50%, transparent)`,
            },
            "&:last-of-type": {
              right: 0,
              background: (theme) =>
                `linear-gradient(to left, ${theme.palette.background.paper} 50%, transparent)`,
            },
          },
          "&:hover .MuiTabs-scrollButtons:not(.Mui-disabled)": {
            opacity: 1,
          },
        }}>
        <MuiTabs
          value={Math.min(activeTab, Math.max(0, tabs.length - 1))}
          onChange={handleTabChange}
          aria-label="tabs widget"
          variant="scrollable"
          scrollButtons="auto"
          sx={{ minHeight: 32 }}>
          {tabs.map((tab, index) => (
            <Tab
              key={tab.id}
              label={tab.name}
              {...a11yProps(index)}
              sx={{
                textTransform: "none",
                minHeight: 32,
                py: 0.5,
                px: 1.5,
                fontSize: "0.85rem",
              }}
            />
          ))}
        </MuiTabs>
      </Box>

      {/* Tab panels */}
      {tabs.map((tab, index) => {
        const tabWidgets = getWidgetsForTab(tab);

        return (
          <TabPanel key={tab.id} value={activeTab} index={index}>
            {tabWidgets.length === 0 ? (
              // Empty state - use standard widget status container
              <WidgetStatusContainer isNotConfigured isNotConfiguredMessage={t("no_widgets_in_tab")} />
            ) : (
              // Render widgets
              <Stack spacing={2}>
                {tabWidgets.map((childWidget) => (
                  <TabChildWidget
                    key={childWidget.id}
                    childWidget={childWidget}
                    projectLayers={projectLayers}
                    projectLayerGroups={projectLayerGroups}
                    viewOnly={viewOnly}
                    isSelected={
                      selectedBuilderItem?.type === "widget" && selectedBuilderItem?.id === childWidget.id
                    }
                    onSelect={() => dispatch(setSelectedBuilderItem(childWidget))}
                  />
                ))}
              </Stack>
            )}
          </TabPanel>
        );
      })}
    </Box>
  );
};

export default TabsWidget;
