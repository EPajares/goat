import { useEffect } from "react";
import { useTranslation } from "react-i18next";
import { toast } from "react-toastify";

import { useJobs } from "@/lib/api/processes";
import { setRunningJobIds } from "@/lib/store/jobs/slice";

import { useAppDispatch, useAppSelector } from "@/hooks/store/ContextHooks";

export function useJobStatus(onSuccess?: () => void, onFailed?: () => void) {
  const { jobs } = useJobs();
  const runningJobIds = useAppSelector((state) => state.jobs.runningJobIds);
  const dispatch = useAppDispatch();
  const { t } = useTranslation("common");

  useEffect(() => {
    if (runningJobIds.length > 0) {
      jobs?.jobs?.forEach((job) => {
        if (runningJobIds.includes(job.jobID)) {
          if (job.status === "running" || job.status === "accepted") return;
          dispatch(setRunningJobIds(runningJobIds.filter((id) => id !== job.jobID)));
          const type = t(job.processID) || "";
          if (job.status === "successful") {
            onSuccess && onSuccess();
            toast.success(`"${type}" - ${t("job_success")}`);
          } else {
            onFailed && onFailed();
            toast.error(`"${type}" - ${t("job_failed")}`);
          }
        }
      });
    }
  }, [runningJobIds, jobs, dispatch, t, onSuccess, onFailed]);
}
