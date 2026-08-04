import { useCallback, useMemo, useState } from "react";

import { createTheCQLBasedOnExpression } from "@/lib/transformers/filter";
import { FilterType, type Expression } from "@/lib/validations/filter";

import type { TableFilterController } from "@/types/map/tableFilter";

type LayerField = { name: string; type: string; kind?: string };

/**
 * Filter controller for tables with nowhere to persist to — a dashboard table,
 * including a published one.
 *
 * Expressions live in component state and are ANDed onto whatever filter the
 * author configured. They are never written back to the project or the published
 * dashboard config, so a viewer narrowing a table cannot change what anyone else
 * sees.
 */
export const useTableViewFilterController = (
  layerFields: LayerField[],
  options?: { canEdit?: boolean }
) => {
  const [expressions, setExpressions] = useState<Expression[]>([]);

  const upsert = useCallback((expression: Expression) => {
    const withType = { ...expression, type: expression.type ?? FilterType.Logical };
    setExpressions((previous) => {
      const index = previous.findIndex((e) => e.id === withType.id);
      if (index < 0) return [...previous, withType];
      return previous.map((e) => (e.id === withType.id ? withType : e));
    });
  }, []);

  const remove = useCallback((id: string) => {
    setExpressions((previous) => previous.filter((e) => e.id !== id));
  }, []);

  const clear = useCallback(() => setExpressions([]), []);

  /** Stringified CQL for the items query, or undefined when nothing is filtered. */
  const cqlFilter = useMemo(() => {
    if (!expressions.length) return undefined;
    return JSON.stringify(createTheCQLBasedOnExpression(expressions, layerFields, "and"));
  }, [expressions, layerFields]);

  const controller = useMemo<TableFilterController>(
    () => ({
      expressions,
      logicalOperator: "and",
      upsert,
      remove,
      canEdit: options?.canEdit ?? true,
    }),
    [expressions, upsert, remove, options?.canEdit]
  );

  return { controller, cqlFilter, clear };
};

/** AND two stringified CQL filters, tolerating either being absent. */
export const combineCqlFilters = (...filters: Array<string | undefined>): string | undefined => {
  const present = filters.filter((filter): filter is string => !!filter);
  if (present.length === 0) return undefined;
  if (present.length === 1) return present[0];
  return JSON.stringify({ op: "and", args: present.map((filter) => JSON.parse(filter)) });
};

export default useTableViewFilterController;
