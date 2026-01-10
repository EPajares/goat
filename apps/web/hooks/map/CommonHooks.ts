import { useMemo } from "react";

import { useLayerQueryables } from "@/lib/api/layers";

type PseudoFieldName = "$area" | "$length" | "$perimeter";

interface PseudoField {
  name: PseudoFieldName;
  type: "string" | "number" | "object";
}

const useLayerFields = (
  dataset_id: string,
  filterType?: "string" | "number" | undefined,
  hiddenFields: string[] = ["layer_id", "id", "h3_3", "h3_6", "geom", "geometry"],
  includePseudoFields: boolean = false
) => {
  const { queryables, isLoading, isError } = useLayerQueryables(dataset_id || "");

  const layerFields = useMemo(() => {
    if (!queryables || !dataset_id) return [];

    // Get fields from queryables
    // API returns "integer" for int columns, normalize to "number" for frontend
    const normalizeType = (type: string) => (type === "integer" ? "number" : type);

    const queryableFields = Object.entries(queryables.properties)
      .filter(([key, value]) => {
        if (hiddenFields.includes(key)) {
          return false;
        }
        const normalizedType = normalizeType(value.type);
        if (filterType) {
          return normalizedType === filterType;
        } else {
          return normalizedType === "string" || normalizedType === "number" || normalizedType === "object";
        }
      })
      .map(([key, value]) => {
        return {
          name: key,
          type: normalizeType(value.type),
        };
      });

    // Determine pseudo fields based on geometry type
    let pseudoFields: PseudoField[] = [];

    if (includePseudoFields && queryables.properties?.geom) {
      const geomRef = queryables.properties.geom?.$ref;

      if (geomRef) {
        // Check for Polygon or MultiPolygon
        if (geomRef.includes("Polygon")) {
          pseudoFields = [{ name: "$area", type: "number" }];
        }
        // Check for LineString or MultiLineString
        else if (geomRef.includes("LineString")) {
          pseudoFields = [{ name: "$length", type: "number" }];
        }
        // Point or MultiPoint - no pseudo fields
      }
    }

    // Filter pseudo fields based on filterType if specified
    const filteredPseudoFields = pseudoFields.filter((field) => {
      if (filterType) {
        return field.type === filterType;
      }
      return true;
    });

    // Combine queryable fields with pseudo fields
    return [...queryableFields, ...filteredPseudoFields];
  }, [dataset_id, filterType, queryables, hiddenFields, includePseudoFields]);

  return {
    layerFields,
    isLoading,
    isError,
  };
};

export default useLayerFields;
export type { PseudoField, PseudoFieldName };
