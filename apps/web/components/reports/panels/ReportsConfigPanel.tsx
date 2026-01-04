"use client";

import { Add as AddIcon, Description as ReportIcon } from "@mui/icons-material";
import {
  Box,
  Button,
  CircularProgress,
  Divider,
  FormControlLabel,
  IconButton,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Stack,
  Switch,
  Tooltip,
  Typography,
} from "@mui/material";
import { styled } from "@mui/material/styles";
import React, { useCallback, useEffect, useMemo, useState } from "react";
import { Trans, useTranslation } from "react-i18next";

import { ICON_NAME, Icon } from "@p4b/ui/components/Icon";

import {
  createReportLayout,
  deleteReportLayout,
  duplicateReportLayout,
  updateReportLayout,
  useReportLayouts,
} from "@/lib/api/reportLayouts";
import type { Project, ProjectLayer } from "@/lib/validations/project";
import type {
  AtlasConfig,
  AtlasFeatureCoverage,
  PageConfig,
  ReportLayout,
  ReportLayoutConfig,
} from "@/lib/validations/reportLayout";

import type { SelectorItem } from "@/types/map/common";

import { useAtlasFeatures } from "@/hooks/reports/useAtlasFeatures";
import { type ExportFormat, useExportReport } from "@/hooks/useExportReport";

import MoreMenu from "@/components/common/PopperMenu";
import type { PopperMenuItem } from "@/components/common/PopperMenu";
import { SIDE_PANEL_WIDTH, SidePanelContainer } from "@/components/common/SidePanel";
import SectionHeader from "@/components/map/panels/common/SectionHeader";
import SectionOptions from "@/components/map/panels/common/SectionOptions";
import Selector from "@/components/map/panels/common/Selector";
import ConfirmModal from "@/components/modals/Confirm";
import ReportLayoutRenameModal from "@/components/modals/ReportLayoutRename";

const PanelContainer = styled(SidePanelContainer)(({ theme }) => ({
  width: SIDE_PANEL_WIDTH,
  minWidth: SIDE_PANEL_WIDTH,
  height: "100%",
  maxHeight: "100%",
  boxShadow: "none",
  borderRight: `1px solid ${theme.palette.background.paper}`,
  display: "flex",
  flexDirection: "column",
  overflow: "hidden",
  position: "relative",
  zIndex: 1,
}));

interface ReportsConfigPanelProps {
  project?: Project;
  projectLayers?: ProjectLayer[];
  selectedReport: ReportLayout | null;
  onSelectReport: (report: ReportLayout | null) => void;
}

// Default config for new report layouts
const getDefaultConfig = (): ReportLayoutConfig => ({
  page: {
    size: "A4",
    orientation: "portrait",
    margins: { top: 10, right: 10, bottom: 10, left: 10 },
    snapToGuides: false,
    showRulers: false,
  },
  layout: {
    type: "grid",
    columns: 12,
    rows: 12,
    gap: 5,
  },
  elements: [],
});

const ReportsConfigPanel: React.FC<ReportsConfigPanelProps> = ({
  project,
  projectLayers = [],
  selectedReport,
  onSelectReport,
}) => {
  const { t } = useTranslation("common");

  // Fetch report layouts from API
  const { reportLayouts, isLoading, mutate } = useReportLayouts(project?.id);

  // Selected report ID (local, synced with parent)
  const [selectedReportId, setSelectedReportId] = useState<string | null>(null);

  // Loading states
  const [isCreating, setIsCreating] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  // Section collapsed state
  const [pageSettingsCollapsed, setPageSettingsCollapsed] = useState(false);
  const [atlasSettingsCollapsed, setAtlasSettingsCollapsed] = useState(true);

  // Local state for settings (derived from selected report)
  const [pageSize, setPageSize] = useState<PageConfig["size"]>("A4");
  const [orientation, setOrientation] = useState<PageConfig["orientation"]>("portrait");
  const [snapToGuides, setSnapToGuides] = useState<boolean>(false);
  const [showRulers, setShowRulers] = useState<boolean>(false);
  const [dpi, setDpi] = useState<number>(300);
  const [exportFormat, setExportFormat] = useState<string>("pdf");

  // Atlas settings state
  const [atlasEnabled, setAtlasEnabled] = useState<boolean>(false);
  const [atlasLayerId, setAtlasLayerId] = useState<number | null>(null);
  const [atlasSortBy, setAtlasSortBy] = useState<string>("");
  const [atlasSortOrder, setAtlasSortOrder] = useState<"asc" | "desc">("asc");
  const [atlasFilter, setAtlasFilter] = useState<string>("");

  // Modal states
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [renameModalOpen, setRenameModalOpen] = useState(false);
  const [actionLayoutId, setActionLayoutId] = useState<string | null>(null);
  const [actionLayoutName, setActionLayoutName] = useState<string>("");

  // Memoized selector items
  const pageSizeItems: SelectorItem[] = useMemo(
    () => [
      { label: "A4", value: "A4" },
      { label: "A3", value: "A3" },
      { label: "Letter", value: "Letter" },
      { label: "Legal", value: "Legal" },
      { label: "Tabloid", value: "Tabloid" },
    ],
    []
  );

  const orientationItems: SelectorItem[] = useMemo(
    () => [
      { label: t("vertical"), value: "portrait" },
      { label: t("horizontal"), value: "landscape" },
    ],
    [t]
  );

  const dpiItems: SelectorItem[] = useMemo(
    () => [
      { label: "72 (Screen)", value: 72 },
      { label: "150 (Low)", value: 150 },
      { label: "300 (High)", value: 300 },
      { label: "600 (Print)", value: 600 },
    ],
    []
  );

  const exportFormatItems: SelectorItem[] = useMemo(
    () => [
      { label: "PDF", value: "pdf" },
      { label: "PNG", value: "png" },
      { label: "SVG", value: "svg" },
    ],
    []
  );

  const coverageLayerItems: SelectorItem[] = useMemo(
    () =>
      projectLayers.map((layer) => ({
        label: layer.name,
        value: layer.id,
      })),
    [projectLayers]
  );

  // Update local state and notify parent when selected report changes
  useEffect(() => {
    if (selectedReportId && reportLayouts) {
      const report = reportLayouts.find((r) => r.id === selectedReportId);
      if (report) {
        onSelectReport(report);
        // Page settings
        setPageSize(report.config.page.size);
        setOrientation(report.config.page.orientation);
        setSnapToGuides(report.config.page.snapToGuides ?? false);
        setShowRulers(report.config.page.showRulers ?? false);
        // Atlas settings
        const atlas = report.config.atlas;
        setAtlasEnabled(atlas?.enabled ?? false);
        if (atlas?.coverage?.type === "feature") {
          setAtlasLayerId(atlas.coverage.layer_project_id);
          setAtlasSortBy(atlas.coverage.sort_by ?? "");
          setAtlasSortOrder(atlas.coverage.sort_order ?? "asc");
          setAtlasFilter(atlas.coverage.filter ?? "");
        } else {
          setAtlasLayerId(null);
          setAtlasSortBy("");
          setAtlasSortOrder("asc");
          setAtlasFilter("");
        }
        // Expand atlas section if enabled
        if (atlas?.enabled) {
          setAtlasSettingsCollapsed(false);
        }
      }
    } else {
      onSelectReport(null);
    }
  }, [selectedReportId, reportLayouts, onSelectReport]);

  // Auto-select first report when layouts load
  useEffect(() => {
    if (reportLayouts && reportLayouts.length > 0 && !selectedReportId) {
      setSelectedReportId(reportLayouts[0].id);
    }
  }, [reportLayouts, selectedReportId]);

  const handleAddReport = useCallback(async () => {
    if (!project?.id) return;

    setIsCreating(true);
    try {
      const newLayout = await createReportLayout(project.id, {
        name: `Layout ${(reportLayouts?.length || 0) + 1}`,
        is_default: false,
        config: getDefaultConfig(),
      });
      await mutate();
      setSelectedReportId(newLayout.id);
    } catch (error) {
      console.error("Failed to create report layout:", error);
    } finally {
      setIsCreating(false);
    }
  }, [project?.id, reportLayouts?.length, mutate]);

  const handleDeleteReport = useCallback(
    async (reportId: string) => {
      if (!project?.id) return;

      try {
        await deleteReportLayout(project.id, reportId);
        await mutate();
        if (selectedReportId === reportId) {
          setSelectedReportId(null);
        }
      } catch (error) {
        console.error("Failed to delete report layout:", error);
      }
    },
    [project?.id, selectedReportId, mutate]
  );

  const handleDuplicateReport = useCallback(
    async (reportId: string) => {
      if (!project?.id) return;

      try {
        const duplicated = await duplicateReportLayout(project.id, reportId);
        await mutate();
        setSelectedReportId(duplicated.id);
      } catch (error) {
        console.error("Failed to duplicate report layout:", error);
      }
    },
    [project?.id, mutate]
  );

  const handleRenameReport = useCallback(
    async (newName: string) => {
      if (!project?.id || !actionLayoutId) return;

      const layout = reportLayouts?.find((r) => r.id === actionLayoutId);
      if (!layout) return;

      try {
        await updateReportLayout(project.id, actionLayoutId, {
          name: newName,
          config: layout.config,
        });
        await mutate();
      } catch (error) {
        console.error("Failed to rename report layout:", error);
      }
    },
    [project?.id, actionLayoutId, reportLayouts, mutate]
  );

  // Save settings to database when they change
  const handleSettingChange = useCallback(
    async (updates: Partial<ReportLayoutConfig["page"]>) => {
      if (!project?.id || !selectedReport) return;

      setIsSaving(true);
      try {
        const updatedConfig: ReportLayoutConfig = {
          ...selectedReport.config,
          page: {
            ...selectedReport.config.page,
            ...updates,
          },
        };
        await updateReportLayout(project.id, selectedReport.id, {
          config: updatedConfig,
        });
        await mutate();
      } catch (error) {
        console.error("Failed to update report layout:", error);
      } finally {
        setIsSaving(false);
      }
    },
    [project?.id, selectedReport, mutate]
  );

  const handlePageSizeChange = (newSize: PageConfig["size"]) => {
    setPageSize(newSize);
    handleSettingChange({ size: newSize });
  };

  const handleOrientationChange = (newOrientation: PageConfig["orientation"]) => {
    setOrientation(newOrientation);
    handleSettingChange({ orientation: newOrientation });
  };

  const handleSnapToGuidesChange = (enabled: boolean) => {
    setSnapToGuides(enabled);
    handleSettingChange({ snapToGuides: enabled });
  };

  const handleShowRulersChange = (enabled: boolean) => {
    setShowRulers(enabled);
    handleSettingChange({ showRulers: enabled });
  };

  // Save atlas settings to database
  const handleAtlasSettingChange = useCallback(
    async (updates: Partial<AtlasConfig>) => {
      if (!project?.id || !selectedReport) return;

      setIsSaving(true);
      try {
        const currentAtlas = selectedReport.config.atlas || { enabled: false };
        const updatedConfig: ReportLayoutConfig = {
          ...selectedReport.config,
          atlas: {
            ...currentAtlas,
            ...updates,
          },
        };
        await updateReportLayout(project.id, selectedReport.id, {
          config: updatedConfig,
        });
        await mutate();
      } catch (error) {
        console.error("Failed to update atlas settings:", error);
      } finally {
        setIsSaving(false);
      }
    },
    [project?.id, selectedReport, mutate]
  );

  const handleAtlasEnabledChange = (enabled: boolean) => {
    setAtlasEnabled(enabled);
    handleAtlasSettingChange({ enabled });
    if (enabled) {
      setAtlasSettingsCollapsed(false);
    }
  };

  const handleAtlasLayerChange = (layerId: number | null) => {
    setAtlasLayerId(layerId);
    if (layerId) {
      const coverage: AtlasFeatureCoverage = {
        type: "feature",
        layer_project_id: layerId,
        sort_by: atlasSortBy || undefined,
        sort_order: atlasSortOrder,
        filter: atlasFilter || null,
      };
      handleAtlasSettingChange({ coverage });
    }
  };

  // Menu items for layout actions
  const getLayoutMenuItems = useCallback(
    (report: ReportLayout): PopperMenuItem[] => [
      {
        id: "rename",
        label: t("rename"),
        icon: ICON_NAME.EDIT,
        onClick: () => {
          setActionLayoutId(report.id);
          setActionLayoutName(report.name);
          setRenameModalOpen(true);
        },
      },
      {
        id: "duplicate",
        label: t("duplicate"),
        icon: ICON_NAME.COPY,
        onClick: () => handleDuplicateReport(report.id),
      },
      {
        id: "delete",
        label: t("delete"),
        icon: ICON_NAME.TRASH,
        color: "error.main",
        onClick: () => {
          setActionLayoutId(report.id);
          setActionLayoutName(report.name);
          setDeleteModalOpen(true);
        },
      },
    ],
    [t, handleDuplicateReport]
  );

  // Print hook (server-side PDF generation via Playwright)
  const { isBusy: isPrinting, exportReport } = useExportReport();

  // Get atlas info for print job (total pages needed by backend)
  const { totalPages: atlasTotalPages } = useAtlasFeatures({
    atlasConfig: selectedReport?.config?.atlas,
    projectLayers,
  });

  const handlePrintReport = useCallback(async () => {
    if (!project?.id || !selectedReport) return;

    try {
      await exportReport({
        projectId: project.id,
        layoutId: selectedReport.id,
        format: exportFormat as ExportFormat,
        totalAtlasPages: atlasTotalPages > 0 ? atlasTotalPages : undefined,
      });
    } catch (error) {
      console.error("Failed to print report:", error);
    }
  }, [project?.id, selectedReport, exportReport, exportFormat, atlasTotalPages]);

  return (
    <PanelContainer>
      {/* Layouts Section */}
      <Box
        sx={{ flexShrink: 1, minHeight: 80, display: "flex", flexDirection: "column", overflow: "hidden" }}>
        {/* Layouts Header */}
        <Stack
          direction="row"
          alignItems="center"
          justifyContent="space-between"
          sx={{ p: 2, pb: 0, mb: 2, flexShrink: 0 }}>
          <Typography variant="subtitle1" fontWeight={600}>
            {t("reports")}
          </Typography>
          <Button
            variant="contained"
            size="small"
            startIcon={isCreating ? <CircularProgress size={16} color="inherit" /> : <AddIcon />}
            onClick={handleAddReport}
            disabled={isCreating || !project?.id}
            sx={{ textTransform: "none" }}>
            {t("add_layout")}
          </Button>
        </Stack>

        {/* Layouts List - Scrollable */}
        <Box
          sx={{
            flex: "1 1 auto",
            minHeight: 0,
            maxHeight: 200,
            overflowY: "auto",
            px: 2,
            "&::-webkit-scrollbar": {
              width: "6px",
            },
            "&::-webkit-scrollbar-thumb": {
              background: "#2836484D",
              borderRadius: "3px",
              "&:hover": {
                background: "#28364880",
              },
            },
          }}>
          {isLoading ? (
            <Box sx={{ display: "flex", justifyContent: "center", py: 4 }}>
              <CircularProgress size={24} />
            </Box>
          ) : (
            <List dense sx={{ mx: -2 }}>
              {reportLayouts?.map((report) => (
                <ListItem
                  key={report.id}
                  disablePadding
                  secondaryAction={
                    <MoreMenu
                      menuItems={getLayoutMenuItems(report)}
                      disablePortal={false}
                      menuButton={
                        <Tooltip title={t("more_options")} placement="top">
                          <IconButton edge="end" size="small">
                            <Icon iconName={ICON_NAME.MORE_VERT} style={{ fontSize: "15px" }} />
                          </IconButton>
                        </Tooltip>
                      }
                    />
                  }>
                  <ListItemButton
                    selected={selectedReportId === report.id}
                    onClick={() => setSelectedReportId(report.id)}>
                    <ListItemIcon sx={{ minWidth: 36 }}>
                      <ReportIcon fontSize="small" />
                    </ListItemIcon>
                    <ListItemText primary={report.name} primaryTypographyProps={{ fontSize: "0.875rem" }} />
                  </ListItemButton>
                </ListItem>
              ))}
              {(!reportLayouts || reportLayouts.length === 0) && (
                <Box sx={{ py: 2, px: 2, textAlign: "center" }}>
                  <Typography variant="body2" color="text.secondary">
                    {t("no_layouts_yet")}
                  </Typography>
                </Box>
              )}
            </List>
          )}
        </Box>
      </Box>

      <Divider sx={{ flexShrink: 0 }} />

      {/* Settings Section */}
      <Box sx={{ flex: "1 1 0", minHeight: 0, display: "flex", flexDirection: "column", overflow: "hidden" }}>
        {/* Settings Header */}
        <Stack
          direction="row"
          alignItems="center"
          justifyContent="space-between"
          sx={{ px: 3, py: 2, flexShrink: 0 }}>
          <Typography variant="body1" fontWeight="bold">
            {t("settings")}
          </Typography>
          <Button variant="outlined" size="small" sx={{ textTransform: "none" }}>
            {t("browse_templates")}
          </Button>
        </Stack>
        <Divider sx={{ flexShrink: 0 }} />
        {/* Settings Body - Scrollable */}
        <Box
          sx={{
            flex: "1 1 0",
            minHeight: 0,
            overflowY: "auto",
            px: 3,
            py: 2,
            "&::-webkit-scrollbar": {
              width: "6px",
            },
            "&::-webkit-scrollbar-thumb": {
              background: "#2836484D",
              borderRadius: "3px",
              "&:hover": {
                background: "#28364880",
              },
            },
          }}>
          <Stack spacing={3}>
            {/* Page Settings Section */}
            <Box sx={{ overflow: "hidden" }}>
              <SectionHeader
                active={true}
                alwaysActive
                label={t("page_settings")}
                icon={ICON_NAME.SETTINGS}
                collapsed={pageSettingsCollapsed}
                setCollapsed={setPageSettingsCollapsed}
                disableAdvanceOptions
              />
              <SectionOptions
                active={!pageSettingsCollapsed}
                baseOptions={
                  <Stack spacing={2}>
                    {/* Page Size */}
                    <Box>
                      <Typography variant="body2" fontWeight={600} sx={{ mb: 1 }}>
                        {t("size")}
                      </Typography>
                      <Selector
                        selectedItems={pageSizeItems.find((item) => item.value === pageSize)}
                        setSelectedItems={(item: SelectorItem | SelectorItem[] | undefined) => {
                          if (item && !Array.isArray(item)) {
                            handlePageSizeChange(item.value as PageConfig["size"]);
                          }
                        }}
                        items={pageSizeItems}
                        disabled={!selectedReport || isSaving}
                      />
                    </Box>

                    {/* Orientation */}
                    <Box>
                      <Typography variant="body2" fontWeight={600} sx={{ mb: 1 }}>
                        {t("orientation")}
                      </Typography>
                      <Selector
                        selectedItems={orientationItems.find((item) => item.value === orientation)}
                        setSelectedItems={(item: SelectorItem | SelectorItem[] | undefined) => {
                          if (item && !Array.isArray(item)) {
                            handleOrientationChange(item.value as PageConfig["orientation"]);
                          }
                        }}
                        items={orientationItems}
                        disabled={!selectedReport || isSaving}
                      />
                    </Box>

                    {/* DPI */}
                    <Box>
                      <Typography variant="body2" fontWeight={600} sx={{ mb: 1 }}>
                        {t("dpi")}
                      </Typography>
                      <Selector
                        selectedItems={dpiItems.find((item) => item.value === dpi)}
                        setSelectedItems={(item: SelectorItem | SelectorItem[] | undefined) => {
                          if (item && !Array.isArray(item)) {
                            setDpi(item.value as number);
                          }
                        }}
                        items={dpiItems}
                        disabled={!selectedReport || isSaving}
                      />
                    </Box>

                    {/* Export Format */}
                    <Box>
                      <Typography variant="body2" fontWeight={600} sx={{ mb: 1 }}>
                        {t("format_export")}
                      </Typography>
                      <Selector
                        selectedItems={exportFormatItems.find((item) => item.value === exportFormat)}
                        setSelectedItems={(item: SelectorItem | SelectorItem[] | undefined) => {
                          if (item && !Array.isArray(item)) {
                            setExportFormat(item.value as string);
                          }
                        }}
                        items={exportFormatItems}
                        disabled={!selectedReport || isSaving}
                      />
                    </Box>

                    {/* Snap to Guides */}
                    <FormControlLabel
                      control={
                        <Switch
                          checked={snapToGuides}
                          onChange={(e) => handleSnapToGuidesChange(e.target.checked)}
                          disabled={!selectedReport || isSaving}
                          size="small"
                        />
                      }
                      label={<Typography variant="body2">{t("snap_to_guides")}</Typography>}
                      sx={{ ml: 0 }}
                    />

                    {/* Show Rulers */}
                    <FormControlLabel
                      control={
                        <Switch
                          checked={showRulers}
                          onChange={(e) => handleShowRulersChange(e.target.checked)}
                          disabled={!selectedReport || isSaving}
                          size="small"
                        />
                      }
                      label={<Typography variant="body2">{t("show_rulers")}</Typography>}
                      sx={{ ml: 0 }}
                    />
                  </Stack>
                }
              />
            </Box>

            {/* Atlas/Map Series Section */}
            <Box sx={{ overflow: "hidden" }}>
              <SectionHeader
                active={atlasEnabled}
                label={t("atlas_map_series")}
                icon={ICON_NAME.LAYERS}
                collapsed={atlasSettingsCollapsed}
                setCollapsed={setAtlasSettingsCollapsed}
                onToggleChange={(e) => handleAtlasEnabledChange(e.target.checked)}
                disableAdvanceOptions
              />
              <SectionOptions
                active={atlasEnabled && !atlasSettingsCollapsed}
                baseOptions={
                  <Stack spacing={2}>
                    {/* Coverage Layer */}
                    <Box>
                      <Typography variant="body2" fontWeight={600} sx={{ mb: 1 }}>
                        {t("coverage_layer")}
                      </Typography>
                      <Selector
                        selectedItems={coverageLayerItems.find((item) => item.value === atlasLayerId)}
                        setSelectedItems={(item: SelectorItem | SelectorItem[] | undefined) => {
                          if (item && !Array.isArray(item)) {
                            handleAtlasLayerChange(item.value as number);
                          } else {
                            handleAtlasLayerChange(null);
                          }
                        }}
                        items={coverageLayerItems}
                        placeholder={t("select_layer")}
                        disabled={!selectedReport || isSaving}
                      />
                    </Box>
                  </Stack>
                }
              />
            </Box>
          </Stack>
        </Box>
      </Box>

      {/* Action Buttons - Fixed at bottom */}
      <Box
        sx={{
          px: 2,
          py: 3,
          borderTop: 1,
          borderColor: "divider",
          flexShrink: 0,
          backgroundColor: "background.default",
        }}>
        <Stack spacing={1.5}>
          {/* Print Button (server-side PDF generation) */}
          <Button
            variant="contained"
            fullWidth
            onClick={handlePrintReport}
            disabled={!selectedReport || isPrinting}
            startIcon={
              isPrinting ? (
                <CircularProgress size={16} color="inherit" />
              ) : (
                <Icon iconName={ICON_NAME.PRINT} style={{ fontSize: "16px" }} />
              )
            }
            sx={{
              textTransform: "none",
              py: 1.5,
            }}>
            {isPrinting ? t("printing") : t("print_layout")}
          </Button>
        </Stack>
      </Box>

      {/* Delete Confirmation Modal */}
      {deleteModalOpen && (
        <ConfirmModal
          open={deleteModalOpen}
          title={t("delete_layout")}
          body={
            <Trans
              i18nKey="common:delete_layout_confirmation"
              values={{ name: actionLayoutName }}
              components={{ b: <b /> }}
            />
          }
          onClose={() => {
            setDeleteModalOpen(false);
            setActionLayoutId(null);
            setActionLayoutName("");
          }}
          closeText={t("cancel")}
          confirmText={t("delete")}
          onConfirm={async () => {
            if (actionLayoutId) {
              await handleDeleteReport(actionLayoutId);
            }
            setDeleteModalOpen(false);
            setActionLayoutId(null);
            setActionLayoutName("");
          }}
        />
      )}

      {/* Rename Modal */}
      <ReportLayoutRenameModal
        open={renameModalOpen}
        layoutName={actionLayoutName}
        onClose={() => {
          setRenameModalOpen(false);
          setActionLayoutId(null);
          setActionLayoutName("");
        }}
        onRename={handleRenameReport}
      />
    </PanelContainer>
  );
};

export default ReportsConfigPanel;
