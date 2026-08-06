import { Delete as DeleteIcon } from "@mui/icons-material";
import { IconButton, Link, Stack, Switch, TextField, Typography, useTheme } from "@mui/material";
import { useEffect, useMemo, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { toast } from "react-toastify";

import type { ProjectLayer, SearchSettings } from "@/lib/validations/project";

import useLayerFields from "@/hooks/map/CommonHooks";

import type { SelectorItem } from "@/types/map/common";

import SettingsGroupHeader from "@/components/builder/widgets/common/SettingsGroupHeader";
import LayerFieldSelector from "@/components/map/common/LayerFieldSelector";
import { pickSearchColumns } from "@/components/map/controls/search/editorSearchLayers";
import Selector from "@/components/map/panels/common/Selector";

const MAX_SEARCH_COLUMNS = 3;

type SearchLayerEntry = SearchSettings["layers"][number];
type SearchableField = ReturnType<typeof useLayerFields>["layerFields"][number];

interface SearchLayerRowProps {
  layer: ProjectLayer;
  columns: string[];
  labelColumn?: string;
  onChange: (next: { columns: string[]; label_column?: string }) => void;
  onRemove: () => void;
}

const SearchLayerRow = ({ layer, columns, labelColumn, onChange, onRemove }: SearchLayerRowProps) => {
  const { t } = useTranslation("common");
  const theme = useTheme();
  const { layerFields, isLoading } = useLayerFields(layer.layer_id, "string");

  // A row only ever needs an auto-pick once: right when it's added, before it
  // has any columns of its own. Rows restored with existing columns (from
  // `settings.layers`) must never be auto-picked, even if the user later
  // clears them back down to zero on purpose.
  const eligibleForAutoPick = useRef(columns.length === 0);
  const autoPickAttempted = useRef(false);

  useEffect(() => {
    if (!eligibleForAutoPick.current || autoPickAttempted.current || isLoading) return;
    autoPickAttempted.current = true;
    const picks = pickSearchColumns(layerFields);
    if (picks.length === 0) {
      // The row disappears again right away, so say why.
      toast.info(t("search_layer_no_text_fields"));
      onRemove();
      return;
    }
    onChange({ columns: picks, label_column: picks[0] });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isLoading, layerFields]);

  const selectedColumnFields = useMemo(
    () =>
      columns
        .map((name) => layerFields.find((field) => field.name === name))
        .filter((field): field is SearchableField => !!field),
    [columns, layerFields]
  );

  const labelOptions = useMemo(() => {
    const ordered = [...selectedColumnFields];
    layerFields.forEach((field) => {
      if (!ordered.some((f) => f.name === field.name)) {
        ordered.push(field);
      }
    });
    return ordered;
  }, [selectedColumnFields, layerFields]);

  const selectedLabelField = useMemo(
    () => layerFields.find((field) => field.name === labelColumn),
    [layerFields, labelColumn]
  );

  return (
    <Stack
      spacing={1}
      sx={{
        p: 1,
        backgroundColor: theme.palette.background.paper,
        borderRadius: 1,
        border: `1px solid ${theme.palette.divider}`,
      }}>
      <Stack direction="row" justifyContent="space-between" alignItems="center">
        <Typography
          variant="body2"
          fontWeight="medium"
          sx={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", flex: 1 }}>
          {layer.name}
        </Typography>
        <IconButton size="small" onClick={onRemove}>
          <DeleteIcon fontSize="small" color="error" />
        </IconButton>
      </Stack>
      <LayerFieldSelector
        multiple
        fields={layerFields}
        selectedField={selectedColumnFields}
        label={t("column")}
        setSelectedField={(fields) => {
          const nextFields = (Array.isArray(fields) ? fields : []).slice(0, MAX_SEARCH_COLUMNS);
          const nextColumns = nextFields.map((field) => field.name);
          // The label column may be any string field of the layer, not just a
          // chosen search column — leave it untouched on column edits. It
          // only ever refers to a field that still exists, since the label
          // selector's options are always drawn from the current field list.
          onChange({ columns: nextColumns, label_column: labelColumn });
        }}
      />
      {columns.length > 0 && (
        <LayerFieldSelector
          fields={labelOptions}
          selectedField={selectedLabelField}
          label={t("search_result_label_column")}
          setSelectedField={(field) => {
            onChange({ columns, label_column: field?.name });
          }}
        />
      )}
    </Stack>
  );
};

interface SearchSettingsSectionProps {
  settings: SearchSettings;
  projectLayers: ProjectLayer[];
  onChange: (next: SearchSettings) => void;
}

export const SearchSettingsSection = ({ settings, projectLayers, onChange }: SearchSettingsSectionProps) => {
  const { t } = useTranslation("common");

  // Layers added via the "add layer" picker but without a column picked yet.
  // They must not be written to `settings.layers` (min 1 column required by
  // the schema) until the user selects at least one column, but they still
  // need to render as a row and disappear from the "add layer" options.
  const [pendingLayerIds, setPendingLayerIds] = useState<number[]>([]);

  const featureLayers = useMemo(
    () => projectLayers.filter((layer) => layer.type === "feature"),
    [projectLayers]
  );

  const rowLayerIds = useMemo(() => {
    const committedIds = settings.layers.map((entry) => entry.layer_project_id);
    const extraIds = pendingLayerIds.filter((id) => !committedIds.includes(id));
    return [...committedIds, ...extraIds];
  }, [settings.layers, pendingLayerIds]);

  const availableLayers = useMemo(
    () => featureLayers.filter((layer) => !rowLayerIds.includes(layer.id)),
    [featureLayers, rowLayerIds]
  );

  const handleRowChange = (
    layerProjectId: number,
    next: { columns: string[]; label_column?: string }
  ) => {
    if (next.columns.length === 0) {
      setPendingLayerIds((ids) => (ids.includes(layerProjectId) ? ids : [...ids, layerProjectId]));
      if (settings.layers.some((entry) => entry.layer_project_id === layerProjectId)) {
        onChange({
          ...settings,
          layers: settings.layers.filter((entry) => entry.layer_project_id !== layerProjectId),
        });
      }
      return;
    }
    const nextEntry: SearchLayerEntry = { layer_project_id: layerProjectId, ...next };
    const exists = settings.layers.some((entry) => entry.layer_project_id === layerProjectId);
    const layers = exists
      ? settings.layers.map((entry) => (entry.layer_project_id === layerProjectId ? nextEntry : entry))
      : [...settings.layers, nextEntry];
    onChange({ ...settings, layers });
  };

  const handleRowRemove = (layerProjectId: number) => {
    setPendingLayerIds((ids) => ids.filter((id) => id !== layerProjectId));
    if (settings.layers.some((entry) => entry.layer_project_id === layerProjectId)) {
      onChange({
        ...settings,
        layers: settings.layers.filter((entry) => entry.layer_project_id !== layerProjectId),
      });
    }
  };

  return (
    <>
      <SettingsGroupHeader label={t("search")} />
      <Stack spacing={2}>
        <Stack direction="row" alignItems="center">
          <Switch
            size="small"
            name="places"
            checked={settings.places}
            onChange={(e) => onChange({ ...settings, places: e.target.checked })}
          />
          <Typography variant="body2" color="textSecondary">
            {t("search_places")}
          </Typography>
        </Stack>
        <Stack spacing={0.5}>
          <Stack direction="row" alignItems="center" justifyContent="space-between">
            <Typography variant="caption" color="text.secondary">
              {t("search_placeholder_label")}
            </Typography>
            {!!settings.placeholder && (
              <Link
                component="button"
                variant="caption"
                underline="always"
                onClick={() => onChange({ ...settings, placeholder: undefined })}
                sx={{ cursor: "pointer" }}>
                {t("reset")}
              </Link>
            )}
          </Stack>
          <TextField
            size="small"
            fullWidth
            value={settings.placeholder ?? ""}
            onChange={(event) =>
              onChange({
                ...settings,
                placeholder: event.target.value ? event.target.value.slice(0, 100) : undefined,
              })
            }
            placeholder={t("search_places_and_data")}
            helperText={t("search_placeholder_helper")}
          />
        </Stack>
        <Typography variant="body2" fontWeight="medium">
          {t("searchable_layers")}
        </Typography>
        {availableLayers.length > 0 && (
          <Selector
            selectedItems={undefined}
            setSelectedItems={(item: SelectorItem | SelectorItem[] | undefined) => {
              if (!item || Array.isArray(item)) return;
              const id = item.value as number;
              setPendingLayerIds((ids) => (ids.includes(id) ? ids : [...ids, id]));
            }}
            items={availableLayers.map((layer) => ({ value: layer.id, label: layer.name }))}
            label={t("add_layer")}
            placeholder={t("select_layer")}
          />
        )}
        {rowLayerIds.map((layerProjectId) => {
          const layer = featureLayers.find((l) => l.id === layerProjectId);
          if (!layer) return null;
          const entry = settings.layers.find((e) => e.layer_project_id === layerProjectId);
          return (
            <SearchLayerRow
              key={layerProjectId}
              layer={layer}
              columns={entry?.columns ?? []}
              labelColumn={entry?.label_column}
              onChange={(next) => handleRowChange(layerProjectId, next)}
              onRemove={() => handleRowRemove(layerProjectId)}
            />
          );
        })}
      </Stack>
    </>
  );
};

export default SearchSettingsSection;
