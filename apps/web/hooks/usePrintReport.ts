import { useCallback, useState } from "react";

export interface PrintOptions {
  projectId: string;
  layoutId: string;
}

export interface UsePrintReportResult {
  isPrinting: boolean;
  error: string | null;
  printReport: (options: PrintOptions) => Promise<void>;
  openPreview: (projectId: string, layoutId: string) => void;
}

/**
 * Hook for printing/exporting reports
 * Uses browser's native print dialog via the print preview page
 */
export function usePrintReport(): UsePrintReportResult {
  const [isPrinting, setIsPrinting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  /**
   * Print report (opens browser print dialog)
   * This opens the print page in a new window and triggers print
   */
  const printReport = useCallback(async (options: PrintOptions): Promise<void> => {
    const { projectId, layoutId } = options;

    setIsPrinting(true);
    setError(null);

    try {
      // Open print page in new window
      const printUrl = `/print/${projectId}/${layoutId}`;
      const printWindow = window.open(printUrl, "_blank", "width=800,height=600");

      if (!printWindow) {
        throw new Error("Failed to open print window. Please allow popups.");
      }

      // Wait for the page to load and trigger print
      printWindow.onload = () => {
        // Wait for content to render
        setTimeout(() => {
          printWindow.print();
          setIsPrinting(false);
        }, 1000);
      };

      // Handle window close
      const checkClosed = setInterval(() => {
        if (printWindow.closed) {
          clearInterval(checkClosed);
          setIsPrinting(false);
        }
      }, 500);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to print report";
      setError(message);
      console.error("Print failed:", err);
      setIsPrinting(false);
      throw err;
    }
  }, []);

  /**
   * Open print preview in new tab
   */
  const openPreview = useCallback((projectId: string, layoutId: string): void => {
    const printUrl = `/print/${projectId}/${layoutId}`;
    window.open(printUrl, "_blank");
  }, []);

  return {
    isPrinting,
    error,
    printReport,
    openPreview,
  };
}
