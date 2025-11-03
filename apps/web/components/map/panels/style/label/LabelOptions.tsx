import { Checkbox, FormControlLabel, Stack, Typography } from "@mui/material";
import { useEffect, useMemo, useState } from "react";

import { useTranslation } from "@/i18n/client";

import { type FeatureLayerProperties, type LayerFieldType, TextLabelSchema } from "@/lib/validations/layer";
import type { ProjectLayer } from "@/lib/validations/project";

import type { SelectorItem } from "@/types/map/common";

import useLayerFields from "@/hooks/map/CommonHooks";
import { useSymbolOptions } from "@/hooks/map/LayerDesignHooks";

import FormLabelHelper from "@/components/common/FormLabelHelper";
import LayerFieldSelector from "@/components/map/common/LayerFieldSelector";
import SectionHeader from "@/components/map/panels/common/SectionHeader";
import SectionOptions from "@/components/map/panels/common/SectionOptions";
import Selector from "@/components/map/panels/common/Selector";
import SliderInput from "@/components/map/panels/common/SliderInput";
import ColorSelector from "@/components/map/panels/style/color/ColorSelector";

const LabelOptions = ({
  layer,
  onStyleChange,
}: {
  layer: ProjectLayer;
  onStyleChange?: (newStyle: FeatureLayerProperties) => void;
}) => {
  const { t } = useTranslation("common");
  const { layerFields } = useLayerFields(layer?.layer_id || "");
  const [collapseAdvancedSettings, setCollapseAdvancedSettings] = useState(true);
  const textLabelOptions = useMemo(() => {
    const textLabelProperties = TextLabelSchema.safeParse(layer?.properties?.text_label);
    if (textLabelProperties.success) {
      return textLabelProperties.data;
    }
    return undefined;
  }, [layer?.properties?.text_label]);

  const [selectedField, setSelectedField] = useState<LayerFieldType | undefined>(undefined);
  useEffect(() => {
    if (textLabelOptions?.field && layerFields && !selectedField) {
      const field = layerFields.find((f) => f.name === textLabelOptions.field);
      setSelectedField(field);
    }
  }, [textLabelOptions?.field, layerFields, selectedField]);

  const [textLabelSize, setTextLabelSize] = useState<number | undefined>(textLabelOptions?.size);
  const [textLabelAnchorX, setTextLabelAnchorX] = useState<number | undefined>(
    textLabelOptions?.offset?.[0] || 0
  );
  const [textLabelAnchorY, setTextLabelAnchorY] = useState<number | undefined>(
    textLabelOptions?.offset?.[1] || 0
  );
  const [textLabelOutlineWidth, setTextLabelOutlineWidth] = useState<number | undefined>(
    textLabelOptions?.outline_width || 0
  );

  const labelFillColor = useMemo(
    () => ({
      selectedColor: textLabelOptions?.color || "#000000",
      isRange: false,
      setColor: (color) => {
        const newStyle = JSON.parse(JSON.stringify(layer.properties)) || {};
        const textLabel = TextLabelSchema.safeParse({
          ...textLabelOptions,
          color,
        });
        if (textLabel.success) {
          newStyle.text_label = textLabel.data;
        }
        onStyleChange?.(newStyle);
      },
    }),
    [layer.properties, onStyleChange, textLabelOptions]
  );
  const { anchorItems } = useSymbolOptions(layer);

  const selectedLabelPlacement = useMemo(() => {
    if (!textLabelOptions?.anchor) {
      return anchorItems[0];
    }
    return anchorItems.find((item) => item.value === textLabelOptions.anchor) || anchorItems[0];
  }, [textLabelOptions?.anchor, anchorItems]);

  return (
    <>
      <SectionHeader active alwaysActive label={t("label_by")} disableAdvanceOptions />
      <SectionOptions
        active={true}
        baseOptions={
          <LayerFieldSelector
            fields={layerFields}
            selectedField={selectedField}
            setSelectedField={(field) => {
              setSelectedField(field);
              const newStyle = JSON.parse(JSON.stringify(layer.properties)) || {};
              if (!field) {
                newStyle.text_label = undefined;
              } else {
                const textLabel = TextLabelSchema.safeParse({
                  ...textLabelOptions,
                  field: field.name,
                });
                if (textLabel.success) {
                  newStyle.text_label = textLabel.data;
                }
              }
              onStyleChange?.(newStyle);
            }}
            label={t("label_by")}
          />
        }
        advancedOptions={<></>}
        collapsed={false}
      />

      <SectionHeader
        active={!!selectedField}
        alwaysActive
        label={t("label_settings")}
        collapsed={collapseAdvancedSettings}
        setCollapsed={setCollapseAdvancedSettings}
      />
      <SectionOptions
        active={!!selectedField}
        collapsed={collapseAdvancedSettings}
        baseOptions={
          <>
            <Stack>
              <FormLabelHelper label={t("size")} color="inherit" />
              <SliderInput
                value={textLabelSize || textLabelOptions?.size || 0}
                onChange={(value) => {
                  setTextLabelSize(value as number);
                }}
                onChangeCommitted={(value) => {
                  const newStyle = JSON.parse(JSON.stringify(layer.properties)) || {};
                  const textLabel = TextLabelSchema.safeParse({
                    ...textLabelOptions,
                    size: value as number,
                  });
                  if (textLabel.success) {
                    newStyle.text_label = textLabel.data;
                  }
                  onStyleChange?.(newStyle);
                }}
                isRange={false}
                rootSx={{
                  pl: 3,
                  pr: 2,
                }}
              />
            </Stack>
            <ColorSelector colorSet={labelFillColor} label={t("color")} />
            <Selector
              selectedItems={selectedLabelPlacement}
              setSelectedItems={(item: SelectorItem | undefined) => {
                const newStyle = JSON.parse(JSON.stringify(layer.properties)) || {};
                const textLabel = TextLabelSchema.safeParse({
                  ...textLabelOptions,
                  anchor: item?.value,
                });
                if (textLabel.success) {
                  newStyle.text_label = textLabel.data;
                }
                onStyleChange?.(newStyle);
              }}
              items={anchorItems}
              label={t("placement")}
              placeholder={t("select_label_placement")}
            />
          </>
        }
        advancedOptions={
          <>
            <Stack>
              <FormLabelHelper label={t("offset_x")} color="inherit" />
              <SliderInput
                min={-5}
                max={5}
                step={0.5}
                value={textLabelAnchorX ?? 0}
                onChange={(value) => {
                  setTextLabelAnchorX(value as number);
                }}
                onChangeCommitted={(value) => {
                  const newStyle = JSON.parse(JSON.stringify(layer.properties)) || {};
                  const textLabel = TextLabelSchema.safeParse({
                    ...textLabelOptions,
                    offset: [value as number, textLabelAnchorY || 0],
                  });
                  if (textLabel.success) {
                    newStyle.text_label = textLabel.data;
                  }
                  onStyleChange?.(newStyle);
                }}
                isRange={false}
                rootSx={{
                  pl: 3,
                  pr: 2,
                }}
              />
            </Stack>

            <Stack>
              <FormLabelHelper label={t("offset_y")} color="inherit" />
              <SliderInput
                value={textLabelAnchorY ?? 0}
                min={-5}
                max={5}
                step={0.5}
                onChange={(value) => {
                  setTextLabelAnchorY(value as number);
                }}
                onChangeCommitted={(value) => {
                  const newStyle = JSON.parse(JSON.stringify(layer.properties)) || {};
                  const textLabel = TextLabelSchema.safeParse({
                    ...textLabelOptions,
                    offset: [textLabelAnchorX || 0, value as number],
                  });
                  if (textLabel.success) {
                    newStyle.text_label = textLabel.data;
                  }
                  onStyleChange?.(newStyle);
                }}
                isRange={false}
                rootSx={{
                  pl: 3,
                  pr: 2,
                }}
              />
            </Stack>

            {/* Allow overlap */}
            <Stack>
              <FormControlLabel
                control={
                  <Checkbox
                    size="small"
                    color="primary"
                    checked={textLabelOptions?.allow_overlap || false}
                    onChange={(e) => {
                      const allowOverlap = e.target.checked;
                      const newStyle = JSON.parse(JSON.stringify(layer.properties)) || {};
                      const textLabel = TextLabelSchema.safeParse({
                        ...textLabelOptions,
                        allow_overlap: allowOverlap,
                      });
                      if (textLabel.success) {
                        newStyle.text_label = textLabel.data;
                      }
                      onStyleChange?.(newStyle);
                    }}
                  />
                }
                label={<Typography variant="body2">{t("allow_overlap")}</Typography>}
              />
            </Stack>

            {/* { Outline color} */}
            <ColorSelector
              colorSet={{
                selectedColor: textLabelOptions?.outline_color || "#ffffff",
                isRange: false,
                setColor: (color) => {
                  const newStyle = JSON.parse(JSON.stringify(layer.properties)) || {};
                  const textLabel = TextLabelSchema.safeParse({
                    ...textLabelOptions,
                    outline_color: color,
                  });
                  if (textLabel.success) {
                    newStyle.text_label = textLabel.data;
                  }
                  onStyleChange?.(newStyle);
                },
              }}
              label={t("halo_color")}
            />

            {/* Outline Width  */}
            <Stack>
              <FormLabelHelper label={t("halo_width")} color="inherit" />
              <SliderInput
                value={textLabelOutlineWidth || textLabelOptions?.outline_width || 0}
                min={0}
                // max is 1/4 of the text label size
                max={(textLabelSize || textLabelOptions?.size || 0) / 4}
                step={1}
                onChange={(value) => {
                  setTextLabelOutlineWidth(value as number);
                }}
                onChangeCommitted={(value) => {
                  const newStyle = JSON.parse(JSON.stringify(layer.properties)) || {};
                  const textLabel = TextLabelSchema.safeParse({
                    ...textLabelOptions,
                    outline_width: value as number,
                  });
                  if (textLabel.success) {
                    newStyle.text_label = textLabel.data;
                  }
                  onStyleChange?.(newStyle);
                }}
                isRange={false}
                rootSx={{
                  pl: 3,
                  pr: 2,
                }}
              />
            </Stack>
          </>
        }
      />
    </>
  );
};

export default LabelOptions;
