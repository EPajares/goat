import type { PaletteMode } from "@mui/material";
import type { ContentWidth } from "./types";

type ThemeConfig = {
  mode: PaletteMode;
  templateName: string;
  routingLoader: boolean;
  disableRipple: boolean;
  navigationSize: number;
  menuTextTruncate: boolean;
  contentWidth: ContentWidth;
  responsiveFontSizes: boolean;
};

const defaultThemeConfig: ThemeConfig = {
  // ** Layout Configs
  templateName: "GOAT",
  mode: "light",
  contentWidth: "boxed",
  // ** Routing Configs
  routingLoader: true,
  // ** Navigation (Menu) Configs
  menuTextTruncate: true,
  navigationSize: 260 /* Number in PX(Pixels) /*! Note: This is for Vertical navigation menu only */,
  // ** Other Configs
  responsiveFontSizes: true,
  disableRipple: false,
};

export default defaultThemeConfig;
