"use client";

import {
  Alert,
  Box,
  Button,
  Chip,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Divider,
  FormControl,
  IconButton,
  InputAdornment,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  MenuItem,
  OutlinedInput,
  Paper,
  Select,
  Stack,
  Tab,
  Tabs,
  TextField,
  Tooltip,
  Typography,
} from "@mui/material";
import dynamic from "next/dynamic";
import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useTranslation } from "react-i18next";

import type { ReactCodeMirrorRef } from "@uiw/react-codemirror";

import { ICON_NAME, Icon } from "@p4b/ui/components/Icon";

import FieldKindIcon, { fieldIndicatorKind } from "@/components/common/FieldKindIcon";

const SqlCodeEditor = dynamic(() => import("./SqlCodeEditor"), { ssr: false });

import type {
  ExpressionPreviewResult,
  FunctionDoc,
  PreviewSqlResponse,
  ValidateExpressionResponse,
  ValidateSqlResponse,
} from "@/lib/api/expressions";
import {
  FUNCTION_CATEGORIES,
  previewExpressionAsAggregation,
  previewSql,
  useExpressionFunctions,
  validateExpression,
  validateSql,
} from "@/lib/api/expressions";

// Operators definition for the formula builder
const OPERATORS = [
  { symbol: "+", label: "Add", syntax: " + " },
  { symbol: "-", label: "Subtract", syntax: " - " },
  { symbol: "*", label: "Multiply", syntax: " * " },
  { symbol: "/", label: "Divide", syntax: " / " },
  { symbol: "%", label: "Modulo", syntax: " % " },
] as const;

// Common SQL aggregate functions for GROUP BY validation
const AGGREGATE_FUNCTIONS = [
  "SUM",
  "AVG",
  "COUNT",
  "MIN",
  "MAX",
  "MEDIAN",
  "STDDEV",
  "STDDEV_POP",
  "STDDEV_SAMP",
  "VARIANCE",
  "VAR_POP",
  "VAR_SAMP",
  "FIRST",
  "LAST",
  "LIST",
  "STRING_AGG",
  "GROUP_CONCAT",
  "BIT_AND",
  "BIT_OR",
  "BIT_XOR",
  "BOOL_AND",
  "BOOL_OR",
  "ARBITRARY",
  "ANY_VALUE",
];

// Field type for the formula builder
export interface FormulaField {
  name: string;
  type: string;
}

// Convert database type to JSON type for type validation
// Handles both raw database types (BIGINT, VARCHAR, etc.) and
// already-normalized types (number, string, integer)
function databaseTypeToJsonType(dbType: string): string {
  const normalizedType = dbType.toLowerCase();

  // Already normalized types (from useLayerFields hook)
  if (normalizedType === "number" || normalizedType === "integer") {
    return "integer"; // Use "integer" which maps to NUMERIC in validator
  }
  if (normalizedType === "string") {
    return "string";
  }
  if (normalizedType === "boolean") {
    return "boolean";
  }
  if (normalizedType === "geometry") {
    return "geometry";
  }

  // Raw database types
  if (
    normalizedType.includes("int") ||
    normalizedType.includes("bigint") ||
    normalizedType.includes("smallint")
  ) {
    return "integer";
  }
  if (
    normalizedType.includes("float") ||
    normalizedType.includes("double") ||
    normalizedType.includes("decimal") ||
    normalizedType.includes("numeric") ||
    normalizedType.includes("real")
  ) {
    return "number";
  }
  if (normalizedType.includes("bool")) {
    return "boolean";
  }
  if (normalizedType.includes("geom") || normalizedType.includes("geography")) {
    return "geometry";
  }
  return "string";
}

// Convert field/database type to SQL type names accepted by DuckDB parser/validator
function databaseTypeToSqlType(dbType: string): string {
  const normalizedType = dbType.toLowerCase();

  if (normalizedType === "number") {
    return "numeric";
  }
  if (normalizedType === "integer") {
    return "integer";
  }
  if (normalizedType === "string") {
    return "varchar";
  }
  if (normalizedType === "boolean") {
    return "boolean";
  }
  if (normalizedType === "geometry") {
    return "geometry";
  }

  if (
    normalizedType.includes("int") ||
    normalizedType.includes("bigint") ||
    normalizedType.includes("smallint")
  ) {
    return "integer";
  }

  if (
    normalizedType.includes("float") ||
    normalizedType.includes("double") ||
    normalizedType.includes("decimal") ||
    normalizedType.includes("numeric") ||
    normalizedType.includes("real")
  ) {
    return "numeric";
  }

  if (normalizedType.includes("bool")) {
    return "boolean";
  }

  if (
    normalizedType.includes("date") ||
    normalizedType.includes("time") ||
    normalizedType.includes("timestamp")
  ) {
    return "timestamp";
  }

  if (normalizedType.includes("geom") || normalizedType.includes("geography")) {
    return "geometry";
  }

  return "varchar";
}


// SQL table definition for SQL mode
export interface SqlTable {
  alias: string; // e.g., "input_1", "buildings"
  fields: FormulaField[]; // Columns in this table
  layerName?: string; // Human-readable display name
  layerId?: string; // Layer UUID for preview
}

/**
 * Replace {{@variable_name}} references with type-appropriate SQL placeholders
 * so that validation/preview queries don't fail on the {{ syntax.
 */
function substituteVariablePlaceholders(
  sqlQuery: string,
  vars?: { name: string; type: string }[]
): string {
  if (!vars || vars.length === 0) return sqlQuery;
  return sqlQuery.replace(/\{\{@([a-zA-Z_][a-zA-Z0-9_]*)\}\}/g, (_match, name: string) => {
    const v = vars.find((v) => v.name === name);
    if (!v) return "NULL";
    return v.type === "number" ? "0" : "''";
  });
}

// Main FormulaBuilder props
export interface FormulaBuilderProps {
  open: boolean;
  onClose: () => void;
  onApply: (expression: string, groupByColumn?: string) => void;
  initialExpression?: string;
  initialGroupByColumn?: string;
  fields: FormulaField[];
  collectionId?: string; // For preview functionality
  title?: string;
  showGroupBy?: boolean;
  mode?: "expression" | "sql"; // Default: "expression"
  tables?: SqlTable[]; // For SQL mode: available tables with their columns
  variables?: { name: string; type: string }[]; // Workflow variables for {{@var}} autocomplete
}

export default function FormulaBuilder({
  open,
  onClose,
  onApply,
  initialExpression = "",
  initialGroupByColumn = "",
  fields,
  collectionId,
  title,
  showGroupBy = true,
  mode = "expression",
  tables,
  variables,
}: FormulaBuilderProps) {
  const { t } = useTranslation("common");
  const inputRef = useRef<HTMLInputElement>(null);
  const editorRef = useRef<ReactCodeMirrorRef | undefined>(undefined);
  const isSqlMode = mode === "sql";

  // State
  const [expression, setExpression] = useState(initialExpression);
  const [functionSearch, setFunctionSearch] = useState("");
  const [selectedCategory, setSelectedCategory] = useState<string>(isSqlMode ? "tables" : "fields");
  const [selectedFunction, setSelectedFunction] = useState<FunctionDoc | null>(null);
  const [validation, setValidation] = useState<ValidateExpressionResponse | null>(null);
  const [sqlValidation, setSqlValidation] = useState<ValidateSqlResponse | null>(null);
  const [preview, setPreview] = useState<ExpressionPreviewResult | null>(null);
  const [sqlPreview, setSqlPreview] = useState<PreviewSqlResponse | null>(null);
  const [isValidating, setIsValidating] = useState(false);
  const [isPreviewing, setIsPreviewing] = useState(false);
  const [cursorPosition, setCursorPosition] = useState(0);
  const [activeTab, setActiveTab] = useState(0);
  const [groupByColumn, setGroupByColumn] = useState<string>("");
  const [hoveredOperator, setHoveredOperator] = useState<(typeof OPERATORS)[number] | null>(null);
  const [hoveredField, setHoveredField] = useState<FormulaField | null>(null);
  const [expandedTable, setExpandedTable] = useState<string | null>(tables?.[0]?.alias ?? null);

  // Fetch functions only when dialog is open
  const {
    functions: allFunctions,
    isLoading: functionsLoading,
    isError: functionsError,
  } = useExpressionFunctions(open);

  // Non-geometry fields for Group By
  const nonGeomFields = useMemo(() => {
    return fields.filter((f) => !f.type.toLowerCase().includes("geom"));
  }, [fields]);

  // CodeMirror schema for SQL autocomplete
  const cmSchema = useMemo(() => {
    if (!tables) return {};
    const schema: Record<string, string[]> = {};
    for (const table of tables) {
      schema[table.alias] = table.fields.map((f) => f.name);
    }
    return schema;
  }, [tables]);

  // Track dialog open/close transitions
  const prevOpenRef = useRef(false);

  // Reset state only when dialog transitions from closed to open
  // (not on every tables/props change while dialog is already open)
  useEffect(() => {
    if (open && !prevOpenRef.current) {
      setExpression(initialExpression);
      setValidation(null);
      setSqlValidation(null);
      setPreview(null);
      setSqlPreview(null);
      setSelectedFunction(null);
      setActiveTab(0);
      setGroupByColumn(initialGroupByColumn);
      setSelectedCategory(isSqlMode ? "tables" : "fields");
      setExpandedTable(tables?.[0]?.alias ?? null);
      setCursorPosition(initialExpression.length);
    }
    prevOpenRef.current = open;
  }, [open, initialExpression, initialGroupByColumn, isSqlMode, tables]);

  // Filter functions by search (across all categories) and also filter fields
  const filteredFunctionsByCategory = useMemo(() => {
    if (!allFunctions) return {};

    const result: Record<string, FunctionDoc[]> = {};
    const search = functionSearch.toLowerCase();

    for (const [category, functions] of Object.entries(allFunctions)) {
      const filtered = search
        ? functions.filter(
            (f) => f.name.toLowerCase().includes(search) || f.syntax.toLowerCase().includes(search)
          )
        : functions;

      if (filtered.length > 0) {
        result[category] = filtered;
      }
    }

    return result;
  }, [allFunctions, functionSearch]);

  // Filter fields by search
  const filteredFields = useMemo(() => {
    if (!functionSearch) return fields;
    const search = functionSearch.toLowerCase();
    return fields.filter((f) => f.name.toLowerCase().includes(search));
  }, [fields, functionSearch]);

  // Column names for validation
  const columnNames = useMemo(() => fields.map((f) => f.name), [fields]);

  // Get items for selected category
  const categoryItems = useMemo(() => {
    if (!allFunctions) return [];

    switch (selectedCategory) {
      case "tables":
        // SQL mode: return tables as groups (handled separately in render)
        return [];
      case "fields":
        return filteredFields.map((f) => ({ type: "field" as const, data: f }));
      case "operators":
        return OPERATORS.map((op) => ({ type: "operator" as const, data: op }));
      default: {
        // Function categories
        const funcs = filteredFunctionsByCategory[selectedCategory] || [];
        return funcs.map((f) => ({ type: "function" as const, data: f }));
      }
    }
  }, [selectedCategory, filteredFields, filteredFunctionsByCategory, allFunctions]);

  // Category list for sidebar
  const categories = useMemo(() => {
    if (isSqlMode) {
      const cats = [
        { key: "tables", label: t("tables"), count: tables?.length || 0 },
        { key: "operators", label: t("operators"), count: OPERATORS.length },
      ];
      // Add function categories
      Object.entries(FUNCTION_CATEGORIES).forEach(([key, { labelKey }]) => {
        const count = allFunctions?.[key]?.length || 0;
        if (count > 0) {
          cats.push({ key, label: t(labelKey), count });
        }
      });
      return cats;
    }

    const cats = [
      { key: "fields", label: t("fields"), count: fields.length },
      { key: "operators", label: t("operators"), count: OPERATORS.length },
    ];
    // Add function categories
    Object.entries(FUNCTION_CATEGORIES).forEach(([key, { labelKey }]) => {
      const count = allFunctions?.[key]?.length || 0;
      if (count > 0) {
        cats.push({ key, label: t(labelKey), count });
      }
    });
    return cats;
  }, [fields.length, allFunctions, t, isSqlMode, tables]);

  // Insert text at cursor position
  const insertAtCursor = useCallback(
    (text: string) => {
      // SQL mode: use CodeMirror's dispatch API
      if (isSqlMode && editorRef.current?.view) {
        const view = editorRef.current.view;
        const { from } = view.state.selection.main;
        view.dispatch(
          view.state.update({
            changes: { from, insert: text },
            selection: { anchor: from + text.length },
          })
        );
        view.focus();
        return;
      }

      // Expression mode: existing logic
      const before = expression.slice(0, cursorPosition);
      const after = expression.slice(cursorPosition);
      const newExpression = before + text + after;
      setExpression(newExpression);
      const newPosition = cursorPosition + text.length;
      setCursorPosition(newPosition);
      setTimeout(() => {
        if (inputRef.current) {
          inputRef.current.focus();
          inputRef.current.setSelectionRange(newPosition, newPosition);
        }
      }, 0);
    },
    [expression, cursorPosition, isSqlMode]
  );

  // Insert field reference
  const insertField = useCallback(
    (fieldName: string) => {
      insertAtCursor(fieldName);
    },
    [insertAtCursor]
  );

  // Smart insert function - wraps the entire expression if it's a simple field
  const smartInsertFunction = useCallback(
    (func: FunctionDoc) => {
      // Check if current expression is just a single field name (no spaces, no operators)
      const trimmedExpression = expression.trim();
      const isSimpleField = fields.some((f) => f.name === trimmedExpression);

      if (isSimpleField) {
        // Wrap the entire field with the function
        // Replace (args) in syntax with (fieldName)
        const wrappedExpression = func.syntax.replace(/\([^)]*\)/, `(${trimmedExpression})`);
        setExpression(wrappedExpression);

        // Position cursor at the end
        const newPosition = wrappedExpression.length;
        setCursorPosition(newPosition);

        setTimeout(() => {
          if (inputRef.current) {
            inputRef.current.focus();
            inputRef.current.setSelectionRange(newPosition, newPosition);
          }
        }, 0);
        setSelectedFunction(func);
        return;
      }

      // Default: just insert the syntax normally at cursor
      insertAtCursor(func.syntax);
      setSelectedFunction(func);
    },
    [expression, fields, insertAtCursor]
  );

  // Insert operator at cursor position
  const insertOperator = useCallback(
    (syntax: string) => {
      insertAtCursor(syntax);
    },
    [insertAtCursor]
  );

  // Check if expression contains aggregate functions
  const hasAggregateFunction = useCallback((expr: string) => {
    const upperExpr = expr.toUpperCase();
    return AGGREGATE_FUNCTIONS.some((fn) => {
      // Match function name followed by opening parenthesis (with optional whitespace)
      const regex = new RegExp(`\\b${fn}\\s*\\(`, "i");
      return regex.test(upperExpr);
    });
  }, []);

  // Validate expression
  const handleValidate = useCallback(async () => {
    if (!expression.trim()) {
      setValidation(null);
      setSqlValidation(null);
      return;
    }

    // SQL mode validation
    if (isSqlMode) {
      setIsValidating(true);
      try {
        // Build table schemas from tables prop
        const tableSchemas: Record<string, Record<string, string>> = {};
        if (tables) {
          for (const table of tables) {
            const colTypes: Record<string, string> = {};
            for (const field of table.fields) {
              colTypes[field.name] = databaseTypeToSqlType(field.type);
            }
            tableSchemas[table.alias] = colTypes;
          }
        }

        const result = await validateSql({
          sql_query: substituteVariablePlaceholders(expression, variables),
          table_schemas: tableSchemas,
        });
        setSqlValidation(result);
      } catch (error) {
        setSqlValidation({
          valid: false,
          errors: [String(error)],
          columns: {},
        });
      } finally {
        setIsValidating(false);
      }
      return;
    }

    // When GROUP BY is selected, first check that expression uses aggregate functions
    if (groupByColumn && !hasAggregateFunction(expression)) {
      setValidation({
        valid: false,
        expression,
        errors: [
          {
            message: t("group_by_requires_aggregate"),
            code: "MISSING_AGGREGATE",
          },
        ],
        warnings: [],
        referenced_columns: [],
        used_functions: [],
      });
      return;
    }

    // Always validate the expression syntax via API
    setIsValidating(true);
    try {
      // Build column_types map from fields
      const columnTypes: Record<string, string> = {};
      for (const field of fields) {
        columnTypes[field.name] = databaseTypeToJsonType(field.type);
      }

      const result = await validateExpression({
        expression,
        column_names: columnNames,
        column_types: columnTypes,
        geometry_column: fields.find((f) => f.type.toLowerCase().includes("geom"))?.name || null,
      });
      setValidation(result);
    } catch (error) {
      setValidation({
        valid: false,
        expression,
        errors: [{ message: String(error), code: "API_ERROR" }],
        warnings: [],
        referenced_columns: [],
        used_functions: [],
      });
    } finally {
      setIsValidating(false);
    }
  }, [expression, columnNames, fields, groupByColumn, hasAggregateFunction, t, isSqlMode, tables, variables]);

  // Preview expression using aggregation-stats endpoint
  const handlePreview = useCallback(async () => {
    if (!expression.trim()) {
      setPreview(null);
      setSqlPreview(null);
      return;
    }

    // SQL mode preview
    if (isSqlMode) {
      if (!tables || tables.length === 0) {
        setSqlPreview(null);
        return;
      }

      setIsPreviewing(true);
      try {
        // Build layers map from tables
        const layersMap: Record<string, string> = {};
        for (const table of tables) {
          if (table.layerId) {
            layersMap[table.alias] = table.layerId;
          }
        }

        if (Object.keys(layersMap).length === 0) {
          // No real layer data available — fall back to schema-based preview.
          // Build table_schemas from table fields and use validateSql to predict output columns.
          const tableSchemas: Record<string, Record<string, string>> = {};
          for (const table of tables) {
            if (table.fields.length > 0) {
              const colMap: Record<string, string> = {};
              for (const f of table.fields) {
                colMap[f.name] = databaseTypeToSqlType(f.type);
              }
              tableSchemas[table.alias] = colMap;
            }
          }

          if (Object.keys(tableSchemas).length === 0) {
            setSqlPreview({
              success: false,
              columns: [],
              rows: [],
              error: "No input schemas available. Connect dataset nodes first.",
            });
            return;
          }

          const validation = await validateSql({
            sql_query: substituteVariablePlaceholders(expression, variables),
            table_schemas: tableSchemas,
          });

          if (validation.valid) {
            setSqlPreview({
              success: true,
              columns: Object.entries(validation.columns).map(([name, type]) => ({
                name,
                type,
              })),
              rows: [],
            });
          } else {
            setSqlPreview({
              success: false,
              columns: [],
              rows: [],
              error: validation.errors.join("; "),
            });
          }
          return;
        }

        const result = await previewSql({
          sql_query: substituteVariablePlaceholders(expression, variables),
          layers: layersMap,
          limit: 10,
        });
        setSqlPreview(result);
      } catch (error) {
        setSqlPreview({
          success: false,
          columns: [],
          rows: [],
          error: String(error),
        });
      } finally {
        setIsPreviewing(false);
      }
      return;
    }

    // Expression mode
    if (!collectionId) {
      setPreview(null);
      return;
    }

    setIsPreviewing(true);
    try {
      const result = await previewExpressionAsAggregation(
        collectionId,
        expression,
        groupByColumn || null,
        10
      );
      setPreview(result);
    } catch (error) {
      setPreview({
        value: null,
        total_count: 0,
        error: String(error),
      });
    } finally {
      setIsPreviewing(false);
    }
  }, [expression, collectionId, groupByColumn, isSqlMode, tables]);

  // Stable refs so effects only fire on actual value changes, not callback identity
  const handleValidateRef = useRef(handleValidate);
  handleValidateRef.current = handleValidate;
  const handlePreviewRef = useRef(handlePreview);
  handlePreviewRef.current = handlePreview;

  // Debounced validation - re-run only when expression or groupByColumn changes
  useEffect(() => {
    const timer = setTimeout(() => {
      if (expression.trim()) {
        handleValidateRef.current();
      } else {
        setValidation(null);
        setSqlValidation(null);
      }
    }, 500);
    return () => clearTimeout(timer);
  }, [expression, groupByColumn]);

  // Computed validation state (works for both modes)
  const isValid = isSqlMode ? sqlValidation?.valid : validation?.valid;
  const validationErrors = isSqlMode
    ? sqlValidation?.errors?.map((e) => ({ message: e, code: "SQL_ERROR" })) || []
    : validation?.errors || [];

  // Auto-preview when switching to Preview tab or when groupByColumn changes
  useEffect(() => {
    if (activeTab === 1 && expression.trim() && isValid !== false) {
      if (isSqlMode || collectionId) {
        handlePreviewRef.current();
      }
    }
  }, [activeTab, expression, collectionId, isValid, groupByColumn, isSqlMode, tables]);

  // Handle apply
  const handleApply = () => {
    if (isValid || isValid === undefined) {
      onApply(expression, groupByColumn || undefined);
      onClose();
    }
  };

  // Handle cursor position tracking
  const handleInputSelect = useCallback(() => {
    const target = inputRef.current;
    if (target) {
      setCursorPosition(target.selectionStart || 0);
    }
  }, []);

  // Validation status icon
  const ValidationIndicator = () => {
    if (isValidating) {
      return <CircularProgress size={16} />;
    }
    if (!expression.trim()) {
      return null;
    }
    if (isValid) {
      return (
        <Tooltip title={isSqlMode ? t("sql_valid") : t("expression_valid")}>
          <span style={{ display: "flex" }}>
            <Icon iconName={ICON_NAME.CIRCLECHECK} fontSize="small" htmlColor="#4caf50" />
          </span>
        </Tooltip>
      );
    }
    if (isValid === false) {
      return (
        <Tooltip title={validationErrors[0]?.message || t("expression_invalid")}>
          <span style={{ display: "flex" }}>
            <Icon iconName={ICON_NAME.XCLOSE} fontSize="small" htmlColor="#f44336" />
          </span>
        </Tooltip>
      );
    }
    return null;
  };

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="md"
      fullWidth
      PaperProps={{
        sx: {
          maxHeight: "85vh",
          minHeight: 600,
        },
      }}>
      <DialogTitle>{title || t("formula_builder")}</DialogTitle>

      <DialogContent dividers sx={{ p: 2, pb: 2, overflow: "hidden" }}>
        <Stack spacing={2}>
          {/* Expression/SQL Input with inline validation */}
          <Box sx={{ position: "relative" }}>
            {isSqlMode ? (
              <SqlCodeEditor
                value={expression}
                onChange={setExpression}
                schema={cmSchema}
                placeholder={t("sql_placeholder")}
                error={isValid === false}
                editorRef={editorRef}
                variables={variables}
              />
            ) : (
              <TextField
                inputRef={inputRef}
                fullWidth
                multiline
                rows={3}
                value={expression}
                onChange={(e) => setExpression(e.target.value)}
                onSelect={handleInputSelect}
                onClick={handleInputSelect}
                placeholder={t("enter_expression_placeholder")}
                sx={{
                  "& .MuiInputBase-input": {
                    fontFamily: "monospace",
                    fontSize: "0.875rem",
                  },
                }}
                error={isValid === false}
              />
            )}
            {/* Validation indicator in top-right corner */}
            <Box
              sx={{
                position: "absolute",
                top: 8,
                right: 8,
                display: "flex",
                alignItems: "center",
                zIndex: 5,
              }}>
              <ValidationIndicator />
            </Box>
          </Box>

          {/* Validation error line (fixed height to avoid layout shift, full details on hover) */}
          <Box sx={{ minHeight: 20, display: "flex", alignItems: "center" }}>
            {isValid === false && !isValidating && validationErrors.length > 0 && (
              <Typography variant="caption" color="error.main" noWrap sx={{ maxWidth: "100%" }}>
                {validationErrors[0]?.message}
              </Typography>
            )}
          </Box>

          {/* Tabs: Build / Preview */}
          <Box sx={{ borderBottom: 1, borderColor: "divider" }}>
            <Tabs value={activeTab} onChange={(_, newValue) => setActiveTab(newValue)}>
              <Tab label={t("build")} />
              <Tab label={t("preview")} />
            </Tabs>
          </Box>

          {/* BUILD TAB */}
          {activeTab === 0 && (
            <Stack spacing={2}>
              {/* Main row: Fields & Functions on left, Function Help on right */}
              <Stack direction="row" spacing={2} sx={{ height: 320, minHeight: 320 }}>
                {/* Three-column layout: Categories | Items | Help */}
                {/* Left: Categories */}
                <Paper
                  variant="outlined"
                  sx={{ width: 120, display: "flex", flexDirection: "column", overflow: "hidden" }}>
                  <Box sx={{ flex: 1, overflow: "auto" }}>
                    <List dense disablePadding>
                      {categories.map((cat) => (
                        <ListItem key={cat.key} disablePadding>
                          <ListItemButton
                            selected={selectedCategory === cat.key}
                            onClick={() => {
                              setSelectedCategory(cat.key);
                              // Clear hover states when switching categories
                              setHoveredField(null);
                              setHoveredOperator(null);
                              setSelectedFunction(null);
                            }}
                            sx={{
                              py: 0.75,
                              px: 1.5,
                              borderLeft: 3,
                              borderColor: selectedCategory === cat.key ? "primary.main" : "transparent",
                              bgcolor: selectedCategory === cat.key ? "action.selected" : "transparent",
                            }}>
                            <ListItemText
                              primary={
                                <Typography
                                  variant="body2"
                                  fontWeight={selectedCategory === cat.key ? "medium" : "normal"}>
                                  {cat.label}
                                </Typography>
                              }
                            />
                          </ListItemButton>
                        </ListItem>
                      ))}
                    </List>
                  </Box>
                </Paper>

                {/* Middle: Items for selected category */}
                <Paper
                  variant="outlined"
                  sx={{
                    flex: 1,
                    display: "flex",
                    flexDirection: "column",
                    overflow: "hidden",
                    maxHeight: 320,
                  }}>
                  <Box sx={{ px: 1, py: 0.75, borderBottom: 1, borderColor: "divider" }}>
                    <OutlinedInput
                      size="small"
                      fullWidth
                      placeholder={t("search_items")}
                      value={functionSearch}
                      onChange={(e) => setFunctionSearch(e.target.value)}
                      sx={{ fontSize: "0.875rem" }}
                      startAdornment={
                        <InputAdornment position="start" sx={{ mr: 1 }}>
                          <Icon
                            iconName={ICON_NAME.SEARCH}
                            fontSize="inherit"
                            sx={{ fontSize: "0.875rem" }}
                          />
                        </InputAdornment>
                      }
                    />
                  </Box>
                  <Box sx={{ flex: 1, overflow: "auto" }}>
                    {functionsLoading ? (
                      <Box sx={{ display: "flex", justifyContent: "center", py: 4 }}>
                        <CircularProgress size={24} />
                      </Box>
                    ) : functionsError ? (
                      <Box sx={{ textAlign: "center", py: 2 }}>
                        <Typography variant="body2" color="error">
                          {t("error_loading_functions")}
                        </Typography>
                      </Box>
                    ) : selectedCategory === "tables" && isSqlMode && tables ? (
                      /* SQL mode: show tables as expandable groups */
                      <List dense disablePadding>
                        {tables.map((table) => {
                          const isExpanded = expandedTable === table.alias;
                          const filteredTableFields = functionSearch
                            ? table.fields.filter((f) =>
                                f.name.toLowerCase().includes(functionSearch.toLowerCase())
                              )
                            : table.fields;

                          return (
                            <React.Fragment key={table.alias}>
                              <ListItem disablePadding>
                                <ListItemButton
                                  onClick={() => setExpandedTable(isExpanded ? null : table.alias)}
                                  sx={{
                                    py: 0.75,
                                    px: 1.5,
                                    bgcolor: isExpanded ? "action.selected" : "transparent",
                                  }}
                                  dense>
                                  <ListItemIcon sx={{ minWidth: 24 }}>
                                    <Icon
                                      iconName={ICON_NAME.TABLE}
                                      sx={{ fontSize: "1rem" }}
                                      color="primary"
                                    />
                                  </ListItemIcon>
                                  <ListItemText
                                    primary={
                                      <Typography variant="body2" fontWeight="bold" fontFamily="monospace" fontSize="0.8rem">
                                        {table.alias}
                                      </Typography>
                                    }
                                    secondary={table.layerName ? (
                                      <Typography variant="caption" color="text.secondary" noWrap>
                                        {table.layerName}
                                      </Typography>
                                    ) : undefined}
                                  />
                                  <Typography variant="caption" color="text.secondary">
                                    {table.fields.length}
                                  </Typography>
                                </ListItemButton>
                              </ListItem>
                              {isExpanded && filteredTableFields.map((field) => (
                                <ListItem key={`${table.alias}.${field.name}`} disablePadding>
                                  <ListItemButton
                                    onClick={() => insertField(`${table.alias}.${field.name}`)}
                                    onMouseEnter={() => setHoveredField(field)}
                                    onMouseLeave={() => setHoveredField(null)}
                                    sx={{ py: 0.25, pl: 4, pr: 1.5 }}
                                    dense>
                                    <ListItemIcon sx={{ minWidth: 28 }}>
                                      <FieldKindIcon kind={fieldIndicatorKind(field)} />
                                    </ListItemIcon>
                                    <ListItemText
                                      primary={
                                        <Typography variant="body2" fontFamily="monospace" fontSize="0.75rem">
                                          {field.name}
                                        </Typography>
                                      }
                                    />
                                    <Typography
                                      variant="caption"
                                      sx={{
                                        fontSize: "0.65rem",
                                        color: "text.disabled",
                                        fontFamily: "monospace",
                                      }}>
                                      {field.type}
                                    </Typography>
                                  </ListItemButton>
                                </ListItem>
                              ))}
                            </React.Fragment>
                          );
                        })}
                      </List>
                    ) : categoryItems.length === 0 ? (
                      <Typography variant="body2" color="text.secondary" sx={{ py: 2, textAlign: "center" }}>
                        {t("no_items_found")}
                      </Typography>
                    ) : (
                      <List dense disablePadding>
                        {categoryItems.map((item) => {
                          if (item.type === "field") {
                            const field = item.data as FormulaField;
                            return (
                              <ListItem key={field.name} disablePadding>
                                <ListItemButton
                                  onClick={() => insertField(field.name)}
                                  onMouseEnter={() => setHoveredField(field)}
                                  onMouseLeave={() => setHoveredField(null)}
                                  sx={{ py: 0.5, px: 1.5 }}
                                  dense>
                                  <ListItemIcon sx={{ minWidth: 28 }}>
                                    <FieldKindIcon kind={fieldIndicatorKind(field)} />
                                  </ListItemIcon>
                                  <ListItemText
                                    primary={
                                      <Typography variant="body2" fontFamily="monospace" fontSize="0.8rem">
                                        {field.name}
                                      </Typography>
                                    }
                                  />
                                  <Typography
                                    variant="caption"
                                    sx={{
                                      fontSize: "0.75rem",
                                      color: "text.disabled",
                                      fontFamily: "monospace",
                                    }}>
                                    ↵
                                  </Typography>
                                </ListItemButton>
                              </ListItem>
                            );
                          }

                          if (item.type === "operator") {
                            const op = item.data as (typeof OPERATORS)[number];
                            return (
                              <ListItem key={op.symbol} disablePadding>
                                <ListItemButton
                                  onClick={() => insertOperator(op.syntax)}
                                  onMouseEnter={() => setHoveredOperator(op)}
                                  onMouseLeave={() => setHoveredOperator(null)}
                                  sx={{ py: 0.5, px: 1.5 }}
                                  dense>
                                  <ListItemIcon sx={{ minWidth: 24 }}>
                                    <Typography
                                      variant="body2"
                                      fontFamily="monospace"
                                      fontSize="0.8rem"
                                      fontWeight="bold"
                                      color="action">
                                      {op.symbol}
                                    </Typography>
                                  </ListItemIcon>
                                  <ListItemText
                                    primary={
                                      <Typography variant="body2" fontSize="0.8rem">
                                        {op.label}
                                      </Typography>
                                    }
                                  />
                                  <Typography
                                    variant="caption"
                                    sx={{
                                      fontSize: "0.75rem",
                                      color: "text.disabled",
                                      fontFamily: "monospace",
                                    }}>
                                    ↵
                                  </Typography>
                                </ListItemButton>
                              </ListItem>
                            );
                          }

                          // Function
                          const func = item.data as FunctionDoc;
                          return (
                            <ListItem key={func.name} disablePadding>
                              <ListItemButton
                                onClick={() => smartInsertFunction(func)}
                                onMouseEnter={() => setSelectedFunction(func)}
                                onMouseLeave={() => setSelectedFunction(null)}
                                sx={{ py: 0.5, px: 1.5 }}
                                dense>
                                <ListItemText
                                  primary={
                                    <Typography variant="body2" fontFamily="monospace" fontSize="0.8rem">
                                      {func.name}
                                    </Typography>
                                  }
                                />
                                <Typography
                                  variant="caption"
                                  sx={{
                                    fontSize: "0.75rem",
                                    color: "text.disabled",
                                    fontFamily: "monospace",
                                  }}>
                                  ↵
                                </Typography>
                              </ListItemButton>
                            </ListItem>
                          );
                        })}
                      </List>
                    )}
                  </Box>
                </Paper>

                {/* Right: Help Panel */}
                <Paper
                  variant="outlined"
                  sx={{ width: 280, p: 1.5, display: "flex", flexDirection: "column" }}>
                  <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 1 }}>
                    <Icon iconName={ICON_NAME.INFO} fontSize="small" color="primary" />
                    <Typography variant="subtitle2">{t("help")}</Typography>
                  </Stack>
                  <Divider sx={{ mb: 1 }} />
                  <Box sx={{ flex: 1, overflow: "auto" }}>
                    {/* Field Help */}
                    {hoveredField ? (
                      <>
                        <Stack direction="row" alignItems="center" spacing={1} sx={{ mb: 1 }}>
                          <FieldKindIcon kind={fieldIndicatorKind(hoveredField)} />
                          <Typography variant="body2" fontWeight="bold" fontFamily="monospace">
                            {hoveredField.name}
                          </Typography>
                        </Stack>
                        <Chip
                          label={hoveredField.type.toUpperCase()}
                          size="small"
                          sx={{ mb: 1.5, height: 20, fontSize: "0.7rem" }}
                        />
                        <Typography variant="caption" color="text.secondary" sx={{ display: "block" }}>
                          {t("field_help_description", { field: hoveredField.name, type: hoveredField.type })}
                        </Typography>
                      </>
                    ) : hoveredOperator ? (
                      /* Operator Help */
                      <>
                        <Typography
                          variant="body2"
                          fontWeight="bold"
                          fontFamily="monospace"
                          fontSize="1.25rem"
                          sx={{ mb: 1 }}>
                          {hoveredOperator.symbol}
                        </Typography>
                        <Typography variant="body2" fontWeight="medium" sx={{ mb: 1 }}>
                          {hoveredOperator.label}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {t(`operator_${hoveredOperator.symbol}_desc`, {
                            defaultValue: t("operator_description", { symbol: hoveredOperator.symbol }),
                          })}
                        </Typography>
                      </>
                    ) : selectedFunction ? (
                      /* Function Help */
                      <>
                        {/* Function name and category */}
                        <Stack
                          direction="row"
                          justifyContent="space-between"
                          alignItems="center"
                          sx={{ mb: 0.5 }}>
                          <Typography variant="body2" fontWeight="bold" color="primary.main">
                            {selectedFunction.name.toUpperCase()}
                          </Typography>
                          <Typography
                            variant="caption"
                            sx={{
                              bgcolor: "action.hover",
                              px: 0.75,
                              py: 0.25,
                              borderRadius: 0.5,
                              textTransform: "capitalize",
                            }}>
                            {t(`category_${selectedFunction.category}`, {
                              defaultValue: selectedFunction.category,
                            })}
                          </Typography>
                        </Stack>

                        {/* Syntax */}
                        <Box
                          sx={{
                            mb: 1,
                            p: 0.75,
                            bgcolor: "action.hover",
                            borderRadius: 0.5,
                            border: 1,
                            borderColor: "divider",
                          }}>
                          <Typography variant="body2" fontFamily="monospace" fontSize="0.8rem">
                            {selectedFunction.syntax}
                          </Typography>
                        </Box>

                        {/* Description */}
                        <Typography
                          variant="caption"
                          color="text.secondary"
                          sx={{ display: "block", mb: 1.5 }}>
                          {t(`func_${selectedFunction.name}_desc`, {
                            defaultValue: t(selectedFunction.description_key, {
                              defaultValue: selectedFunction.description_key,
                            }),
                          })}
                        </Typography>

                        {/* Parameters */}
                        {selectedFunction.parameters.length > 0 && (
                          <Box sx={{ mb: 1.5 }}>
                            <Typography
                              variant="caption"
                              fontWeight="bold"
                              sx={{ display: "block", mb: 0.5 }}>
                              {t("parameters")}:
                            </Typography>
                            {selectedFunction.parameters.map((param, idx) => (
                              <Stack key={idx} direction="row" spacing={0.5} sx={{ mb: 0.25 }}>
                                <Typography variant="caption" fontFamily="monospace" color="primary.main">
                                  {param.name}
                                </Typography>
                                <Typography variant="caption" color="text.secondary">
                                  ({param.type.toLowerCase()}){param.optional ? ` - ${t("optional")}` : ""}
                                </Typography>
                              </Stack>
                            ))}
                          </Box>
                        )}

                        {/* Example */}
                        <Box sx={{ bgcolor: "action.hover", p: 1, borderRadius: 1 }}>
                          <Typography variant="caption" color="text.secondary" fontWeight="bold">
                            {t("example")}:
                          </Typography>
                          <Typography
                            variant="body2"
                            fontFamily="monospace"
                            fontSize="0.75rem"
                            sx={{ mt: 0.25 }}>
                            {selectedFunction.example}
                          </Typography>
                        </Box>
                      </>
                    ) : (
                      <Box sx={{ textAlign: "center", py: 4 }}>
                        <Icon
                          iconName={ICON_NAME.INFO}
                          fontSize="large"
                          sx={{ color: "action.disabled", mb: 1 }}
                        />
                        <Typography variant="caption" color="text.secondary" sx={{ display: "block" }}>
                          {t("hover_for_help")}
                        </Typography>
                      </Box>
                    )}
                  </Box>
                </Paper>
              </Stack>

              {/* Group By Panel - single select (hidden in SQL mode) */}
              {showGroupBy && !isSqlMode && (
                <Paper variant="outlined" sx={{ p: 1.5 }}>
                  <Stack direction="row" spacing={2} alignItems="center">
                    <Stack
                      direction="row"
                      spacing={1}
                      alignItems="center"
                      sx={{ minWidth: 150, flexShrink: 0 }}>
                      <Icon iconName={ICON_NAME.AGGREGATE} fontSize="small" color="primary" />
                      <Typography variant="subtitle2">{t("group_by")}</Typography>
                      <Typography variant="caption" color="text.secondary">
                        ({t("optional")})
                      </Typography>
                    </Stack>
                    <FormControl fullWidth size="small">
                      <Select
                        displayEmpty
                        value={groupByColumn}
                        onChange={(e) => setGroupByColumn(e.target.value as string)}
                        MenuProps={{
                          PaperProps: {
                            sx: { maxHeight: 300 },
                          },
                        }}
                        renderValue={(selected) => {
                          if (!selected) {
                            return (
                              <Typography variant="body2" color="text.secondary">
                                {t("select_column")}
                              </Typography>
                            );
                          }
                          return (
                            <Typography variant="body2" fontFamily="monospace">
                              {selected}
                            </Typography>
                          );
                        }}>
                        <MenuItem value="">
                          <Typography variant="body2" color="text.secondary">
                            {t("none")}
                          </Typography>
                        </MenuItem>
                        {nonGeomFields.map((field) => (
                          <MenuItem key={field.name} value={field.name}>
                            <Stack direction="row" spacing={1} alignItems="center">
                              <FieldKindIcon kind={fieldIndicatorKind(field)} />
                              <Typography variant="body2" fontFamily="monospace">
                                {field.name}
                              </Typography>
                            </Stack>
                          </MenuItem>
                        ))}
                      </Select>
                    </FormControl>
                    {groupByColumn && (
                      <IconButton size="small" onClick={() => setGroupByColumn("")} sx={{ flexShrink: 0 }}>
                        <Icon iconName={ICON_NAME.XCLOSE} fontSize="small" />
                      </IconButton>
                    )}
                  </Stack>
                </Paper>
              )}
            </Stack>
          )}

          {/* PREVIEW TAB (auto-runs) */}
          {activeTab === 1 && (
            <Box sx={{ minHeight: 300 }}>
              {isPreviewing && (
                <Box sx={{ display: "flex", justifyContent: "center", alignItems: "center", py: 8 }}>
                  <CircularProgress />
                </Box>
              )}

              {/* SQL mode preview - tabular results */}
              {!isPreviewing && isSqlMode && sqlPreview && (
                <>
                  {sqlPreview.success && sqlPreview.columns.length > 0 ? (
                    <Stack spacing={2}>
                      {sqlPreview.total_count !== null && sqlPreview.total_count !== undefined && (
                        <Typography variant="body2" color="text.secondary" sx={{ textAlign: "right" }}>
                          {t("total_rows")}: {sqlPreview.total_count}
                        </Typography>
                      )}
                      <Paper variant="outlined" sx={{ overflow: "auto", maxHeight: 300 }}>
                        <Box component="table" sx={{ width: "100%", borderCollapse: "collapse", fontSize: "0.8rem", fontFamily: "monospace" }}>
                          <Box component="thead">
                            <Box component="tr" sx={{ bgcolor: "action.hover" }}>
                              {sqlPreview.columns.map((col) => (
                                <Box
                                  component="th"
                                  key={col.name}
                                  sx={{
                                    px: 1.5,
                                    py: 0.75,
                                    textAlign: "left",
                                    borderBottom: 1,
                                    borderColor: "divider",
                                    fontWeight: "bold",
                                    whiteSpace: "nowrap",
                                  }}>
                                  {col.name}
                                  <Typography
                                    component="span"
                                    variant="caption"
                                    sx={{ display: "block", color: "text.secondary", fontSize: "0.65rem" }}>
                                    {col.type}
                                  </Typography>
                                </Box>
                              ))}
                            </Box>
                          </Box>
                          <Box component="tbody">
                            {sqlPreview.rows.map((row, rowIdx) => (
                              <Box
                                component="tr"
                                key={rowIdx}
                                sx={{ bgcolor: rowIdx % 2 === 0 ? "transparent" : "action.hover" }}>
                                {sqlPreview.columns.map((col) => (
                                  <Box
                                    component="td"
                                    key={col.name}
                                    sx={{
                                      px: 1.5,
                                      py: 0.5,
                                      borderBottom: 1,
                                      borderColor: "divider",
                                      maxWidth: 200,
                                      overflow: "hidden",
                                      textOverflow: "ellipsis",
                                      whiteSpace: "nowrap",
                                    }}>
                                    {row.values[col.name] !== null && row.values[col.name] !== undefined
                                      ? String(row.values[col.name])
                                      : <Typography component="span" variant="caption" color="text.disabled">NULL</Typography>
                                    }
                                  </Box>
                                ))}
                              </Box>
                            ))}
                          </Box>
                        </Box>
                      </Paper>
                      <Typography variant="caption" color="text.secondary">
                        {t("showing_rows", { count: sqlPreview.rows.length })}
                      </Typography>
                    </Stack>
                  ) : (
                    <Alert severity="error">
                      <Typography variant="body2">{sqlPreview.error || t("no_results")}</Typography>
                    </Alert>
                  )}
                </>
              )}

              {/* Expression mode preview */}
              {!isPreviewing && !isSqlMode && preview && (
                <>
                  {!preview.error ? (
                    <Stack spacing={2}>
                      {/* Summary info */}
                      <Typography variant="body2" color="text.secondary" sx={{ textAlign: "right" }}>
                        {t("total_rows")}: {preview.total_count}
                      </Typography>

                      {/* Results display */}
                      {groupByColumn && preview.items && preview.items.length > 0 ? (
                        /* Grouped results - show as simple list */
                        <Paper variant="outlined" sx={{ p: 2 }}>
                          <Typography variant="subtitle2" sx={{ mb: 2 }}>
                            {t("result")} {t("grouped_by")} {groupByColumn}
                          </Typography>
                          <Stack spacing={1}>
                            {preview.items.slice(0, 10).map((item, idx) => (
                              <Stack
                                key={idx}
                                direction="row"
                                justifyContent="space-between"
                                alignItems="center"
                                sx={{
                                  py: 0.5,
                                  px: 1,
                                  bgcolor: idx % 2 === 0 ? "action.hover" : "transparent",
                                  borderRadius: 1,
                                }}>
                                <Typography variant="body2" color="text.secondary">
                                  {item.grouped_value !== null ? String(item.grouped_value) : "NULL"}
                                </Typography>
                                <Typography
                                  variant="body2"
                                  fontWeight="bold"
                                  fontFamily="monospace"
                                  color="primary.main">
                                  {item.operation_value !== null ? String(item.operation_value) : "NULL"}
                                </Typography>
                              </Stack>
                            ))}
                          </Stack>
                        </Paper>
                      ) : (
                        /* Single aggregated result */
                        <Paper
                          variant="outlined"
                          sx={{
                            p: 4,
                            textAlign: "center",
                            bgcolor: "action.hover",
                          }}>
                          <Typography
                            variant="caption"
                            color="text.secondary"
                            sx={{ display: "block", mb: 1 }}>
                            {t("result")}
                          </Typography>
                          <Typography
                            variant="h3"
                            fontFamily="monospace"
                            fontWeight="bold"
                            color="primary.main">
                            {preview.value !== null ? String(preview.value) : "NULL"}
                          </Typography>
                          <Typography
                            variant="caption"
                            color="text.secondary"
                            sx={{ display: "block", mt: 1 }}>
                            {t("aggregated_over_rows", { count: preview.total_count })}
                          </Typography>
                        </Paper>
                      )}
                    </Stack>
                  ) : (
                    <Alert severity="error">
                      <Typography variant="body2">{preview.error}</Typography>
                    </Alert>
                  )}
                </>
              )}

              {!isPreviewing && !preview && !expression.trim() && (
                <Box
                  sx={{
                    display: "flex",
                    flexDirection: "column",
                    alignItems: "center",
                    justifyContent: "center",
                    py: 8,
                  }}>
                  <Icon iconName={ICON_NAME.CODE} sx={{ fontSize: 48, color: "action.disabled", mb: 2 }} />
                  <Typography variant="body1" color="text.secondary">
                    {t("enter_expression_to_preview")}
                  </Typography>
                </Box>
              )}

              {!isPreviewing && !preview && expression.trim() && validation?.valid === false && (
                <Box
                  sx={{
                    display: "flex",
                    flexDirection: "column",
                    alignItems: "center",
                    justifyContent: "center",
                    py: 8,
                  }}>
                  <Icon iconName={ICON_NAME.XCLOSE} sx={{ fontSize: 48, color: "error.main", mb: 2 }} />
                  <Typography variant="body1" color="text.secondary">
                    {t("fix_expression_errors_to_preview")}
                  </Typography>
                </Box>
              )}
            </Box>
          )}
        </Stack>
      </DialogContent>

      <DialogActions
        disableSpacing
        sx={{
          mt: 2,
          pb: 2,
        }}>
        <Button onClick={onClose} variant="text">
          <Typography variant="body2" fontWeight="bold">
            {t("cancel")}
          </Typography>
        </Button>
        <Button onClick={handleApply} variant="text" color="primary" disabled={isValid === false}>
          <Typography variant="body2" fontWeight="bold" color="inherit">
            {t("apply")}
          </Typography>
        </Button>
      </DialogActions>
    </Dialog>
  );
}
