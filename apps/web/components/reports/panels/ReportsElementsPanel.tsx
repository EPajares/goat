"use client";

import { useDraggable } from "@dnd-kit/core";
import { Download as DownloadIcon } from "@mui/icons-material";
import {
  Box,
  Card,
  CardHeader,
  CircularProgress,
  Divider,
  Grid,
  IconButton,
  Stack,
  Tooltip,
  Typography,
  useTheme,
} from "@mui/material";
import React, { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";

import { Icon } from "@p4b/ui/components/Icon";

import { useJobs } from "@/lib/api/processes";
import type { Project, ProjectLayer } from "@/lib/validations/project";
import type { ReportElement, ReportElementType, ReportLayout } from "@/lib/validations/reportLayout";

import SettingsGroupHeader from "@/components/builder/widgets/common/SettingsGroupHeader";
import SidePanel, { SidePanelTabPanel, SidePanelTabs } from "@/components/common/SidePanel";
import JobProgressItem from "@/components/jobs/JobProgressItem";
import { reportElementIconMap } from "@/components/reports/elements/ReportElementIconMap";
import ElementConfiguration from "@/components/reports/elements/config/ElementConfiguration";

interface ReportsElementsPanelProps {
  project?: Project;
  projectLayers?: ProjectLayer[];
  selectedReport?: ReportLayout | null;
  selectedElementId?: string | null;
  onElementSelect?: (elementId: string | null) => void;
  onElementUpdate?: (elementId: string, updates: Partial<ReportElement>) => void;
  onElementDelete?: (elementId: string) => void;
}

interface ElementConfig {
  type: ReportElementType;
  label: string;
}

// Draggable element item component - styled same as builder's DraggableItem
interface DraggableElementItemProps {
  type: ReportElementType;
  label: string;
}

const DraggableElementItem: React.FC<DraggableElementItemProps> = ({ type, label }) => {
  const theme = useTheme();
  const { attributes, listeners, setNodeRef, isDragging } = useDraggable({
    id: `report-element-${type}`,
    data: {
      type: "report-element",
      elementType: type,
    },
  });

  return (
    <Card
      ref={setNodeRef}
      {...listeners}
      {...attributes}
      sx={{
        cursor: isDragging ? "grabbing" : "grab",
        maxWidth: "130px",
        borderRadius: "6px",
        opacity: isDragging ? 0.5 : 1,
        transition: "opacity 0.2s",
      }}>
      <CardHeader
        sx={{
          px: 2,
          py: 4,
          ".MuiCardHeader-content": {
            width: "100%",
            color: isDragging ? theme.palette.primary.main : theme.palette.text.secondary,
          },
        }}
        title={
          <Stack
            direction="row"
            alignItems="center"
            justifyContent="space-between"
            spacing={2}
            style={{
              color: theme.palette.text.secondary,
            }}>
            <Typography variant="body2" fontWeight="bold" noWrap color="inherit">
              {label}
            </Typography>
            <Icon
              iconName={reportElementIconMap[type]}
              style={{
                fontSize: "1.2rem",
                color: isDragging ? theme.palette.primary.main : "inherit",
              }}
            />
          </Stack>
        }
      />
    </Card>
  );
};

// Elements tab content
const ElementsTabContent: React.FC = () => {
  const { t } = useTranslation("common");

  const mapElements: ElementConfig[] = [
    { type: "map", label: t("map") },
    { type: "legend", label: t("legend") },
    { type: "scalebar", label: t("scalebar") },
    { type: "north_arrow", label: t("north_arrow") },
  ];

  const contentElements: ElementConfig[] = [
    { type: "text", label: t("text") },
    { type: "image", label: t("image") },
    { type: "divider", label: t("divider") },
  ];

  // Separate chart types like in the builder
  const chartElements: ElementConfig[] = [
    { type: "histogram_chart", label: t("histogram_chart") },
    { type: "categories_chart", label: t("categories_chart") },
    { type: "pie_chart", label: t("pie_chart") },
  ];

  const dataElements: ElementConfig[] = [{ type: "table", label: t("table") }];

  const utilityElements: ElementConfig[] = [
    { type: "qr_code", label: t("qr_code") },
    { type: "metadata", label: t("metadata") },
  ];

  return (
    <Stack spacing={4} sx={{ p: 3 }}>
      {/* Map Elements Section */}
      <Box sx={{ mb: 8 }}>
        <SettingsGroupHeader label={t("map_elements")} />
        <Grid container spacing={4}>
          {mapElements.map((element) => (
            <Grid item xs={6} key={element.type}>
              <DraggableElementItem type={element.type} label={element.label} />
            </Grid>
          ))}
        </Grid>
      </Box>

      {/* Content Elements Section */}
      <Box sx={{ mb: 8 }}>
        <SettingsGroupHeader label={t("content")} />
        <Grid container spacing={4}>
          {contentElements.map((element) => (
            <Grid item xs={6} key={element.type}>
              <DraggableElementItem type={element.type} label={element.label} />
            </Grid>
          ))}
        </Grid>
      </Box>

      {/* Charts Section - separate chart types like builder */}
      <Box sx={{ mb: 8 }}>
        <SettingsGroupHeader label={t("charts")} />
        <Grid container spacing={4}>
          {chartElements.map((element) => (
            <Grid item xs={6} key={element.type}>
              <DraggableElementItem type={element.type} label={element.label} />
            </Grid>
          ))}
        </Grid>
      </Box>

      {/* Data Elements Section */}
      <Box sx={{ mb: 8 }}>
        <SettingsGroupHeader label={t("data")} />
        <Grid container spacing={4}>
          {dataElements.map((element) => (
            <Grid item xs={6} key={element.type}>
              <DraggableElementItem type={element.type} label={element.label} />
            </Grid>
          ))}
        </Grid>
      </Box>

      {/* Utility Elements Section */}
      <Box sx={{ mb: 8 }}>
        <SettingsGroupHeader label={t("utilities")} />
        <Grid container spacing={4}>
          {utilityElements.map((element) => (
            <Grid item xs={6} key={element.type}>
              <DraggableElementItem type={element.type} label={element.label} />
            </Grid>
          ))}
        </Grid>
      </Box>
    </Stack>
  );
};

// History tab content - shows print jobs for the current layout
interface HistoryTabContentProps {
  projectId?: string;
  layoutId?: string;
}

const HistoryTabContent: React.FC<HistoryTabContentProps> = ({ projectId, layoutId }) => {
  const { t } = useTranslation("common");

  // Fetch all print jobs for this project (don't filter by read status to get history)
  // Note: We fetch all jobs for the project and filter client-side by layout_id
  const { jobs, isLoading, mutate } = useJobs(
    projectId
      ? {
          processID: "print_report",
        }
      : undefined
  );

  // Helper to parse payload (can be string or object)
  const parsePayload = (
    payload: unknown
  ): {
    layout_id?: string;
    s3_key?: string;
    file_name?: string;
    format?: string;
    layout_name?: string;
  } | null => {
    if (!payload) return null;
    if (typeof payload === "string") {
      try {
        return JSON.parse(payload);
      } catch {
        return null;
      }
    }
    return payload as {
      layout_id?: string;
      s3_key?: string;
      file_name?: string;
      format?: string;
      layout_name?: string;
    };
  };

  // Filter jobs by type and layout_id from payload
  const printJobs = useMemo(() => {
    if (!jobs?.jobs || !layoutId) return [];
    return jobs.jobs.filter((job) => {
      // Filter by job type first
      if (job.processID !== "print_report") return false;
      // Then filter by layout_id in payload (payload can be string or object)
      const payload = parsePayload(job.payload);
      return payload?.layout_id === layoutId;
    });
  }, [jobs?.jobs, layoutId]);

  // Check if there are running jobs
  const hasRunningJobs = useMemo(() => {
    return printJobs.some((job) => job.status === "running" || job.status === "accepted");
  }, [printJobs]);

  // Poll for updates - always poll at a slower rate, faster when jobs are running
  useEffect(() => {
    const intervalId = setInterval(
      () => {
        mutate();
      },
      hasRunningJobs ? 3000 : 10000
    );

    return () => clearInterval(intervalId);
  }, [hasRunningJobs, mutate]);

  const [downloadingJobId, setDownloadingJobId] = useState<string | null>(null);

  const handleDownload = async (jobId: string, fallbackFileName: string) => {
    if (!projectId) return;

    setDownloadingJobId(jobId);
    try {
      // Get a fresh download URL from the API
      const { apiRequestAuth } = await import("@/lib/api/fetcher");
      const response = await apiRequestAuth(
        `${process.env.NEXT_PUBLIC_API_URL}/api/v2/project/${projectId}/print/${jobId}/download`
      );

      if (!response.ok) {
        throw new Error("Failed to get download URL");
      }

      const data = await response.json();

      // Trigger download
      const link = document.createElement("a");
      link.href = data.download_url;
      link.download = data.file_name || fallbackFileName;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } catch (error) {
      console.error("Download failed:", error);
    } finally {
      setDownloadingJobId(null);
    }
  };

  if (isLoading) {
    return (
      <Box sx={{ display: "flex", justifyContent: "center", alignItems: "center", height: 200 }}>
        <CircularProgress size={24} />
      </Box>
    );
  }

  return (
    <Box>
      {printJobs.length === 0 ? (
        <Box
          sx={{
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            height: 200,
            textAlign: "center",
          }}>
          <Typography variant="body2" color="text.secondary">
            {t("no_print_history")}
          </Typography>
        </Box>
      ) : (
        <Stack direction="column">
          {printJobs.map((job, index) => {
            const payload = parsePayload(job.payload);
            // Show download button for finished jobs that have s3_key
            const canDownload = job.status === "successful" && payload?.s3_key;
            const isDownloading = downloadingJobId === job.jobID;

            // Create download button to pass as custom action
            const downloadButton = canDownload ? (
              <Tooltip title={t("download")}>
                <IconButton
                  size="small"
                  onClick={() => handleDownload(job.jobID, payload?.file_name || "report.pdf")}
                  disabled={isDownloading}
                  sx={{ fontSize: "1.2rem", color: "success.main" }}>
                  {isDownloading ? (
                    <CircularProgress size={18} color="success" />
                  ) : (
                    <DownloadIcon fontSize="small" />
                  )}
                </IconButton>
              </Tooltip>
            ) : undefined;

            return (
              <Box key={job.jobID} sx={{ overflow: "hidden" }}>
                <JobProgressItem
                  id={job.jobID}
                  type={job.processID}
                  status={job.status}
                  name={job.jobID}
                  date={job.updated || job.created || ""}
                  errorMessage={job.status === "failed" ? job.message : undefined}
                  actionButton={downloadButton}
                />
                {index < printJobs.length - 1 && <Divider />}
              </Box>
            );
          })}
        </Stack>
      )}
    </Box>
  );
};

const ReportsElementsPanel: React.FC<ReportsElementsPanelProps> = ({
  project,
  projectLayers,
  selectedReport,
  selectedElementId,
  onElementSelect,
  onElementUpdate,
  onElementDelete,
}) => {
  const { t } = useTranslation("common");
  const [activeTab, setActiveTab] = useState(0);

  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  // Find the selected element
  const selectedElement = useMemo(() => {
    if (!selectedElementId || !selectedReport?.config?.elements) {
      return null;
    }
    return selectedReport.config.elements.find((el) => el.id === selectedElementId) ?? null;
  }, [selectedElementId, selectedReport?.config?.elements]);

  // Determine if we should show configuration (like builder's showConfiguration)
  const showConfiguration = useMemo(() => {
    return selectedElement !== null;
  }, [selectedElement]);

  // Handle element update
  const handleElementUpdate = (updates: Partial<ReportElement>) => {
    if (selectedElementId && onElementUpdate) {
      onElementUpdate(selectedElementId, updates);
    }
  };

  // Handle element delete
  const handleElementDelete = () => {
    if (selectedElementId && onElementDelete) {
      onElementDelete(selectedElementId);
    }
  };

  // Handle back (deselect element)
  const handleBack = () => {
    if (onElementSelect) {
      onElementSelect(null);
    }
  };

  // If an element is selected, show its configuration
  if (showConfiguration && selectedElement) {
    return (
      <SidePanel sx={{ borderLeft: (theme) => `1px solid ${theme.palette.background.paper}` }}>
        <ElementConfiguration
          element={selectedElement}
          projectLayers={projectLayers}
          onChange={handleElementUpdate}
          onDelete={handleElementDelete}
          onBack={handleBack}
        />
      </SidePanel>
    );
  }

  // Otherwise show the elements palette (default view)
  return (
    <SidePanel sx={{ borderLeft: (theme) => `1px solid ${theme.palette.background.paper}` }}>
      <SidePanelTabs
        value={activeTab}
        onChange={handleTabChange}
        tabs={[
          { label: t("elements"), id: "elements" },
          { label: t("history"), id: "history" },
        ]}
        ariaLabel="report panel tabs"
      />
      <SidePanelTabPanel value={activeTab} index={0} id="elements">
        <ElementsTabContent />
      </SidePanelTabPanel>
      <SidePanelTabPanel value={activeTab} index={1} id="history">
        <HistoryTabContent projectId={project?.id} layoutId={selectedReport?.id} />
      </SidePanelTabPanel>
    </SidePanel>
  );
};

export default ReportsElementsPanel;
