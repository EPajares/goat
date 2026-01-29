import { useMemo } from "react";

import { useLayerUniqueValues } from "@/lib/api/layers";

export const MAX_FILTER_VALUES = 20;

interface UseFilterValuesParams {
  layerId: string;
  fieldName: string;
  customOrder?: string[];
  cqlFilter?: object;
}

export const useFilterValues = ({ layerId, fieldName, customOrder, cqlFilter }: UseFilterValuesParams) => {
  const queryParams = useMemo(
    () => ({
      size: 100,
      page: 1,
      order: "descendent" as const,
      ...(cqlFilter ? { query: JSON.stringify(cqlFilter) } : {}),
    }),
    [cqlFilter]
  );

  const { data, isLoading } = useLayerUniqueValues(layerId, fieldName, queryParams);

  // Check if there are more values than the limit
  const totalValuesCount = data?.items?.length || 0;
  const hasMoreThanLimit = totalValuesCount > MAX_FILTER_VALUES;

  const allValues = useMemo(() => {
    const dataValues = data?.items?.map((item) => item.value) || [];

    // Apply custom order if provided
    let orderedValues: string[];
    if (customOrder === undefined) {
      // No custom order set - show all values in default order
      orderedValues = dataValues;
    } else if (customOrder.length === 0) {
      // Empty array means user explicitly removed all - show nothing
      orderedValues = [];
    } else {
      // Custom order set - filter and order by it
      // Only show values that are in customOrder AND exist in data
      orderedValues = customOrder.filter((v) => dataValues.includes(v));
    }

    // Limit to MAX_FILTER_VALUES
    return orderedValues.slice(0, MAX_FILTER_VALUES);
  }, [data?.items, customOrder]);

  return {
    allValues,
    isLoading,
    totalValuesCount,
    hasMoreThanLimit,
  };
};
