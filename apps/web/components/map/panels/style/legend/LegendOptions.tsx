import { Checkbox, FormControlLabel, Stack, TextField, Typography } from "@mui/material";
import { useState } from "react";

import { useTranslation } from "@/i18n/client";

import type { FeatureLayerProperties } from "@/lib/validations/layer";
import type { ProjectLayer } from "@/lib/validations/project";

import SectionHeader from "@/components/map/panels/common/SectionHeader";
import SectionOptions from "@/components/map/panels/common/SectionOptions";

export const LegendOptions = ({
  layer,
  onStyleChange,
}: {
  layer: ProjectLayer;
  onStyleChange?: (newStyle: FeatureLayerProperties) => void;
}) => {
  const { t } = useTranslation("common");

  const [legendCaption, setLegendCaption] = useState<string>(layer.properties?.legend?.caption || "");

  return (
    <>
      <SectionHeader active alwaysActive label={t("options")} disableAdvanceOptions />
      <SectionOptions
        active={true}
        baseOptions={
          <Stack spacing={4} sx={{ mb: 4 }}>
            <Stack>
              <FormControlLabel
                control={
                  <Checkbox
                    size="small"
                    color="primary"
                    checked={!!layer.properties?.legend?.show}
                    onChange={(e) => {
                      const showInLegend = e.target.checked;
                      const newStyle = JSON.parse(JSON.stringify(layer.properties)) || {};
                      newStyle.legend = {
                        ...newStyle.legend,
                        show: showInLegend,
                      };
                      onStyleChange?.(newStyle as FeatureLayerProperties);
                    }}
                  />
                }
                label={<Typography variant="body2">{t("show")}</Typography>}
              />
            </Stack>
            {layer.properties?.legend?.show && (
              <TextField
                value={legendCaption}
                inputProps={{ style: { fontSize: 13 } }}
                InputLabelProps={{ style: { fontSize: 13 } }}
                placeholder={t("caption")}
                onChange={(e) => {
                  setLegendCaption(e.target.value);
                }}
                onBlur={() => {
                  const newStyle = JSON.parse(JSON.stringify(layer.properties)) || {};
                  newStyle.legend = {
                    ...newStyle.legend,
                    caption: legendCaption,
                  };
                  onStyleChange?.(newStyle as FeatureLayerProperties);
                }}
                fullWidth
                size="small"
                label={t("caption")}
                variant="outlined"
              />
            )}
          </Stack>
        }
        advancedOptions={<></>}
        collapsed={false}
      />
    </>
  );
};
