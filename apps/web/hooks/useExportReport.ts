import { useCallback, useState } from "react";
import { useTranslation } from "react-i18next";
import { toast } from "react-toastify";
import { useSWRConfig } from "swr";

import { JOBS_API_BASE_URL, executeProcessAsync } from "@/lib/api/processes";

export type ExportFormat = "pdf" | "png";

export interface ExportOptions {
  projectId: string;
  layoutId: string;
  format?: ExportFormat;
  atlasPageIndices?: number[];
  /** Total number of atlas pages (used by backend when atlasPageIndices is not provided) */
  totalAtlasPages?: number;
}

export interface UseExportReportResult {
  isBusy: boolean;
  exportReport: (options: ExportOptions) => Promise<void>;
}

/**
 * Hook for exporting reports to PDF/PNG via OGC API Processes.
 * Submits a PrintReport job and shows a toast - doesn't wait for completion.
 * Job progress can be tracked in the Jobs Popper.
 */
export function useExportReport(): UseExportReportResult {
  const { t } = useTranslation("common");
  const [isBusy, setIsBusy] = useState(false);
  const { mutate } = useSWRConfig();

  /**
   * Start export job via OGC API Processes
   */
  const exportReport = useCallback(
    async (options: ExportOptions): Promise<void> => {
      const { projectId, layoutId, format = "pdf", atlasPageIndices, totalAtlasPages } = options;

      setIsBusy(true);

      try {
        // Execute PrintReport process via OGC API Processes
        const inputs: Record<string, unknown> = {
          project_id: projectId,
          layout_id: layoutId,
          format,
        };

        // Only include atlas_page_indices if provided
        if (atlasPageIndices !== undefined) {
          inputs.atlas_page_indices = atlasPageIndices;
        }

        // Pass total atlas pages so backend doesn't need to query
        if (totalAtlasPages !== undefined) {
          inputs.total_atlas_pages = totalAtlasPages;
        }

        const job = await executeProcessAsync("PrintReport", inputs);

        if (job.jobID) {
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
