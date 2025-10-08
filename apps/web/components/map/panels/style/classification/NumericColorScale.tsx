import { Box, Grid, MenuItem, Select, Stack, TextField, Typography, useTheme } from "@mui/material";
import { useMemo } from "react";
import { useTranslation } from "react-i18next";

import { formatNumber } from "@/lib/utils/helpers";
import type { ClassBreaks, ColorMap, ColorRange } from "@/lib/validations/layer";
import { classBreaks } from "@/lib/validations/layer";

import type { ColorScaleSelectorProps } from "@/types/map/color";

type NumericColorScaleProps = ColorScaleSelectorProps & {
  setIsClickAwayEnabled: (isClickAwayEnabled: boolean) => void;
  onCancel?: () => void;
};

const NumericColorScale = (props: NumericColorScaleProps) => {
  const theme = useTheme();
  const { classBreaksValues } = props;
  const { t } = useTranslation("common");

  const colorMapValues = useMemo(() => {
    if (!classBreaksValues || !Array.isArray(classBreaksValues.breaks)) {
      return [];
    }
    const intervalValues: ColorMap = [];
    const staticColor = "#000000";
    classBreaksValues.breaks.forEach((value, index) => {
      const colors = (props.colorSet.selectedColor as ColorRange).colors;
      const color = colors[index] !== undefined ? colors[index] : staticColor;
      const roundedValue = formatNumber(value, 2).toString();
      intervalValues.push([[roundedValue], color]);
      if (index === classBreaksValues.breaks.length - 1) {
        intervalValues.push([null, colors[index + 1] !== undefined ? colors[index + 1] : staticColor]);
      }
    });

    return intervalValues;
  }, [classBreaksValues, props.colorSet.selectedColor]);

  return (
    <Box sx={{ p: 3 }}>
      <Select
        fullWidth
        size="small"
        IconComponent={() => null}
        value={props.selectedColorScaleMethod}
        onOpen={() => {
          props.setIsClickAwayEnabled && props.setIsClickAwayEnabled(false);
        }}
        MenuProps={{
          TransitionProps: {
            onExited: () => {
              props.setIsClickAwayEnabled && props.setIsClickAwayEnabled(true);
            },
          },
        }}
        onChange={(e) => {
          props.setSelectedColorScaleMethod(e.target.value as ClassBreaks);
        }}>
        {classBreaks.options.map((option, index) => (
          <MenuItem key={index} value={String(option)}>
            {t(`${option}`)}
          </MenuItem>
        ))}
      </Select>
      <Stack direction="row" justifyContent="space-between" alignItems="center" py={2}>
        <Typography variant="caption">
          Min: <b>{classBreaksValues?.min ? formatNumber(classBreaksValues?.min) : ""}</b>
        </Typography>
        <Typography variant="caption">
          Max: <b>{classBreaksValues?.max ? formatNumber(classBreaksValues?.max) : ""}</b>
        </Typography>
      </Stack>
      <Box sx={{ maxHeight: "240px", overflowY: "auto", pt: 2 }}>
        <Grid container alignItems="center" justifyContent="center" spacing={2}>
          {colorMapValues &&
            colorMapValues.map((colorMapValue, index) => (
              <>
                <Grid item xs={2} key={`color_${colorMapValues[index][1]}`}>
                  <div
                    style={{
                      borderRadius: "4px",
                      width: "32px",
                      height: "20px",
                      backgroundColor: colorMapValue[1],
                    }}
                  />
                </Grid>
                <Grid item xs={10} key={`color_${colorMapValues[index][0]}`}>
                  <Stack justifyContent="end" alignItems="center" spacing={1} direction="row" sx={{ px: 2 }}>
                    <TextField
                      margin="dense"
                      value={index === 0 ? `<${classBreaksValues?.min}` : colorMapValues[index - 1][0]}
                      disabled
                      InputProps={{ sx: { height: "32px" } }}
                      sx={{
                        "& .MuiOutlinedInput-input": {
                          padding: `0 ${theme.spacing(2)}`,
                        },
                      }}
                    />
                    <Typography>-</Typography>
                    <TextField
                      margin="dense"
                      value={
                        colorMapValues[index][0] === null
                          ? `>${classBreaksValues?.max}`
                          : colorMapValues[index][0]
                      }
                      disabled
                      InputProps={{ sx: { height: "32px" } }}
                      sx={{
                        "& .MuiOutlinedInput-input": {
                          padding: `0 ${theme.spacing(2)}`,
                        },
                      }}
                    />
                  </Stack>
                </Grid>
              </>
            ))}
        </Grid>
      </Box>
      <Stack sx={{ pt: 4 }}>
        <Typography variant="caption">{t("common:change_colors_and_steps")}</Typography>
      </Stack>
    </Box>
  );
};

export default NumericColorScale;
