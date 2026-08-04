import ArrowDownwardIcon from "@mui/icons-material/ArrowDownward";
import ArrowUpwardIcon from "@mui/icons-material/ArrowUpward";
import BarChartIcon from "@mui/icons-material/BarChart";
import CalculateIcon from "@mui/icons-material/Calculate";
import CloseIcon from "@mui/icons-material/Close";
import DeleteIcon from "@mui/icons-material/Delete";
import DownloadIcon from "@mui/icons-material/Download";
import EditIcon from "@mui/icons-material/Edit";
import FilterAltIcon from "@mui/icons-material/FilterAlt";
import LockIcon from "@mui/icons-material/Lock";
import PushPinIcon from "@mui/icons-material/PushPin";
import PushPinOutlinedIcon from "@mui/icons-material/PushPinOutlined";
import bbox from "@turf/bbox";
import dayjs from "dayjs";
import utc from "dayjs/plugin/utc";

import { ICON_NAME, Icon } from "@p4b/ui/components/Icon";
import { TEMPORAL_VALUE_FORMAT } from "@p4b/ui/components/temporalFormats";
import FullscreenIcon from "@mui/icons-material/Fullscreen";
import FullscreenExitIcon from "@mui/icons-material/FullscreenExit";
import SearchIcon from "@mui/icons-material/Search";
import { alpha, emphasize } from "@mui/material/styles";
import {
  Badge,
  Box,
  Button,
  CircularProgress,
  Divider,
  IconButton,
  InputAdornment,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Menu,
  MenuItem,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TablePagination,
  TableRow,
  TextField,
  Tooltip,
  Typography,
} from "@mui/material";
import type { Theme } from "@mui/material/styles";
import { debounce } from "@mui/material/utils";
import { useParams } from "next/navigation";
import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { toast } from "react-toastify";

import {
  deleteColumn,
  deleteFeaturesBulk,
  useDatasetCollectionItems,
  useLayerQueryables,
} from "@/lib/api/layers";
import type { FieldKind } from "@/lib/validations/layer";
import { BOOLEAN_SELECT_ITEMS, parseBooleanInput } from "@/lib/utils/fieldInput";
import { formatFieldValue } from "@/lib/utils/formatFieldValue";
import FieldKindIcon, { fieldIndicatorKind } from "@/components/common/FieldKindIcon";
import { COLUMN_MENU_DIVIDER_SX, COLUMN_MENU_PAPER_SX } from "@/components/common/columnMenuStyles";
import { MAX_EDITABLE_LAYER_SIZE } from "@/lib/constants";
import type { GetCollectionItemsQueryParams } from "@/lib/validations/layer";
import type { ProjectLayer } from "@/lib/validations/project";

import {
  addPendingFeature,
  commitFeature,
  startEditing,
  stopEditing,
  updatePendingProperties,
} from "@/lib/store/featureEditor/slice";
import { setSelectedLayers } from "@/lib/store/layer/slice";
import { setActiveRightPanel, setHighlightedFeature, setPopupInfo } from "@/lib/store/map/slice";
import { MapSidebarItemID } from "@/types/map/common";
import { useAppDispatch, useAppSelector } from "@/hooks/store/ContextHooks";
import { useMap } from "react-map-gl/maplibre";
import useLayerFields from "@/hooks/map/CommonHooks";

import { updateProjectLayer, useProjectLayers } from "@/lib/api/projects";
import { useUserProfile } from "@/lib/api/users";
import ColumnStatsPanel from "@/components/map/panels/ColumnStatsPanel";
import ColumnFilterPopover from "@/components/map/panels/ColumnFilterPopover";
import { filterColumnType } from "@/lib/utils/columnFilterOperators";
import useProjectLayerFilterController from "@/hooks/map/useProjectLayerFilterController";
import ConfirmModal from "@/components/modals/Confirm";
import EditFieldsModal from "@/components/modals/EditFields";

dayjs.extend(utc);

type SortDirection = "asc" | "desc";
type EditingCell = { rowId: string; column: string } | null;
type DirtyCell = { rowId: string; column: string; originalValue: unknown; newValue: unknown };

interface EditableDataTableProps {
  layerId: string;
  projectLayer: ProjectLayer;
  layerName?: string;
  isExpanded?: boolean;
  isEditor?: boolean;
  onToggleExpand?: () => void;
  onClose?: () => void;
  onDownload?: () => void;
}

const ROWS_PER_PAGE_OPTIONS = [10, 25, 50, 100];

const EditableDataTable: React.FC<EditableDataTableProps> = ({
  layerId,
  projectLayer,
  layerName,
  isExpanded,
  isEditor = true,
  onToggleExpand,
  onClose,
  onDownload,
}) => {
  const { t } = useTranslation("common");
  const dispatch = useAppDispatch();
  const { map } = useMap();
  const { projectId } = useParams();
  const { userProfile } = useUserProfile();
  const { layers: projectLayers, mutate: mutateProjectLayers } = useProjectLayers(projectId as string);
  const activeRightPanel = useAppSelector((state) => state.map.activeRightPanel);
  const editLayerId = useAppSelector((state) => state.featureEditor.activeLayerId);
  const pendingFeatures = useAppSelector((state) => state.featureEditor.pendingFeatures);
  const isEditing = editLayerId === layerId;
  const { layerFields, isLoading: areFieldsLoading } = useLayerFields(layerId);
  const { queryables, mutate: mutateQueryables } = useLayerQueryables(layerId);

  // CQL filter from layer settings — applied to table queries and stats
  const cqlArgs = projectLayer?.query?.cql?.args;
  const activeFilterCount = cqlArgs?.length ?? 0;
  const cqlFilter = useMemo(() => {
    const cql = projectLayer?.query?.cql;
    if (!cql || !cql.args?.length) return undefined;
    return JSON.stringify(cql);
  }, [projectLayer?.query?.cql]);

  // Pagination state
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(25);

  // Sort state
  const [sortBy, setSortBy] = useState<string | undefined>(undefined);
  const [sortDirection, setSortDirection] = useState<SortDirection>("asc");

  // Selection state (single row)
  const [selectedRowId, setSelectedRowId] = useState<string | null>(null);

  // Editing state
  const [editingCell, setEditingCell] = useState<EditingCell>(null);
  const [editValue, setEditValue] = useState<string>("");

  // Dirty tracking
  const [dirtyCells, setDirtyCells] = useState<Map<string, DirtyCell>>(new Map());

  // Search state
  const [searchOpen, setSearchOpen] = useState(false);
  const [searchText, setSearchText] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");

  // eslint-disable-next-line react-hooks/exhaustive-deps
  const debouncedSetSearch = useCallback(debounce((val: string) => setDebouncedSearch(val), 400), []);

  // Column header menu state
  const [columnMenuAnchor, setColumnMenuAnchor] = useState<HTMLElement | null>(null);
  const [columnMenuField, setColumnMenuField] = useState<string | null>(null);

  // Edit fields modal state
  const [editFieldsOpen, setEditFieldsOpen] = useState(false);
  const [editFieldsInitialField, setEditFieldsInitialField] = useState<string | null>(null);

  // Stop editing confirmation state
  const [stopEditConfirmOpen, setStopEditConfirmOpen] = useState(false);

  // Delete column confirmation state
  const [deleteColumnConfirmOpen, setDeleteColumnConfirmOpen] = useState(false);
  const [pendingDeleteColumn, setPendingDeleteColumn] = useState<string | null>(null);

  // Column stats state
  const [statsColumn, setStatsColumn] = useState<string | null>(null);
  const statsNavRef = useRef(false); // true when navigating via prev/next buttons

  // Column filter popover state
  const [quickFilterAnchor, setQuickFilterAnchor] = useState<HTMLElement | null>(null);
  const [quickFilterColumn, setQuickFilterColumn] = useState<string | null>(null);

  // Filters live on the project layer, shared with the layer Filter panel.
  const filterController = useProjectLayerFilterController({
    projectId: projectId as string,
    projectLayer,
    canEdit: isEditor,
  });

  // Drives the column menu's "Filter" vs "Edit filter" wording. Filter state is
  // shown in the layer Filter panel and the toolbar's badge, not on the column.
  const filteredColumns = useMemo(
    () => new Set(filterController.expressions.map((e) => e.attribute)),
    [filterController.expressions]
  );

  // Row context menu state
  const [rowMenuAnchor, setRowMenuAnchor] = useState<{ top: number; left: number } | null>(null);
  const [rowMenuRowId, setRowMenuRowId] = useState<string | null>(null);
  const tableContainerRef = useRef<HTMLDivElement>(null);

  // Column resize state
  const [columnWidths, setColumnWidths] = useState<Record<string, number>>({});
  const activeResizeRef = useRef<{
    columnKey: string;
    startX: number;
    startWidth: number;
  } | null>(null);

  // Frozen (pinned-left) columns and column widths — persisted per project
  // layer under other_properties.table_config so they survive reloads.
  const tableConfig = useMemo(() => {
    return ((projectLayer.other_properties as Record<string, unknown> | null | undefined)
      ?.table_config ?? {}) as { frozen_columns?: unknown; column_widths?: unknown };
  }, [projectLayer.other_properties]);

  const frozenColumns = useMemo<string[]>(() => {
    if (!Array.isArray(tableConfig.frozen_columns)) return [];
    const valid = new Set(layerFields.map((f) => f.name));
    return tableConfig.frozen_columns.filter(
      (c): c is string => typeof c === "string" && valid.has(c)
    );
  }, [tableConfig, layerFields]);

  // Seed widths from the persisted config; in-session drags take precedence.
  // Without this, the sticky offsets of the 2nd+ frozen column would be
  // computed from fallback widths that don't match the rendered widths.
  const persistedWidths = useMemo<Record<string, number>>(() => {
    const out: Record<string, number> = {};
    if (tableConfig.column_widths && typeof tableConfig.column_widths === "object") {
      for (const [k, v] of Object.entries(tableConfig.column_widths as Record<string, unknown>)) {
        if (typeof v === "number" && Number.isFinite(v) && v > 0) out[k] = v;
      }
    }
    return out;
  }, [tableConfig]);

  useEffect(() => {
    setColumnWidths((prev) => ({ ...persistedWidths, ...prev }));
  }, [persistedWidths]);

  // Filter to primitive fields only (no objects/geometry); frozen columns
  // render first, in their frozen order.
  const displayFields = useMemo(() => {
    const primitive = layerFields.filter((f) => f.type !== "object" && f.type !== "geometry");
    if (frozenColumns.length === 0) return primitive;
    const frozen = frozenColumns
      .map((name) => primitive.find((f) => f.name === name))
      .filter((f): f is (typeof primitive)[number] => !!f);
    return [...frozen, ...primitive.filter((f) => !frozenColumns.includes(f.name))];
  }, [layerFields, frozenColumns]);

  // Sticky left offset per frozen column: row-number column (48px) plus the
  // widths of all frozen columns before it. Frozen columns always have an
  // entry in columnWidths (set when freezing), 160 is a safety fallback.
  const ROW_NUMBER_COL_WIDTH = 48;
  const FROZEN_FALLBACK_WIDTH = 160;
  const frozenOffsets = useMemo<Record<string, number>>(() => {
    const offsets: Record<string, number> = {};
    let left = ROW_NUMBER_COL_WIDTH;
    for (const name of frozenColumns) {
      offsets[name] = left;
      left += columnWidths[name] ?? FROZEN_FALLBACK_WIDTH;
    }
    return offsets;
  }, [frozenColumns, columnWidths]);

  // Frozen columns must render at exactly the width the offset math assumes,
  // so their explicit width always resolves (fallback included).
  const effectiveColumnWidth = useCallback(
    (name: string): number | undefined =>
      frozenOffsets[name] !== undefined
        ? (columnWidths[name] ?? FROZEN_FALLBACK_WIDTH)
        : columnWidths[name],
    [frozenOffsets, columnWidths]
  );

  // Per-column metadata from queryables: kind, is_computed, display_config
  // Keyed by field name for O(1) lookup during rendering
  const columnMeta = useMemo(() => {
    const meta: Record<
      string,
      { kind: FieldKind; iconKind: FieldKind; isComputed: boolean; displayConfig: Record<string, unknown> }
    > = {};
    if (!queryables?.properties) return meta;
    for (const [fieldName, prop] of Object.entries(queryables.properties)) {
      // Infer kind from JSON type if not explicitly provided by the backend.
      // Formula columns format and edit as their inferred result kind.
      const declaredKind = (prop as { kind?: string }).kind;
      const rawKind =
        declaredKind === "formula"
          ? ((prop as { output_kind?: string }).output_kind ?? "string")
          : declaredKind;
      const kind: FieldKind =
        rawKind === "area" ||
        rawKind === "length" ||
        rawKind === "perimeter" ||
        rawKind === "datetime" ||
        rawKind === "boolean"
          ? rawKind
          : rawKind === "number" || prop.type === "number" || prop.type === "integer"
            ? "number"
            : prop.type === "boolean"
              ? "boolean"
              : "string";
      const isComputed = !!(prop as { is_computed?: boolean }).is_computed;
      const displayConfig = ((prop as { display_config?: Record<string, unknown> }).display_config) ?? {};
      // The header icon shows the declared kind (a formula column keeps the
      // formula icon), while `kind` drives value formatting and editing.
      const iconKind: FieldKind = declaredKind === "formula" ? "formula" : kind;
      meta[fieldName] = { kind, iconKind, isComputed, displayConfig };
    }
    return meta;
  }, [queryables]);

  // Build search CQL — OR across all display fields (temporary, not persisted)
  const searchCql = useMemo(() => {
    const term = debouncedSearch.trim();
    if (!term || displayFields.length === 0) return undefined;
    const isNum = !isNaN(Number(term));
    const args: object[] = [];
    for (const field of displayFields) {
      if (field.type === "string") {
        args.push({ op: "like", args: [{ property: field.name }, `%${term}%`] });
      } else if ((field.type === "number" || field.type === "integer") && isNum) {
        args.push({ op: "=", args: [{ property: field.name }, Number(term)] });
      }
    }
    if (args.length === 0) return undefined;
    return args.length === 1 ? args[0] : { op: "or", args };
  }, [debouncedSearch, displayFields]);

  // Combine layer CQL filter + search CQL into one filter param
  const combinedFilter = useMemo(() => {
    const layerCql = projectLayer?.query?.cql;
    const hasLayerCql = layerCql && layerCql.args?.length;
    if (!hasLayerCql && !searchCql) return undefined;
    if (!hasLayerCql) return JSON.stringify(searchCql);
    if (!searchCql) return JSON.stringify(layerCql);
    // Merge: AND(layerFilter, searchFilter)
    return JSON.stringify({ op: "and", args: [layerCql, searchCql] });
  }, [projectLayer?.query?.cql, searchCql]);

  // Build query params
  const queryParams = useMemo<GetCollectionItemsQueryParams>(() => {
    const params: GetCollectionItemsQueryParams = {
      limit: rowsPerPage,
      offset: page * rowsPerPage,
    };
    if (sortBy) {
      params.sortby = sortDirection === "desc" ? `-${sortBy}` : sortBy;
    }
    if (combinedFilter) {
      params.filter = combinedFilter;
    }
    return params;
  }, [page, rowsPerPage, sortBy, sortDirection, combinedFilter]);

  // Fetch data
  const { data: collectionData, isLoading, mutate } = useDatasetCollectionItems(layerId, queryParams);

  const filteredFeatures = collectionData?.features || [];

  // Reset page when layer changes
  useEffect(() => {
    setPage(0);
    setSelectedRowId(null);
    setDirtyCells(new Map());
    setEditingCell(null);
    setSearchText("");
    setDebouncedSearch("");
    setSearchOpen(false);
    setStatsColumn(null);
    dispatch(setHighlightedFeature(undefined));
  }, [layerId, dispatch]);

  // Reset page to 0 when the active filter changes so results are always
  // visible. Compare by VALUE: saves and table-config updates recreate the
  // project layer (and its query object) with identical content, and an
  // identity-based reset would wipe the page + scroll position on every
  // cell edit.
  const combinedFilterKey = useMemo(() => JSON.stringify(combinedFilter ?? null), [combinedFilter]);
  useEffect(() => {
    setPage(0);
  }, [combinedFilterKey]);

  // Clear highlight on unmount (table closed)
  useEffect(() => {
    return () => {
      dispatch(setHighlightedFeature(undefined));
    };
  }, [dispatch]);

  // Scroll to active stats column only when navigating via prev/next
  useEffect(() => {
    if (!statsNavRef.current || !statsColumn || !tableContainerRef.current) return;
    statsNavRef.current = false;
    const idx = displayFields.findIndex((f) => f.name === statsColumn);
    if (idx < 0) return;
    // Find the header cell by index (+1 for the row-number column)
    const headerRow = tableContainerRef.current.querySelector("thead tr");
    const cell = headerRow?.children[idx + 1] as HTMLElement | undefined;
    if (cell) {
      cell.scrollIntoView({ behavior: "smooth", block: "nearest", inline: "nearest" });
    }
  }, [statsColumn, displayFields]);

  // --- Column Resize ---

  const startColumnResize = useCallback(
    (event: React.MouseEvent, columnKey: string) => {
      event.preventDefault();
      event.stopPropagation();
      const currentWidth = (event.currentTarget.parentElement as HTMLElement | null)?.getBoundingClientRect().width;
      activeResizeRef.current = {
        columnKey,
        startX: event.clientX,
        startWidth: columnWidths[columnKey] ?? currentWidth ?? 140,
      };
    },
    [columnWidths]
  );

  useEffect(() => {
    const handleMouseMove = (event: MouseEvent) => {
      const activeResize = activeResizeRef.current;
      if (!activeResize) return;
      const nextWidth = Math.max(60, Math.min(600, activeResize.startWidth + (event.clientX - activeResize.startX)));
      setColumnWidths((prev) => {
        const next = { ...prev, [activeResize.columnKey]: nextWidth };
        widthsLiveRef.current = next;
        return next;
      });
    };

    const handleMouseUp = () => {
      if (activeResizeRef.current) {
        activeResizeRef.current = null;
        // Persist the final width so sticky offsets stay correct on reload
        persistWidthsRef.current();
      }
    };

    window.addEventListener("mousemove", handleMouseMove);
    window.addEventListener("mouseup", handleMouseUp);
    return () => {
      window.removeEventListener("mousemove", handleMouseMove);
      window.removeEventListener("mouseup", handleMouseUp);
    };
  }, []);

  // --- Sort ---

  const handleSort = (field: string, direction?: SortDirection) => {
    if (direction) {
      setSortBy(field);
      setSortDirection(direction);
    } else if (sortBy === field) {
      setSortDirection((prev) => (prev === "asc" ? "desc" : "asc"));
    } else {
      setSortBy(field);
      setSortDirection("asc");
    }
    setPage(0);
  };

  // --- Selection (single row) ---

  const editorActiveFeatureId = useAppSelector((state) => state.featureEditor.activeFeatureId);

  const selectRow = (rowId: string) => {
    setSelectedRowId(rowId);
    dispatch(setPopupInfo(undefined));

    // Highlight feature on the map (only outside edit mode)
    if (!isEditing) {
      const feature = collectionData?.features.find((f, i) => `${f.id}-${page}-${i}` === rowId);
      if (feature) {
        // Determine the MapLibre layer type from the geometry type
        const geomType = projectLayer.feature_layer_geometry_type;
        const isCustomMarker = !!projectLayer.properties?.["custom_marker"];
        const layerType = geomType === "polygon" ? "fill" : geomType === "line" ? "line" : isCustomMarker ? "symbol" : "circle";
        dispatch(setHighlightedFeature({
          id: feature.id != null ? Number(feature.id) : undefined,
          properties: feature.properties || {},
          layer: { id: projectLayer.id.toString(), type: layerType },
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        } as any));
      }
    }
  };

  // Edit-tool → table sync: picking a feature on the map with the edit tools
  // selects its table row, so the two selections can never point at
  // different features. New features drawn in draw mode have UUID ids that
  // don't match any row and are ignored.
  useEffect(() => {
    if (!isEditing || !editorActiveFeatureId || !collectionData?.features) return;
    const idx = collectionData.features.findIndex((f) => String(f.id) === editorActiveFeatureId);
    if (idx < 0) return;
    setSelectedRowId(`${collectionData.features[idx].id}-${page}-${idx}`);
  }, [editorActiveFeatureId, isEditing, collectionData, page]);

  const handleRowDoubleClick = (rowId: string) => {
    if (!map) return;
    const feature = collectionData?.features.find((f, i) => `${f.id}-${page}-${i}` === rowId);
    if (feature?.geometry) {
      const bounds = bbox(feature) as [number, number, number, number];
      map.fitBounds(bounds, { padding: 100, maxZoom: 18, duration: 1000 });
    }
  };

  // --- Cell Editing ---

  const getCellValue = (rowId: string, column: string, originalValue: unknown): unknown => {
    const key = `${rowId}:${column}`;
    const dirty = dirtyCells.get(key);
    return dirty ? dirty.newValue : originalValue;
  };

  // Track selected (highlighted) cell — separate from editing
  const [selectedCell, setSelectedCell] = useState<{ rowId: string; column: string } | null>(null);

  // Clear dirty CELL state when editing stops or pending features are
  // cleared (save/discard). Row selection and its map highlight survive a
  // save on purpose — losing them forced users to re-find their place.
  const pendingCount = Object.keys(pendingFeatures).length;
  useEffect(() => {
    if (!isEditing || pendingCount === 0) {
      setDirtyCells(new Map());
      setEditingCell(null);
      setSelectedCell(null);
      dispatch(setHighlightedFeature(undefined));
    }
  }, [isEditing, pendingCount, dispatch]);

  const handleCellClick = (rowId: string, column: string, value: unknown) => {
    if (!isEditing) return; // Cells are only editable in edit mode
    // Computed columns are always read-only — never enter edit mode
    if (columnMeta[column]?.isComputed) return;
    // Already editing this cell: ignore. Clicks inside the editor bubble up
    // to the cell through the React tree — including clicks on the boolean
    // select's menu, which renders in a portal — and re-entering edit mode
    // here would reseed editValue with the stored value, so the later blur
    // commit would silently undo the selection the user just made.
    if (editingCell?.rowId === rowId && editingCell?.column === column) return;
    // First click on a row only selects it; a click within the already
    // selected row opens that cell's editor directly. selectedRowId still
    // holds the pre-click value here (selectRow ran in the same event), so
    // this compares against the row that was selected before the click.
    if (selectedRowId !== rowId) {
      setSelectedCell(null);
      setEditingCell(null);
      return;
    }
    setSelectedCell({ rowId, column });
    setEditingCell({ rowId, column });
    const displayValue = getCellValue(rowId, column, value);
    if (displayValue === null || displayValue === undefined) {
      setEditValue("");
    } else if (columnMeta[column]?.kind === "datetime") {
      // The native datetime-local input needs the UTC wall time without
      // offset suffix, not the serialized "...Z" form
      const parsed = dayjs.utc(String(displayValue));
      setEditValue(parsed.isValid() ? parsed.format(TEMPORAL_VALUE_FORMAT) : String(displayValue));
    } else {
      setEditValue(String(displayValue));
    }
  };

  // Commits the current edit. `rawValue` overrides the editValue state for
  // editors that commit synchronously on change (boolean select) instead of
  // on blur, where the state update would not be visible yet.
  const commitCellEdit = (rawValue?: string) => {
    if (!editingCell) return;
    const editedValue = rawValue ?? editValue;

    const { rowId, column } = editingCell;
    const feature = collectionData?.features.find((f, i) => `${f.id}-${page}-${i}` === rowId);
    const originalValue = feature?.properties?.[column];
    const key = `${rowId}:${column}`;

    // Parse the value based on field type
    const field = displayFields.find((f) => f.name === column);
    let parsedValue: unknown = editedValue;
    if (field?.type === "number" || field?.type === "integer") {
      parsedValue = editedValue === "" ? null : Number(editedValue);
    } else if (columnMeta[column]?.kind === "boolean") {
      parsedValue = parseBooleanInput(editedValue);
    } else if (editedValue === "") {
      parsedValue = null;
    }

    // Check if value actually changed. Datetimes compare as instants: the
    // editor holds "YYYY-MM-DDTHH:mm:ss" while the stored value may carry
    // fractional seconds and a "Z" suffix for the same point in time.
    const isSameDatetime =
      columnMeta[column]?.kind === "datetime" &&
      typeof parsedValue === "string" &&
      typeof originalValue === "string" &&
      dayjs.utc(parsedValue).valueOf() === dayjs.utc(originalValue).valueOf();
    const unchanged = parsedValue === originalValue || isSameDatetime || (parsedValue === null && (originalValue === null || originalValue === undefined));
    if (unchanged) {
      setDirtyCells((prev) => {
        const next = new Map(prev);
        next.delete(key);
        return next;
      });
    } else {
      setDirtyCells((prev) => {
        const next = new Map(prev);
        next.set(key, { rowId, column, originalValue, newValue: parsedValue });
        return next;
      });

      // Dispatch to Redux pending features when in edit mode
      if (isEditing && feature) {
        const featureId = getFeatureId(rowId);
        const existingPending = pendingFeatures[featureId];
        if (existingPending) {
          // Update existing pending feature's properties
          dispatch(updatePendingProperties({
            id: featureId,
            properties: { ...existingPending.properties, [column]: parsedValue },
          }));
        } else {
          // Create a new pending feature for this row
          dispatch(addPendingFeature({
            id: featureId,
            drawFeatureId: null,
            geometry: (feature.geometry as GeoJSON.Geometry) || null,
            properties: { ...feature.properties, [column]: parsedValue },
            committed: false,
            action: "update",
            originalGeometry: (feature.geometry as GeoJSON.Geometry) || null,
            originalProperties: { ...feature.properties },
          }));
        }
        // Auto-commit table edits (no "Done" button needed for inline editing)
        if (!pendingFeatures[featureId]?.committed) {
          dispatch(commitFeature(featureId));
        }
      }
    }

    setEditingCell(null);
    setSelectedCell(null);
  };

  const handleCellBlur = () => commitCellEdit();

  const handleCellKeyDown = (event: React.KeyboardEvent) => {
    if (event.key === "Enter") {
      handleCellBlur();
    } else if (event.key === "Escape") {
      setEditingCell(null);
    }
  };

  // --- Delete Column ---

  const handleDeleteColumnRequest = (columnName: string) => {
    setPendingDeleteColumn(columnName);
    setDeleteColumnConfirmOpen(true);
  };

  const handleDeleteColumnConfirm = async () => {
    if (!pendingDeleteColumn) return;
    const columnName = pendingDeleteColumn;
    setDeleteColumnConfirmOpen(false);
    setPendingDeleteColumn(null);
    try {
      await deleteColumn(layerId, columnName);
      // Clear any state referencing the deleted column
      if (statsColumn === columnName) setStatsColumn(null);
      if (quickFilterColumn === columnName) {
        setQuickFilterColumn(null);
        setQuickFilterAnchor(null);
      }
      if (sortBy === columnName) {
        setSortBy(undefined);
        setSortDirection("asc");
      }
      // Refresh data and schema
      mutate();
      mutateQueryables();
      // Optimistically update project layers for tile cache busting
      if (projectLayers) {
        const now = new Date().toISOString();
        mutateProjectLayers(
          projectLayers.map((l) =>
            l.layer_id === layerId ? { ...l, updated_at: now } : l
          ),
          { revalidate: false },
        );
      }
      toast.success(t("column_deleted", { defaultValue: "Column deleted" }));
    } catch (error) {
      toast.error(t("error_deleting_column", { defaultValue: "Failed to delete column" }));
      console.error("Delete column error:", error);
    }
  };


  // --- Column Header Menu ---

  const columnMenuWidthRef = useRef<number | null>(null);

  const handleColumnMenuOpen = (event: React.MouseEvent<HTMLElement>, fieldName: string) => {
    event.preventDefault();
    event.stopPropagation();
    // Remember the header cell's rendered width: freezing needs a concrete
    // width to compute the next column's sticky offset.
    columnMenuWidthRef.current = event.currentTarget.closest("th")?.offsetWidth ?? null;
    setColumnMenuAnchor(event.currentTarget);
    setColumnMenuField(fieldName);
  };

  // Persist table preferences (frozen columns + column widths) under
  // other_properties.table_config: optimistic local update drives the UI;
  // only editors persist (viewers get session-local behavior that resets on
  // revalidation).
  const persistTableConfig = useCallback(
    async (nextFrozen: string[], nextWidths: Record<string, number>) => {
      if (!projectLayers || !projectId) return;
      const layers = JSON.parse(JSON.stringify(projectLayers)) as ProjectLayer[];
      const index = layers.findIndex((l) => l.id === projectLayer.id);
      if (index < 0) return;
      const other = (layers[index].other_properties ?? {}) as Record<string, unknown>;
      layers[index].other_properties = {
        ...other,
        table_config: { frozen_columns: nextFrozen, column_widths: nextWidths },
      };
      await mutateProjectLayers(layers, false);
      if (isEditor) {
        try {
          await updateProjectLayer(projectId as string, projectLayer.id, layers[index]);
        } catch (error) {
          console.error("Failed to persist table config:", error);
          await mutateProjectLayers();
        }
      }
    },
    [projectLayers, projectId, projectLayer.id, mutateProjectLayers, isEditor]
  );

  const handleToggleFreeze = useCallback(
    async (fieldName: string) => {
      const isFrozen = frozenColumns.includes(fieldName);
      const nextFrozen = isFrozen
        ? frozenColumns.filter((c) => c !== fieldName)
        : [...frozenColumns, fieldName];

      // Ensure the frozen column has a concrete width for offset math
      let nextWidths = columnWidths;
      if (!isFrozen && !columnWidths[fieldName]) {
        const measured = columnMenuWidthRef.current;
        nextWidths = {
          ...columnWidths,
          [fieldName]: measured && measured > 0 ? measured : FROZEN_FALLBACK_WIDTH,
        };
        setColumnWidths(nextWidths);
      }

      await persistTableConfig(nextFrozen, nextWidths);
    },
    [frozenColumns, columnWidths, persistTableConfig]
  );

  // Latest persist call for the window-level resize handlers (mounted once).
  // widthsLiveRef carries the in-flight drag value: on mouseup the final
  // setColumnWidths may not have re-rendered yet, so state alone would be
  // a few pixels stale.
  const widthsLiveRef = useRef<Record<string, number> | null>(null);
  const persistWidthsRef = useRef<() => void>(() => undefined);
  persistWidthsRef.current = () => {
    void persistTableConfig(frozenColumns, widthsLiveRef.current ?? columnWidths);
  };

  // --- Row Context Menu ---

  const handleRowContextMenu = (event: React.MouseEvent, rowId: string) => {
    event.preventDefault();
    setRowMenuAnchor({ top: event.clientY, left: event.clientX });
    setRowMenuRowId(rowId);
    setSelectedRowId(rowId);
  };

  const handleRowMenuClose = () => {
    setRowMenuAnchor(null);
    setRowMenuRowId(null);
  };

  const handleZoomToFeature = () => {
    if (!rowMenuRowId || !map) return;
    const feature = collectionData?.features.find(
      (f, i) => `${f.id}-${page}-${i}` === rowMenuRowId
    );
    if (feature?.geometry) {
      const bounds = bbox(feature) as [number, number, number, number];
      map.fitBounds(bounds, { padding: 100, maxZoom: 18, duration: 1000 });
    }
    handleRowMenuClose();
  };

  const getFeatureId = (rowId: string): string => {
    const parts = rowId.split("-");
    return parts.slice(0, -2).join("-");
  };

  const handleDeleteRow = async () => {
    if (!rowMenuRowId) return;
    try {
      await deleteFeaturesBulk(layerId, [getFeatureId(rowMenuRowId)]);
      setSelectedRowId(null);
      mutate();
      toast.success(t("rows_deleted", { defaultValue: "{{count}} row(s) deleted", count: 1 }));
    } catch (error) {
      toast.error(t("error_deleting_rows", { defaultValue: "Failed to delete rows" }));
      console.error("Delete error:", error);
    }
    handleRowMenuClose();
  };

  const handleColumnMenuClose = () => {
    setColumnMenuAnchor(null);
    setColumnMenuField(null);
  };

  // --- Pagination ---

  const handleChangePage = (_: unknown, newPage: number) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  const totalCount = collectionData?.numberMatched ?? 0;

  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: "column",
        flex: 1,
        minHeight: 0,
      }}>
      {/* Header / Toolbar — single row */}
      <Box
        sx={{
          display: "flex",
          alignItems: "center",
          minHeight: 42,
          gap: 1,
          px: 1.5,
          py: 0.5,
          borderBottom: "1px solid",
          borderColor: "divider",
          flexShrink: 0,
        }}>
        {/* Left: layer name */}
        <Typography variant="body2" fontWeight="bold" noWrap sx={{ mr: 1 }}>
          {layerName}
        </Typography>

        <Box sx={{ flex: 1 }} />

        {/* Right: action buttons + utility icons */}
        {isEditor && (
          <Button
            size="small"
            variant="outlined"
            startIcon={<EditIcon />}
            onClick={() => {
              setEditFieldsInitialField(null);
              setEditFieldsOpen(true);
            }}
            sx={{ textTransform: "none", whiteSpace: "nowrap" }}>
            {t("edit_fields")}
          </Button>
        )}
        {isEditor && (isEditing || (projectLayer.user_id === userProfile?.id && (!projectLayer.size || projectLayer.size <= MAX_EDITABLE_LAYER_SIZE))) && (
          <Button
            size="small"
            variant="outlined"
            color={isEditing ? "error" : "primary"}
            startIcon={isEditing ? <CloseIcon /> : <EditIcon />}
            onClick={() => {
              if (isEditing) {
                if (pendingCount > 0) {
                  setStopEditConfirmOpen(true);
                } else {
                  dispatch(stopEditing());
                }
              } else {
                dispatch(startEditing({
                  layerId,
                  geometryType: projectLayer.feature_layer_geometry_type as "point" | "line" | "polygon" | null ?? null,
                }));
              }
            }}
            sx={{ textTransform: "none", whiteSpace: "nowrap" }}>
            {isEditing ? t("stop_editing") : t("edit_features")}
          </Button>
        )}

        <Divider orientation="vertical" flexItem sx={{ mx: 0.5 }} />

        {searchOpen ? (
          <TextField
            autoFocus
            size="small"
            placeholder={t("search", { defaultValue: "Search..." })}
            value={searchText}
            onChange={(e) => {
              setSearchText(e.target.value);
              debouncedSetSearch(e.target.value);
              setPage(0);
            }}
            onKeyDown={(e) => {
              if (e.key === "Escape") {
                setSearchOpen(false);
                setSearchText("");
                setDebouncedSearch("");
              }
            }}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon fontSize="small" />
                </InputAdornment>
              ),
              endAdornment: (
                <InputAdornment position="end">
                  <IconButton
                    size="small"
                    onClick={() => {
                      setSearchOpen(false);
                      setSearchText("");
                      setDebouncedSearch("");
                    }}>
                    <CloseIcon sx={{ fontSize: 14 }} />
                  </IconButton>
                </InputAdornment>
              ),
            }}
            sx={{ width: 200, "& .MuiInputBase-root": { height: 28, fontSize: "0.8rem" } }}
          />
        ) : (
          <Tooltip title={t("search", { defaultValue: "Search" })}>
            <IconButton size="small" onClick={() => setSearchOpen(true)}>
              <SearchIcon fontSize="small" />
            </IconButton>
          </Tooltip>
        )}
        <Tooltip title={t("filter", { defaultValue: "Filter" })}>
          <IconButton
            size="small"
            color={activeFilterCount > 0 ? "primary" : "default"}
            onClick={() => {
              if (activeRightPanel === MapSidebarItemID.FILTER) {
                dispatch(setActiveRightPanel(undefined));
              } else {
                dispatch(setSelectedLayers([projectLayer.id]));
                dispatch(setActiveRightPanel(MapSidebarItemID.FILTER));
              }
            }}>
            <Badge
              badgeContent={activeFilterCount}
              color="primary"
              sx={{
                "& .MuiBadge-badge": {
                  fontSize: 9,
                  height: 15,
                  minWidth: 15,
                },
              }}>
              <FilterAltIcon fontSize="small" />
            </Badge>
          </IconButton>
        </Tooltip>
        <Tooltip title={isExpanded ? t("collapse", { defaultValue: "Collapse" }) : t("expand", { defaultValue: "Expand" })}>
          <IconButton size="small" onClick={onToggleExpand}>
            {isExpanded ? <FullscreenExitIcon fontSize="small" /> : <FullscreenIcon fontSize="small" />}
          </IconButton>
        </Tooltip>
        <Tooltip title={t("download", { defaultValue: "Download" })}>
          <span>
            <IconButton size="small" disabled={!onDownload} onClick={onDownload}>
              <DownloadIcon fontSize="small" />
            </IconButton>
          </span>
        </Tooltip>
        {onClose && (
          <Tooltip title={t("close", { defaultValue: "Close" })}>
            <IconButton size="small" onClick={onClose}>
              <CloseIcon fontSize="small" />
            </IconButton>
          </Tooltip>
        )}
      </Box>

      {/* Stop Editing Confirmation */}
      <ConfirmModal
        open={stopEditConfirmOpen}
        title={t("stop_editing")}
        body={t("discard_edits_confirmation")}
        closeText={t("cancel")}
        confirmText={t("discard_edits")}
        onClose={() => setStopEditConfirmOpen(false)}
        onConfirm={() => {
          setStopEditConfirmOpen(false);
          dispatch(stopEditing());
        }}
      />

      {/* Delete Column Confirmation */}
      <ConfirmModal
        open={deleteColumnConfirmOpen}
        title={t("delete_field")}
        body={t("delete_field_confirmation", { name: pendingDeleteColumn })}
        closeText={t("cancel")}
        confirmText={t("delete")}
        onClose={() => {
          setDeleteColumnConfirmOpen(false);
          setPendingDeleteColumn(null);
        }}
        onConfirm={handleDeleteColumnConfirm}
      />

      {/* Edit Fields Modal */}
      <EditFieldsModal
        open={editFieldsOpen}
        onClose={() => {
          setEditFieldsOpen(false);
          setEditFieldsInitialField(null);
          mutate();
          // Optimistically update updated_at so tile URLs get a new cache-buster
          if (projectLayers) {
            const now = new Date().toISOString();
            mutateProjectLayers(
              projectLayers.map((l) =>
                l.layer_id === layerId ? { ...l, updated_at: now } : l
              ),
              { revalidate: false },
            );
          }
        }}
        layerId={layerId}
        initialFieldName={editFieldsInitialField}
      />

      {/* Table + Stats panel side by side */}
      <Box sx={{ display: "flex", flex: 1, minHeight: 0 }}>
      <TableContainer
        ref={tableContainerRef}
        sx={{
          flex: 1,
          minHeight: 0,
          overflow: "auto",
          // Thin, theme-aware scrollbars. The standard properties are what
          // modern Chromium and Firefox honor (matching the app's global
          // scrollbar colors); the -webkit pseudos remain for older engines.
          scrollbarWidth: "thin",
          scrollbarColor: (theme) =>
            `${theme.palette.mode === "dark" ? "#374A62" : theme.palette.grey[400]} transparent`,
          "&::-webkit-scrollbar": { width: 6, height: 6 },
          "&::-webkit-scrollbar-thumb": {
            backgroundColor: (theme) =>
              theme.palette.mode === "dark" ? "#374A62" : theme.palette.grey[400],
            borderRadius: 3,
          },
          "&::-webkit-scrollbar-track": { backgroundColor: "transparent" },
          "&::-webkit-scrollbar-corner": { background: "transparent" },
        }}>
        {(isLoading || areFieldsLoading) && !collectionData ? (
          <Box sx={{ display: "flex", justifyContent: "center", alignItems: "center", height: "100%" }}>
            <CircularProgress size={32} />
          </Box>
        ) : displayFields.length === 0 ? (
          <Box sx={{ display: "flex", justifyContent: "center", alignItems: "center", height: "100%" }}>
            <Typography variant="body2" color="text.secondary">
              {t("no_attributes")}
            </Typography>
          </Box>
        ) : (
          <Table
            size="small"
            stickyHeader
            sx={{
              width: "max-content",
              minWidth: "100%",
              "& .MuiTableCell-root": {
                verticalAlign: "top",
                borderRight: "1px solid",
                borderColor: "divider",
              },
              "& .MuiTableRow-root > .MuiTableCell-root:last-of-type": {
                borderRight: 0,
              },
              "& .MuiTableCell-stickyHeader": {
                backgroundColor: (theme) => emphasize(theme.palette.background.paper, 0.03),
                zIndex: 3,
              },
              // Corner cell (over the row numbers) must stick horizontally too
              // and paint above the column headers scrolling underneath it.
              // Declared here because this selector outranks the cell's own sx.
              "& .MuiTableCell-stickyHeader:first-of-type": {
                left: 0,
                zIndex: 5,
              },
              // Frozen column headers paint above the scrolling headers
              // (same specificity trick as the corner cell above).
              "& .MuiTableCell-stickyHeader.frozen-header": {
                zIndex: 4,
              },
              // Row hover must reach frozen cells too — they're opaque, so
              // the row-level hover background can't show through. Skip
              // cells that already carry a state tint (dirty/selected).
              "& .MuiTableRow-root:hover .frozen-body-cell:not(.frozen-cell-tinted)": {
                background: (theme) =>
                  `linear-gradient(${theme.palette.action.hover}, ${theme.palette.action.hover}), ${theme.palette.background.paper}`,
              },
            }}>
            <TableHead>
              <TableRow>
                {/* Row number column */}
                <TableCell
                  sx={{
                    width: 48,
                    minWidth: 48,
                    maxWidth: 48,
                    position: "sticky",
                    left: 0,
                    zIndex: 4,
                    backgroundColor: (theme) => emphasize(theme.palette.background.paper, 0.03),
                    textAlign: "center",
                    px: 0,
                  }}>
                  <Typography variant="caption" color="text.secondary">
                    #
                  </Typography>
                </TableCell>
                {displayFields.map((field) => {
                  const w = effectiveColumnWidth(field.name);
                  const frozenLeft = frozenOffsets[field.name];
                  return (
                    <TableCell
                      key={field.name}
                      className={frozenLeft !== undefined ? "frozen-header" : undefined}
                      sx={{
                        ...(w ? { width: w, minWidth: w, maxWidth: w } : { minWidth: 100 }),
                        ...(frozenLeft !== undefined && {
                          position: "sticky",
                          left: frozenLeft,
                          backgroundColor: (theme) => emphasize(theme.palette.background.paper, 0.03),
                        }),
                        cursor: "pointer",
                        userSelect: "none",
                        whiteSpace: "nowrap",
                        ...(statsColumn === field.name && {
                          boxShadow: (theme) =>
                            `inset 2px 0 0 0 ${theme.palette.primary.main}, inset -2px 0 0 0 ${theme.palette.primary.main}, inset 0 2px 0 0 ${theme.palette.primary.main}`,
                        }),
                      }}
                      onClick={(e) => handleColumnMenuOpen(e, field.name)}>
                      <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                        <FieldKindIcon kind={columnMeta[field.name]?.iconKind ?? fieldIndicatorKind(field)} />
                        <Typography variant="body2" fontWeight="bold" noWrap sx={{ flex: 1, minWidth: 0 }}>
                          {field.name}
                        </Typography>
                      </Box>
                      {/* Resize handle */}
                      <Box
                        sx={{
                          position: "absolute",
                          top: 0,
                          right: 0,
                          width: 8,
                          height: "100%",
                          cursor: "col-resize",
                          userSelect: "none",
                          zIndex: 2,
                        }}
                        onClick={(e) => e.stopPropagation()}
                        onMouseDown={(e) => startColumnResize(e, field.name)}
                      />
                    </TableCell>
                  );
                })}
              </TableRow>
            </TableHead>
            <TableBody>
              {filteredFeatures.length === 0 && (
                <TableRow>
                  <TableCell colSpan={displayFields.length + 1} align="center" sx={{ py: 4 }}>
                    <Typography variant="body2" color="text.secondary">
                      {t("no_data", { defaultValue: "No data" })}
                    </Typography>
                  </TableCell>
                </TableRow>
              )}
              {filteredFeatures.map((feature, index) => {
                const rowId = `${feature.id}-${page}-${index}`;
                const isSelected = selectedRowId === rowId;
                const isRowDirty = Array.from(dirtyCells.values()).some((c) => c.rowId === rowId);
                const rowNumber = page * rowsPerPage + index + 1;

                return (
                  <TableRow
                    key={rowId}
                    hover
                    selected={isSelected}
                    onClick={() => selectRow(rowId)}
                    onDoubleClick={() => handleRowDoubleClick(rowId)}
                    onContextMenu={(e) => handleRowContextMenu(e, rowId)}
                    sx={{
                      cursor: "pointer",
                      backgroundColor: isRowDirty ? "rgba(255, 193, 7, 0.08)" : undefined,
                    }}>
                    <TableCell
                      sx={{
                        position: "sticky",
                        left: 0,
                        zIndex: 1,
                        // Must be opaque (action.selected/hover are translucent):
                        // scrolled data cells slide underneath and would show through
                        backgroundColor: (theme) =>
                          emphasize(theme.palette.background.paper, isSelected ? 0.08 : 0.03),
                        textAlign: "center",
                        px: 0,
                      }}>
                      <Typography variant="caption" color="text.secondary">
                        {rowNumber}
                      </Typography>
                    </TableCell>
                    {displayFields.map((field) => {
                      const originalValue = feature.properties?.[field.name];
                      const displayValue = getCellValue(rowId, field.name, originalValue);
                      const isEditing = editingCell?.rowId === rowId && editingCell?.column === field.name;
                      const isSelected = selectedCell?.rowId === rowId && selectedCell?.column === field.name;
                      const isDirty = dirtyCells.has(`${rowId}:${field.name}`);
                      const meta = columnMeta[field.name];
                      const isComputed = meta?.isComputed ?? false;
                      const fieldKind = meta?.kind ?? (field.type === "number" ? "number" : "string");
                      const fieldDisplayConfig = meta?.displayConfig ?? {};

                      // Format value using formatFieldValue when the column has a non-trivial kind or display_config
                      const hasNonDefaultDisplay =
                        fieldKind !== "string" || Object.keys(fieldDisplayConfig).length > 0;
                      const formattedValue =
                        displayValue === null || displayValue === undefined
                          ? ""
                          : hasNonDefaultDisplay
                            ? formatFieldValue(displayValue, fieldKind as FieldKind, fieldDisplayConfig)
                            : String(displayValue);

                      const frozenLeft = frozenOffsets[field.name];
                      const bodyWidth = effectiveColumnWidth(field.name);
                      const isRowSelected = selectedRowId === rowId;
                      // Frozen cells must be opaque: scrolled columns slide
                      // underneath. Layer the translucent state tint (cell
                      // state or row selection) over the opaque paper
                      // background via a gradient.
                      // Row selection must match MUI's TableRow.Mui-selected
                      // color exactly (primary at selectedOpacity)
                      const frozenTint = (theme: Theme): string | null =>
                        isDirty
                          ? "rgba(255, 193, 7, 0.12)"
                          : isSelected && !isEditing
                            ? "rgba(128, 128, 128, 0.12)"
                            : isRowSelected
                              ? alpha(theme.palette.primary.main, theme.palette.action.selectedOpacity)
                              : null;
                      return (
                        <TableCell
                          key={field.name}
                          className={
                            frozenLeft !== undefined
                              ? `frozen-body-cell${isDirty || (isSelected && !isEditing) || isRowSelected ? " frozen-cell-tinted" : ""}`
                              : undefined
                          }
                          sx={{
                            ...(bodyWidth ? { width: bodyWidth, minWidth: bodyWidth, maxWidth: bodyWidth } : {}),
                            cursor: isComputed ? "default" : "text",
                            position: "relative",
                            ...(frozenLeft !== undefined && {
                              position: "sticky",
                              left: frozenLeft,
                              zIndex: 1,
                              // Base is plain paper so frozen data cells are
                              // indistinguishable from normal cells; only the
                              // header/row-number chrome uses the emphasized
                              // shade.
                              background: (theme) => {
                                const tint = frozenTint(theme);
                                const base = theme.palette.background.paper;
                                return tint
                                  ? `linear-gradient(${tint}, ${tint}), ${base}`
                                  : base;
                              },
                            }),
                            // Computed columns get a subtle read-only tint
                            // (frozen cells handle their background above)
                            backgroundColor:
                              frozenLeft !== undefined
                                ? undefined
                                : isDirty
                                  ? "rgba(255, 193, 7, 0.12)"
                                  : isComputed
                                    ? (theme) => `${theme.palette.action.disabledBackground}40`
                                    : isSelected && !isEditing
                                      ? "action.hover"
                                      : undefined,
                            p: isEditing ? 0 : undefined,
                            ...(isEditing && {
                              outline: (theme) => `2px solid ${theme.palette.primary.main}`,
                              outlineOffset: -2,
                            }),
                            ...(statsColumn === field.name && {
                              boxShadow: (theme) =>
                                `inset 2px 0 0 0 ${theme.palette.primary.main}, inset -2px 0 0 0 ${theme.palette.primary.main}`,
                            }),
                          }}
                          onClick={(e) => {
                            e.stopPropagation();
                            selectRow(rowId);
                            handleCellClick(rowId, field.name, originalValue);
                          }}>
                          {isEditing ? (
                            fieldKind === "boolean" ? (
                              <TextField
                                select
                                autoFocus
                                fullWidth
                                size="small"
                                value={editValue}
                                onChange={(e) => commitCellEdit(e.target.value)}
                                onBlur={handleCellBlur}
                                variant="outlined"
                                SelectProps={{ defaultOpen: true, displayEmpty: true }}
                                sx={{
                                  "& .MuiInputBase-root": {
                                    fontSize: "0.875rem",
                                    borderRadius: 0,
                                  },
                                  // Match the 6px/16px padding of a small
                                  // TableCell so entering edit mode never
                                  // changes the row height
                                  "& .MuiInputBase-input": {
                                    py: "6px",
                                    px: "16px",
                                  },
                                  "& .MuiOutlinedInput-notchedOutline": {
                                    border: "none",
                                  },
                                }}>
                                {BOOLEAN_SELECT_ITEMS.map((item) => (
                                  <MenuItem key={item.value} value={item.value}>
                                    {item.label}
                                  </MenuItem>
                                ))}
                              </TextField>
                            ) : (
                            <TextField
                              autoFocus
                              fullWidth
                              size="small"
                              value={editValue}
                              onChange={(e) => setEditValue(e.target.value)}
                              onBlur={handleCellBlur}
                              onKeyDown={handleCellKeyDown}
                              type={
                                fieldKind === "datetime"
                                  ? "datetime-local"
                                  : field.type === "number" || field.type === "integer"
                                    ? "number"
                                    : "text"
                              }
                              variant="outlined"
                              sx={{
                                "& .MuiInputBase-root": {
                                  fontSize: "0.875rem",
                                  borderRadius: 0,
                                },
                                // Match the 6px/16px padding of a small
                                // TableCell so entering edit mode never
                                // changes the row height
                                "& .MuiInputBase-input": {
                                  py: "6px",
                                  px: "16px",
                                },
                                "& .MuiOutlinedInput-notchedOutline": {
                                  border: "none",
                                },
                              }}
                            />
                            )
                          ) : (
                            <Box sx={{ display: "flex", alignItems: "center", gap: 0.5 }}>
                              <Typography
                                variant="body2"
                                noWrap
                                sx={{
                                  display: "block",
                                  lineHeight: 1.43,
                                  minHeight: "1.43em",
                                  flex: 1,
                                }}>
                                {formattedValue}
                              </Typography>
                              {isComputed && (
                                <Tooltip title={t("computed_read_only", { defaultValue: "Computed (read-only)" })}>
                                  <LockIcon sx={{ fontSize: 10, color: "text.disabled", flexShrink: 0 }} />
                                </Tooltip>
                              )}
                            </Box>
                          )}
                        </TableCell>
                      );
                    })}
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        )}
      </TableContainer>

      {/* Column Stats Panel */}
      {statsColumn && (
        <ColumnStatsPanel
          layerId={layerId}
          columnName={statsColumn}
          columnType={displayFields.find((f) => f.name === statsColumn)?.type ?? "string"}
          columnKind={columnMeta[statsColumn]?.kind}
          cqlFilter={cqlFilter}
          onClose={() => setStatsColumn(null)}
          onPrev={() => {
            const idx = displayFields.findIndex((f) => f.name === statsColumn);
            const prevIdx = idx <= 0 ? displayFields.length - 1 : idx - 1;
            statsNavRef.current = true;
            setStatsColumn(displayFields[prevIdx].name);
          }}
          onNext={() => {
            const idx = displayFields.findIndex((f) => f.name === statsColumn);
            const nextIdx = idx >= displayFields.length - 1 ? 0 : idx + 1;
            statsNavRef.current = true;
            setStatsColumn(displayFields[nextIdx].name);
          }}
        />
      )}
      </Box>

      {/* Pagination */}
      <TablePagination
        component="div"
        count={totalCount}
        page={page}
        onPageChange={handleChangePage}
        rowsPerPage={rowsPerPage}
        onRowsPerPageChange={handleChangeRowsPerPage}
        rowsPerPageOptions={ROWS_PER_PAGE_OPTIONS}
        sx={{ borderTop: "1px solid", borderColor: "divider", flexShrink: 0 }}
      />

      {/* Column Header Context Menu */}
      <Menu
        anchorEl={columnMenuAnchor}
        open={!!columnMenuAnchor}
        onClose={handleColumnMenuClose}
        slotProps={{ paper: { sx: COLUMN_MENU_PAPER_SX } }}>
        <MenuItem
          onClick={() => {
            if (columnMenuField) handleSort(columnMenuField, "asc");
            handleColumnMenuClose();
          }}>
          <ListItemIcon>
            <ArrowUpwardIcon />
          </ListItemIcon>
          <ListItemText>{t("sort_asc", { defaultValue: "Sort A-Z" })}</ListItemText>
        </MenuItem>
        <MenuItem
          onClick={() => {
            if (columnMenuField) handleSort(columnMenuField, "desc");
            handleColumnMenuClose();
          }}>
          <ListItemIcon>
            <ArrowDownwardIcon />
          </ListItemIcon>
          <ListItemText>{t("sort_desc", { defaultValue: "Sort Z-A" })}</ListItemText>
        </MenuItem>
        <Divider sx={COLUMN_MENU_DIVIDER_SX} />
        <MenuItem
          onClick={() => {
            if (columnMenuField) handleToggleFreeze(columnMenuField);
            handleColumnMenuClose();
          }}>
          <ListItemIcon>
            {columnMenuField && frozenColumns.includes(columnMenuField) ? (
              <PushPinIcon />
            ) : (
              <PushPinOutlinedIcon />
            )}
          </ListItemIcon>
          <ListItemText>
            {columnMenuField && frozenColumns.includes(columnMenuField)
              ? t("unfreeze_column", { defaultValue: "Unfreeze column" })
              : t("freeze_column", { defaultValue: "Freeze column" })}
          </ListItemText>
        </MenuItem>
        <Divider sx={COLUMN_MENU_DIVIDER_SX} />
        {isEditor && (
          <MenuItem
            onClick={() => {
              if (columnMenuField) {
                setEditFieldsInitialField(columnMenuField);
                setEditFieldsOpen(true);
              }
              handleColumnMenuClose();
            }}>
            <ListItemIcon>
              <EditIcon />
            </ListItemIcon>
            <ListItemText>{t("edit_field", { defaultValue: "Edit field" })}</ListItemText>
          </MenuItem>
        )}
        <MenuItem
          onClick={() => {
            if (columnMenuField) setStatsColumn(columnMenuField);
            handleColumnMenuClose();
          }}>
          <ListItemIcon>
            <BarChartIcon />
          </ListItemIcon>
          <ListItemText>{t("view_stats", { defaultValue: "View stats" })}</ListItemText>
        </MenuItem>
        <MenuItem
          onClick={() => {
            if (columnMenuField && columnMenuAnchor) {
              setQuickFilterColumn(columnMenuField);
              setQuickFilterAnchor(columnMenuAnchor.closest("th") ?? columnMenuAnchor);
            }
            handleColumnMenuClose();
          }}>
          <ListItemIcon>
            <FilterAltIcon />
          </ListItemIcon>
          <ListItemText>
            {columnMenuField && filteredColumns.has(columnMenuField)
              ? t("edit_filter", { defaultValue: "Edit filter" })
              : t("add_filter", { defaultValue: "Add filter" })}
          </ListItemText>
        </MenuItem>
        {isEditor && (
          <MenuItem disabled>
            <ListItemIcon>
              <CalculateIcon />
            </ListItemIcon>
            <ListItemText>{t("calculate_field", { defaultValue: "Calculate field" })}</ListItemText>
          </MenuItem>
        )}
        {isEditor && [
          <Divider key="delete-column-divider" sx={COLUMN_MENU_DIVIDER_SX} />,
          <MenuItem
            key="delete-column"
            onClick={() => {
              if (columnMenuField) handleDeleteColumnRequest(columnMenuField);
              handleColumnMenuClose();
            }}
            sx={{ color: "error.main" }}>
            <ListItemIcon>
              <DeleteIcon sx={{ color: "error.main" }} />
            </ListItemIcon>
            <ListItemText>{t("delete_column", { defaultValue: "Delete column" })}</ListItemText>
          </MenuItem>,
        ]}
      </Menu>

      {/* Row Context Menu */}
      <Menu
        open={!!rowMenuAnchor}
        onClose={handleRowMenuClose}
        anchorReference="anchorPosition"
        anchorPosition={rowMenuAnchor ?? undefined}
        slotProps={{
          paper: {
            sx: { minWidth: 220, maxWidth: 340, py: 2 },
          },
        }}
        MenuListProps={{ dense: true, disablePadding: true }}>
        <ListItemButton onClick={handleZoomToFeature}>
          <ListItemIcon sx={{ minWidth: 0, pr: 4 }}>
            <Icon iconName={ICON_NAME.ZOOM_IN} style={{ fontSize: 15 }} htmlColor="inherit" />
          </ListItemIcon>
          <ListItemText primary={t("zoom_to_feature", { defaultValue: "Zoom to feature" })} />
        </ListItemButton>
        {isEditor && (
          <ListItemButton
            onClick={handleDeleteRow}
            sx={{ color: (theme) => theme.palette.error.main }}>
            <ListItemIcon sx={{ minWidth: 0, pr: 4, color: "inherit" }}>
              <Icon iconName={ICON_NAME.TRASH} style={{ fontSize: 15 }} htmlColor="inherit" />
            </ListItemIcon>
            <ListItemText
              primary={t("delete")}
              sx={{ "& .MuiTypography-root": { color: "inherit" } }}
            />
          </ListItemButton>
        )}
      </Menu>

      {/* Column Filter Popover */}
      {quickFilterColumn && (
        <ColumnFilterPopover
          key={quickFilterColumn}
          anchorEl={quickFilterAnchor}
          columnName={quickFilterColumn}
          columnType={filterColumnType({
            type: displayFields.find((f) => f.name === quickFilterColumn)?.type,
            kind: columnMeta[quickFilterColumn]?.kind,
          })}
          iconKind={
            columnMeta[quickFilterColumn]?.iconKind ??
            fieldIndicatorKind(displayFields.find((f) => f.name === quickFilterColumn) ?? {})
          }
          layerId={layerId}
          controller={filterController}
          onClose={() => {
            setQuickFilterAnchor(null);
            setQuickFilterColumn(null);
          }}
        />
      )}
    </Box>
  );
};

// Memoized: the parent DataPanel re-renders on drag start/end (isDragging) and
// the full table is far too heavy to rebuild for a border-color change.
export default React.memo(EditableDataTable);
