import type { WidgetChartConfig } from "@/lib/validations/widget";

export type ChartDataConfigurationProps = {
  config: WidgetChartConfig;
  onChange: (config: WidgetChartConfig) => void;
};
