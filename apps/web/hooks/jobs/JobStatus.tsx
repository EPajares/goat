import { useCallback, useEffect, useRef } from "react";
import { useTranslation } from "react-i18next";
import { toast } from "react-toastify";

import { useJobs } from "@/lib/api/processes";
import { setRunningJobIds } from "@/lib/store/jobs/slice";

import { useAppDispatch, useAppSelector } from "@/hooks/store/ContextHooks";

export function useJobStatus(onSuccess?: () => void, onFailed?: () => void) {
  const runningJobIds = useAppSelector((state) => state.jobs.runningJobIds);
  const { jobs, mutate: mutateJobs } = useJobs({ read: false });
  const dispatch = useAppDispatch();
  const { t } = useTranslation("common");
  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Stable callback refs to avoid stale closures
  const onSuccessRef = useRef(onSuccess);
  const onFailedRef = useRef(onFailed);
  useEffect(() => {
    onSuccessRef.current = onSuccess;
    onFailedRef.current = onFailed;
  }, [onSuccess, onFailed]);

  // Start/stop polling based on runningJobIds
  useEffect(() => {
    if (runningJobIds.length > 0 && !pollIntervalRef.current) {
      // Start polling every 2 seconds
      pollIntervalRef.current = setInterval(() => {
        mutateJobs();
      }, 2000);
      // Also trigger immediate fetch
      mutateJobs();
    } else if (runningJobIds.length === 0 && pollIntervalRef.current) {
      // Stop polling when no jobs to track
      clearInterval(pollIntervalRef.current);
      pollIntervalRef.current = null;
    }

    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
        pollIntervalRef.current = null;
      }
    };
  }, [runningJobIds.length, mutateJobs]);

  // Check job status and call callbacks
  const checkJobStatus = useCallback(() => {
    if (runningJobIds.length === 0 || !jobs?.jobs) return;

    jobs.jobs.forEach((job) => {
      if (runningJobIds.includes(job.jobID)) {
        if (job.status === "running" || job.status === "accepted") return;

        dispatch(setRunningJobIds(runningJobIds.filter((id) => id !== job.jobID)));
        const type = t(job.processID) || "";

        if (job.status === "successful") {
          onSuccessRef.current?.();
          // Don't show success toast for delete jobs - already handled optimistically
          const isDeleteJob =
            job.processID === "LayerDelete" || job.processID.toLowerCase().includes("delete");
          if (!isDeleteJob) {
            toast.success(`"${type}" - ${t("job_success")}`);
          }
        } else {
          onFailedRef.current?.();
          toast.error(`"${type}" - ${t("job_failed")}`);
        }
      }
    });
  }, [runningJobIds, jobs, dispatch, t]);

  useEffect(() => {
    checkJobStatus();
  }, [checkJobStatus]);
}
