export const DEFAULT_ROWS_PER_PAGE_OPTIONS = [10, 25, 50];

/**
 * Page number for an offset/limit pair, as `TablePagination` wants it.
 * Floors, so a rows-per-page change that leaves a partial offset still yields
 * an integer page, and tolerates a zero limit.
 */
export const offsetToPage = (offset: number | undefined, limit: number): number =>
  limit > 0 ? Math.floor((offset ?? 0) / limit) : 0;
