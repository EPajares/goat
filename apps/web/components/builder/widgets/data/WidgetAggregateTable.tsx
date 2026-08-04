import ArrowUpwardIcon from "@mui/icons-material/ArrowUpward";
import { Box } from "@mui/material";
import { Table, TableBody, TableCell, TableHead, TableRow, Typography } from "@mui/material";
import React, { useState } from "react";

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

const formatCellValue = (value: unknown): string => {
  if (value === null || value === undefined) return "";
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
};

interface WidgetAggregateTableProps {
  /** Column definitions, in display order. */
  tableColumns: Array<{ key: string; label: string; align?: "left" | "right" }>;
  /** Pre-shaped rows. Collapsible modes mark them with _isParent/_isChild/_isSubHeader. */
  tableRows: Array<Record<string, unknown>>;
  totalsRow?: Record<string, unknown>;
  stickyHeaderEnabled?: boolean;
  headerColor?: string;
  emptyMessage?: React.ReactNode;
  formatCellValueForColumn?: (
    columnKey: string,
    value: unknown,
    row?: Record<string, unknown>
  ) => React.ReactNode;
  getColumnWidth?: (columnKey: string) => number | undefined;
  renderHeaderLabel?: (columnKey: string, label: string, align?: "left" | "right") => React.ReactNode;
  onHeaderResizeStart?: (event: React.MouseEvent, columnKey: string) => void;
  onReorderColumns?: (fromColumnKey: string, toColumnKey: string) => void;
  onRowClick?: (row: Record<string, unknown>, rowIndex: number) => void;
  getRowSx?: (row: Record<string, unknown>) => Record<string, unknown> | undefined;
  onColumnSortClick?: (columnKey: string) => void;
  sortColumn?: string;
  sortDirection?: "asc" | "desc";
}

/**
 * Renders the table widget's aggregated output: grouped metrics and SQL results,
 * including the collapsible parent/child shapes and a totals row.
 *
 * Rows here are already computed, so this takes columns and cells rather than
 * layer features. Record rows come from FeatureTable instead.
 */
const WidgetAggregateTable: React.FC<WidgetAggregateTableProps> = ({
  tableColumns,
  tableRows,
  totalsRow,
  stickyHeaderEnabled = true,
  headerColor,
  emptyMessage,
  formatCellValueForColumn,
  getColumnWidth,
  renderHeaderLabel,
  onHeaderResizeStart,
  onReorderColumns,
  onRowClick,
  getRowSx,
  onColumnSortClick,
  sortColumn,
  sortDirection,
}) => {
  const [draggedColumnKey, setDraggedColumnKey] = useState<string | null>(null);

  const getHeaderCellDropSx = (columnKey: string) => {
    if (!draggedColumnKey || draggedColumnKey === columnKey) return undefined;
    return { outline: "1px dashed", outlineColor: "primary.main" };
  };

  const stickyHeaderCellSx = stickyHeaderEnabled
    ? {
        "& .MuiTableCell-stickyHeader": {
          position: "sticky",
          top: 0,
          zIndex: 3,
          backgroundColor: headerColor ?? "background.paper",
          boxShadow: "inset 0 -1px 0 rgba(0, 0, 0, 0.12)",
        },
      }
    : {
        "& .MuiTableCell-head": {
          position: "relative",
          ...(headerColor ? { backgroundColor: headerColor } : {}),
        },
      };

  return (
    <Table
      size="small"
      stickyHeader={stickyHeaderEnabled}
      sx={{
        tableLayout: "fixed",
        width: "100%",
        "& .MuiTableCell-root": {
          verticalAlign: "top",
          borderRight: 1,
          borderColor: "divider",
        },
        "& .MuiTableRow-root > .MuiTableCell-root:last-of-type": {
          borderRight: 0,
        },
        ...stickyHeaderCellSx,
      }}>
      <TableHead>
        <TableRow>
          {tableColumns.map((column) => (
            <TableCell
              key={column.key}
              align={column.align || "left"}
              draggable={Boolean(onReorderColumns)}
              onDragStart={(event) => {
                if (!onReorderColumns) return;
                const target = event.target as HTMLElement;
                if (target.closest("[data-resize-handle='true']")) {
                  event.preventDefault();
                  return;
                }
                setDraggedColumnKey(column.key);
                event.dataTransfer.effectAllowed = "move";
                event.dataTransfer.setData("text/plain", column.key);
              }}
              onDragEnd={() => setDraggedColumnKey(null)}
              onDragOver={(event) => {
                if (!onReorderColumns) return;
                event.preventDefault();
                event.dataTransfer.dropEffect = "move";
              }}
              onDrop={(event) => {
                if (!onReorderColumns) return;
                event.preventDefault();
                const fromColumnKey = draggedColumnKey || event.dataTransfer.getData("text/plain");
                if (fromColumnKey && fromColumnKey !== column.key) {
                  onReorderColumns(fromColumnKey, column.key);
                }
                setDraggedColumnKey(null);
              }}
              onClick={
                onColumnSortClick
                  ? (e) => {
                      if ((e.target as HTMLElement).closest("[data-resize-handle='true']")) return;
                      onColumnSortClick(column.key);
                    }
                  : undefined
              }
              sx={{
                width: getColumnWidth?.(column.key),
                maxWidth: 900,
                position: "relative",
                cursor: onReorderColumns ? "grab" : onColumnSortClick ? "pointer" : undefined,
                ...getHeaderCellDropSx(column.key),
                ...(onColumnSortClick && {
                  "&:hover .col-sort-arrow": { opacity: sortColumn === column.key ? 1 : 0.35 },
                }),
              }}>
              <Box sx={{ display: "flex", alignItems: "center", justifyContent: "space-between", pr: 0 }}>
                <Box sx={{ flex: 1, minWidth: 0 }}>
                  {renderHeaderLabel ? (
                    renderHeaderLabel(column.key, column.label, column.align || "left")
                  ) : (
                    <Typography
                      variant="body2"
                      fontWeight="bold"
                      align={column.align || "left"}
                      sx={TWO_LINE_CLAMP_SX}>
                      {column.label}
                    </Typography>
                  )}
                </Box>
                {onColumnSortClick && (
                  <Box
                    className="col-sort-arrow"
                    sx={{
                      display: "flex",
                      alignItems: "center",
                      color: "primary.main",
                      opacity: sortColumn === column.key ? 1 : 0,
                      transform:
                        sortColumn === column.key && sortDirection === "desc" ? "rotate(180deg)" : "none",
                      transition: "opacity 0.15s, transform 0.2s",
                      flexShrink: 0,
                      ml: 0.5,
                    }}>
                    <ArrowUpwardIcon sx={{ fontSize: 14 }} />
                  </Box>
                )}
              </Box>
              {onHeaderResizeStart && (
                <Box
                  data-resize-handle="true"
                  onClick={(e) => e.stopPropagation()}
                  onMouseDown={(event) => onHeaderResizeStart(event, column.key)}
                  sx={{
                    position: "absolute",
                    top: 0,
                    right: -1,
                    width: 5,
                    height: "100%",
                    cursor: "col-resize",
                    userSelect: "none",
                    zIndex: 2,
                    backgroundColor: "transparent",
                    transition: "background-color 0.15s ease",
                    "&:hover": {
                      backgroundColor: "primary.main",
                    },
                  }}
                />
              )}
            </TableCell>
          ))}
        </TableRow>
      </TableHead>
      <TableBody>
        {tableRows.length === 0 && (
          <TableRow>
            <TableCell align="center" colSpan={Math.max(tableColumns.length, 1)}>
              {emptyMessage || <NoValuesFound />}
            </TableCell>
          </TableRow>
        )}
        {tableRows.map((row, rowIndex) => (
          <TableRow
            key={`aggregate-row-${rowIndex}`}
            onClick={onRowClick ? () => onRowClick(row, rowIndex) : undefined}
            sx={{
              ...(onRowClick && row._isParent ? { cursor: "pointer" } : {}),
              ...(getRowSx?.(row) || {}),
            }}>
            {tableColumns.map((column) => (
              <TableCell
                key={`${column.key}-${rowIndex}`}
                align={column.align || "left"}
                sx={{ width: getColumnWidth?.(column.key) }}>
                <Typography variant="body2" sx={TWO_LINE_CLAMP_SX}>
                  {formatCellValueForColumn
                    ? formatCellValueForColumn(column.key, row[column.key], row)
                    : formatCellValue(row[column.key]) || "-"}
                </Typography>
              </TableCell>
            ))}
          </TableRow>
        ))}
        {totalsRow && (
          <TableRow
            sx={{
              "& .MuiTableCell-root": {
                fontWeight: 700,
                backgroundColor: "background.paper",
                borderTop: 1,
                borderColor: "divider",
              },
            }}>
            {tableColumns.map((column) => (
              <TableCell
                key={`aggregate-total-${column.key}`}
                align={column.align || "left"}
                sx={{ width: getColumnWidth?.(column.key) }}>
                <Typography variant="body2" fontWeight="bold">
                  {formatCellValueForColumn
                    ? formatCellValueForColumn(column.key, totalsRow[column.key])
                    : formatCellValue(totalsRow[column.key]) || "-"}
                </Typography>
              </TableCell>
            ))}
          </TableRow>
        )}
      </TableBody>
    </Table>
  );
};

export default WidgetAggregateTable;
