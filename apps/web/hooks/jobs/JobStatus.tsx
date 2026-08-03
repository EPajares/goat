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
          // Don't show success toast for:
          // - delete jobs: already handled optimistically
          // - layer_export/print_report: handled in JobsPopper with auto-download
          // - workflow_runner: handled by useWorkflowExecution
          // - finalize_layer: show custom message
          const isDeleteJob =
            job.processID === "layer_delete" || job.processID.toLowerCase().includes("delete");
          const isDownloadJob = job.processID === "layer_export" || job.processID === "print_report";
          const isWorkflowJob = job.processID === "workflow_runner";
          const isFinalizeJob = job.processID === "finalize_layer";
          if (isFinalizeJob) {
            toast.success(t("layer_saved_successfully"));
          } else if (!isDeleteJob && !isDownloadJob && !isWorkflowJob) {
            toast.success(`"${type}" - ${t("job_success")}`);
          }
        } else {
          onFailedRef.current?.();
          const isFinalizeJob = job.processID === "finalize_layer";
          // workflow_runner failures are surfaced by useWorkflowExecution
          // with a contextual message; don't double-toast here.
          const isWorkflowJob = job.processID === "workflow_runner";
          if (isFinalizeJob) {
            toast.error(t("layer_save_failed"));
          } else if (!isWorkflowJob) {
            toast.error(`"${type}" - ${t("job_failed")}`);
          }
        }
      }
    });
  }, [runningJobIds, jobs, dispatch, t]);

  useEffect(() => {
    checkJobStatus();
  }, [checkJobStatus]);
}

/** Mounts the job-status polling in an isolated subtree. The jobs SWR data
 * changes identity on every poll, so whichever component calls useJobStatus
 * re-renders each time — hosting it here keeps those re-renders away from the
 * caller (MapPage renders its entire tree in ~300ms dev otherwise). */
export function JobStatusWatcher({ onSuccess, onFailed }: { onSuccess?: () => void; onFailed?: () => void }) {
  useJobStatus(onSuccess, onFailed);
  return null;
}
