import { Box, Collapse, IconButton, LinearProgress, Stack, Typography, useTheme } from "@mui/material";
import { format, parseISO } from "date-fns";
import type { ReactNode } from "react";
import { useState } from "react";
import { useTranslation } from "react-i18next";

import { ICON_NAME, Icon } from "@p4b/ui/components/Icon";

import type { JobStatusType, JobType } from "@/lib/api/processes";

import { OverflowTypograpy } from "@/components/common/OverflowTypography";

interface JobProgressItemProps {
  id: string;
  type: JobType;
  status: JobStatusType;
  errorMessage?: string;
  name: string;
  date: string;
  /** Optional custom action button to replace the default status icon */
  actionButton?: ReactNode;
}

// OGC status to icon mapping
const statusIcons: Record<JobStatusType, ICON_NAME> = {
  running: ICON_NAME.CLOSE,
  accepted: ICON_NAME.CLOCK,
  successful: ICON_NAME.CIRCLECHECK,
  failed: ICON_NAME.CIRCLEINFO,
  dismissed: ICON_NAME.CIRCLEINFO,
};

export default function JobProgressItem(props: JobProgressItemProps) {
  const { t } = useTranslation("common");
  const theme = useTheme();
  const { type, status, name, date } = props;
  const [showDetails, setShowDetails] = useState(false);

  // OGC status to color mapping
  const statusColors: Record<JobStatusType, string> = {
    running: theme.palette.primary.main,
    accepted: theme.palette.grey[500],
    successful: theme.palette.success.main,
    failed: theme.palette.error.main,
    dismissed: theme.palette.error.main,
  };

  // Map OGC status to display text keys
  const statusTextMap: Record<JobStatusType, string> = {
    running: "running",
    accepted: "pending",
    successful: "finished_successfully",
    failed: "failed",
    dismissed: "terminated",
  };
  return (
    <Box
      display="flex"
      alignItems="center"
      sx={{
        width: "100%",
        pl: 4,
        pr: 2,
        py: 1,
      }}
      aria-label={name}
      role="job_item">
      <Box flexGrow={1} flexShrink={1} flexBasis="100%" sx={{ mr: 2 }} width="0">
        <Stack spacing={2}>
          <Box textOverflow="ellipsis" overflow="hidden">
            <OverflowTypograpy
              variant="body2"
              fontWeight="bold"
              tooltipProps={{
                placement: "top",
                arrow: true,
              }}>
              <>
                {t(type)} -{" "}
                {format(parseISO(date), "hh:mma dd/MM/yyyy").replace("PM", " PM").replace("AM", " AM")}
              </>
            </OverflowTypograpy>
          </Box>
          <LinearProgress
            {...(status === "failed" || status === "successful" || status === "dismissed"
              ? { variant: "determinate", value: 100 }
              : {})}
            sx={{
              width: "100%",
              ...(status === "accepted" && {
                backgroundColor: theme.palette.grey[300],
              }),
              "& .MuiLinearProgress-bar": {
                backgroundColor: statusColors[status],
              },
            }}
          />
          <Stack direction="row" justifyContent="space-between" alignItems="center">
            <Typography variant="caption" fontWeight="bold">
              {t(statusTextMap[status])}
            </Typography>
            {props.errorMessage && (
              <Typography
                variant="caption"
                fontWeight="bold"
                color="primary"
                style={{ cursor: "pointer" }}
                onClick={() => setShowDetails(!showDetails)}>
                {t("details")}
              </Typography>
            )}
          </Stack>
          {props.errorMessage && (
            <Collapse in={showDetails}>
              <Box>
                <Typography variant="caption" fontWeight="bold" fontStyle="italic">
                  {props.errorMessage}
                </Typography>
              </Box>
            </Collapse>
          )}
        </Stack>
      </Box>
      {props.actionButton ? (
        props.actionButton
      ) : (
        <IconButton
          size="small"
          disabled={status === "accepted" || status === "running"}
          sx={{
            fontSize: "1.2rem",
            color: statusColors[status],
          }}>
          <Icon iconName={statusIcons[status]} htmlColor="inherit" fontSize="inherit" />
        </IconButton>
      )}
    </Box>
  );
}
