// Print-specific schemas (not stored in report_layout)
import * as z from "zod";

/**
 * Print schemas - Re-exports from validations for backward compatibility
 *
 * @deprecated Import from '@/lib/validations/reportLayout' instead
 */

// Re-export all schemas and types from the canonical location
export {
  // Schemas
  pageConfigSchema,
  layoutGridConfigSchema,
  layoutGridConfigSchema as layoutConfigSchema, // Alias for backward compatibility
  elementPositionSchema,
  elementStyleSchema,
  reportElementTypes,
  reportElementTypes as printElementTypes, // Alias for backward compatibility
  reportElementSchema,
  reportElementSchema as printElementSchema, // Alias for backward compatibility
  themeConfigSchema,
  atlasConfigSchema,
  atlasCoverageSchema,
  atlasGridCoverageSchema,
  atlasFeatureCoverageSchema,
  atlasPageLabelSchema,
  mapAtlasControlSchema,
  mapAtlasHighlightSchema,
  mapElementConfigSchema,
  reportLayoutConfigSchema,
  reportLayoutSchema,
  // Types
  type PageConfig,
  type LayoutGridConfig,
  type LayoutGridConfig as LayoutConfig, // Alias for backward compatibility
  type ElementPosition,
  type ElementStyle,
  type ReportElementType,
  type ReportElementType as PrintElementType, // Alias for backward compatibility
  type ReportElement,
  type ReportElement as PrintElement, // Alias for backward compatibility
  type ThemeConfig,
  type AtlasConfig,
  type AtlasCoverage,
  type AtlasGridCoverage,
  type AtlasFeatureCoverage,
  type AtlasPageLabel,
  type MapAtlasControl,
  type MapAtlasHighlight,
  type MapElementConfig,
  type ReportLayoutConfig,
  type ReportLayout,
} from "@/lib/validations/reportLayout";

// Print job output settings
export const printOutputSchema = z.object({
  format: z.enum(["pdf", "png"]),
  quality: z.number().min(1).max(100).default(95),
  compress: z.boolean().default(true),
});

// Print job schema (for tracking print jobs - not stored in report_layout)
export const printJobSchema = z.object({
  id: z.string().uuid(),
  user_id: z.string().uuid(),
  project_id: z.string().uuid(),
  report_layout_id: z.string().uuid(),
  status: z.enum(["pending", "processing", "completed", "failed"]),
  output: printOutputSchema,
  file_url: z.string().url().optional(),
  file_size: z.number().optional(),
  error_message: z.string().optional(),
  created_at: z.string(),
  completed_at: z.string().optional(),
});

export type PrintOutput = z.infer<typeof printOutputSchema>;
export type PrintJob = z.infer<typeof printJobSchema>;
