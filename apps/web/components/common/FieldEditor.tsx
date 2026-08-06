import type { DragEndEvent } from "@dnd-kit/core";
import dynamic from "next/dynamic";
import { DndContext, closestCenter } from "@dnd-kit/core";
import { restrictToVerticalAxis } from "@dnd-kit/modifiers";
import { SortableContext, useSortable, verticalListSortingStrategy } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { DragIndicator as DragIndicatorIcon } from "@mui/icons-material";
import {
  Box,
  Button,
  FormControlLabel,
  IconButton,
  Input,
  MenuItem,
  Select,
  Stack,
  Switch,
  Typography,
  alpha,
  useTheme,
} from "@mui/material";
import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";

import { ICON_NAME, Icon } from "@p4b/ui/components/Icon";

import FieldKindIcon from "@/components/common/FieldKindIcon";
import { type FormulaField } from "@/components/modals/FormulaBuilder";
const FormulaBuilder = dynamic(() => import("@/components/modals/FormulaBuilder"), { ssr: false });
import { formatFieldValue } from "@/lib/utils/formatFieldValue";
import type { FieldDefinition, FieldKind } from "@/lib/validations/layer";
import { ALLOWED_KINDS_BY_GEOM_TYPE, COMPUTED_KINDS, RESERVED_FIELD_NAMES } from "@/lib/validations/layer";

import type { SelectorItem } from "@/types/map/common";

import Selector from "@/components/map/panels/common/Selector";

const DECIMALS_OPTIONS: ("auto" | number)[] = ["auto", 0, 1, 2, 3, 4, 5];

const UNIT_OPTIONS_BY_KIND: Record<FieldKind, string[]> = {
  string: [],
  number: [],
  area: ["auto", "mm²", "cm²", "m²", "ha", "km²"],
  perimeter: ["auto", "mm", "cm", "m", "km"],
  length: ["auto", "mm", "cm", "m", "km"],
  datetime: [],
  boolean: [],
  formula: [],
};

const PREVIEW_VALUES_BY_KIND: Record<FieldKind, number[]> = {
  string: [],
  number: [1234.567, 12.35],
  area: [42500, 12.35],
  perimeter: [4250, 12.35],
  length: [4250, 12.35],
  datetime: [],
  boolean: [],
  formula: [],
};

interface FieldEditorProps {
  fields: FieldDefinition[];
  onChange: (fields: FieldDefinition[]) => void;
  selectedFieldId: string | null;
  onSelectField: (id: string | null) => void;
  /** Optional override for remove — e.g. to show a confirmation dialog for existing fields */
  onRemoveOverride?: (id: string) => void;
  /** IDs of fields whose type cannot be changed (existing DB columns) */
  lockedFieldIds?: Set<string>;
  /** Layer geometry type — controls which computed kinds are offered. */
  geometryType?:
    | "point"
    | "multipoint"
    | "line"
    | "multiline"
    | "polygon"
    | "multipolygon"
    | null;
  /**
   * When provided, clicking "Add field" calls this instead of creating an
   * in-place stub. Use this to open an AddFieldDialog from the parent.
   */
  onAddField?: () => void;
  /**
   * Dataset/layer id — enables formula fields (the formula builder validates
   * and previews expressions against this collection).
   */
  layerId?: string;
}

const ALL_FIELD_TYPE_ITEMS: Record<FieldKind, SelectorItem> = {
  string: { value: "string", label: "Text", iconNode: <FieldKindIcon kind="string" /> },
  number: { value: "number", label: "Number", iconNode: <FieldKindIcon kind="number" /> },
  area: { value: "area", label: "Area", iconNode: <FieldKindIcon kind="area" /> },
  perimeter: { value: "perimeter", label: "Perimeter", iconNode: <FieldKindIcon kind="perimeter" /> },
  length: { value: "length", label: "Length", iconNode: <FieldKindIcon kind="length" /> },
  datetime: { value: "datetime", label: "Date", iconNode: <FieldKindIcon kind="datetime" /> },
  boolean: { value: "boolean", label: "Boolean", iconNode: <FieldKindIcon kind="boolean" /> },
  formula: { value: "formula", label: "Formula", iconNode: <FieldKindIcon kind="formula" /> },
};

const NUMERIC_KINDS: FieldKind[] = ["number", "area", "perimeter", "length"];

// --- Sortable field row ---

interface SortableFieldRowProps {
  field: FieldDefinition;
  isSelected: boolean;
  error?: string;
  warning?: string;
  onSelect: () => void;
  onRename: (newName: string) => void;
  onDuplicate: () => void;
  onRemove: () => void;
}

const SortableFieldRow = ({
  field,
  isSelected,
  error,
  warning,
  onSelect,
  onRename,
  onDuplicate,
  onRemove,
}: SortableFieldRowProps) => {
  const theme = useTheme();
  const { attributes, listeners, setNodeRef, transform, transition } = useSortable({ id: field.id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  };

  return (
    <Box ref={setNodeRef} style={style}>
      <Stack
        direction="row"
        alignItems="center"
        onClick={onSelect}
        sx={{
          px: 0.5,
          py: 1.25,
          cursor: "pointer",
          borderLeft: isSelected
            ? `3px solid ${error ? theme.palette.error.main : theme.palette.primary.main}`
            : "3px solid transparent",
          backgroundColor: isSelected
            ? alpha(theme.palette.primary.main, 0.08)
            : "transparent",
          "&:hover": {
            backgroundColor: isSelected
              ? alpha(theme.palette.primary.main, 0.12)
              : theme.palette.action.hover,
            "& .field-actions": { opacity: 1 },
            "& .field-drag-handle": { opacity: 1 },
          },
        }}>
        {/* Drag handle */}
        <Box
          {...attributes}
          {...listeners}
          className="field-drag-handle"
          onClick={(e) => e.stopPropagation()}
          sx={{ cursor: "grab", display: "flex", alignItems: "center", mr: 0.5, opacity: 0 }}>
          <DragIndicatorIcon sx={{ fontSize: 16, color: theme.palette.text.secondary }} />
        </Box>

        {/* Type indicator */}
        <FieldKindIcon kind={field.kind} error={!!error} />

        {/* Always-visible input */}
        <Input
          value={field.name}
          onChange={(e) => onRename(e.target.value)}
          onFocus={onSelect}
          disableUnderline
          placeholder="Field name"
          autoFocus={isSelected}
          error={!!error}
          inputProps={{ maxLength: 128 }}
          sx={{
            flex: 1,
            ml: 0.5,
            "& .MuiInputBase-input": {
              py: 0.5,
              fontSize: "0.875rem",
            },
          }}
        />

        {/* Action buttons — visible on hover */}
        <Stack
          className="field-actions"
          direction="row"
          spacing={0}
          sx={{ flexShrink: 0, opacity: 0 }}>
          <IconButton
            size="small"
            onClick={(e) => {
              e.stopPropagation();
              onDuplicate();
            }}>
            <Icon
              iconName={ICON_NAME.COPY}
              style={{ fontSize: 14 }}
              htmlColor={theme.palette.text.secondary}
            />
          </IconButton>
          <IconButton
            size="small"
            onClick={(e) => {
              e.stopPropagation();
              onRemove();
            }}>
            <Icon
              iconName={ICON_NAME.MINUS}
              style={{ fontSize: 14 }}
              htmlColor={theme.palette.text.secondary}
            />
          </IconButton>
        </Stack>
      </Stack>
      {/* Error or warning message */}
      {error && (
        <Typography
          variant="caption"
          color="error"
          sx={{ pl: 6, pb: 0.5, display: "block" }}>
          {error}
        </Typography>
      )}
      {!error && warning && (
        <Typography
          variant="caption"
          color="warning.main"
          sx={{ pl: 6, pb: 0.5, display: "block" }}>
          {warning}
        </Typography>
      )}
    </Box>
  );
};

// --- Main FieldEditor ---

const FieldEditor: React.FC<FieldEditorProps> = ({
  fields,
  onChange,
  selectedFieldId,
  onSelectField,
  onRemoveOverride,
  lockedFieldIds,
  geometryType,
  onAddField,
  layerId,
}) => {
  const { t } = useTranslation("common");
  const theme = useTheme();
  const [formulaBuilderOpen, setFormulaBuilderOpen] = useState(false);

  const selectedField = fields.find((f) => f.id === selectedFieldId) ?? null;

  // Columns the formula builder can reference: every other field, typed for
  // its client-side validation (formula fields count as their result kind).
  const formulaFields: FormulaField[] = useMemo(
    () =>
      fields
        .filter((f) => f.id !== selectedFieldId)
        .map((f) => {
          const kind = f.kind === "formula" ? (f.output_kind ?? "string") : f.kind;
          const type =
            kind === "number" || kind === "area" || kind === "perimeter" || kind === "length"
              ? "number"
              : kind === "boolean"
                ? "boolean"
                : "string";
          return { name: f.name, type };
        }),
    [fields, selectedFieldId]
  );

  const handleFormulaChange = (id: string, expression: string) => {
    onChange(fields.map((f) => (f.id === id ? { ...f, formula: expression } : f)));
  };

  // Formula fields validate and backfill against the existing table, so they
  // are only offered when editing an existing dataset (layerId present) —
  // not in the create-new-dataset flow.
  const baseKinds: FieldKind[] = geometryType
    ? ALLOWED_KINDS_BY_GEOM_TYPE[geometryType] ?? ["string", "number", "datetime", "boolean", "formula"]
    : ["string", "number", "datetime", "boolean", "formula"];
  const availableKinds: FieldKind[] = baseKinds.filter((k) => k !== "formula" || !!layerId);

  const fieldTypeItems: SelectorItem[] = availableKinds.map((k) => ALL_FIELD_TYPE_ITEMS[k]);
  const hasFields = fields.length > 0;

  // Compute per-field validation errors
  // Simple identifier check — names that are safe for all export formats
  const SAFE_NAME_REGEX = /^[a-zA-Z_][a-zA-Z0-9_]*$/;

  const { fieldErrors, fieldWarnings } = useMemo(() => {
    const errors: Record<string, string> = {};
    const warnings: Record<string, string> = {};
    const nameCounts = new Map<string, number>();

    // Count occurrences of each name (case-insensitive)
    for (const field of fields) {
      const lower = field.name.toLowerCase();
      nameCounts.set(lower, (nameCounts.get(lower) || 0) + 1);
    }

    for (const field of fields) {
      const name = field.name;
      if (!name || name.trim().length === 0) {
        errors[field.id] = t("field_name_required");
      } else if (RESERVED_FIELD_NAMES.includes(name.toLowerCase())) {
        errors[field.id] = t("field_name_reserved");
      } else if ((nameCounts.get(name.toLowerCase()) || 0) > 1) {
        errors[field.id] = t("field_name_unique");
      } else if (!SAFE_NAME_REGEX.test(name)) {
        warnings[field.id] = t("field_name_special_chars_warning");
      }
      if (!errors[field.id] && field.kind === "formula" && !field.formula?.trim()) {
        errors[field.id] = t("formula_required");
      }
    }
    return { fieldErrors: errors, fieldWarnings: warnings };
  }, [fields, t]);

  const handleAddField = () => {
    // If caller provides an onAddField handler, delegate to it (e.g. to open
    // an AddFieldDialog) rather than creating an in-place stub.
    if (onAddField) {
      onAddField();
      return;
    }

    // Fallback: create an in-place stub (used by CreateLayer and other
    // consumers that don't have a dedicated add-field dialog).
    // Auto-increment name: new_field, new_field_2, new_field_3, ...
    const baseName = t("field_name_default");
    const existingNames = new Set(fields.map((f) => f.name.toLowerCase()));
    let fieldName = baseName;
    let counter = 2;
    while (existingNames.has(fieldName.toLowerCase())) {
      fieldName = `${baseName}_${counter}`;
      counter++;
    }
    const newField: FieldDefinition = {
      id: crypto.randomUUID(),
      name: fieldName,
      kind: "string",
      is_computed: false,
      display_config: {},
    };
    onChange([...fields, newField]);
    onSelectField(newField.id);
  };

  const handleDuplicate = (field: FieldDefinition) => {
    const copySuffix = t("field_name_copy_suffix");
    const existingNames = new Set(fields.map((f) => f.name.toLowerCase()));
    let copyName = `${field.name}_${copySuffix}`;
    let counter = 2;
    while (existingNames.has(copyName.toLowerCase())) {
      copyName = `${field.name}_${copySuffix}_${counter}`;
      counter++;
    }
    const copy: FieldDefinition = {
      id: crypto.randomUUID(),
      name: copyName,
      kind: field.kind,
      is_computed: field.is_computed,
      display_config: field.display_config,
    };
    const idx = fields.findIndex((f) => f.id === field.id);
    const next = [...fields];
    next.splice(idx + 1, 0, copy);
    onChange(next);
    onSelectField(copy.id);
  };

  const handleRemove = (id: string) => {
    if (onRemoveOverride) {
      onRemoveOverride(id);
      return;
    }
    const next = fields.filter((f) => f.id !== id);
    onChange(next);
    if (selectedFieldId === id) {
      onSelectField(next.length > 0 ? next[0].id : null);
    }
  };

  const handleRenameField = (id: string, newName: string) => {
    onChange(fields.map((f) => (f.id === id ? { ...f, name: newName } : f)));
  };

  const handleTypeChange = (id: string, item: SelectorItem | SelectorItem[] | undefined) => {
    if (!item || Array.isArray(item)) return;
    onChange(fields.map((f) => (f.id === id ? { ...f, kind: item.value as FieldKind } : f)));
  };

  const handleDisplayConfigChange = (
    id: string,
    partial: Record<string, unknown>,
  ) => {
    onChange(
      fields.map((f) =>
        f.id === id
          ? { ...f, display_config: { ...(f.display_config ?? {}), ...partial } }
          : f,
      ),
    );
  };

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;
    if (over && active.id !== over.id) {
      const oldIndex = fields.findIndex((f) => f.id === active.id);
      const newIndex = fields.findIndex((f) => f.id === over.id);
      const reordered = [...fields];
      const [removed] = reordered.splice(oldIndex, 1);
      reordered.splice(newIndex, 0, removed);
      onChange(reordered);
    }
  };

  // Empty state — no fields defined yet
  if (!hasFields) {
    return (
      <Stack
        sx={{ height: 340 }}
        alignItems="center"
        justifyContent="center"
        spacing={2}>
        <Icon
          iconName={ICON_NAME.TABLE}
          fontSize="small"
          htmlColor={theme.palette.text.secondary}
        />
        <Typography variant="body2" color="text.secondary">
          {t("no_fields")}
        </Typography>
        <Button
          variant="text"
          size="small"
          startIcon={<Icon iconName={ICON_NAME.PLUS} style={{ fontSize: 11 }} />}
          onClick={handleAddField}
          sx={{ textTransform: "none" }}>
          {t("add_field")}
        </Button>
      </Stack>
    );
  }

  return (
    <Stack direction="row" sx={{ height: 340 }} spacing={0}>
      {/* Left column — field list */}
      <Box
        sx={{
          width: "55%",
          borderRight: `1px solid ${theme.palette.divider}`,
          display: "flex",
          flexDirection: "column",
          overflow: "hidden",
        }}>
        <Box sx={{ flexGrow: 1, overflowY: "auto" }}>
          <DndContext
            collisionDetection={closestCenter}
            modifiers={[restrictToVerticalAxis]}
            onDragEnd={handleDragEnd}>
            <SortableContext
              items={fields.map((f) => f.id)}
              strategy={verticalListSortingStrategy}>
              {fields.map((field) => (
                <SortableFieldRow
                  key={field.id}
                  field={field}
                  isSelected={field.id === selectedFieldId}
                  error={fieldErrors[field.id]}
                  warning={fieldWarnings[field.id]}
                  onSelect={() => onSelectField(field.id)}
                  onRename={(newName) => handleRenameField(field.id, newName)}
                  onDuplicate={() => handleDuplicate(field)}
                  onRemove={() => handleRemove(field.id)}
                />
              ))}
            </SortableContext>
          </DndContext>
        </Box>

        {/* Add field button */}
        <Box
          sx={{
            px: 1,
            py: 1.5,
            borderTop: `1px solid ${theme.palette.divider}`,
          }}>
          <Button
            variant="text"
            size="small"
            startIcon={<Icon iconName={ICON_NAME.PLUS} style={{ fontSize: 11 }} />}
            onClick={handleAddField}
            sx={{ textTransform: "none" }}>
            {t("add_field")}
          </Button>
        </Box>
      </Box>

      {/* Right column — settings */}
      <Box
        sx={{
          width: "45%",
          p: 2,
          display: "flex",
          flexDirection: "column",
          overflowY: "auto",
        }}>
        {selectedField ? (
          (() => {
            const cfg = (selectedField.display_config ?? {}) as {
              decimals?: "auto" | number;
              unit?: string;
              thousands_separator?: boolean;
              abbreviate?: boolean;
              always_show_sign?: boolean;
            };
            // Formula fields format as their inferred result kind; unknown
            // until first saved (the backend infers it), so no formatting
            // options are offered for a brand-new formula field.
            const isFormula = selectedField.kind === "formula";
            const formatKind = (
              isFormula ? selectedField.output_kind : selectedField.kind
            ) as FieldKind | undefined;
            const showFormat = !!formatKind && NUMERIC_KINDS.includes(formatKind);
            const unitOptions = formatKind ? UNIT_OPTIONS_BY_KIND[formatKind] : [];
            const previewValues = formatKind ? PREVIEW_VALUES_BY_KIND[formatKind] : [];
            return (
              <Stack spacing={2}>
                <Typography variant="subtitle2" fontWeight="bold">
                  {selectedField.name}
                </Typography>
                {COMPUTED_KINDS.has(selectedField.kind) && (
                  <Box sx={{ display: "inline-flex", alignItems: "center", gap: 0.5 }}>
                    <Icon iconName={ICON_NAME.LOCK} style={{ fontSize: 12 }} />
                    <Typography variant="caption" color="text.secondary">
                      {t("computed_read_only")}
                    </Typography>
                  </Box>
                )}
                <Selector
                  label={t("field_type")}
                  selectedItems={
                    ALL_FIELD_TYPE_ITEMS[selectedField.kind] ??
                    fieldTypeItems.find((i) => i.value === selectedField.kind)
                  }
                  setSelectedItems={(item) => handleTypeChange(selectedField.id, item)}
                  items={fieldTypeItems}
                  disabled={lockedFieldIds?.has(selectedField.id)}
                />

                {isFormula && (
                  <Stack spacing={1}>
                    <Typography variant="caption" color="text.secondary">
                      {t("formula")}
                    </Typography>
                    {selectedField.formula ? (
                      <Box
                        sx={{
                          px: 1.5,
                          py: 1,
                          bgcolor: "action.hover",
                          borderRadius: 1,
                          fontFamily: "monospace",
                          fontSize: "0.75rem",
                          whiteSpace: "pre-wrap",
                          wordBreak: "break-word",
                          maxHeight: 120,
                          overflowY: "auto",
                        }}>
                        {selectedField.formula}
                      </Box>
                    ) : (
                      <Typography variant="caption" color="text.disabled">
                        {t("no_formula_yet")}
                      </Typography>
                    )}
                    <Button
                      variant="outlined"
                      size="small"
                      startIcon={<Icon iconName={ICON_NAME.CODE} style={{ fontSize: 14 }} />}
                      onClick={() => setFormulaBuilderOpen(true)}
                      sx={{ alignSelf: "flex-start", textTransform: "none" }}>
                      {selectedField.formula ? t("edit_formula") : t("add_formula")}
                    </Button>
                  </Stack>
                )}

                {showFormat && (
                  <>
                    <Typography variant="caption" color="text.secondary" sx={{ mt: 1 }}>
                      {t("number_format")}
                    </Typography>
                    <Stack direction="row" spacing={1}>
                      <Select
                        size="small"
                        fullWidth
                        value={String(cfg.decimals ?? "auto")}
                        onChange={(e) => {
                          const v = e.target.value;
                          handleDisplayConfigChange(selectedField.id, {
                            decimals: v === "auto" ? "auto" : Number(v),
                          });
                        }}>
                        {DECIMALS_OPTIONS.map((o) => (
                          <MenuItem key={String(o)} value={String(o)}>
                            {o === "auto" ? t("auto") : o}
                          </MenuItem>
                        ))}
                      </Select>
                      {unitOptions.length > 0 && (
                        <Select
                          size="small"
                          fullWidth
                          value={cfg.unit ?? "auto"}
                          onChange={(e) =>
                            handleDisplayConfigChange(selectedField.id, {
                              unit: e.target.value,
                            })
                          }>
                          {unitOptions.map((u) => (
                            <MenuItem key={u} value={u}>
                              {u === "auto" ? t("auto") : u}
                            </MenuItem>
                          ))}
                        </Select>
                      )}
                    </Stack>
                    <FormControlLabel
                      control={
                        <Switch
                          size="small"
                          checked={cfg.thousands_separator ?? false}
                          onChange={(e) =>
                            handleDisplayConfigChange(selectedField.id, {
                              thousands_separator: e.target.checked,
                            })
                          }
                        />
                      }
                      label={
                        <Typography variant="caption">
                          {t("show_thousands_separator")}
                        </Typography>
                      }
                    />
                    <FormControlLabel
                      control={
                        <Switch
                          size="small"
                          checked={cfg.abbreviate ?? false}
                          onChange={(e) =>
                            handleDisplayConfigChange(selectedField.id, {
                              abbreviate: e.target.checked,
                            })
                          }
                        />
                      }
                      label={
                        <Typography variant="caption">
                          {t("abbreviate_large_numbers")}
                        </Typography>
                      }
                    />
                    <FormControlLabel
                      control={
                        <Switch
                          size="small"
                          checked={cfg.always_show_sign ?? false}
                          onChange={(e) =>
                            handleDisplayConfigChange(selectedField.id, {
                              always_show_sign: e.target.checked,
                            })
                          }
                        />
                      }
                      label={
                        <Typography variant="caption">
                          {t("always_show_sign")}
                        </Typography>
                      }
                    />

                    {previewValues.length > 0 && (
                      <Box>
                        <Typography variant="caption" color="text.secondary">
                          {t("examples")}
                        </Typography>
                        <Stack spacing={0.5} sx={{ mt: 0.5 }}>
                          {previewValues.map((v) => (
                            <Box
                              key={v}
                              sx={{
                                px: 1,
                                py: 0.5,
                                bgcolor: "action.hover",
                                borderRadius: 1,
                                fontFamily: "monospace",
                                fontSize: "0.75rem",
                              }}>
                              {formatFieldValue(v, formatKind ?? selectedField.kind, cfg)}
                            </Box>
                          ))}
                        </Stack>
                      </Box>
                    )}
                  </>
                )}
              </Stack>
            );
          })()
        ) : (
          <Box
            sx={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              height: "100%",
            }}>
            <Typography variant="body2" color="text.secondary">
              {t("select_field_to_edit")}
            </Typography>
          </Box>
        )}
      </Box>
      {selectedField?.kind === "formula" && (
        <FormulaBuilder
          open={formulaBuilderOpen}
          onClose={() => setFormulaBuilderOpen(false)}
          onApply={(expression) => {
            handleFormulaChange(selectedField.id, expression);
            setFormulaBuilderOpen(false);
          }}
          initialExpression={selectedField.formula ?? ""}
          fields={formulaFields}
          collectionId={layerId}
          showGroupBy={false}
          title={t("formula")}
        />
      )}
    </Stack>
  );
};

export default FieldEditor;
