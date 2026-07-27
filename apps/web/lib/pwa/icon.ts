import sharp from "sharp";

// 48/96 serve favicons (Google requires a multiple of 48px square,
// otherwise it ignores the icon and falls back to /favicon.ico);
// 180/192/512 serve PWA / home-screen icons.
export const PWA_ICON_SIZES = [48, 96, 180, 192, 512] as const;
export type PwaIconSize = (typeof PWA_ICON_SIZES)[number];

export function isAllowedIconSize(size: number): size is PwaIconSize {
  return (PWA_ICON_SIZES as readonly number[]).includes(size);
}

export const ICON_SOURCES = ["app", "favicon"] as const;
export type IconSource = (typeof ICON_SOURCES)[number];

export function isIconSource(source: string): source is IconSource {
  return (ICON_SOURCES as readonly string[]).includes(source);
}

export interface IconSettings {
  app_icon_url?: string | null;
  favicon_url?: string | null;
}

// Sources deliberately never fall back to each other — small favicons
// make bad home-screen icons and vice versa. null means: use the GOAT logo.
export function resolveIconUrl(
  settings: IconSettings | null | undefined,
  source: IconSource
): string | null {
  const url = source === "favicon" ? settings?.favicon_url : settings?.app_icon_url;
  return url ? url : null;
}

export async function rasterizeToPng(source: Buffer, size: number): Promise<Buffer> {
  // density only affects vector input (SVG); it makes sharp render the
  // SVG large enough that the resize is a downscale, not a blurry upscale.
  return sharp(source, { density: 300 })
    .resize(size, size, {
      fit: "contain",
      background: { r: 0, g: 0, b: 0, alpha: 0 },
    })
    .png()
    .toBuffer();
}
