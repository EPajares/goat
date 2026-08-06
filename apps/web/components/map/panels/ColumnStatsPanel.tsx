import ChevronLeftIcon from "@mui/icons-material/ChevronLeft";
import ChevronRightIcon from "@mui/icons-material/ChevronRight";
import CloseIcon from "@mui/icons-material/Close";
import {
  Box,
  CircularProgress,
  Divider,
  IconButton,
  Stack,
  Tooltip,
  Typography,
  useTheme,
} from "@mui/material";
import React from "react";
import { useTranslation } from "react-i18next";
import useSWR from "swr";

import { apiRequestAuth } from "@/lib/api/fetcher";
import { formatFieldValue } from "@/lib/utils/formatFieldValue";
import type { FieldKind } from "@/lib/validations/layer";

const PROCESSES_API_BASE_URL = `${process.env.NEXT_PUBLIC_PROCESSES_URL}/processes`;

const TOP_VALUES_LIMIT = 10;
const HISTOGRAM_BINS = 20;

// ── Types ──────────────────────────────────────────────────────────────

interface ColumnStatsPanelProps {
  layerId: string;
  columnName: string;
  columnType: string;
  /** Field kind ("datetime"/"boolean"/...) for kind-aware value formatting */
  columnKind?: string;
  cqlFilter?: string;
  onClose: () => void;
  onPrev: () => void;
  onNext: () => void;
}

interface UniqueValuesResponse {
  attribute: string;
  total: number;
  values: { value: string | number | null; count: number }[];
}

interface ClassBreaksResponse {
  attribute: string;
  method: string;
  breaks: number[];
  min: number | null;
  max: number | null;
  mean: number | null;
  std_dev: number | null;
}

interface HistogramResponse {
  bins: { range: [number, number]; count: number }[];
  missing_count: number;
  total_rows: number;
}

interface FeatureCountResponse {
  count: number;
}

// ── Data fetching ──────────────────────────────────────────────────────

async function fetchProcess<T>(processId: string, inputs: Record<string, unknown>): Promise<T> {
  const response = await apiRequestAuth(`${PROCESSES_API_BASE_URL}/${processId}/execution`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ inputs }),
  });
  if (!response.ok) throw new Error(`Failed to fetch ${processId}`);
  return response.json();
}

function useColumnStats(layerId: string, columnName: string, columnType: string, cqlFilter?: string) {
  const isNumeric = columnType === "number" || columnType === "integer";

  const swrOpts = { shouldRetryOnError: false } as const;

  const filterInputs = cqlFilter ? { filter: cqlFilter } : {};

  const { data: uniqueValues, isLoading: uvLoading } = useSWR<UniqueValuesResponse>(
    layerId && columnName ? [`col-stats-uv`, layerId, columnName, cqlFilter] : null,
    () =>
      fetchProcess("unique-values", {
        collection: layerId,
        attribute: columnName,
        order: "descendent",
        limit: TOP_VALUES_LIMIT,
        offset: 0,
        ...filterInputs,
      }),
    swrOpts
  );

  const { data: classBreaks, isLoading: cbLoading } = useSWR<ClassBreaksResponse>(
    isNumeric && layerId && columnName ? [`col-stats-cb`, layerId, columnName, cqlFilter] : null,
    () =>
      fetchProcess("class-breaks", {
        collection: layerId,
        attribute: columnName,
        method: "quantile",
        breaks: 5,
        ...filterInputs,
      }),
    swrOpts
  );

  // Wait for unique values to determine optimal bin count
  const numBins = uniqueValues ? Math.max(2, Math.min(HISTOGRAM_BINS, uniqueValues.total)) : null;
  const { data: histogram, isLoading: histLoading } = useSWR<HistogramResponse>(
    isNumeric && layerId && columnName && numBins ? [`col-stats-hist`, layerId, columnName, numBins, cqlFilter] : null,
    () =>
      fetchProcess("histogram", {
        collection: layerId,
        column: columnName,
        num_bins: numBins,
        method: "equal_interval",
        ...filterInputs,
      }),
    swrOpts
  );

  const { data: featureCount, isLoading: fcLoading } = useSWR<FeatureCountResponse>(
    layerId ? [`col-stats-fc`, layerId, cqlFilter] : null,
    () => fetchProcess("feature-count", { collection: layerId, ...filterInputs }),
    swrOpts
  );

  const totalRows = featureCount?.count ?? null;
  const uniqueTotal = uniqueValues?.total ?? null;
  // For numeric columns, histogram gives us exact missing_count
  const nullCount = isNumeric
    ? (histogram?.missing_count ?? null)
    : totalRows !== null && uniqueValues
      ? totalRows - uniqueValues.values.reduce((sum, v) => sum + v.count, 0)
      : null;

  return {
    uniqueValues,
    classBreaks: isNumeric ? classBreaks : null,
    histogram: isNumeric ? histogram : null,
    totalRows,
    uniqueTotal,
    nullCount: nullCount !== null && nullCount >= 0 ? nullCount : null,
    isLoading: uvLoading || cbLoading || fcLoading || histLoading,
    isNumeric,
  };
}

// ── Formatting helpers ─────────────────────────────────────────────────

function formatNumber(n: number | null | undefined): string {
  if (n === null || n === undefined) return "-";
  if (Number.isInteger(n)) return n.toLocaleString();
  return n.toLocaleString(undefined, { maximumFractionDigits: 2 });
}

function formatPercent(count: number, total: number): string {
  if (!total) return "";
  const pct = (count / total) * 100;
  return `(${pct < 0.1 ? "<0.1" : pct.toFixed(1)}%)`;
}

function formatCompact(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
  return n.toLocaleString();
}

// ── Histogram chart ────────────────────────────────────────────────────

function HistogramChart({ bins }: { bins: HistogramResponse["bins"] }) {
  const theme = useTheme();
  const maxCount = bins.reduce((max, b) => Math.max(max, b.count), 0);
  if (!maxCount) return null;

  // Trim leading/trailing empty bins so the chart focuses on where data exists
  let startIdx = 0;
  let endIdx = bins.length - 1;
  while (startIdx < bins.length && bins[startIdx].count === 0) startIdx++;
  while (endIdx > startIdx && bins[endIdx].count === 0) endIdx--;
  const trimmedBins = bins.slice(startIdx, endIdx + 1);

  const minVal = trimmedBins[0]?.range[0];
  const maxVal = trimmedBins[trimmedBins.length - 1]?.range[1];

  return (
    <Box sx={{ mb: 1.5 }}>
      {/* Y-axis max label */}
      <Typography variant="caption" color="text.disabled" sx={{ fontSize: "0.65rem" }}>
        {formatCompact(maxCount)}
      </Typography>
      {/* Bars */}
      <Stack direction="row" alignItems="flex-end" spacing="1px" sx={{ height: 60 }}>
        {trimmedBins.map((bin, idx) => {
          const heightPct = (bin.count / maxCount) * 100;
          return (
            <Tooltip
              key={idx}
              title={`${formatNumber(bin.range[0])} – ${formatNumber(bin.range[1])}: ${formatNumber(bin.count)}`}
              placement="top"
              arrow>
              <Box
                sx={{
                  flex: 1,
                  height: bin.count > 0 ? `${Math.max(heightPct, 2)}%` : 0,
                  backgroundColor: theme.palette.primary.main,
                  opacity: 0.6,
                  borderRadius: "1px 1px 0 0",
                  minWidth: 2,
                  transition: "opacity 0.15s",
                  "&:hover": { opacity: 1 },
                }}
              />
            </Tooltip>
          );
        })}
      </Stack>
      {/* X-axis labels */}
      <Stack direction="row" justifyContent="space-between" sx={{ mt: 0.25 }}>
        <Typography variant="caption" color="text.disabled" sx={{ fontSize: "0.65rem" }}>
          {formatNumber(minVal)}
        </Typography>
        <Typography variant="caption" color="text.disabled" sx={{ fontSize: "0.65rem" }}>
          {formatNumber(maxVal)}
        </Typography>
      </Stack>
    </Box>
  );
}

// ── Top values list (shared by string & numeric) ───────────────────────

function TopValuesList({
  values,
  maxCount,
  kind,
}: {
  values: UniqueValuesResponse["values"];
  maxCount: number;
  kind?: string;
}) {
  const theme = useTheme();
  const { t } = useTranslation("common");

  if (values.length === 0) {
    return (
      <Typography variant="caption" color="text.disabled">
        {t("no_data", { defaultValue: "No data" })}
      </Typography>
    );
  }

  return (
    <Stack spacing={0.25}>
      {values.map((item, idx) => (
        <Stack key={idx} direction="row" alignItems="center" sx={{ position: "relative" }}>
          <Box
            sx={{
              position: "absolute",
              left: 0,
              top: 0,
              bottom: 0,
              width: `${(item.count / maxCount) * 100}%`,
              backgroundColor: theme.palette.primary.main,
              opacity: 0.08,
              borderRadius: 0.5,
            }}
          />
          <Typography variant="caption" noWrap sx={{ flex: 1, zIndex: 1, py: 0.25, px: 0.5 }}>
            {item.value === null ? (
              <em style={{ color: theme.palette.text.disabled }}>null</em>
            ) : kind && kind !== "string" && kind !== "number" ? (
              formatFieldValue(item.value, kind as FieldKind, {})
            ) : (
              String(item.value)
            )}
          </Typography>
          <Typography
            variant="caption"
            color="text.secondary"
            sx={{ flexShrink: 0, zIndex: 1, fontVariantNumeric: "tabular-nums", px: 0.5 }}>
            {formatNumber(item.count)}
          </Typography>
        </Stack>
      ))}
    </Stack>
  );
}

// ── Stat row ───────────────────────────────────────────────────────────

function StatRow({ label, value }: { label: string; value: string }) {
  return (
    <Stack direction="row" justifyContent="space-between" alignItems="center">
      <Typography variant="caption" color="text.secondary">
        {label}
      </Typography>
      <Typography variant="caption" fontWeight="bold" sx={{ fontVariantNumeric: "tabular-nums" }}>
        {value}
      </Typography>
    </Stack>
  );
}

// ── Main component ─────────────────────────────────────────────────────

const ColumnStatsPanel: React.FC<ColumnStatsPanelProps> = ({
  layerId,
  columnName,
  columnType,
  columnKind,
  cqlFilter,
  onClose,
  onPrev,
  onNext,
}) => {
  const { t } = useTranslation("common");
  const { uniqueValues, classBreaks, histogram, totalRows, uniqueTotal, nullCount, isLoading, isNumeric } =
    useColumnStats(layerId, columnName, columnType, cqlFilter);

  const maxCount = uniqueValues?.values.reduce((max, v) => Math.max(max, v.count), 0) ?? 1;

  return (
    <Box
      sx={{
        width: 280,
        minWidth: 280,
        display: "flex",
        flexDirection: "column",
        borderLeft: "1px solid",
        borderColor: "divider",
        backgroundColor: "background.paper",
        overflow: "hidden",
      }}>
      {/* Header */}
      <Stack
        direction="row"
        alignItems="center"
        sx={{
          px: 1.5,
          py: 1,
          borderBottom: "1px solid",
          borderColor: "divider",
          gap: 0.5,
          flexShrink: 0,
        }}>
        <Typography variant="body2" fontWeight="bold" noWrap sx={{ flex: 1 }}>
          {columnName}
        </Typography>
        <Tooltip title={t("previous", { defaultValue: "Previous" })}>
          <IconButton size="small" onClick={onPrev}>
            <ChevronLeftIcon fontSize="small" />
          </IconButton>
        </Tooltip>
        <Tooltip title={t("next", { defaultValue: "Next" })}>
          <IconButton size="small" onClick={onNext}>
            <ChevronRightIcon fontSize="small" />
          </IconButton>
        </Tooltip>
        <Tooltip title={t("close", { defaultValue: "Close" })}>
          <IconButton size="small" onClick={onClose}>
            <CloseIcon fontSize="small" />
          </IconButton>
        </Tooltip>
      </Stack>

      {/* Content */}
      <Box sx={{ flex: 1, minHeight: 0, overflow: "auto", px: 1.5, py: 1 }}>
        {isLoading ? (
          <Box sx={{ display: "flex", justifyContent: "center", py: 4 }}>
            <CircularProgress size={24} />
          </Box>
        ) : isNumeric ? (
          /* ── Numeric column layout ── */
          <>
            {/* Histogram */}
            {histogram && histogram.bins.length > 0 && <HistogramChart bins={histogram.bins} />}

            {/* Numeric summary stats */}
            {classBreaks && (
              <>
                <Stack spacing={0.5} sx={{ mb: 1.5 }}>
                  <StatRow label={t("min", { defaultValue: "Min" })} value={formatNumber(classBreaks.min)} />
                  <StatRow label={t("max", { defaultValue: "Max" })} value={formatNumber(classBreaks.max)} />
                  <StatRow label={t("mean", { defaultValue: "Mean" })} value={formatNumber(classBreaks.mean)} />
                  <StatRow
                    label={t("std_dev", { defaultValue: "Std Dev" })}
                    value={formatNumber(classBreaks.std_dev)}
                  />
                </Stack>
                <Divider sx={{ my: 1 }} />
              </>
            )}

            {/* Totals */}
            <Stack spacing={0.5}>
              <StatRow label={t("total_values", { defaultValue: "Total Values" })} value={formatNumber(totalRows)} />
              <StatRow
                label={t("unique_values", { defaultValue: "Unique Values" })}
                value={formatNumber(uniqueTotal)}
              />
              {nullCount !== null && totalRows !== null && (
                <StatRow
                  label={t("null", { defaultValue: "Null" })}
                  value={`${formatNumber(nullCount)} ${formatPercent(nullCount, totalRows)}`}
                />
              )}
            </Stack>
          </>
        ) : (
          /* ── String / other column layout ── */
          <>
            {/* Top Values */}
            <Typography
              variant="caption"
              color="text.secondary"
              fontWeight="bold"
              sx={{ mb: 0.5, display: "block" }}>
              {t("top_values", { defaultValue: "Top Values" })}
            </Typography>
            <TopValuesList values={uniqueValues?.values ?? []} maxCount={maxCount} kind={columnKind} />

            {/* Totals */}
            <Divider sx={{ my: 1 }} />
            <Stack spacing={0.5}>
              <StatRow label={t("total_values", { defaultValue: "Total Values" })} value={formatNumber(totalRows)} />
              <StatRow
                label={t("unique_values", { defaultValue: "Unique Values" })}
                value={formatNumber(uniqueTotal)}
              />
              {nullCount !== null && totalRows !== null && (
                <StatRow
                  label={t("null", { defaultValue: "Null" })}
                  value={`${formatNumber(nullCount)} ${formatPercent(nullCount, totalRows)}`}
                />
              )}
            </Stack>
          </>
        )}
      </Box>
    </Box>
  );
};

export default ColumnStatsPanel;
