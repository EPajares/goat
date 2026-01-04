/**
 * PDF Renderer - Server-side PDF generation using Playwright
 * This runs in Node.js (API routes or backend service)
 */
import type { Browser, Page } from "playwright";
import { chromium } from "playwright";

export interface PDFGenerationOptions {
  /** Target URL or HTML content */
  source: string | { html: string };

  /** Page format (A4, Letter, etc.) */
  format?: "A4" | "A3" | "Letter" | "Legal" | "Tabloid";

  /** Custom dimensions in mm (overrides format) */
  width?: string;
  height?: string;

  /** Page margins */
  margin?: {
    top?: string;
    right?: string;
    bottom?: string;
    left?: string;
  };

  /** Print background colors/images */
  printBackground?: boolean;

  /** Wait for specific selector before generating PDF */
  waitForSelector?: string;

  /** Wait for custom function to return true */
  waitForFunction?: string;

  /** Maximum wait time in ms */
  timeout?: number;

  /** Scale factor for content */
  scale?: number;

  /** Display header/footer on every page */
  displayHeaderFooter?: boolean;
  headerTemplate?: string;
  footerTemplate?: string;
}

export interface ScreenshotOptions {
  /** Screenshot type */
  type?: "png" | "jpeg";

  /** Quality for JPEG (0-100) */
  quality?: number;

  /** Capture full page or just viewport */
  fullPage?: boolean;

  /** Clip to specific area */
  clip?: {
    x: number;
    y: number;
    width: number;
    height: number;
  };
}

/**
 * PDF Renderer class - Manages browser lifecycle
 */
export class PDFRenderer {
  private browser: Browser | null = null;

  /**
   * Initialize browser instance
   */
  async init(): Promise<void> {
    if (this.browser && this.browser.isConnected()) {
      return; // Already initialized
    }

    this.browser = await chromium.launch({
      headless: true,
      args: ["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage", "--disable-gpu"],
    });
  }

  /**
   * Generate PDF from URL or HTML content
   */
  async generatePDF(options: PDFGenerationOptions): Promise<Buffer> {
    await this.init();
    if (!this.browser) throw new Error("Browser not initialized");

    const context = await this.browser.newContext({
      viewport: { width: 1920, height: 1080 },
      deviceScaleFactor: 2, // High DPI
    });

    const page = await context.newPage();

    try {
      // Load content
      if (typeof options.source === "string") {
        // URL
        await page.goto(options.source, {
          waitUntil: "networkidle",
          timeout: options.timeout || 30000,
        });
      } else {
        // HTML content
        await page.setContent(options.source.html, {
          waitUntil: "networkidle",
          timeout: options.timeout || 30000,
        });
      }

      // Wait for specific conditions
      if (options.waitForSelector) {
        await page.waitForSelector(options.waitForSelector, {
          state: "visible",
          timeout: options.timeout || 30000,
        });
      }

      if (options.waitForFunction) {
        await page.waitForFunction(options.waitForFunction, {
          timeout: options.timeout || 30000,
        });
      }

      // Generate PDF
      const pdf = await page.pdf({
        format: options.format,
        width: options.width,
        height: options.height,
        margin: options.margin || {
          top: "10mm",
          right: "10mm",
          bottom: "10mm",
          left: "10mm",
        },
        printBackground: options.printBackground ?? true,
        scale: options.scale ?? 1,
        displayHeaderFooter: options.displayHeaderFooter ?? false,
        headerTemplate: options.headerTemplate,
        footerTemplate: options.footerTemplate,
        preferCSSPageSize: false,
      });

      return Buffer.from(pdf);
    } finally {
      await context.close();
    }
  }

  /**
   * Generate screenshot from URL or HTML content
   */
  async generateScreenshot(
    source: string | { html: string },
    options: ScreenshotOptions = {}
  ): Promise<Buffer> {
    await this.init();
    if (!this.browser) throw new Error("Browser not initialized");

    const context = await this.browser.newContext({
      viewport: { width: 1920, height: 1080 },
      deviceScaleFactor: 2,
    });

    const page = await context.newPage();

    try {
      // Load content
      if (typeof source === "string") {
        await page.goto(source, { waitUntil: "networkidle" });
      } else {
        await page.setContent(source.html, { waitUntil: "networkidle" });
      }

      const screenshot = await page.screenshot({
        type: options.type || "png",
        quality: options.quality,
        fullPage: options.fullPage ?? true,
        clip: options.clip,
      });

      return Buffer.from(screenshot);
    } finally {
      await context.close();
    }
  }

  /**
   * Execute custom function in page context
   * Useful for preparing content before PDF generation
   */
  async executeFunctionInPage<T>(
    source: string | { html: string },
    fn: (page: Page) => Promise<T>
  ): Promise<T> {
    await this.init();
    if (!this.browser) throw new Error("Browser not initialized");

    const context = await this.browser.newContext();
    const page = await context.newPage();

    try {
      if (typeof source === "string") {
        await page.goto(source, { waitUntil: "networkidle" });
      } else {
        await page.setContent(source.html, { waitUntil: "networkidle" });
      }

      return await fn(page);
    } finally {
      await context.close();
    }
  }

  /**
   * Close browser and cleanup
   */
  async close(): Promise<void> {
    if (this.browser) {
      await this.browser.close();
      this.browser = null;
    }
  }
}

/**
 * Singleton instance for reuse across requests
 */
let rendererInstance: PDFRenderer | null = null;

export function getPDFRenderer(): PDFRenderer {
  if (!rendererInstance) {
    rendererInstance = new PDFRenderer();
  }
  return rendererInstance;
}

/**
 * Cleanup function for graceful shutdown
 */
export async function cleanupPDFRenderer(): Promise<void> {
  if (rendererInstance) {
    await rendererInstance.close();
    rendererInstance = null;
  }
}
