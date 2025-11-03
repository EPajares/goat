import { ICON_NAME } from "@p4b/ui/components/Icon";

import type { WidgetTypes } from "@/lib/validations/widget";
import { chartTypes, dataTypes, elementTypes, informationTypes } from "@/lib/validations/widget";

type IconMap = {
    [K in WidgetTypes]: ICON_NAME;
};

export const iconMap: IconMap = {
    // informationTypes
    [informationTypes.enum.layers]: ICON_NAME.LAYERS,
    [informationTypes.enum.bookmarks]: ICON_NAME.BOOKMARK,
    [informationTypes.enum.comments]: ICON_NAME.COMMENT,

    // dataTypes
    [dataTypes.enum.filter]: ICON_NAME.FILTER,
    [dataTypes.enum.table]: ICON_NAME.TABLE,
    [dataTypes.enum.numbers]: ICON_NAME.NUMBER,
    [dataTypes.enum.feature_list]: ICON_NAME.LIST,

    // chartTypes
    [chartTypes.enum.categories_chart]: ICON_NAME.HORIZONTAL_BAR_CHART,
    [chartTypes.enum.histogram_chart]: ICON_NAME.VERTICAL_BAR_CHART,
    [chartTypes.enum.pie_chart]: ICON_NAME.CHART_PIE,

    // elementTypes
    [elementTypes.enum.text]: ICON_NAME.FONT,
    [elementTypes.enum.divider]: ICON_NAME.DIVIDER,
    [elementTypes.enum.image]: ICON_NAME.IMAGE,
};
