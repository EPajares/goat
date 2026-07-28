import { useMemo } from "react";
import { useTranslation } from "react-i18next";

import type { PaletteMode } from "@mui/material";
import { createTheme, useTheme } from "@mui/material/styles";

import { createAppTheme } from "@p4b/ui/theme/ThemeProvider";

/** Converts a hex color like `#3A3541` to the `"R, G, B"` string used by the palette. */
function hexToRgb(hex: string): string | null {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
  if (!result) return null;
  return `${parseInt(result[1], 16)}, ${parseInt(result[2], 16)}, ${parseInt(result[3], 16)}`;
}

/**
 * Returns a MUI theme with brand overrides applied when set.
 *
 * - `primaryColor` overrides `palette.primary`. Active tab text is pinned to
 *   neutral so only the underline indicator picks up the brand color.
 * - `iconColor` overrides `palette.action.active` — icon buttons only.
 *   Does NOT touch `text.secondary` to keep captions/labels readable.
 * - `fontColor` replaces the base text RGB used to derive the full text and
 *   action palette: `text.{primary,secondary,disabled}`, all `action.*` tokens,
 *   and `divider`. If `iconColor` is also set it takes precedence over
 *   `action.active` regardless of `fontColor`.
 *
 *   NOTE: the shared typography.ts bakes explicit `color` values into every
 *   variant at base-theme creation time (hardcoded rgba strings). A nested
 *   ThemeProvider alone cannot change those values — we must override the
 *   `typography` section and the `MuiInputLabel` component override too.
 *
 * Falls back to the base theme when none are provided.
 */
export function useBrandedTheme(
  primaryColor: string | undefined,
  iconColor: string | undefined,
  fontColor: string | undefined,
  /**
   * Pins the palette mode instead of inheriting the surrounding theme. Public
   * dashboards pass "light": a published dashboard has to look the same for
   * every visitor, and the app theme otherwise carries the *viewer's* own
   * light/dark preference into someone else's branded dashboard.
   */
  forceMode?: PaletteMode,
) {
  const inheritedTheme = useTheme();
  const { i18n } = useTranslation("common");
  const locale = i18n?.language === "de" ? "de" : "en";
  const baseTheme = useMemo(
    () =>
      forceMode && forceMode !== inheritedTheme.palette.mode
        ? createAppTheme({ mode: forceMode, locale })
        : inheritedTheme,
    [forceMode, inheritedTheme, locale],
  );
  return useMemo(() => {
    if (!primaryColor && !iconColor && !fontColor) return baseTheme;

    const palette: Record<string, unknown> = {};
    const typography: Record<string, unknown> = {};

    if (primaryColor) {
      palette.primary = baseTheme.palette.augmentColor({ color: { main: primaryColor } });
    }

    if (fontColor) {
      const rgb = hexToRgb(fontColor);
      if (rgb) {
        const primary = `rgba(${rgb}, 0.87)`;
        const secondary = `rgba(${rgb}, 0.68)`;

        palette.text = {
          primary,
          secondary,
          disabled: `rgba(${rgb}, 0.38)`,
        };
        palette.divider = `rgba(${rgb}, 0.12)`;
        // Build full action palette from font color; iconColor overrides active below.
        palette.action = {
          active: `rgba(${rgb}, 0.70)`,
          hover: `rgba(${rgb}, 0.04)`,
          selected: `rgba(${rgb}, 0.08)`,
          disabled: `rgba(${rgb}, 0.30)`,
          disabledBackground: `rgba(${rgb}, 0.18)`,
          focus: `rgba(${rgb}, 0.12)`,
        };

        // The shared theme's typography.ts bakes explicit color values into every
        // variant using the base palette. Override them here so Typography inside
        // the dashboard picks up the new font color.
        for (const variant of ["h1", "h2", "h3", "h4", "h5", "h6", "subtitle1", "body1", "button"]) {
          typography[variant] = { color: primary };
        }
        for (const variant of ["subtitle2", "body2", "caption", "overline"]) {
          typography[variant] = { color: secondary };
        }
      }
    }

    // iconColor always wins over the font-color-derived action.active
    if (iconColor) {
      palette.action = {
        ...(palette.action as Record<string, unknown> ?? baseTheme.palette.action),
        active: iconColor,
      };
    }

    const components: Record<string, unknown> = {};
    if (primaryColor) {
      components.MuiTab = {
        styleOverrides: {
          textColorPrimary: {
            "&.Mui-selected": {
              color: baseTheme.palette.text.primary,
            },
          },
        },
      };
    }

    // The base theme's input override bakes InputLabel color as a hardcoded string.
    // Re-override it here so filter/selector labels also respect fontColor.
    if (fontColor && (palette.text as Record<string, string> | undefined)?.secondary) {
      const secondary = (palette.text as Record<string, string>).secondary;
      components.MuiInputLabel = {
        styleOverrides: {
          root: { color: secondary },
        },
      };
    }

    return createTheme(baseTheme, { palette, components, typography });
  }, [baseTheme, primaryColor, iconColor, fontColor]);
}
