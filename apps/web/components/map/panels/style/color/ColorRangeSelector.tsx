// Copyright (c) 2023 Uber Technologies, Inc; Plan4Better GmbH
//
// Permission is hereby granted, free of charge, to any person obtaining a copy
// of this software and associated documentation files (the "Software"), to deal
// in the Software without restriction, including without limitation the rights
// to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
// copies of the Software, and to permit persons to whom the Software is
// furnished to do so, subject to the following conditions:
//
// The above copyright notice and this permission notice shall be included in
// all copies or substantial portions of the Software.
//
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
// IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
// FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
// AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
// LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
// OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
// THE SOFTWARE.
import { MenuItem, Select, Stack, Switch, Tooltip, Typography } from "@mui/material";
// eslint-disable-next-line you-dont-need-lodash-underscore/uniq
import uniq from "lodash.uniq";
import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";

import { COLOR_RANGES } from "@/lib/constants/color";
import { numberSort } from "@/lib/utils/helpers";
import type { ColorRange } from "@/lib/validations/layer";

import ColorPaletteGroup from "@/components/map/panels/style/color/ColorPaletteGroup";
import CustomPalette from "@/components/map/panels/style/color/CustomPalette";

type ColorRangeSelectorProps = {
  selectedColorRange: ColorRange;
  onSelectColorRange: (p: ColorRange) => void;
  scaleType?: string;
  setIsBusy?: (p: boolean) => void;
  setIsOpen?: (p: boolean) => void;
};

export const ALL_TYPES: string[] = uniq(
  COLOR_RANGES.map((c) => c.type)
    .filter((ctype) => ctype)
    .concat(["all"]) as string[]
);

export const ALL_STEPS: number[] = uniq(COLOR_RANGES.map((d) => d.colors.length)).sort(numberSort);

const CONFIG_SETTINGS = {
  type: {
    type: "select",
    options: ALL_TYPES,
  },
  steps: {
    type: "select",
    options: ALL_STEPS,
  },
  reversed: {
    type: "switch",
    options: [true, false],
  },
  custom: {
    label: "custom_palette",
    type: "switch",
    options: [true, false],
  },
};

type PaletteConfigProps = {
  disabled?: boolean;
  label: string;
  value: string | number | boolean;
  config: {
    type: string;
    options: (string | number | boolean)[];
  };
  onChange: (v: string | number | boolean | object | null) => void;
  setIsBusy?: (p: boolean) => void;
};

const PaletteConfig = (props: PaletteConfigProps) => {
  const { label, value, config, onChange, disabled } = props;
  const { t } = useTranslation("common");
  return (
    <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ pl: 4, pr: 3 }}>
      <Typography variant="body2">{t(`${label}`)}</Typography>
      {config.type === "select" && (
        <Tooltip title={t("steps_disabled_tooltip")} placement="left" disableHoverListener={!disabled}>
          <Select
            disabled={disabled}
            size="small"
            IconComponent={() => null}
            value={value as string}
            onOpen={() => {
              props.setIsBusy && props.setIsBusy(true);
            }}
            MenuProps={{
              TransitionProps: {
                onExited: () => {
                  props.setIsBusy && props.setIsBusy(false);
                },
              },
            }}
            onChange={(e) => {
              onChange(e.target.value);
            }}>
            {config.options.map((option, index) => (
              <MenuItem key={index} value={String(option)}>
                {t(`${option}`)}
              </MenuItem>
            ))}
          </Select>
        </Tooltip>
      )}
      {config.type === "switch" && (
        <Tooltip title={t("steps_disabled_tooltip")} placement="left" disableHoverListener={!disabled}>
          <div>
            <Switch
              disabled={disabled}
              checked={value as boolean}
              id={`${label}-toggle`}
              onChange={() => onChange(!value)}
              size="small"
            />
          </div>
        </Tooltip>
      )}
    </Stack>
  );
};

const ColorRangeSelector = (props: ColorRangeSelectorProps) => {
  const { selectedColorRange, onSelectColorRange } = props;

  const [colorRangeConfig, setColorRangeConfig] = useState({
    type:
      ["ordinal", "custom_breaks"].includes(props.scaleType as string) || selectedColorRange.type === "custom"
        ? "all"
        : selectedColorRange.type,
    steps: selectedColorRange.colors.length || 6,
    reversed: selectedColorRange.reversed || false,
    custom: selectedColorRange.type === "custom",
  });

  const filteredColorRange = useMemo(() => {
    return COLOR_RANGES.filter((colorRange) => {
      const isType = colorRangeConfig.type === "all" || colorRangeConfig.type === colorRange.type;
      const isStep = Number(colorRangeConfig.steps) === colorRange.colors.length;

      return isType && isStep;
    });
  }, [colorRangeConfig]);

  return (
    <Stack spacing={2}>
      {(colorRangeConfig.custom && !["ordinal", "custom_breaks"].includes(props.scaleType as string)
        ? ["custom"]
        : Object.keys(colorRangeConfig)
      ).map((key) => (
        <PaletteConfig
          disabled={
            ["ordinal", "custom_breaks"].includes(props.scaleType as string) &&
            ["steps", "custom"].includes(key)
          }
          key={key}
          label={CONFIG_SETTINGS[key].label || key}
          config={CONFIG_SETTINGS[key]}
          value={colorRangeConfig[key]}
          onChange={(value) => {
            setColorRangeConfig({
              ...colorRangeConfig,
              [key]: value,
            });
          }}
          setIsBusy={props.setIsBusy}
        />
      ))}
      {colorRangeConfig.custom && !["ordinal", "custom_breaks"].includes(props.scaleType as string) ? (
        <CustomPalette
          onApply={(colorRange: ColorRange) => {
            onSelectColorRange(colorRange);
            props.setIsOpen && props.setIsOpen(false);
          }}
          onCancel={() => {
            props.setIsOpen && props.setIsOpen(false);
          }}
          customPalette={selectedColorRange}
        />
      ) : (
        <ColorPaletteGroup
          colorRanges={filteredColorRange}
          onSelect={onSelectColorRange}
          selected={selectedColorRange}
          reversed={colorRangeConfig.reversed}
        />
      )}
    </Stack>
  );
};

export default ColorRangeSelector;
