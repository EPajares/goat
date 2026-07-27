import sharp from "sharp";
import { describe, expect, it } from "vitest";

import { isAllowedIconSize, isIconSource, rasterizeToPng, resolveIconUrl } from "@/lib/pwa/icon";

const SVG = Buffer.from(
  `<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100"><circle cx="50" cy="50" r="40" fill="#2BB381"/></svg>`
);

describe("isAllowedIconSize", () => {
  it("accepts 48, 96, 180, 192, 512", () => {
    expect(isAllowedIconSize(48)).toBe(true);
    expect(isAllowedIconSize(96)).toBe(true);
    expect(isAllowedIconSize(180)).toBe(true);
    expect(isAllowedIconSize(192)).toBe(true);
    expect(isAllowedIconSize(512)).toBe(true);
  });
  it("rejects other sizes", () => {
    expect(isAllowedIconSize(0)).toBe(false);
    expect(isAllowedIconSize(256)).toBe(false);
    expect(isAllowedIconSize(NaN)).toBe(false);
  });
});

describe("isIconSource", () => {
  it("accepts app and favicon", () => {
    expect(isIconSource("app")).toBe(true);
    expect(isIconSource("favicon")).toBe(true);
  });
  it("rejects anything else", () => {
    expect(isIconSource("")).toBe(false);
    expect(isIconSource("logo")).toBe(false);
  });
});

describe("resolveIconUrl", () => {
  it("returns the configured app icon for the app source", () => {
    expect(resolveIconUrl({ app_icon_url: "https://x.test/icon.svg" }, "app")).toBe(
      "https://x.test/icon.svg"
    );
  });
  it("returns the configured favicon for the favicon source", () => {
    expect(
      resolveIconUrl(
        { app_icon_url: "https://x.test/icon.svg", favicon_url: "https://x.test/fav.png" },
        "favicon"
      )
    ).toBe("https://x.test/fav.png");
  });
  it("never crosses sources (app icon is not a favicon fallback and vice versa)", () => {
    expect(resolveIconUrl({ favicon_url: "https://x.test/fav.png" }, "app")).toBeNull();
    expect(resolveIconUrl({ app_icon_url: "https://x.test/icon.svg" }, "favicon")).toBeNull();
  });
  it("returns null for absent/empty settings (GOAT fallback)", () => {
    expect(resolveIconUrl({ app_icon_url: "" }, "app")).toBeNull();
    expect(resolveIconUrl({}, "favicon")).toBeNull();
    expect(resolveIconUrl(undefined, "app")).toBeNull();
    expect(resolveIconUrl(null, "favicon")).toBeNull();
  });
});

describe("rasterizeToPng", () => {
  it("produces a square PNG of the requested size from SVG", async () => {
    const png = await rasterizeToPng(SVG, 192);
    const meta = await sharp(png).metadata();
    expect(meta.format).toBe("png");
    expect(meta.width).toBe(192);
    expect(meta.height).toBe(192);
  });
  it("throws on garbage input", async () => {
    await expect(rasterizeToPng(Buffer.from("not an image"), 192)).rejects.toThrow();
  });
});
