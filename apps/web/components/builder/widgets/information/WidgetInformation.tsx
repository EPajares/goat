import { Box, Typography } from "@mui/material";

import type { ProjectLayer } from "@/lib/validations/project";
import type { WidgetInformationConfig } from "@/lib/validations/widget";
import { informationTypes } from "@/lib/validations/widget";

import { LayerInformationWidget } from "@/components/builder/widgets/information/Layers";

interface WidgetInformationProps {
  config: WidgetInformationConfig;
  projectLayers: ProjectLayer[];
  viewOnly?: boolean;
}

const WidgetInformation: React.FC<WidgetInformationProps> = ({ config, projectLayers, viewOnly }) => {
  return (
    <Box>
      {config.setup?.title && (
        <Typography variant="body1" fontWeight="bold" align="left" gutterBottom>
          {config.setup?.title}
        </Typography>
      )}
      {config.type === informationTypes.Values.layers && (
        <LayerInformationWidget config={config} projectLayers={projectLayers} viewOnly={viewOnly} />
      )}
      {config.options?.description && (
        <Typography variant="body2" align="left">
          {config.options.description}
        </Typography>
      )}
    </Box>
  );
};

export default WidgetInformation;
