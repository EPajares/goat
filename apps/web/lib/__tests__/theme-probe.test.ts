import { alpha, createTheme } from "@mui/material/styles";
import { expect, it } from "vitest";

import { createAppTheme } from "@p4b/ui/theme/ThemeProvider";

it.each(["light", "dark"] as const)("createAppTheme %s builds", (mode) => {
  const t = createAppTheme({ mode, locale: "en" });
  expect(t.palette.mode).toBe(mode);
});

// MUI ≥5.15.13 requires every palette value to be a valid CSS color: components
// like Switch iterate palette entries and feed them through decomposeColor
// (mui/material-ui#41939). A bare "R, G, B" triplet in the palette crashes at
// render, so customColors.main must stay a parseable color in both modes.
it.each(["light", "dark"] as const)("%s palette customColors.main is a parseable color", (mode) => {
  const t = createAppTheme({ mode, locale: "en" });
  const main = (t.palette as unknown as { customColors: { main: string } }).customColors.main;
  expect(() => alpha(main, 0.5)).not.toThrow();
});

it("branded second createTheme pass does not throw", () => {
  const base = createAppTheme({ mode: "dark", locale: "en" });
  const augmented = base.palette.augmentColor({ color: { main: "#ff0000" } });
  const t2 = createTheme(base, { palette: { primary: augmented } });
  expect(t2.palette.primary.main).toBe("#ff0000");
});
