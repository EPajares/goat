import {
  Box,
  Button,
  Checkbox,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Divider,
  FormControlLabel,
  Stack,
  Typography,
  useTheme,
} from "@mui/material";
import { useParams } from "next/navigation";
import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";

import { ICON_NAME } from "@p4b/ui/components/Icon";
import { Loading } from "@p4b/ui/components/Loading";

import { useProjectLayerChartData } from "@/lib/api/projects";
import type { ProjectLayer } from "@/lib/validations/project";

import type { SelectorItem } from "@/types/map/common";

import useLayerFields from "@/hooks/map/CommonHooks";

import EmptySection from "@/components/common/EmptySection";
import FormLabelHelper from "@/components/common/FormLabelHelper";
import { Plot } from "@/components/common/PlotlyPlot";
import Selector from "@/components/map/panels/common/Selector";

type MapLayerChartDialogProps = {
  open: boolean;
  onClose: () => void;
  layer: ProjectLayer;
  projectId: string;
};

const MapLayerChartModal: React.FC<MapLayerChartDialogProps> = ({ open, onClose, layer, projectId }) => {
  const { t } = useTranslation("common");
  const theme = useTheme();
  const params = useParams();
  const [cumSum, setCumSum] = useState(false);
  const { chartData, isLoading, isError } = useProjectLayerChartData(projectId, layer.id, cumSum);
  const { layerFields: fields, isLoading: areFieldsLoading } = useLayerFields(layer.layer_id, undefined);

  const chartTypes: SelectorItem[] = useMemo(() => {
    return [
      {
        label: t("vertical_bar_chart"),
        value: "vertical_bar",
        icon: ICON_NAME.VERTICAL_BAR_CHART,
      },
      {
        label: t("horizontal_bar_chart"),
        value: "horizontal_bar",
        icon: ICON_NAME.HORIZONTAL_BAR_CHART,
      },
      {
        label: t("line_chart"),
        value: "line",
        icon: ICON_NAME.LINE_CHART,
      },
    ];
  }, [t]);

  const [selectedChartType, setSelectedChartType] = useState<SelectorItem | undefined>(chartTypes[0]);

  const lng = typeof params.lng === "string" ? params.lng : "en";
  const [chartType, setChartType] = useState<"bar" | "line">("bar");
  const [orientation, setOrientation] = useState<"v" | "h">("v");

  const chartLabelConfig = useMemo(() => {
    if (!layer.charts || !chartData) return {};
    let x = layer.charts["x_label"];
    let y = layer.charts["y_label"];
    let xTitle = x;
    let yTitle = cumSum ? `${y} (cumsum)` : y;
    const grouped = chartData["group"];
    if (chartType === "bar" && orientation === "h") {
      [x, y] = [y, x];
      [xTitle, yTitle] = [yTitle, xTitle];
    }
    const xFieldType = fields.find((field) => field.name === x)?.type;
    const yFieldType = fields.find((field) => field.name === y)?.type;
    const config = {
      xaxis: {
        type: xFieldType === "string" ? "category" : undefined,
        title: xTitle,
      },
      yaxis: {
        type: yFieldType === "string" ? "category" : undefined,
        title: yTitle,
      },
      title: `${xTitle} vs ${yTitle}`,
    };
    if (grouped) {
      config["barmode"] = "stack";
    }
    return config;
  }, [chartData, chartType, cumSum, fields, layer.charts, orientation]);

  const chartDataConfig = useMemo(() => {
    if (!chartData) return [];
    let x = chartData["x"];
    let y = chartData["y"];
    if (chartType === "bar" && orientation === "h") {
      [x, y] = [y, x];
    }
    const grouped = chartData["group"];
    if (grouped) {
      return grouped.map((group, index) => {
        return {
          type: chartType,
          x: x[index],
          y: y[index],
          name: group,
          orientation: chartType === "bar" ? orientation : undefined,
        };
      });
    } else {
      return [
        {
          type: chartType,
          x: x,
          y: y,
          orientation: chartType === "bar" ? orientation : undefined,
        },
      ];
    }
  }, [chartData, chartType, orientation]);

  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="md">
      <DialogTitle>{`${layer.name} - ${t("chart")}`}</DialogTitle>
      <Divider />
      <DialogContent sx={{ px: 2, pt: 0, mt: 0, pb: 0 }}>
        <Box>
          {chartData && fields && layer.charts && (
            <Stack sx={{ p: 2 }}>
              <Selector
                selectedItems={selectedChartType}
                setSelectedItems={(item: SelectorItem) => {
                  setSelectedChartType(item);
                  if (item.value === "vertical_bar") {
                    setChartType("bar");
                    setOrientation("v");
                  }
                  if (item.value === "horizontal_bar") {
                    setChartType("bar");
                    setOrientation("h");
                  }
                  if (item.value === "line") {
                    setChartType("line");
                  }
                }}
                items={chartTypes}
                label={t("select_chart_type")}
                placeholder="Test"
              />
              <Divider />
              <FormLabelHelper label={t("settings")} color="inherit" />
              <FormControlLabel
                control={
                  <Checkbox
                    size="small"
                    checked={cumSum}
                    onChange={(e) => setCumSum(e.target.checked)}
                    color="primary"
                  />
                }
                label={
                  <Typography variant="body2" fontWeight="bold">
                    {t("cumsum")}
                  </Typography>
                }
              />
              <Divider />
            </Stack>
          )}
          {isError && <EmptySection icon={ICON_NAME.CIRCLEINFO} label={t("error_loading_chart_data")} />}{" "}
          {(isLoading || areFieldsLoading) && (
            <Box
              sx={{
                display: "flex",
                justifyContent: "center",
                alignItems: "center",
              }}>
              <Loading size={40} />
            </Box>
          )}
          {!chartData && !isLoading && !isError && (
            <EmptySection icon={ICON_NAME.DATABASE} label={t("no_chart_data")} />
          )}
          {chartData && fields && layer.charts && (
            <Plot
              data={chartDataConfig}
              layout={{
                paper_bgcolor: "transparent",
                plot_bgcolor: "transparent",
                font: {
                  color: theme.palette.text.primary,
                },
                modebar: {
                  bgcolor: "transparent",
                  color: theme.palette.text.primary,
                  activecolor: theme.palette.primary.main,
                },
                ...chartLabelConfig,
              }}
              config={
                lng === "de"
                  ? {
                      locale: "de",
                      toImageButtonOptions: {
                        filename: `${layer.name}_chart`,
                        format: "png",
                      },
                    }
                  : {
                      toImageButtonOptions: {
                        filename: `${layer.name}_chart`,
                        format: "png",
                      },
                    }
              }
            />
          )}
        </Box>
      </DialogContent>
      <DialogActions
        disableSpacing
        sx={{
          pb: 2,
        }}>
        <Button onClick={onClose} variant="text" sx={{ borderRadius: 0 }}>
          <Typography variant="body2" fontWeight="bold">
            {t("cancel")}
          </Typography>
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default MapLayerChartModal;
