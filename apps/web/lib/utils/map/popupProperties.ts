import type { FormatNumberTypes } from "@/lib/validations/common";
import {
  type LayerInteractionFieldListContent,
  layerInteractionContentType,
} from "@/lib/validations/layer";

import type { MapPopoverInfoProps } from "@/types/map/popover";

/**
 * Internal columns that must never be shown to the user in a popup.
 */
const HIDDEN_SYSTEM_PROPERTIES = new Set([
  "layer_id",
  "id",
  "_rowid",
  "feature_id",
  "h3_3",
  "h3_6",
  "cluster",
  "clustered",
  "point_count",
  "point_count_abbreviated",
  "sqrt_point_count",
  "ags_gemeinde",
  "ags_landkreis",
]);

export function isSystemPropertyKey(key: string): boolean {
  return HIDDEN_SYSTEM_PROPERTIES.has(key);
}

/**
 * Split raw feature properties into the two buckets a feature popup consumes:
 * values that parse to a JSON object/array go to `jsonProperties` (rendered as
 * nested content), everything else stays a primitive property.
 */
export function splitPopupProperties(raw: Record<string, unknown> | undefined): {
  properties: NonNullable<MapPopoverInfoProps["properties"]>;
  jsonProperties: NonNullable<MapPopoverInfoProps["jsonProperties"]>;
} {
  const jsonProperties: Record<string, unknown> = {};
  const properties: Record<string, unknown> = {};
  if (raw) {
    for (const key in raw) {
      if (isSystemPropertyKey(key)) continue;
      const value = raw[key];
      try {
        const parsedValue = JSON.parse(value as string);
        if (typeof parsedValue === "object" && parsedValue !== null) {
          jsonProperties[key] = parsedValue;
        } else {
          throw new Error("Parsed value is not an object");
        }
      } catch {
        properties[key] = value;
      }
    }
  }
  return {
    properties: properties as NonNullable<MapPopoverInfoProps["properties"]>,
    jsonProperties: jsonProperties as NonNullable<MapPopoverInfoProps["jsonProperties"]>,
  };
}

/** A ProjectLayer/Layer as far as popup configuration is concerned. */
export type PopupConfigLayerLike = { properties?: unknown } | null | undefined;

export type PopupTrigger = "click" | "hover" | "click_and_hover";

/**
 * Resolve the effective popup trigger for a layer. Prefers the new `popup`
 * schema; falls back to the legacy `interaction.type` for layers that haven't
 * been migrated yet. `undefined` means "this layer shows no popup at all"
 * (explicitly disabled, or legacy `interaction.type === "none"`).
 *
 * Layers with no popup *and* no interaction config (e.g. layers freshly added
 * from the data explorer) default to "click" — same behavior as
 * `seedPopupFromInteraction`, so runtime interaction detection stays in sync
 * with what the renderer actually shows.
 */
export function getEffectivePopupTrigger(layer: PopupConfigLayerLike): PopupTrigger | undefined {
  const props =
    ((layer?.properties ?? undefined) as
      | {
          interaction?: { type?: string };
          popup?: { enabled?: boolean; trigger?: PopupTrigger };
        }
      | undefined) ?? {};
  const popup = props.popup;
  if (popup) {
    if (popup.enabled === false) return undefined;
    if (
      popup.trigger === "click" ||
      popup.trigger === "hover" ||
      popup.trigger === "click_and_hover"
    ) {
      return popup.trigger;
    }
  }
  // Legacy fallback: only `click` and `none` are wired in the existing
  // useInteractionOptions hook, so `hover` here is rare but accepted.
  if (props.interaction?.type === "click") return "click";
  if (props.interaction?.type === "hover") return "hover";
  if (props.interaction?.type === "none") return undefined;
  // Nothing configured at all → treat as clickable. Matches
  // seedPopupFromInteraction(undefined), which produces
  // `{ enabled: true, trigger: "click", ... }`.
  return "click";
}

export type PopupFieldConfig = {
  fieldOrder: string[];
  fieldLabels: Record<string, string>;
  fieldDecorators: Record<string, { prefix?: string; suffix?: string; format?: FormatNumberTypes }>;
  hasFieldList: boolean;
};

/**
 * Build field-list metadata (labels, order, decorators) from all `field_list`
 * interaction contents of a layer. Raw values stay keyed by column name so the
 * popup renderer can apply kind-aware formatting (e.g. m² → ha for area fields).
 */
export function buildPopupFieldConfig(layer: PopupConfigLayerLike): PopupFieldConfig {
  const interactionFieldLists = (
    layer?.properties as { interaction?: { content?: { type?: string }[] } } | undefined
  )?.interaction?.content?.filter(
    (content) => content.type === layerInteractionContentType.Enum.field_list
  ) as LayerInteractionFieldListContent[] | undefined;

  const fieldLabels: Record<string, string> = {};
  const fieldOrder: string[] = [];
  const fieldDecorators: Record<
    string,
    { prefix?: string; suffix?: string; format?: FormatNumberTypes }
  > = {};
  interactionFieldLists?.forEach((content) => {
    content.attributes.forEach((attr) => {
      if (fieldOrder.includes(attr.name)) return; // first definition wins
      fieldOrder.push(attr.name);
      fieldLabels[attr.name] = attr.label || attr.name;
      if (attr.format || attr.prefix || attr.suffix) {
        fieldDecorators[attr.name] = {
          format: attr.format as FormatNumberTypes | undefined,
          prefix: attr.prefix,
          suffix: attr.suffix,
        };
      }
    });
  });

  return { fieldOrder, fieldLabels, fieldDecorators, hasFieldList: fieldOrder.length > 0 };
}

/**
 * Narrow raw feature properties to the layer's configured field list. Layers
 * without a field list pass all properties through unchanged.
 */
export function selectPopupProperties(
  fieldConfig: PopupFieldConfig,
  raw: Record<string, unknown>
): Record<string, unknown> {
  if (!fieldConfig.hasFieldList) return raw;
  return fieldConfig.fieldOrder.reduce(
    (acc, name) => {
      if (!isSystemPropertyKey(name)) {
        acc[name] = raw[name];
      }
      return acc;
    },
    {} as Record<string, unknown>
  );
}

/**
 * The `fieldLabels` / `fieldOrder` / `fieldDecorators` slice of a `setPopupInfo`
 * payload, empty when the layer has no field list configured.
 */
export function popupFieldInfo(fieldConfig: PopupFieldConfig): {
  fieldLabels?: Record<string, string>;
  fieldOrder?: string[];
  fieldDecorators?: Record<
    string,
    { prefix?: string; suffix?: string; format?: FormatNumberTypes }
  >;
} {
  if (!fieldConfig.hasFieldList) return {};
  return {
    fieldLabels: fieldConfig.fieldLabels,
    fieldOrder: fieldConfig.fieldOrder,
    ...(Object.keys(fieldConfig.fieldDecorators).length > 0 && {
      fieldDecorators: fieldConfig.fieldDecorators,
    }),
  };
}
