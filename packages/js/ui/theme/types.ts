import type { PaletteMode } from "@mui/material"

declare module '@mui/material/styles' {
    interface Palette {
      customColors: {
        main: string
        tableHeaderBg: string
        primaryGradient: string
      }
    }
    interface PaletteOptions {
      customColors?: {
        main?: string
        tableHeaderBg?: string
        primaryGradient?: string
      }
    }
  }

  export type ContentWidth = 'full' | 'boxed'

  export type ThemeColor = 'primary' | 'secondary' | 'error' | 'warning' | 'info' | 'success'

  export type Settings = {
    mode: PaletteMode
    themeColor?: ThemeColor
    locale?: string
  }
