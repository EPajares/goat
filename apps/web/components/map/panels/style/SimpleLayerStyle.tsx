import { Box } from "@mui/material";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

import type { FeatureLayerProperties } from "@/lib/validations/layer";
import type { ProjectLayer } from "@/lib/validations/project";

import FormLabelHelper from "@/components/common/FormLabelHelper";
import SliderInput from "@/components/map/panels/common/SliderInput";

interface SimpleLayerStyleProps {
  activeLayer: ProjectLayer;
  onStyleChange?: (layerId: string, styleChanges: { opacity: number }) => void;
}

const SimpleLayerStyle = ({ activeLayer, onStyleChange }: SimpleLayerStyleProps) => {
  const { t } = useTranslation("common");

  // Get initial opacity from layer properties or default to 1
  const layerProperties = activeLayer?.properties as FeatureLayerProperties;
  const initialOpacity = layerProperties?.opacity ?? 1;
  const [opacity, setOpacity] = useState(initialOpacity);

  // Reset opacity when active layer changes
  useEffect(() => {
    const newOpacity = (activeLayer?.properties as FeatureLayerProperties)?.opacity ?? 1;
    setOpacity(newOpacity);
  }, [activeLayer]);

  const handleOpacityChange = (value: number) => {
    setOpacity(value);
  };

  const handleOpacityChangeCommitted = (value: number) => {
    if (onStyleChange && activeLayer) {
      onStyleChange(activeLayer.id.toString(), { opacity: value });
    }
  };

  if (!activeLayer) {
    return (
      <Box sx={{ p: 2 }}>
        <div>{t("no_layer_selected", { defaultValue: "No layer selected" })}</div>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 2 }}>
      <FormLabelHelper label={t("opacity")} color="inherit" />
      <SliderInput
        value={opacity}
        isRange={false}
        rootSx={{
          pl: 1,
          pt: 0,
          "&&": {
            mt: 0,
          },
        }}
        min={0}
        max={1}
        step={0.01}
        onChange={handleOpacityChange}
        onChangeCommitted={handleOpacityChangeCommitted}
      />
    </Box>
  );
};

export default SimpleLayerStyle;
