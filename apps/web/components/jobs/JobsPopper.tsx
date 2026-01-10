import DownloadIcon from "@mui/icons-material/Download";
import OpenInNewIcon from "@mui/icons-material/OpenInNew";
import { Badge, Box, Divider, IconButton, Paper, Stack, Tooltip, Typography, styled } from "@mui/material";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { toast } from "react-toastify";

import { ICON_NAME, Icon } from "@p4b/ui/components/Icon";

import { type Job, useJobs } from "@/lib/api/processes";

import { ArrowPopper as JobStatusMenu } from "@/components/ArrowPoper";
import JobProgressItem from "@/components/jobs/JobProgressItem";

const StyledBadge = styled(Badge)(({ theme }) => ({
  "& .MuiBadge-badge": {
    backgroundColor: "#44b700",
    color: "#44b700",
    boxShadow: `0 0 0 2px ${theme.palette.background.paper}`,
    "&::after": {
      position: "absolute",
      top: 0,
      left: 0,
      width: "100%",
      height: "100%",
      borderRadius: "50%",
      animation: "ripple 1.2s infinite ease-in-out",
      border: "1px solid currentColor",
      content: '""',
    },
  },
  "@keyframes ripple": {
    "0%": {
      transform: "scale(.8)",
      opacity: 1,
    },
    "100%": {
      transform: "scale(2.4)",
      opacity: 0,
    },
  },
}));

export default function JobsPopper() {
  const { t } = useTranslation("common");
  const [open, setOpen] = useState(false);
  const { jobs } = useJobs({ read: false });

  // Track which export jobs have been auto-downloaded to avoid duplicate downloads
  const downloadedJobsRef = useRef<Set<string>>(new Set());
  // Track which print jobs have shown toast notifications
  const notifiedPrintJobsRef = useRef<Set<string>>(new Set());
  // Track jobs that were already successful on initial load (don't auto-download these)
  const initialSuccessfulJobsRef = useRef<Set<string> | null>(null);
  // Track print jobs that were already completed on initial load (don't show toast for these)
  const initialCompletedPrintJobsRef = useRef<Set<string> | null>(null);

  // Filter to get running/accepted jobs using OGC status
  const runningJobs = useMemo(() => {
    return jobs?.jobs?.filter((job) => job.status === "running" || job.status === "accepted");
  }, [jobs?.jobs]);

  // Handle download for LayerExport jobs
  const handleExportDownload = useCallback(
    async (payload: Record<string, unknown> | undefined, showToast = false) => {
      if (!payload) return;
      try {
        const downloadUrl = payload.download_url as string;
        const fileName = (payload.file_name as string) || "export.zip";
        if (!downloadUrl) {
          throw new Error("No download_url in job payload");
        }
        // Trigger download
        const link = document.createElement("a");
        link.href = downloadUrl;
        link.download = fileName;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);

        if (showToast) {
          toast.success(t("download_started") || "Download started");
        }
      } catch (error) {
        console.error("Download failed:", error);
        if (showToast) {
          toast.error(t("error_downloading") || "Download failed");
        }
      }
    },
    [t]
  );

  // Auto-download completed export jobs (only for jobs that complete AFTER initial load)
  useEffect(() => {
    if (!jobs?.jobs) return;

    // On first load, capture which jobs are already successful (don't auto-download these)
    if (initialSuccessfulJobsRef.current === null) {
      initialSuccessfulJobsRef.current = new Set(
        jobs.jobs
          .filter((job) => job.processID === "layer_export" && job.status === "successful")
          .map((job) => job.jobID)
      );
      return;
    }

    jobs.jobs.forEach((job) => {
      // Only auto-download layer_export jobs that:
      // 1. Completed successfully
      // 2. Were NOT already successful on initial load
      // 3. Haven't been downloaded yet in this session
      if (
        job.processID === "layer_export" &&
        job.status === "successful" &&
        !initialSuccessfulJobsRef.current?.has(job.jobID) &&
        !downloadedJobsRef.current.has(job.jobID)
      ) {
        const result = job.result as Record<string, unknown> | undefined;
        if (result?.download_url) {
          // Mark as downloaded before triggering to prevent race conditions
          downloadedJobsRef.current.add(job.jobID);
          handleExportDownload(result, true);
        }
      }
    });
  }, [jobs?.jobs, handleExportDownload]);

  // Show toast notifications for completed print_report jobs
  useEffect(() => {
    if (!jobs?.jobs) return;

    // On first load, capture which print jobs are already completed (don't show toast for these)
    if (initialCompletedPrintJobsRef.current === null) {
      initialCompletedPrintJobsRef.current = new Set(
        jobs.jobs
          .filter(
            (job) =>
              job.processID === "print_report" &&
              (job.status === "successful" || job.status === "failed" || job.status === "dismissed")
          )
          .map((job) => job.jobID)
      );
      return;
    }

    jobs.jobs.forEach((job) => {
      // Only show toast for print_report jobs that:
      // 1. Have completed (successful or failed)
      // 2. Were NOT already completed on initial load
      // 3. Haven't shown a toast yet in this session
      if (
        job.processID === "print_report" &&
        !initialCompletedPrintJobsRef.current?.has(job.jobID) &&
        !notifiedPrintJobsRef.current.has(job.jobID)
      ) {
        if (job.status === "successful") {
          notifiedPrintJobsRef.current.add(job.jobID);
          toast.success(`"${t("print_report")}" - ${t("job_success")}`);
        } else if (job.status === "failed" || job.status === "dismissed") {
          notifiedPrintJobsRef.current.add(job.jobID);
          toast.error(`"${t("print_report")}" - ${t("job_failed")}`);
        }
      }
    });
  }, [jobs?.jobs, t]);

  // Helper to render download button for export jobs
  const renderExportDownloadButton = (job: Job) => {
    const result = job.result as Record<string, unknown> | undefined;
    const canDownload = job.status === "successful" && result?.download_url;

    if (!canDownload) return undefined;

    return (
      <Tooltip title={t("download")}>
        <IconButton
          size="small"
          onClick={() => handleExportDownload(result)}
          sx={{ fontSize: "1.2rem", color: "success.main" }}>
          <DownloadIcon fontSize="small" />
        </IconButton>
      </Tooltip>
    );
  };

  // Helper to render open button for print_report jobs
  const renderPrintReportOpenButton = (job: Job) => {
    const result = job.result as Record<string, unknown> | undefined;
    const canOpen = job.status === "successful" && result?.download_url;

    if (!canOpen) return undefined;

    const handleOpenPdf = () => {
      window.open(result.download_url as string, "_blank");
    };

    return (
      <Tooltip title={t("view")}>
        <IconButton size="small" onClick={handleOpenPdf} sx={{ fontSize: "1.2rem", color: "success.main" }}>
          <OpenInNewIcon fontSize="small" />
        </IconButton>
      </Tooltip>
    );
  };

  // Get action button based on job type
  const getActionButton = (job: Job) => {
    if (job.processID === "layer_export") {
      return renderExportDownloadButton(job);
    }
    if (job.processID === "print_report") {
      return renderPrintReportOpenButton(job);
    }
    return undefined;
  };

  return (
    <>
      {jobs?.jobs && jobs.jobs.length > 0 && (
        <JobStatusMenu
          content={
            <Paper
              sx={{
                width: "320px",
                overflow: "auto",
                pt: 4,
                pb: 2,
              }}>
              <Box>
                <Typography variant="body1" fontWeight="bold" sx={{ px: 4, py: 1 }}>
                  {t("job_status")}
                </Typography>
                <Divider sx={{ mb: 0, pb: 0 }} />
              </Box>
              <Box
                sx={{
                  maxHeight: "300px",
                  overflowY: "auto",
                  overflowX: "hidden",
                  py: 2,
                }}>
                <Stack direction="column">
                  {jobs?.jobs?.map((job, index) => {
                    const actionButton = getActionButton(job);

                    return (
                      <Box key={job.jobID}>
                        <JobProgressItem
                          id={job.jobID}
                          type={job.processID}
                          status={job.status}
                          name={job.jobID}
                          date={job.updated || job.created || ""}
                          errorMessage={job.status === "failed" ? job.message : undefined}
                          actionButton={actionButton}
                        />
                        {index < jobs.jobs.length - 1 && <Divider />}
                      </Box>
                    );
                  })}
                </Stack>
              </Box>
            </Paper>
          }
          open={open}
          placement="bottom"
          onClose={() => setOpen(false)}>
          {jobs?.jobs && jobs.jobs.length > 0 ? (
            <Tooltip title={t("job_status")}>
              <IconButton
                onClick={() => {
                  setOpen(!open);
                }}
                size="small"
                sx={{
                  ...(open && {
                    color: "primary.main",
                  }),
                }}>
                {runningJobs && runningJobs?.length > 0 && (
                  <StyledBadge
                    overlap="circular"
                    anchorOrigin={{ vertical: "bottom", horizontal: "right" }}
                    variant="dot">
                    <Icon fontSize="inherit" iconName={ICON_NAME.BARS_PROGRESS} htmlColor="inherit" />
                  </StyledBadge>
                )}
                {!runningJobs ||
                  (runningJobs?.length === 0 && (
                    <Icon fontSize="inherit" iconName={ICON_NAME.BARS_PROGRESS} htmlColor="inherit" />
                  ))}
              </IconButton>
            </Tooltip>
          ) : (
            <></>
          )}
        </JobStatusMenu>
      )}
    </>
  );
}
