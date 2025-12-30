import { useCallback, useState } from "react";
import { useTranslation } from "react-i18next";
import { toast } from "react-toastify";
import { useSWRConfig } from "swr";

import { apiRequestAuth } from "@/lib/api/fetcher";
import { JOBS_API_BASE_URL } from "@/lib/api/processes";

const PROJECTS_API_BASE_URL = `${process.env.NEXT_PUBLIC_API_URL}/api/v2/project`;

export type ExportFormat = "pdf" | "png";

export interface ExportOptions {
  projectId: string;
  layoutId: string;
  format?: ExportFormat;
}

export interface UseExportReportResult {
  isBusy: boolean;
  exportReport: (options: ExportOptions) => Promise<void>;
}

/**
 * Hook for exporting reports to PDF/PNG via the backend.
 * Submits the job and shows a toast - doesn't wait for completion.
 * Job progress can be tracked in the Jobs Popper.
 */
export function useExportReport(): UseExportReportResult {
  const { t } = useTranslation("common");
  const [isBusy, setIsBusy] = useState(false);
  const { mutate } = useSWRConfig();

  /**
   * Start export job
   */
  const exportReport = useCallback(
    async (options: ExportOptions): Promise<void> => {
      const { projectId, layoutId, format = "pdf" } = options;

      setIsBusy(true);

      try {
        const response = await apiRequestAuth(`${PROJECTS_API_BASE_URL}/${projectId}/print`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            layout_id: layoutId,
            format,
          }),
        });

        if (!response.ok) {
          throw new Error("Request failed");
        }

        const data = await response.json();
        if (data.job_id) {
          toast.info(`"${t("print_report")}" - ${t("job_started")}`);
          // Refresh all jobs queries to show the new job in both popper and history
          mutate((key) => Array.isArray(key) && key[0]?.startsWith(JOBS_API_BASE_URL));
        }
      } catch (err) {
        toast.error(`"${t("print_report")}" - ${t("job_failed")}`);
        throw err;
      } finally {
        setIsBusy(false);
      }
    },
    [t, mutate]
  );

  return {
    isBusy,
    exportReport,
  };
}
