import type { Metadata } from "next";
import React from "react";

import "./print.css";

export const metadata: Metadata = {
  title: "Print Report",
  robots: "noindex, nofollow", // Don't index print pages
};

/**
 * Minimal layout for print pages - no navigation, headers, or other UI chrome.
 * This ensures Playwright captures only the report content.
 */
export default function PrintLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
