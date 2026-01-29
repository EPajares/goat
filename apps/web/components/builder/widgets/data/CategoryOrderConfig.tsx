import { Typography } from "@mui/material";
import { useMemo } from "react";
import { useTranslation } from "react-i18next";

import { useLayerUniqueValues } from "@/lib/api/layers";

import OrderableList from "@/components/builder/widgets/common/OrderableList";

import { MAX_FILTER_VALUES } from "./useFilterValues";

export interface CategoryOrderConfigProps {
  layerId: string | undefined;
  fieldName: string | undefined;
  customOrder: string[] | undefined;
  onOrderChange: (order: string[]) => void;
  cqlFilter?: object;
}

/**
 * Configuration panel for ordering and filtering layer field categories.
 * Fetches unique values from a layer field and allows reordering/filtering them.
 */
const CategoryOrderConfig = ({
  layerId,
  fieldName,
  customOrder,
  onOrderChange,
  cqlFilter,
}: CategoryOrderConfigProps) => {
  const { t } = useTranslation("common");

  const queryParams = useMemo(
    () => ({
      size: 100,
      page: 1,
      order: "descendent" as const,
      ...(cqlFilter ? { query: JSON.stringify(cqlFilter) } : {}),
    }),
    [cqlFilter]
  );

  const { data, isLoading } = useLayerUniqueValues(
    layerId || "",
    fieldName || "",
    layerId && fieldName ? queryParams : undefined
  );

  const totalValuesCount = data?.items?.length || 0;
  const hasMoreThanLimit = totalValuesCount > MAX_FILTER_VALUES;

  // All available values from the data
  const allValues = useMemo(() => {
    const values = data?.items?.map((item) => item.value) || [];
    return values.slice(0, MAX_FILTER_VALUES);
  }, [data?.items]);

  if (!layerId || !fieldName) {
    return (
      <Typography variant="caption" color="text.secondary" sx={{ fontStyle: "italic" }}>
        {t("select_dataset_and_field_first")}
      </Typography>
    );
  }

  return (
    <OrderableList
      allItems={allValues}
      visibleItems={customOrder}
      onOrderChange={onOrderChange}
      isLoading={isLoading}
      warningMessage={
        hasMoreThanLimit
          ? t("filter_limit_warning", { count: MAX_FILTER_VALUES, total: totalValuesCount })
          : undefined
      }
      addLabel={t("add_category")}
      addPlaceholder={t("select_category")}
      emptyMessage={t("no_values_found")}
    />
  );
};

export default CategoryOrderConfig;
