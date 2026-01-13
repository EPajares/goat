import { Box, Typography } from "@mui/material";

import type { BuilderWidgetSchema, ProjectLayer, ProjectLayerGroup } from "@/lib/validations/project";
import type { TabsContainerSchema, WidgetElementConfig } from "@/lib/validations/widget";

import DividerElementWidget from "@/components/builder/widgets/elements/Divider";
import ImageElementWidget from "@/components/builder/widgets/elements/Image";
import TabsWidget from "@/components/builder/widgets/elements/Tabs";
import TextElementWidget from "@/components/builder/widgets/elements/text/Text";

interface WidgetElementProps {
  widget?: BuilderWidgetSchema;
  config: WidgetElementConfig;
  viewOnly?: boolean;
  onWidgetUpdate?: (newData: WidgetElementConfig) => void;
  fitMode?: "auto" | "contain";
  // For tabs widget
  projectLayers?: ProjectLayer[];
  projectLayerGroups?: ProjectLayerGroup[];
  panelWidgets?: BuilderWidgetSchema[];
}

const hasOptions = (
  config: WidgetElementConfig
): config is WidgetElementConfig & { options: { description?: string } } =>
  "options" in config && typeof config.options === "object" && config.options !== null;

const WidgetElement: React.FC<WidgetElementProps> = ({
  widget,
  config,
  onWidgetUpdate,
  viewOnly,
  fitMode,
  projectLayers,
  projectLayerGroups,
  panelWidgets,
}) => {
  return (
    <Box sx={{ width: "100%", height: fitMode === "contain" || config.type === "text" ? "100%" : undefined }}>
      {config.type === "text" && (
        <TextElementWidget config={config} viewOnly={viewOnly} onWidgetUpdate={onWidgetUpdate} />
      )}
      {config.type === "divider" && <DividerElementWidget config={config} />}
      {config.type === "image" && (
        <ImageElementWidget
          config={config}
          viewOnly={viewOnly}
          onWidgetUpdate={onWidgetUpdate}
          fitMode={fitMode}
        />
      )}
      {config.type === "tabs" && widget && projectLayers && projectLayerGroups && (
        <TabsWidget
          widget={widget}
          config={config as TabsContainerSchema}
          projectLayers={projectLayers}
          projectLayerGroups={projectLayerGroups}
          viewOnly={viewOnly}
          panelWidgets={panelWidgets}
          onWidgetUpdate={(updatedWidget) => {
            if (updatedWidget.config) {
              onWidgetUpdate?.(updatedWidget.config as WidgetElementConfig);
            }
          }}
        />
      )}
      {hasOptions(config) && config.options.description && (
        <Typography variant="body2" align="left">
          {config.options.description}
        </Typography>
      )}
    </Box>
  );
};

export default WidgetElement;
