import { Box, Typography } from "@mui/material";

import type { WidgetElementConfig } from "@/lib/validations/widget";

import DividerElementWidget from "@/components/builder/widgets/elements/Divider";
import ImageElementWidget from "@/components/builder/widgets/elements/Image";
import TextElementWidget from "@/components/builder/widgets/elements/text/Text";

interface WidgetElementProps {
  config: WidgetElementConfig;
  viewOnly?: boolean;
  onWidgetUpdate?: (newData: WidgetElementConfig) => void;
}

const hasOptions = (
  config: WidgetElementConfig
): config is WidgetElementConfig & { options: { description?: string } } =>
  "options" in config && typeof config.options === "object" && config.options !== null;

const WidgetElement: React.FC<WidgetElementProps> = ({ config, onWidgetUpdate, viewOnly }) => {
  return (
    <Box sx={{ width: "100%" }}>
      {config.type === "text" && (
        <TextElementWidget config={config} viewOnly={viewOnly} onWidgetUpdate={onWidgetUpdate} />
      )}
      {config.type === "divider" && <DividerElementWidget config={config} />}
      {config.type === "image" && (
        <ImageElementWidget config={config} viewOnly={viewOnly} onWidgetUpdate={onWidgetUpdate} />
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
