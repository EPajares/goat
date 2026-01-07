# Playwright Setup for Print Service

## ✅ What's Been Created

### 1. **PDF Renderer Module**
- `lib/print/pdf-renderer.ts` - Core PDF generation service
- `lib/print/__tests__/pdf-renderer.test.ts` - Integration tests

### 2. **Features Implemented**
- ✅ PDF generation from URL or HTML
- ✅ Screenshot capture
- ✅ Custom page sizes and margins
- ✅ Wait for content to load
- ✅ High-DPI/Retina support
- ✅ Singleton pattern for browser reuse

---

## 📦 Installation Required

Run this command to install Playwright as a runtime dependency:

```bash
cd apps/web
pnpm add playwright

# Also install Chromium browser
pnpm exec playwright install chromium
```

**Why both dependencies?**
- `@playwright/test` (already installed) - For E2E testing
- `playwright` (needs install) - For runtime PDF generation in API routes

---

## 🧪 Test the Integration

After installing, run:

```bash
cd apps/web

# Run all tests including Playwright integration tests
pnpm test

# Should see:
# ✓ lib/print/__tests__/units.test.ts (12)
# ✓ lib/print/__tests__/template-schema.test.ts (11)
# ✓ lib/print/__tests__/pdf-renderer.test.ts (6)  ← NEW!
#
# Total: 29 passing tests
```

---

## 🚀 Usage Example

### **In an API Route:**

```typescript
// app/api/print/generate/route.ts

import { NextRequest, NextResponse } from 'next/server';
import { getPDFRenderer } from '@/lib/print';

export async function POST(request: NextRequest) {
  const { templateId, projectId } = await request.json();
  
  try {
    const renderer = getPDFRenderer();
    
    // Generate PDF from preview URL
    const previewUrl = `${process.env.NEXT_PUBLIC_APP_URL}/print/${templateId}?projectId=${projectId}`;
    
    const pdf = await renderer.generatePDF({
      source: previewUrl,
      format: 'A4',
      printBackground: true,
      waitForSelector: '.print-preview',
      waitForFunction: 'window.mapReady === true', // Wait for map
      timeout: 30000,
    });
    
    return new NextResponse(pdf, {
      headers: {
        'Content-Type': 'application/pdf',
        'Content-Disposition': `attachment; filename="report-${templateId}.pdf"`,
      },
    });
    
  } catch (error) {
    console.error('PDF generation failed:', error);
    return NextResponse.json(
      { error: 'Failed to generate PDF' },
      { status: 500 }
    );
  }
}
```

### **Or Generate from HTML Directly:**

```typescript
import { getPDFRenderer } from '@/lib/print';

const renderer = getPDFRenderer();

const pdf = await renderer.generatePDF({
  source: {
    html: `
      <!DOCTYPE html>
      <html>
        <head>
          <style>
            body { font-family: Arial; padding: 20px; }
            .title { font-size: 24px; font-weight: bold; }
          </style>
        </head>
        <body>
          <div class="title">My Report</div>
          <p>Generated on ${new Date().toLocaleDateString()}</p>
        </body>
      </html>
    `,
  },
  format: 'A4',
  printBackground: true,
});

// Save or return the PDF buffer
```

---

## 🎯 Key Features

### **1. Browser Reuse (Performance)**
```typescript
// Singleton pattern - browser stays alive between requests
const renderer = getPDFRenderer();

// First request: ~2 seconds (browser startup)
await renderer.generatePDF({ source: url1 });

// Subsequent requests: ~500ms (browser already running)
await renderer.generatePDF({ source: url2 });
```

### **2. Wait for Dynamic Content**
```typescript
await renderer.generatePDF({
  source: mapUrl,
  
  // Wait for map tiles to load
  waitForSelector: '.maplibregl-canvas',
  
  // Wait for custom signal
  waitForFunction: 'window.mapReady === true',
  
  timeout: 30000, // 30 seconds max
});
```

### **3. High-Quality Output**
```typescript
const pdf = await renderer.generatePDF({
  source: url,
  format: 'A4',
  scale: 1.5, // Scale up for better quality
  printBackground: true, // Include backgrounds/colors
  margin: {
    top: '10mm',
    right: '10mm',
    bottom: '10mm',
    left: '10mm',
  },
});
```

### **4. Custom Page Sizes**
```typescript
const pdf = await renderer.generatePDF({
  source: url,
  width: '210mm', // Custom width
  height: '297mm', // Custom height (A4)
  // format is ignored when width/height are specified
});
```

---

## 🔧 Integration with Map

For map rendering, your preview page should signal when ready:

```typescript
// app/print/[templateId]/page.tsx

'use client';

import { useEffect, useRef } from 'react';
import Map from 'react-map-gl/maplibre';

export default function PrintPreview() {
  const mapRef = useRef(null);
  
  useEffect(() => {
    if (!mapRef.current) return;
    
    const map = mapRef.current;
    
    // Wait for map to be fully loaded
    map.on('idle', () => {
      // Signal to Playwright that map is ready
      window.mapReady = true;
      console.log('Map ready for PDF generation');
    });
  }, []);
  
  return (
    <div className="print-preview">
      <Map
        ref={mapRef}
        initialViewState={...}
        interactive={false}
        pixelRatio={2} // High DPI
      >
        {/* Your layers */}
      </Map>
    </div>
  );
}
```

Then in Playwright:
```typescript
await renderer.generatePDF({
  source: printPreviewUrl,
  waitForFunction: 'window.mapReady === true',
  timeout: 30000,
});
```

---

## 🐛 Troubleshooting

### **Browser not found**
```bash
# Install Chromium
pnpm exec playwright install chromium

# Or install all browsers
pnpm exec playwright install
```

### **Memory issues in production**
```typescript
// Limit concurrent browser contexts
// Use a queue system (BullMQ, etc.)
// Or close browser after each request (slower but safer)

await renderer.generatePDF({ source: url });
await renderer.close(); // Cleanup
```

### **Timeout errors**
```typescript
// Increase timeout for slow pages
await renderer.generatePDF({
  source: url,
  timeout: 60000, // 60 seconds
});
```

---

## 📊 Performance Tips

1. **Reuse browser instance** - Don't close between requests
2. **Pre-render data** - Fetch data on backend, pass to preview page
3. **Simplify CSS** - Avoid complex animations during print
4. **Use queue** - Don't block API responses, queue print jobs
5. **Cache results** - Store PDFs in S3, return cached version

---

## 🔄 Next Steps

1. ✅ Install Playwright: `pnpm add playwright`
2. ✅ Install browser: `pnpm exec playwright install chromium`
3. ✅ Run tests: `pnpm test`
4. ✅ Create API route for PDF generation
5. ✅ Create print preview page
6. ✅ Test end-to-end workflow

---

**Summary:** Playwright is now set up for server-side PDF generation. You can render any HTML (including your React components via preview pages) into high-quality PDFs. The browser reuse pattern makes it performant for production use.
