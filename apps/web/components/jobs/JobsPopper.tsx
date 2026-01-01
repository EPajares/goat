import DownloadIcon from "@mui/icons-material/Download";
import {
  Badge,
  Box,
  Button,
  Divider,
  IconButton,
  Paper,
  Stack,
  Tooltip,
  Typography,
  styled,
} from "@mui/material";
import { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";

import { ICON_NAME, Icon } from "@p4b/ui/components/Icon";

import { type Job, setJobsReadStatus, useJobs } from "@/lib/api/processes";

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
  const { jobs, mutate } = useJobs();

  // Filter to get running/accepted jobs using OGC status
  const runningJobs = useMemo(() => {
    return jobs?.jobs?.filter((job) => job.status === "running" || job.status === "accepted");
  }, [jobs?.jobs]);

  // Poll faster (every 2 seconds) when there are pending/running jobs
  const [intervalId, setIntervalId] = useState<number | null>(null);
  useEffect(() => {
    if (!runningJobs) return;
    const activeJobsCount = runningJobs.length;
    if (activeJobsCount === 0) {
      // no running jobs, clear interval and return
      if (intervalId) {
        clearInterval(intervalId);
        setIntervalId(null);
      }
      return;
    }

    // at least one running job, set interval if not already set
    if (!intervalId) {
      const id = setInterval(() => {
        mutate();
      }, 2000) as unknown as number;
      setIntervalId(id);
    }

    // cleanup function
    return () => {
      if (intervalId) {
        clearInterval(intervalId);
        setIntervalId(null);
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [runningJobs, intervalId]);

  const [isBusy, setIsBusy] = useState(false);

  const handleClearAll = async () => {
    const jobIds = jobs?.jobs?.map((job) => job.jobID);
    if (!jobIds) return;
    setIsBusy(true);
    try {
      await setJobsReadStatus(jobIds);
      mutate();
    } catch (err) {
      console.error(err);
    } finally {
      setIsBusy(false);
    }
  };

  // Handle download for LayerExport jobs
  const handleExportDownload = async (payload: Record<string, unknown> | undefined) => {
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
    } catch (error) {
      console.error("Download failed:", error);
    }
  };

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
                    // Add download button for layer_export jobs
                    const actionButton =
                      job.processID === "layer_export" ? renderExportDownloadButton(job) : undefined;

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
              <Divider sx={{ mt: 0 }} />
              <Stack direction="row" justifyContent="end" alignItems="center" sx={{ py: 1 }}>
                <Button
                  disabled={isBusy}
                  variant="text"
                  onClick={handleClearAll}
                  sx={{
                    mr: 4,
                  }}>
                  <Typography variant="body2" fontWeight="bold" color="inherit">
                    {t("clear_all")}
                  </Typography>
                </Button>
              </Stack>
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
