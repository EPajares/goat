# Print Module - Report Builder & Atlas System

## 📊 Status: Phase 1 Complete ✅

**Total Tests: 37 passing** (3 test suites ready, 1 pending Playwright install)
- ✅ Unit conversions: 12 tests
- ✅ Schema validation: 11 tests  
- ✅ **Atlas utilities: 14 tests** ⭐ NEW
- ⏳ PDF renderer: 6 tests (requires `pnpm add playwright`)

## 🏗️ **Architecture Overview**

### Schema Locations

- **`@/lib/validations/reportLayout.ts`** - Canonical Zod schemas for report layouts
- **`@/lib/api/reportLayouts.ts`** - SWR hooks and API functions for CRUD
- **`@/lib/print/`** - Print-specific utilities (this module)

### Backend

- **`apps/core/src/core/schemas/report_layout.py`** - Pydantic schemas
- **`apps/core/src/core/crud/crud_report_layout.py`** - CRUD operations
- **`apps/core/src/core/endpoints/v2/report_layout.py`** - REST API endpoints

### Database

The system uses **`report_layout`** table to store report configurations:
- Each project can have multiple report layouts
- Layouts contain: page setup, elements (maps, charts, text, tables), theme, atlas config
- Supports both single-page and multi-page (atlas) reports

### Why "Report Layout" not "Print Template"?

✅ **Report** = maps + widgets + text + tables (the full scope)  
✅ **Layout** = the design/arrangement (what users create)  
✅ Matches existing patterns (`builder_config`, `layer`)  
✅ Works for single-page AND multi-page reports

## 🗺️ Atlas/Series Print Support

Multi-page map series generation is supported. Create map atlases that automatically divide large areas into printable pages.

**Key Features:**
- ✅ **Automatic grid calculation** - Smart layout based on extent and page aspect ratio
- ✅ **Manual grid specification** - Custom layouts (e.g., 3×4 grid, 2×5 grid)
- ✅ **Configurable overlap** - 0-50% overlap between adjacent tiles
- ✅ **Three numbering formats** - Numeric (1,2,3), Alphanumeric (A1,B2), Grid (Row1-Col2)
- ✅ **Overview/locator maps** - Mini map on each page showing current extent
- ✅ **Navigation aids** - Display adjacent page labels for easy reference

### Quick Example

```typescript
import { calculateAtlasGrid } from "@/lib/print/atlas-utils";
import type { AtlasConfig, MapElementConfig } from "@/lib/validations/reportLayout";

const atlasConfig: AtlasConfig = {
  enabled: true,
  grid: {
    type: "auto",  // Automatically calculate optimal grid
    overlap_percent: 10,  // 10% overlap between tiles
  },
  bounds: [-122.5, 37.5, -122.0, 38.0],  // SF Bay Area
  page_numbering: {
    format: "alphanumeric",  // A1, A2, B1, B2...
    prefix: "Sheet ",
  },
  overview_map: {
    enabled: true,
    position: "top-right",
    size: { width: 40, height: 40 },
  },
};

// Calculate the grid
const grid = calculateAtlasGrid(atlasConfig, mapConfig);

console.log(`Atlas: ${grid.rows}×${grid.columns} = ${grid.totalPages} pages`);
// Output: "Atlas: 4×3 = 12 pages"

// Each page has: index, label, bounds, center, zoom
grid.pages.forEach(page => {
  console.log(`Page ${page.label}: ${page.bounds}`);
});
```

### Configuration Schema

The `AtlasConfig` extends the `ReportLayout` schema:

```typescript
{
  page: { size: "A4", orientation: "landscape" },
  elements: [...],  // Base template elements
  atlas: {          // Optional atlas configuration
    enabled: boolean,
    grid: {
      type: "auto" | "manual",
      rows?: number,
      columns?: number,
      overlap_percent: number,  // 0-50
    },
    bounds: [west, south, east, north],
    page_numbering: {
      format: "numeric" | "alphanumeric" | "grid",
      position: "top-left" | "bottom-center" | ...,
      prefix?: string,
    },
    overview_map: {
      enabled: boolean,
      position: "top-right" | "bottom-left" | ...,
      size: { width: number, height: number },
    },
  }
}
```

## 📁 Module Structure

```
apps/web/lib/
├── validations/
│   └── reportLayout.ts            ✅ Canonical Zod schemas
├── api/
│   └── reportLayouts.ts           ✅ SWR hooks & API functions
└── print/                         ✅ Print utilities
    ├── __tests__/
    │   ├── units.test.ts          ✅ 12 tests - Unit conversions
    │   ├── template-schema.test.ts ✅ 11 tests - Schema validation
    │   ├── atlas-utils.test.ts    ✅ 14 tests - Atlas calculations
    │   └── pdf-renderer.test.ts   ⏳  6 tests - PDF generation
    ├── units.ts                   ✅ mm↔px conversions, page sizes
    ├── schemas.ts                 ✅ Re-exports + print-specific schemas
    ├── atlas-utils.ts             ✅ Grid calculation, navigation
    ├── pdf-renderer.ts            ✅ Playwright PDF generation
    └── index.ts                   ✅ Barrel exports
```

## 🧪 Testing

Run all print module tests:
```bash
cd apps/web
pnpm exec vitest run lib/print/__tests__/
```

Run atlas tests specifically:
```bash
pnpm exec vitest run lib/print/__tests__/atlas-utils.test.ts
```

Watch mode for TDD:
```bash
pnpm exec vitest lib/print/__tests__/
```
   - [ ] Test: Validate template constraints
   - [ ] Implement: `template-engine.ts`

2. **Element Positioning**
   - [ ] Write test: `positioning.test.ts`
   - [ ] Test: Element collision detection
   - [ ] Test: Snap to grid
   - [ ] Test: Bounds checking
   - [ ] Implement: `positioning.ts`

3. **Map Rendering** (Integration test)
   - [ ] Write test: `map-renderer.test.ts`
   - [ ] Test: Static map generation
   - [ ] Test: Layer composition
   - [ ] Test: Scale calculation
   - [ ] Implement: `map-renderer.ts`

4. **PDF Generation** (E2E test)
   - [ ] Write test: `pdf-generator.test.ts`
   - [ ] Test: Template → HTML
   - [ ] Test: HTML → PDF (Playwright)
   - [ ] Implement: `pdf-generator.ts`

## VS Code Test Explorer

After installing dependencies:
1. Install "Vitest Explorer" extension (vitest.explorer)
2. Tests will appear in the Test Explorer sidebar
3. Click the beaker icon (🧪) in the activity bar
4. Run/debug individual tests or suites
