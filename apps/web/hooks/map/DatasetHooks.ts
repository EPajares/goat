/* eslint-disable @typescript-eslint/no-explicit-any */
import { debounce } from "@mui/material";
import { useCallback, useMemo, useState } from "react";

import { useTranslation } from "@/i18n/client";

import { useLayerUniqueValues } from "@/lib/api/layers";
import type { GetLayerUniqueValuesQueryParams } from "@/lib/validations/layer";


export const useGetMetadataValueTranslation = () => {
  const { t, i18n } = useTranslation(["common", "countries"]);

  const getMetadataValueTranslation = useCallback(
    (key: string, value: string) => {
      if (!value) return " — ";
      let translationPath = `common:metadata.${key}.${value}`;
      if (key === "geographical_code") {
        translationPath = `countries:${value.toUpperCase()}`;
      }
      if (key === "language_code") {
        translationPath = `languages:${value}`;
      }

      return i18n.exists(translationPath) ? t(translationPath) : value;
    },
    [i18n, t]
  );

  return getMetadataValueTranslation;
};

type UseDatasetValueSelectorMethods = {
  selectedValues: string[] | null; // replace with the actual type of selectedValues
  onSelectedValuesChange: (values: string[] | null) => void; // replace with the actual type of onSelectedValuesChange
  fieldName: string;
  datasetId: string;
  cqlFilter?: object | undefined;
  onDone?: () => void;
};

export const useDatasetValueSelectorMethods = ({
  selectedValues,
  onSelectedValuesChange,
  fieldName,
  datasetId,
  cqlFilter,
  onDone,
}: UseDatasetValueSelectorMethods) => {
  const [searchText, setSearchText] = useState("");
  const [queryParams, setQueryParams] = useState<GetLayerUniqueValuesQueryParams>({
    size: 100,
    page: 1,
    order: "descendent",
    ...(cqlFilter ? { query: JSON.stringify(cqlFilter) } : {})
  });

  const _selectedValues = useMemo(() => selectedValues || [], [selectedValues]);

  const { data, isLoading } = useLayerUniqueValues(datasetId, fieldName, queryParams);
  const debouncedSetSearchText = debounce((value) => {
    let query: any = {
      op: "like",
      args: [
        {
          property: fieldName,
        },
        `%${value}%`,
      ],
    };
    if (cqlFilter) {
      query = {
        op: "and",
        args: [
          cqlFilter,
          {
            op: "like",
            args: [
              {
                property: fieldName,
              },
              `%${value}%`,
            ],
          },
        ],
      };
    }
    if (value !== "") {
      setQueryParams((params) => ({ ...params, query: JSON.stringify(query) }));
    } else {
      // Reset query based on cqlFilter presence
      if (cqlFilter) {
        setQueryParams((params) => ({
          ...params,
          query: JSON.stringify(cqlFilter),
        }));
      } else {
        setQueryParams((params) => {
          const { query: _, ...rest } = params;
          return rest;
        });
      }
    }
  }, 300);

  const handleClearText = () => {
    setSearchText("");
    if (cqlFilter) {
      setQueryParams((params) => ({
        ...params,
        query: JSON.stringify(cqlFilter),
      }));
    } else {
      setQueryParams((params) => {
        const { query: _, ...rest } = params;
        return rest;
      });
    }
  };

  const handleDelete = (value) => {
    const filtered = _selectedValues.filter((v) => v !== value);
    onSelectedValuesChange(filtered?.length > 0 ? filtered : null);
  };

  const handleClick = (item) => {
    const newValues = _selectedValues.includes(item.value)
      ? _selectedValues.filter((value) => value !== item.value)
      : [..._selectedValues, item.value];
    onSelectedValuesChange(newValues?.length > 0 ? newValues : null);
  };

  const handleClear = () => {
    onSelectedValuesChange(null);
  };

  const handleDone = () => {
    onDone && onDone();
  };

  return {
    data,
    isLoading,
    searchText,
    setSearchText,
    queryParams,
    setQueryParams,
    debouncedSetSearchText,
    handleClearText,
    handleDelete,
    handleClick,
    handleClear,
    handleDone,
  };
};
