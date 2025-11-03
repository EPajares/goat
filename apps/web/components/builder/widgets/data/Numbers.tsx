import { Stack, Typography, useTheme } from "@mui/material";
import { useMemo } from "react";
import { useTranslation } from "react-i18next";

import { ICON_NAME, Icon } from "@p4b/ui/components/Icon";

import { useProjectLayerAggregationStats } from "@/lib/api/projects";
import { formatNumber } from "@/lib/utils/format-number";
import type { AggregationStatsQueryParams } from "@/lib/validations/project";
import { type ProjectLayer, aggregationStatsQueryParams } from "@/lib/validations/project";
import { type NumbersDataSchema, numbersDataConfigSchema } from "@/lib/validations/widget";

import { useChartWidget } from "@/hooks/map/DashboardBuilderHooks";

import { StaleDataLoader } from "@/components/builder/widgets/common/StaleDataLoader";
import { WidgetStatusContainer } from "@/components/builder/widgets/common/WidgetStatusContainer";

interface NumbersDataProps {
  config: NumbersDataSchema;
  projectLayers: ProjectLayer[];
  viewOnly?: boolean;
}

export const NumbersDataWidget = ({ config: rawConfig }: NumbersDataProps) => {
  const { i18n } = useTranslation("common");
  const theme = useTheme();
  const { config, queryParams, projectId } = useChartWidget(
    rawConfig,
    numbersDataConfigSchema,
    aggregationStatsQueryParams
  );

  const { aggregationStats, isLoading, isError } = useProjectLayerAggregationStats(
    projectId,
    config?.setup?.layer_project_id,
    queryParams as AggregationStatsQueryParams
  );

  const displayValue = useMemo(() => {
    return aggregationStats?.items?.[0]?.operation_value || 0;
  }, [aggregationStats]);

  const renderIcon = useMemo(() => {
    const icon = config?.setup?.icon;
    if (!icon) return null;
    // Check if the icon is a URL
    if (typeof icon === "string" && (icon.startsWith("http://") || icon.startsWith("https://"))) {
      const isSvg = icon.endsWith(".svg");
      return (
        <img
          src={icon}
          alt="icon"
          style={{
            width: 40,
            height: 40,
            ...(isSvg &&
              theme.palette.mode === "dark" && {
                filter: "invert(100%) brightness(200%)", // Makes the SVG white in dark mode
              }),
          }}
        />
      );
    }
    // Check if the icon is included in ICON_NAME
    if (typeof icon === "string" && Object.values(ICON_NAME).includes(icon as ICON_NAME)) {
      return <Icon iconName={icon as ICON_NAME} fontSize="large" />;
    }
    // If the icon is neither a valid URL nor in ICON_NAME, don't render anything
    return null;
  }, [config?.setup?.icon, theme.palette.mode]);

  const isWidgetConfigured = useMemo(() => {
    return config?.setup?.layer_project_id && queryParams;
  }, [config, queryParams]);

  return (
    <>
      <WidgetStatusContainer
        isLoading={isLoading && !aggregationStats && !isError}
        isNotConfigured={!isWidgetConfigured}
        isError={isError}
        height={100}
      />

      {config && !isError && aggregationStats && isWidgetConfigured && (
        <Stack direction="row" spacing={4} alignItems="center">
          {renderIcon}
          <Typography variant="h4" fontWeight="bold">
            {formatNumber(displayValue, config.options?.format, i18n.language)}
          </Typography>
        </Stack>
      )}

      <StaleDataLoader isLoading={isLoading} hasData={!!aggregationStats} />
    </>
  );
};
