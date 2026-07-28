import {
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Typography,
  useTheme,
} from "@mui/material";
import { useCallback, useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { toast } from "react-toastify";

import { COLLECTIONS_API_BASE_URL, addColumn, deleteColumn, renameColumn, updateColumnDisplayConfig, updateColumnFormula, useDataset, useLayerQueryables } from "@/lib/api/layers";
import type { FieldDefinition, FieldKind } from "@/lib/validations/layer";
import { mutate as globalMutate } from "swr";

import FieldEditor from "@/components/common/FieldEditor";
import ConfirmModal from "@/components/modals/Confirm";

interface EditFieldsModalProps {
  open: boolean;
  onClose: () => void;
  layerId: string;
  /** If provided, this field will be pre-selected on open */
  initialFieldName?: string | null;
  /**
   * Layer geometry type — passed through to FieldEditor to filter the kind
   * dropdown. If omitted, geometryType is fetched from the layer record via
   * useDataset. This prop serves as an optional override / initial hint.
   */
  geometryType?:
    | "point"
    | "multipoint"
    | "line"
    | "multiline"
    | "polygon"
    | "multipolygon"
    | null;
}


/** Hidden system fields that should not appear in the editor */
const HIDDEN_FIELDS = ["layer_id", "id", "h3_3", "h3_6", "geom", "geometry"];

const EditFieldsModal: React.FC<EditFieldsModalProps> = ({
  open,
  onClose,
  layerId,
  initialFieldName,
  geometryType: geometryTypeProp,
}) => {
  const { t } = useTranslation("common");
  const theme = useTheme();
  const { queryables, mutate: mutateQueryables } = useLayerQueryables(layerId);
  const { dataset } = useDataset(layerId);

  // Derive geometry type: prefer the fetched layer record, fall back to the prop.
  // The fetched type is "point" | "line" | "polygon" (no multi-variants from the
  // backend enum), so we cast it to the broader union used by FieldEditor /
  // AddFieldDialog which also accepts multi-variants from callers.
  const layerGeometryType = (
    dataset?.feature_layer_geometry_type ?? geometryTypeProp ?? null
  ) as
    | "point"
    | "multipoint"
    | "line"
    | "multiline"
    | "polygon"
    | "multipolygon"
    | null;

  const [fields, setFields] = useState<FieldDefinition[]>([]);
  const [selectedFieldId, setSelectedFieldId] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);

  // Delete confirmation
  const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false);
  const [pendingDeleteId, setPendingDeleteId] = useState<string | null>(null);

  // Track original field state for diffing on save
  const [originalFields, setOriginalFields] = useState<FieldDefinition[]>([]);

  // Load fields from queryables when modal opens
  useEffect(() => {
    if (!open || !queryables?.properties) return;

    const loaded: FieldDefinition[] = Object.entries(queryables.properties)
      .filter(([name]) => !HIDDEN_FIELDS.includes(name))
      .filter(([, schema]) => {
        const t = (schema as { type?: string }).type;
        return t !== "object" && t !== "geometry";
      })
      .map(([name, schema]) => {
        const s = schema as {
          kind?: FieldKind;
          is_computed?: boolean;
          display_config?: Record<string, unknown>;
          type?: string;
          formula?: string;
          output_kind?: string;
        };
        return {
          id: name,
          name,
          kind: s.kind ?? (s.type === "number" || s.type === "integer" ? "number" : "string"),
          is_computed: s.is_computed ?? false,
          display_config: s.display_config ?? {},
          formula: s.formula,
          output_kind: s.output_kind,
        };
      });

    setFields(loaded);
    setOriginalFields(loaded);

    if (initialFieldName) {
      const match = loaded.find((f) => f.name === initialFieldName);
      if (match) setSelectedFieldId(match.id);
    }
  }, [open, queryables, initialFieldName]);

  /** Revalidate all SWR keys for this layer (queryables, collection items, etc.) */
  const revalidateLayer = useCallback(() => {
    mutateQueryables();
    // Revalidate any SWR key that starts with the collection URL for this
    // layer. Single-argument mutate keeps the cached data on screen while
    // refetching (a data argument — even undefined — would clear the cache).
    // Items keys are [url, params] arrays, so match those too.
    globalMutate((key) => {
      const prefix = `${COLLECTIONS_API_BASE_URL}/${layerId}`;
      if (typeof key === "string") return key.startsWith(prefix);
      if (Array.isArray(key) && typeof key[0] === "string") return key[0].startsWith(prefix);
      return false;
    });
  }, [layerId, mutateQueryables]);

  // Build a map of original field names by ID for diffing
  const originalMap = useMemo(
    () => new Map(originalFields.map((f) => [f.id, f])),
    [originalFields]
  );

  // Existing fields whose type cannot be changed
  const lockedFieldIds = useMemo(
    () => new Set(originalFields.map((f) => f.id)),
    [originalFields]
  );

  const handleFieldsChange = useCallback((updated: FieldDefinition[]) => {
    setFields(updated);
  }, []);

  const handleRemoveRequest = useCallback((id: string) => {
    // For existing fields (id matches an original), show confirmation
    const isExisting = originalFields.some((f) => f.id === id);
    if (isExisting) {
      setPendingDeleteId(id);
      setDeleteConfirmOpen(true);
    } else {
      // New unsaved field — remove immediately
      setFields((prev) => prev.filter((f) => f.id !== id));
      setSelectedFieldId((prev) => (prev === id ? null : prev));
    }
  }, [originalFields]);

  const handleConfirmDelete = useCallback(async () => {
    if (!pendingDeleteId) return;
    const field = fields.find((f) => f.id === pendingDeleteId);
    if (!field) return;

    try {
      setIsSaving(true);
      await deleteColumn(layerId, field.name);
      setFields((prev) => prev.filter((f) => f.id !== pendingDeleteId));
      setOriginalFields((prev) => prev.filter((f) => f.id !== pendingDeleteId));
      if (selectedFieldId === pendingDeleteId) setSelectedFieldId(null);
      toast.success(t("field_deleted"));
      revalidateLayer();
    } catch (error) {
      console.error("Failed to delete field:", error);
      toast.error(t("error_deleting_field"));
    } finally {
      setIsSaving(false);
      setDeleteConfirmOpen(false);
      setPendingDeleteId(null);
    }
  }, [pendingDeleteId, fields, layerId, selectedFieldId, t, revalidateLayer]);

  const handleSave = async () => {
    try {
      setIsSaving(true);

      // Diff: find added, renamed, and type-changed fields
      const originalIds = new Set(originalFields.map((f) => f.id));

      for (const field of fields) {
        if (!originalIds.has(field.id)) {
          // New field — add column with kind + display_config (+ formula)
          await addColumn(layerId, {
            name: field.name,
            kind: field.kind,
            display_config: field.display_config ?? {},
            ...(field.kind === "formula" ? { formula: field.formula } : {}),
          });
        } else {
          const orig = originalMap.get(field.id);
          if (orig && orig.name !== field.name) {
            await renameColumn(layerId, orig.name, field.name);
          }
          // Formula change: the backend revalidates, re-infers the result
          // type and recomputes the whole column.
          if (
            orig &&
            field.kind === "formula" &&
            field.formula &&
            field.formula !== orig.formula
          ) {
            await updateColumnFormula(layerId, field.name, field.formula);
          }
          // Persist display_config edits on existing fields
          const origConfig = JSON.stringify(orig?.display_config ?? {});
          const nextConfig = JSON.stringify(field.display_config ?? {});
          if (orig && origConfig !== nextConfig) {
            await updateColumnDisplayConfig(
              layerId,
              field.name,
              field.display_config ?? {},
            );
          }
          // Note: kind changes on existing columns are not supported.
        }
      }

      toast.success(t("fields_saved"));
      revalidateLayer();
      onClose();
    } catch (error) {
      console.error("Failed to save fields:", error);
      toast.error(t("error_saving_fields"));
    } finally {
      setIsSaving(false);
    }
  };

  // Check if there are unsaved changes
  const hasChanges = useMemo(() => {
    if (fields.length !== originalFields.length) return true;
    return fields.some((f) => {
      const orig = originalMap.get(f.id);
      if (!orig) return true; // new field
      if (orig.name !== f.name) return true;
      if ((orig.formula ?? "") !== (f.formula ?? "")) return true;
      return (
        JSON.stringify(orig.display_config ?? {}) !==
        JSON.stringify(f.display_config ?? {})
      );
    });
  }, [fields, originalFields, originalMap]);

  const pendingDeleteField = fields.find((f) => f.id === pendingDeleteId);

  return (
    <>
      <Dialog open={open} onClose={onClose} fullWidth maxWidth="md">
        <DialogTitle>{t("edit_fields")}</DialogTitle>
        <DialogContent sx={{ p: 0 }}>
          <FieldEditor
            fields={fields}
            onChange={handleFieldsChange}
            selectedFieldId={selectedFieldId}
            onSelectField={setSelectedFieldId}
            onRemoveOverride={handleRemoveRequest}
            lockedFieldIds={lockedFieldIds}
            geometryType={layerGeometryType}
            layerId={layerId}
          />
        </DialogContent>
        <DialogActions
          sx={{
            "&.MuiDialogActions-root": {
              px: 3,
              py: 2,
              borderTop: `1px solid ${theme.palette.divider}`,
            },
            justifyContent: "flex-end",
          }}>
          <Button variant="text" onClick={onClose}>
            <Typography variant="body2" fontWeight="bold">
              {t("cancel")}
            </Typography>
          </Button>
          <Button
            variant="contained"
            color="primary"
            onClick={handleSave}
            disabled={!hasChanges || isSaving}>
            <Typography variant="body2" fontWeight="bold" color="inherit">
              {t("save")}
            </Typography>
          </Button>
        </DialogActions>
      </Dialog>

      <ConfirmModal
        open={deleteConfirmOpen}
        title={t("delete_field")}
        body={t("delete_field_confirmation", { name: pendingDeleteField?.name })}
        closeText={t("cancel")}
        confirmText={t("delete")}
        onClose={() => {
          setDeleteConfirmOpen(false);
          setPendingDeleteId(null);
        }}
        onConfirm={handleConfirmDelete}
      />
    </>
  );
};

export default EditFieldsModal;
