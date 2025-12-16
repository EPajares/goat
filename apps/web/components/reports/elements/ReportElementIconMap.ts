import { ICON_NAME } from "@p4b/ui/components/Icon";

import type { ReportElementType } from "@/lib/validations/reportLayout";

// Map report element types to their icons - matching builder widget icons
export const reportElementIconMap: Record<ReportElementType, ICON_NAME> = {
  map: ICON_NAME.MAP,
  chart: ICON_NAME.CHART, // Legacy
  histogram_chart: ICON_NAME.VERTICAL_BAR_CHART,
  categories_chart: ICON_NAME.HORIZONTAL_BAR_CHART,
  pie_chart: ICON_NAME.CHART_PIE,
  text: ICON_NAME.TEXT,
  image: ICON_NAME.IMAGE,
  legend: ICON_NAME.LEGEND,
  scalebar: ICON_NAME.RULER_HORIZONTAL,
  north_arrow: ICON_NAME.LOCATION_CROSSHAIRS,
  table: ICON_NAME.TABLE,
  divider: ICON_NAME.DIVIDER,
  qr_code: ICON_NAME.BOUNDING_BOX,
  metadata: ICON_NAME.INFO,
};
