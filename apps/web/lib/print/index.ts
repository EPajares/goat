/**
 * Print module - Core utilities and types for print/export functionality
 */

// Core utilities
/**
 * Print utilities and schemas
 *
 * This module provides utilities for report printing/PDF generation.
 *
 * For report layout schemas, prefer importing from:
 * @see {@link @/lib/validations/reportLayout}
 *
 * For API hooks (CRUD operations), use:
 * @see {@link @/lib/api/reportLayouts}
 */

// Core schemas (re-exports from validations + print-specific schemas)
export * from "./schemas";

// Unit conversions (mm <-> px, paper sizes, etc.)
export * from "./units";

// PDF rendering utilities (Playwright-based)
export * from "./pdf-renderer";

// Atlas/multi-page utilities
export * from "./atlas-utils";

// Re-export commonly used types
export type {
  ReportLayout,
  PrintElement,
  PrintJob,
  PageConfig,
  LayoutConfig,
  ElementPosition,
  MapElementConfig,
  AtlasConfig,
} from "./schemas";

export type { PageSize, PageOrientation } from "./units";
