import { useMemo } from "react";

import { useTranslation } from 'react-i18next'

import type { SelectorItem } from "@/types/map/common";

const useLogicalExpressionOperations = (
  selectedField?: "string" | "number" | "date" | "boolean" | "object"
) => {
  const { t } = useTranslation("common");
  const logicalExpressionTypes: SelectorItem[] = useMemo(() => {
    const baseItems = [
      {
        label: t("filter_expressions.is"),
        value: "is",
      },
      {
        label: t("filter_expressions.is_not"),
        value: "is_not",
      },
      {
        label: t("filter_expressions.includes"),
        value: "includes",
      },
      {
        label: t("filter_expressions.excludes"),
        value: "excludes",
      },
      {
        label: t("filter_expressions.is_blank"),
        value: "is_blank",
      },
      {
        label: t("filter_expressions.is_not_blank"),
        value: "is_not_blank",
      },
    ];
    if (selectedField === "number") {
      return [
        ...baseItems,
        {
          label: t("filter_expressions.is_at_least"),
          value: "is_at_least",
        },
        {
          label: t("filter_expressions.is_less_than"),
          value: "is_less_than",
        },
        {
          label: t("filter_expressions.is_at_most"),
          value: "is_at_most",
        },
        {
          label: t("filter_expressions.is_greater_than"),
          value: "is_greater_than",
        },
        {
          label: t("filter_expressions.is_between"),
          value: "is_between",
        },
      ];
    } else if (selectedField === "string") {
      return [
        ...baseItems,
        {
          label: t("filter_expressions.starts_with"),
          value: "starts_with",
        },
        {
          label: t("filter_expressions.ends_with"),
          value: "ends_with",
        },
        {
          label: t("filter_expressions.contains_the_text"),
          value: "contains_the_text",
        },
        {
          label: t("filter_expressions.does_not_contains_the_text"),
          value: "does_not_contains_the_text",
        },
        {
          label: t("filter_expressions.is_empty_string"),
          value: "is_empty_string",
        },
        {
          label: t("filter_expressions.is_not_empty_string"),
          value: "is_not_empty_string",
        },
      ];
    } else if (selectedField === "date") {
      return [
        {
          label: t("filter_expressions.is_on"),
          value: "is_on",
        },
        {
          label: t("filter_expressions.is_not_on"),
          value: "is_not_on",
        },
        {
          label: t("filter_expressions.is_before"),
          value: "is_before",
        },
        {
          label: t("filter_expressions.is_after"),
          value: "is_after",
        },
        {
          label: t("filter_expressions.in_the_last"),
          value: "in_the_last",
        },
        {
          label: t("filter_expressions.not_in_the_last"),
          value: "not_in_the_last",
        },
        {
          label: t("filter_expressions.is_between"),
          value: "is_between",
        },
        {
          label: t("filter_expressions.is_not_between"),
          value: "is_not_between",
        },
      ];
    } else {
      return baseItems;
    }
  }, [selectedField, t]);

  return { logicalExpressionTypes };
};

export default useLogicalExpressionOperations;
