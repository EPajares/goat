import ArrowUpwardIcon from "@mui/icons-material/ArrowUpward";
import KeyboardArrowDownIcon from "@mui/icons-material/KeyboardArrowDown";
import KeyboardArrowUpIcon from "@mui/icons-material/KeyboardArrowUp";
import { Box, Collapse, Divider, IconButton, ListItemIcon, ListItemText, Menu, MenuItem, Skeleton } from "@mui/material";
import { Stack, Table, TableBody, TableCell, TableHead, TableRow, Typography } from "@mui/material";
import React, { useMemo, useState } from "react";

import type { DatasetCollectionItems, FieldKind } from "@/lib/validations/layer";
import { resolveDisplayKind } from "@/lib/validations/layer";
import { formatFieldValue } from "@/lib/utils/formatFieldValue";

import FieldKindIcon, { fieldIndicatorKind } from "@/components/common/FieldKindIcon";
import { COLUMN_MENU_DIVIDER_SX, COLUMN_MENU_PAPER_SX } from "@/components/common/columnMenuStyles";
import NoValuesFound from "@/components/map/common/NoValuesFound";

const TWO_LINE_CLAMP_SX = {
  display: "-webkit-box",
  WebkitLineClamp: 2,
  WebkitBoxOrient: "vertical" as const,
  overflow: "hidden",
  textOverflow: "ellipsis",
  whiteSpace: "normal",
  wordBreak: "break-word",
  lineHeight: 1.25,
  maxHeight: "2.5em",
};

export type FeatureTableColumnMenuItem = {
  key: string;
  label: string;
  icon?: React.ReactNode;
  onSelect: (anchorEl: HTMLElement) => void;
  dividerBefore?: boolean;
};

export type FeatureTableField = {
  name: string;
  type: string;
  kind?: string;
  output_kind?: string;
  display_config?: Record<string, unknown>;
};

/**
 * Default cell rendering: formats by the field's display kind so datetimes,
 * booleans and measurements read the way they do everywhere else.
 */
export const formatFeatureValue = (value: unknown, field?: FeatureTableField): string => {
  if (value === null || value === undefined) return "";
  if (typeof value === "object") return JSON.stringify(value);
  const displayKind = field ? resolveDisplayKind(field) : undefined;
  if (displayKind && displayKind !== "string") {
    return formatFieldValue(value, displayKind as FieldKind, field?.display_config ?? {});
  }
  return String(value);
};

/** An object field holding a list of records renders as a nested table. */
export const isArrayOfRecords = (value: unknown): value is Array<Record<string, unknown>> =>
  Array.isArray(value) &&
  value.length > 0 &&
  typeof value[0] === "object" &&
  value[0] !== null &&
  !Array.isArray(value[0]);

type FeatureRowProps = {
  row: { id?: string | number; properties: Record<string, unknown> };
  primitiveFields: FeatureTableField[];
  objectFields: FeatureTableField[];
  formatCellValue?: (fieldName: string, value: unknown) => React.ReactNode;
  getColumnWidth?: (fieldName: string) => number | undefined;
};

const FeatureRow = ({
  row,
  primitiveFields,
  objectFields,
  formatCellValue,
  getColumnWidth,
}: FeatureRowProps) => {
  const [open, setOpen] = useState(false);

  return (
    <>
      <TableRow>
        {objectFields.length > 0 && (
          <TableCell>
            <IconButton aria-label="expand row" size="small" onClick={() => setOpen(!open)}>
              {open ? <KeyboardArrowUpIcon /> : <KeyboardArrowDownIcon />}
            </IconButton>
          </TableCell>
        )}
        {primitiveFields.map((field) => (
          <TableCell key={field.name} sx={{ width: getColumnWidth?.(field.name) }}>
            <Typography variant="body2" sx={TWO_LINE_CLAMP_SX}>
              {formatCellValue
                ? formatCellValue(field.name, row.properties[field.name])
                : formatFeatureValue(row.properties[field.name], field)}
            </Typography>
          </TableCell>
        ))}
      </TableRow>

      {objectFields.length > 0 && (
        <TableRow>
          <TableCell style={{ paddingBottom: 0, paddingTop: 0 }} colSpan={primitiveFields.length + 1}>
            <Collapse in={open} timeout="auto" unmountOnExit>
              <Box sx={{ margin: 2 }}>
                {objectFields.map((field) => {
                  const rawValue = row.properties[field.name];
                  let jsonData: unknown = rawValue;
                  if (typeof rawValue === "string") {
                    try {
                      jsonData = JSON.parse(rawValue);
                    } catch {
                      // Not valid JSON — show it as-is.
                    }
                  }
                  const jsonDataRows = isArrayOfRecords(jsonData) ? jsonData : undefined;

                  return (
                    <React.Fragment key={field.name}>
                      <Stack direction="row" spacing={1} alignItems="center" sx={{ py: 1, pl: 4 }}>
                        <FieldKindIcon kind={fieldIndicatorKind(field)} />
                        <Typography variant="body2" fontWeight="bold">
                          {field.name}
                        </Typography>
                      </Stack>
                      {jsonDataRows ? (
                        <Table size="small" aria-label={`${field.name} values`}>
                          <TableHead>
                            <TableRow>
                              {Object.keys(jsonDataRows[0]).map((key) => (
                                <TableCell key={key}>{key}</TableCell>
                              ))}
                            </TableRow>
                          </TableHead>
                          <TableBody>
                            {jsonDataRows.map((item, rowIndex) => (
                              <TableRow key={rowIndex}>
                                {Object.values(item).map((value, cellIndex) => (
                                  <TableCell key={cellIndex}>{formatFeatureValue(value)}</TableCell>
                                ))}
                              </TableRow>
                            ))}
                          </TableBody>
                        </Table>
                      ) : (
                        <Typography>{JSON.stringify(jsonData, null, 2)}</Typography>
                      )}
                    </React.Fragment>
                  );
                })}
              </Box>
            </Collapse>
          </TableCell>
        </TableRow>
      )}
    </>
  );
};

export type FeatureTableProps = {
  fields: FeatureTableField[];
  data?: DatasetCollectionItems;
  isLoading?: boolean;
  /** "bordered" adds the vertical column dividers the dashboard widget uses. */
  variant?: "plain" | "bordered";
  stickyHeader?: boolean;
  headerColor?: string;
  headerLabelMap?: Record<string, string>;
  renderHeaderLabel?: (fieldName: string, label: string) => React.ReactNode;
  formatCellValue?: (fieldName: string, value: unknown) => React.ReactNode;
  getColumnWidth?: (fieldName: string) => number | undefined;
  onHeaderResizeStart?: (event: React.MouseEvent, fieldName: string) => void;
  onReorderColumns?: (fromFieldName: string, toFieldName: string) => void;
  /**
   * Items for the menu opened by clicking a header. The host decides what a
   * column can do; the table only owns the anchor. `onSelect` receives the
   * header cell so the host can anchor a popover of its own to it.
   */
  columnMenuItems?: (fieldName: string) => FeatureTableColumnMenuItem[];
  sortColumn?: string;
  sortDirection?: "asc" | "desc";
  emptyMessage?: React.ReactNode;
};

/**
 * Renders a page of features from a layer. Presentational only — callers own
 * fetching, paging and filtering, because some of them (the workflows panel)
 * synthesise rows for temp layers instead of reading them from the API.
 */
const FeatureTable: React.FC<FeatureTableProps> = ({
  fields,
  data,
  isLoading = false,
  variant = "plain",
  stickyHeader = true,
  headerColor,
  headerLabelMap,
  renderHeaderLabel,
  formatCellValue,
  getColumnWidth,
  onHeaderResizeStart,
  onReorderColumns,
  columnMenuItems,
  sortColumn,
  sortDirection,
  emptyMessage,
}) => {
  const primitiveFields = useMemo(() => fields.filter((field) => field.type !== "object"), [fields]);
  const objectFields = useMemo(() => fields.filter((field) => field.type === "object"), [fields]);
  const [draggedColumn, setDraggedColumn] = useState<string | null>(null);
  const [menuColumn, setMenuColumn] = useState<{ field: string; anchorEl: HTMLElement } | null>(null);

  const columnCount = primitiveFields.length + (objectFields.length > 0 ? 1 : 0);

  if (isLoading && !data) {
    return (
      <>
        <Skeleton variant="rectangular" height={60} sx={{ m: 4 }} />
        <Skeleton variant="rectangular" height={240} sx={{ m: 4 }} />
      </>
    );
  }

  if (!data) return null;

  const menuItems = menuColumn ? columnMenuItems?.(menuColumn.field) ?? [] : [];

  return (
    <>
    <Table
      size="small"
      stickyHeader={stickyHeader}
      sx={{
        tableLayout: "auto",
        width: "max-content",
        minWidth: "100%",
        "& .MuiTableCell-root": {
          verticalAlign: "top",
          ...(variant === "bordered" && { borderRight: 1, borderColor: "divider" }),
        },
        ...(variant === "bordered" && {
          "& .MuiTableRow-root > .MuiTableCell-root:last-of-type": { borderRight: 0 },
        }),
        ...(headerColor && {
          "& .MuiTableCell-head": { backgroundColor: headerColor },
        }),
      }}>
      <TableHead>
        <TableRow>
          {objectFields.length > 0 && <TableCell />}
          {primitiveFields.map((field) => {
            const label = headerLabelMap?.[field.name] || field.name;
            const isSorted = sortColumn === field.name;
            return (
              <TableCell
                key={field.name}
                draggable={Boolean(onReorderColumns)}
                onDragStart={(event) => {
                  if (!onReorderColumns) return;
                  if ((event.target as HTMLElement).closest("[data-resize-handle='true']")) {
                    event.preventDefault();
                    return;
                  }
                  setDraggedColumn(field.name);
                  event.dataTransfer.effectAllowed = "move";
                  event.dataTransfer.setData("text/plain", field.name);
                }}
                onDragEnd={() => setDraggedColumn(null)}
                onDragOver={(event) => {
                  if (!onReorderColumns) return;
                  event.preventDefault();
                  event.dataTransfer.dropEffect = "move";
                }}
                onDrop={(event) => {
                  if (!onReorderColumns) return;
                  event.preventDefault();
                  const from = draggedColumn || event.dataTransfer.getData("text/plain");
                  if (from && from !== field.name) onReorderColumns(from, field.name);
                  setDraggedColumn(null);
                }}
                onClick={
                  columnMenuItems
                    ? (event) => {
                        if ((event.target as HTMLElement).closest("[data-resize-handle='true']")) return;
                        setMenuColumn({ field: field.name, anchorEl: event.currentTarget });
                      }
                    : undefined
                }
                sx={{
                  width: getColumnWidth?.(field.name),
                  maxWidth: 900,
                  // The resize handle is absolutely positioned, so the cell has to
                  // be a positioned ancestor. A sticky header already is one, and
                  // overriding that here would unstick it.
                  ...(!stickyHeader && { position: "relative" }),
                  cursor: onReorderColumns ? "grab" : columnMenuItems ? "pointer" : undefined,
                  ...(draggedColumn &&
                    draggedColumn !== field.name && {
                      outline: "1px dashed",
                      outlineColor: "primary.main",
                    }),
                }}>
                <Stack direction="row" spacing={1} alignItems="center" sx={{ py: 1 }}>
                  {renderHeaderLabel ? (
                    <Box sx={{ flex: 1, minWidth: 0 }}>{renderHeaderLabel(field.name, label)}</Box>
                  ) : (
                    <>
                      <FieldKindIcon kind={fieldIndicatorKind(field)} />
                      <Typography variant="body2" fontWeight="bold" sx={{ ...TWO_LINE_CLAMP_SX, flex: 1 }}>
                        {label}
                      </Typography>
                    </>
                  )}
                  {/* State only: which column is sorted, and which way. */}
                  {isSorted && (
                    <Box
                      className="col-sort-arrow"
                      sx={{
                        display: "flex",
                        alignItems: "center",
                        color: "primary.main",
                        transform: sortDirection === "desc" ? "rotate(180deg)" : "none",
                        transition: "transform 0.2s",
                        flexShrink: 0,
                      }}>
                      <ArrowUpwardIcon sx={{ fontSize: 14 }} />
                    </Box>
                  )}
                </Stack>
                {onHeaderResizeStart && (
                  <Box
                    data-resize-handle="true"
                    onClick={(event) => event.stopPropagation()}
                    onMouseDown={(event) => onHeaderResizeStart(event, field.name)}
                    sx={{
                      position: "absolute",
                      top: 0,
                      right: -1,
                      width: 5,
                      height: "100%",
                      cursor: "col-resize",
                      userSelect: "none",
                      zIndex: 2,
                      transition: "background-color 0.15s ease",
                      "&:hover": { backgroundColor: "primary.main" },
                    }}
                  />
                )}
              </TableCell>
            );
          })}
        </TableRow>
      </TableHead>
      <TableBody>
        {data.features.length === 0 && (
          <TableRow>
            <TableCell align="center" colSpan={Math.max(columnCount, 1)} sx={{ borderBottom: "none" }}>
              {emptyMessage || <NoValuesFound />}
            </TableCell>
          </TableRow>
        )}
        {data.features.map((row, index) => (
          // Position first, so the key is unique even if the caller hands us the
          // same feature twice (paged lists that accumulate can). The id keeps
          // identity tied to the feature, so an expanded object row does not
          // stay open over a different feature after a sort.
          <FeatureRow
            key={`${index}-${row.id ?? ""}`}
            row={row}
            primitiveFields={primitiveFields}
            objectFields={objectFields}
            formatCellValue={formatCellValue}
            getColumnWidth={getColumnWidth}
          />
        ))}
      </TableBody>
    </Table>

    {/* Column menu — the host supplies the items, the table owns the anchor. */}
    <Menu
      open={!!menuColumn}
      anchorEl={menuColumn?.anchorEl ?? null}
      onClose={() => setMenuColumn(null)}
      anchorOrigin={{ vertical: "bottom", horizontal: "left" }}
      transformOrigin={{ vertical: "top", horizontal: "left" }}
      slotProps={{ paper: { sx: COLUMN_MENU_PAPER_SX } }}>
      {menuItems.flatMap((item) => {
        const entry = (
          <MenuItem
            key={item.key}
            onClick={() => {
              const anchorEl = menuColumn?.anchorEl;
              setMenuColumn(null);
              if (anchorEl) item.onSelect(anchorEl);
            }}>
            {item.icon && <ListItemIcon>{item.icon}</ListItemIcon>}
            <ListItemText>{item.label}</ListItemText>
          </MenuItem>
        );
        return item.dividerBefore
          ? [<Divider key={`${item.key}-divider`} sx={COLUMN_MENU_DIVIDER_SX} />, entry]
          : [entry];
      })}
    </Menu>
    </>
  );
};

export default FeatureTable;
