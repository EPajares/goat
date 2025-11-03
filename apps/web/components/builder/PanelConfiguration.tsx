import { Button, Stack, Typography } from "@mui/material";
import { useEffect, useMemo, useState } from "react";

import { ICON_NAME } from "@p4b/ui/components/Icon";

import { useTranslation } from "@/i18n/client";

import type { BuilderPanelSchema } from "@/lib/validations/project";

import type { SelectorItem } from "@/types/map/common";

import FormLabelHelper from "@/components/common/FormLabelHelper";
import SectionHeader from "@/components/map/panels/common/SectionHeader";
import SectionOptions from "@/components/map/panels/common/SectionOptions";
import Selector from "@/components/map/panels/common/Selector";
import SliderInput from "@/components/map/panels/common/SliderInput";

interface PanelContainerProps {
  panel: BuilderPanelSchema;
  onDelete: () => void;
  onChange: (panel: BuilderPanelSchema) => void;
}

const ConfigSection = ({
  title,
  icon,
  children,
}: {
  title: string;
  icon: ICON_NAME;
  children: React.ReactNode;
}) => (
  <>
    <SectionHeader active alwaysActive label={title} icon={icon} disableAdvanceOptions />
    <SectionOptions active baseOptions={<>{children}</>} />
  </>
);

const PanelConfiguration = ({ panel, onDelete, onChange }: PanelContainerProps) => {
  const { t } = useTranslation("common");

  // Style configuration
  const panelStyle = useMemo(
    () => ({
      value: panel.config?.options?.style || "default",
      label: t(panel.config?.options?.style || "default"),
    }),
    [panel, t]
  );

  const panelStyleOptions = useMemo(
    () => [
      { value: "default", label: t("default") },
      { value: "rounded", label: t("rounded") },
      { value: "floated", label: t("floated") },
    ],
    [t]
  );

  // Alignment configuration
  const panelAlignItem = useMemo(
    () => ({
      value: panel.config?.position?.alignItems || "start",
      label: t(panel.config?.position?.alignItems || "start"),
    }),
    [panel, t]
  );

  const panelAlignItemOptions = useMemo(
    () => [
      { value: "start", label: t("start") },
      { value: "center", label: t("center") },
      { value: "end", label: t("end") },
    ],
    [t]
  );

  // State management
  const [opacity, setOpacity] = useState(panel.config?.appearance?.opacity ?? 1);
  const [backgroundBlur, setBackgroundBlur] = useState(panel.config?.appearance?.backgroundBlur ?? 0);
  const [shadow, setShadow] = useState(panel.config?.appearance?.shadow ?? 0);
  const [spacing, setSpacing] = useState(panel.config?.position?.spacing ?? 0);

  useEffect(() => {
    setOpacity(panel.config?.appearance?.opacity ?? 1);
    setBackgroundBlur(panel.config?.appearance?.backgroundBlur ?? 0);
    setShadow(panel.config?.appearance?.shadow ?? 0);
    setSpacing(panel.config?.position?.spacing ?? 0);
  }, [panel]);

  // Handlers
  const updateConfig = (path: string, value: unknown) => {
    const [root, ...rest] = path.split(".");
    onChange({
      ...panel,
      config: {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        ...((panel.config || {}) as any),
        [root]: rest.reduce(
          (acc, key, index) => ({
            ...acc,
            [key]: index === rest.length - 1 ? value : acc?.[key],
          }),
          panel.config?.[root] || {}
        ),
      },
    });
  };

  const renderSelector = (
    selectedItem: SelectorItem,
    options: SelectorItem[],
    label: string,
    configPath: string
  ) => (
    <Selector
      selectedItems={selectedItem}
      setSelectedItems={(item) => updateConfig(configPath, (item as SelectorItem).value)}
      items={options}
      label={label}
    />
  );

  const renderSlider = (
    label: string,
    value: number,
    configPath: string,
    min: number,
    max: number,
    step: number
  ) => (
    <Stack>
      <FormLabelHelper label={label} color="inherit" />
      <SliderInput
        value={value}
        isRange={false}
        rootSx={{ pl: 1, pt: 0, "&&": { mt: 0 } }}
        min={min}
        max={max}
        step={step}
        onChange={(val) => {
          if (typeof val === "number") {
            switch (configPath.split(".")[1]) {
              case "opacity":
                setOpacity(val);
                break;
              case "backgroundBlur":
                setBackgroundBlur(val);
                break;
              case "shadow":
                setShadow(val);
                break;
              case "spacing":
                setSpacing(val);
                break;
            }
          }
        }}
        onChangeCommitted={(val) => typeof val === "number" && updateConfig(configPath, val)}
      />
    </Stack>
  );

  return (
    <Stack direction="column" spacing={2} justifyContent="space-between">
      <Stack direction="column" spacing={3}>
        <ConfigSection title={t("options")} icon={ICON_NAME.SLIDERS}>
          {renderSelector(panelStyle, panelStyleOptions, t("select_panel_style"), "options.style")}
        </ConfigSection>

        <ConfigSection title={t("appearance")} icon={ICON_NAME.PANEL_APPERANCE}>
          {renderSlider(t("opacity"), opacity, "appearance.opacity", 0, 1, 0.1)}
          {renderSlider(t("background_blur"), backgroundBlur, "appearance.backgroundBlur", 0, 20, 1)}
          {renderSlider(t("shadow"), shadow, "appearance.shadow", 0, 10, 1)}
        </ConfigSection>

        <ConfigSection title={t("position")} icon={ICON_NAME.PANEL_POSITION}>
          {renderSelector(panelAlignItem, panelAlignItemOptions, t("align_items"), "position.alignItems")}
          {renderSlider(t("spacing"), spacing, "position.spacing", 0, 10, 1)}
        </ConfigSection>
      </Stack>

      <Button onClick={onDelete} fullWidth size="small" color="error">
        <Typography variant="body2" fontWeight="bold" color="inherit">
          {t("common:delete_panel")}
        </Typography>
      </Button>
    </Stack>
  );
};

export default PanelConfiguration;
