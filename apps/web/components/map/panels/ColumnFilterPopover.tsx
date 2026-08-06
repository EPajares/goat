import CheckIcon from "@mui/icons-material/Check";
import KeyboardArrowDownIcon from "@mui/icons-material/KeyboardArrowDown";
import WarningAmberIcon from "@mui/icons-material/WarningAmber";
import { Box, Button, Divider, Menu, MenuItem, Popover, Stack, TextField, Typography } from "@mui/material";
import React, { useCallback, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { v4 } from "uuid";

import TemporalPicker from "@p4b/ui/components/TemporalPicker";

import { createTheCQLBasedOnExpression } from "@/lib/transformers/filter";
import {
  type FilterColumnType,
  type FilterDraft,
  draftFromExpression,
  draftToExpression,
  emptyDraft,
  isDraftComplete,
  isQuickFilterOperator,
  operatorBody,
  quickFilterOperators,
  toggleDraftValue,
} from "@/lib/utils/columnFilterOperators";
import { FilterType } from "@/lib/validations/filter";

import type { TableFilterController } from "@/types/map/tableFilter";

import useLayerFields from "@/hooks/map/CommonHooks";

import FieldKindIcon, { type FieldIndicatorKind } from "@/components/common/FieldKindIcon";
import ColumnValueCheckList from "@/components/map/panels/common/ColumnValueCheckList";

const POPOVER_WIDTH = 300;
const MAX_POPOVER_HEIGHT = 460;
/** Below this, the value list is too cramped to be worth opening downward. */
const MIN_USABLE_HEIGHT = 300;
const VIEWPORT_MARGIN = 16;

type ColumnFilterPopoverProps = {
  anchorEl: HTMLElement | null;
  columnName: string;
  columnType: FilterColumnType;
  iconKind: FieldIndicatorKind;
  layerId: string;
  controller: TableFilterController;
  onClose: () => void;
};

const ColumnFilterPopover: React.FC<ColumnFilterPopoverProps> = ({
  anchorEl,
  columnName,
  columnType,
  iconKind,
  layerId,
  controller,
  onClose,
}) => {
  const { t } = useTranslation("common");
  const { layerFields } = useLayerFields(layerId);

  const columnExpressions = useMemo(
    () => controller.expressions.filter((e) => e.attribute === columnName),
    [controller.expressions, columnName]
  );

  /**
   * The popover owns one expression per column: the first one this vocabulary
   * can represent. Anything else (spatial, empty-string, a compound built in
   * the Filter panel) is left alone and reported instead of being overwritten.
   */
  const editedExpression = useMemo(
    () => columnExpressions.find((e) => isQuickFilterOperator(columnType, e.expression)),
    [columnExpressions, columnType]
  );

  const otherExpressionCount = columnExpressions.length - (editedExpression ? 1 : 0);

  const [draft, setDraft] = useState<FilterDraft>(() =>
    editedExpression ? draftFromExpression(columnType, editedExpression) : emptyDraft(columnType)
  );
  const [isSaving, setIsSaving] = useState(false);
  const [operatorAnchor, setOperatorAnchor] = useState<HTMLElement | null>(null);

  const body = operatorBody(columnType, draft.operator);
  const isComplete = isDraftComplete(columnType, draft);
  const operators = quickFilterOperators(columnType);

  /**
   * The data table docks to the bottom of the window, so a header near the
   * bottom leaves no room below it. MUI does not flip on its own — pick the
   * roomier side and cap the height to it.
   */
  const placement = useMemo(() => {
    if (!anchorEl || typeof window === "undefined") {
      return { anchor: "bottom", transform: "top", maxHeight: MAX_POPOVER_HEIGHT } as const;
    }
    const rect = anchorEl.getBoundingClientRect();
    const below = window.innerHeight - rect.bottom - VIEWPORT_MARGIN;
    const above = rect.top - VIEWPORT_MARGIN;
    if (below >= MIN_USABLE_HEIGHT || below >= above) {
      return { anchor: "bottom", transform: "top", maxHeight: Math.min(MAX_POPOVER_HEIGHT, below) } as const;
    }
    return { anchor: "top", transform: "bottom", maxHeight: Math.min(MAX_POPOVER_HEIGHT, above) } as const;
  }, [anchorEl]);

  /**
   * Value lists are scoped by every other active filter but never this column's
   * own, so the list stays consistent with the table without hiding the values
   * already selected here.
   */
  const valueListFilter = useMemo(() => {
    if (body !== "values") return undefined;
    const others = controller.expressions.filter((e) => e.attribute !== columnName);
    if (!others.length) return undefined;
    return createTheCQLBasedOnExpression(others, layerFields, controller.logicalOperator);
  }, [body, controller.expressions, controller.logicalOperator, columnName, layerFields]);

  const handleOperatorChange = useCallback(
    (operator: string) => {
      setDraft((previous) => {
        // Ticked values survive an is / is not swap; every other change alters
        // the shape of the editor, so the value is no longer meaningful.
        if (operatorBody(columnType, operator) === operatorBody(columnType, previous.operator)) {
          return { ...previous, operator };
        }
        return { ...emptyDraft(columnType), operator, editingId: previous.editingId };
      });
      setOperatorAnchor(null);
    },
    [columnType]
  );

  const handleApply = useCallback(async () => {
    if (!isComplete || isSaving) return;
    setIsSaving(true);
    const expression = draftToExpression(columnType, columnName, draft, v4);
    onClose();
    await controller.upsert({ ...expression, type: FilterType.Logical });
  }, [isComplete, isSaving, columnType, columnName, draft, controller, onClose]);

  const handleRemove = useCallback(async () => {
    if (!editedExpression) return;
    onClose();
    await controller.remove(editedExpression.id);
  }, [editedExpression, controller, onClose]);

  const renderBody = () => {
    switch (body) {
      case "values":
        return (
          <ColumnValueCheckList
            layerId={layerId}
            fieldName={columnName}
            selectedValues={draft.values}
            onToggle={(value) => setDraft((previous) => toggleDraftValue(previous, value))}
            cqlFilter={valueListFilter}
          />
        );
      case "text":
        return (
          <Box sx={{ px: 2, py: 2 }}>
            <TextField
              autoFocus
              size="small"
              fullWidth
              value={draft.text}
              onChange={(event) => setDraft((previous) => ({ ...previous, text: event.target.value }))}
              onKeyDown={(event) => {
                if (event.key === "Enter") handleApply();
              }}
              placeholder={t("filter_expressions.enter_value")}
            />
          </Box>
        );
      case "number":
      case "days":
        return (
          <Box sx={{ px: 2, py: 2 }}>
            <TextField
              autoFocus
              size="small"
              fullWidth
              type="number"
              value={draft.first}
              onChange={(event) => setDraft((previous) => ({ ...previous, first: event.target.value }))}
              onKeyDown={(event) => {
                if (event.key === "Enter") handleApply();
              }}
              label={body === "days" ? t("number_of_days") : undefined}
              placeholder={body === "days" ? undefined : t("filter_expressions.enter_number")}
            />
          </Box>
        );
      case "range":
        return (
          <Stack direction="row" spacing={2} sx={{ px: 2, py: 2 }}>
            {(["first", "second"] as const).map((key) => (
              <TextField
                key={key}
                autoFocus={key === "first"}
                size="small"
                fullWidth
                type="number"
                label={key === "first" ? t("from") : t("to")}
                value={draft[key]}
                onChange={(event) => setDraft((previous) => ({ ...previous, [key]: event.target.value }))}
              />
            ))}
          </Stack>
        );
      case "date":
        return (
          <Box sx={{ px: 2, py: 2 }}>
            <TemporalPicker
              kind="datetime"
              label={t("select_date")}
              value={draft.first}
              onChange={(value) => setDraft((previous) => ({ ...previous, first: value }))}
            />
          </Box>
        );
      case "daterange":
        return (
          <Stack direction="column" spacing={2} sx={{ px: 2, py: 2 }}>
            {(["first", "second"] as const).map((key) => (
              <TemporalPicker
                key={key}
                kind="datetime"
                label={key === "first" ? t("from") : t("to")}
                value={draft[key]}
                onChange={(value) => setDraft((previous) => ({ ...previous, [key]: value }))}
              />
            ))}
          </Stack>
        );
      case "none":
        return (
          <Typography variant="body2" color="text.secondary" sx={{ px: 2, py: 2, fontStyle: "italic" }}>
            {t("operator_needs_no_value", {
              defaultValue: "This operator needs no value. Press Done to apply it.",
            })}
          </Typography>
        );
    }
  };

  return (
    <Popover
      open={!!anchorEl}
      anchorEl={anchorEl}
      onClose={onClose}
      anchorOrigin={{ vertical: placement.anchor, horizontal: "left" }}
      transformOrigin={{ vertical: placement.transform, horizontal: "left" }}
      slotProps={{
        paper: {
          sx: {
            width: POPOVER_WIDTH,
            my: 0.5,
            maxHeight: placement.maxHeight,
            // A value list arrives asynchronously, so a content-sized paper grows
            // once it loads. MUI re-positions on every render while open, and an
            // upward-opening popover is anchored by its bottom edge — so growing
            // would shift its top and the whole panel would appear to jump. Claim
            // the height up front and let the list scroll inside it instead.
            ...(body === "values" && { height: placement.maxHeight }),
            display: "flex",
            flexDirection: "column",
          },
        },
      }}>
      {/* Field and operator share one line, so the values stay the tallest thing. */}
      <Stack
        direction="row"
        spacing={2}
        alignItems="center"
        sx={{ px: 2, py: 2, flexShrink: 0 }}>
        <FieldKindIcon kind={iconKind} />
        <Typography variant="body2" fontWeight="bold" noWrap sx={{ flex: 1, minWidth: 0 }}>
          {columnName}
        </Typography>
        {/* variant is explicit: the theme defaults every Button to contained,
            which would make this a filled primary pill. */}
        <Button
          variant="text"
          color="inherit"
          size="small"
          onClick={(event) => setOperatorAnchor(event.currentTarget)}
          endIcon={<KeyboardArrowDownIcon sx={{ fontSize: 16 }} />}
          sx={{
            flexShrink: 0,
            maxWidth: 150,
            px: 2,
            py: 0.5,
            "& .MuiButton-endIcon": { ml: 1 },
          }}>
          <Typography variant="body2" fontWeight="bold" noWrap>
            {t(`filter_expressions.${draft.operator}`)}
          </Typography>
        </Button>
      </Stack>

      <Divider sx={{ flexShrink: 0 }} />

      {/* Only the body scrolls; the column, operator and actions stay put. */}
      <Box sx={{ display: "flex", flexDirection: "column", flex: 1, minHeight: 0 }}>{renderBody()}</Box>

      {otherExpressionCount > 0 && (
        <Stack
          direction="row"
          spacing={2}
          sx={{
            px: 2,
            py: 2,
            borderTop: 1,
            borderColor: "divider",
            bgcolor: "action.hover",
            flexShrink: 0,
          }}>
          <WarningAmberIcon sx={{ fontSize: 16, color: "warning.main", flexShrink: 0 }} />
          <Typography variant="caption" color="text.secondary">
            {t("column_has_other_filters", {
              count: otherExpressionCount,
              column: columnName,
              defaultValue:
                "{{column}} has {{count}} other filter. Manage it in the layer Filter panel.",
            })}
          </Typography>
        </Stack>
      )}

      <Divider sx={{ flexShrink: 0 }} />

      {/* Text buttons throughout, as in the widget's column popover and ConfirmModal. */}
      <Stack direction="row" alignItems="center" spacing={1} sx={{ px: 2, py: 2, flexShrink: 0 }}>
        {editedExpression && (
          <Button variant="text" color="error" onClick={handleRemove}>
            <Typography variant="body2" fontWeight="bold" color="inherit">
              {t("remove")}
            </Typography>
          </Button>
        )}
        <Box sx={{ flex: 1 }} />
        <Button variant="text" onClick={onClose}>
          <Typography variant="body2" fontWeight="bold">
            {t("cancel")}
          </Typography>
        </Button>
        <Button variant="text" color="primary" disabled={!isComplete} onClick={handleApply}>
          <Typography variant="body2" fontWeight="bold" color="inherit">
            {t("done")}
          </Typography>
        </Button>
      </Stack>

      {/* Operators are grouped: value matching, then text/range matching, then
          the ones that need no value at all. */}
      <Menu
        open={!!operatorAnchor}
        anchorEl={operatorAnchor}
        onClose={() => setOperatorAnchor(null)}
        anchorOrigin={{ vertical: "bottom", horizontal: "left" }}
        transformOrigin={{ vertical: "top", horizontal: "left" }}
        slotProps={{ paper: { sx: { minWidth: 190 } } }}>
        {operators.flatMap((operator) => {
          const isSelected = operator.value === draft.operator;
          const item = (
            <MenuItem
              key={operator.value}
              sx={{ px: 2, py: 2 }}
              onClick={() => handleOperatorChange(operator.value)}>
              <CheckIcon
                sx={{
                  fontSize: 14,
                  mr: 2,
                  color: "primary.main",
                  visibility: isSelected ? "visible" : "hidden",
                }}
              />
              <Typography variant="body2" fontWeight={isSelected ? "bold" : "regular"}>
                {t(`filter_expressions.${operator.value}`)}
              </Typography>
            </MenuItem>
          );
          return operator.dividerBefore
            ? [<Divider key={`${operator.value}-divider`} sx={{ my: 1 }} />, item]
            : [item];
        })}
      </Menu>
    </Popover>
  );
};

export default ColumnFilterPopover;
