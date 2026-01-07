import { describe, expect, it } from "vitest";

import { getPageDimensions, inchesToMm, mmToInches, mmToPx, pxToMm } from "../units";

describe("Print Unit Conversions", () => {
  describe("mmToPx", () => {
    it("should convert millimeters to pixels at default DPI (96)", () => {
      expect(mmToPx(25.4)).toBeCloseTo(96, 0); // 1 inch = 25.4mm = 96px
      expect(mmToPx(10)).toBeCloseTo(37.8, 1);
    });

    it("should convert millimeters to pixels at custom DPI", () => {
      expect(mmToPx(25.4, 300)).toBeCloseTo(300, 0); // 1 inch at 300 DPI
      expect(mmToPx(10, 300)).toBeCloseTo(118.11, 1);
    });

    it("should handle zero", () => {
      expect(mmToPx(0)).toBe(0);
    });
  });

  describe("pxToMm", () => {
    it("should convert pixels to millimeters at default DPI", () => {
      expect(pxToMm(96)).toBeCloseTo(25.4, 1); // 96px = 1 inch = 25.4mm
      expect(pxToMm(37.8)).toBeCloseTo(10, 0);
    });

    it("should convert pixels to millimeters at custom DPI", () => {
      expect(pxToMm(300, 300)).toBeCloseTo(25.4, 1);
    });

    it("should be inverse of mmToPx", () => {
      const original = 100;
      expect(pxToMm(mmToPx(original))).toBeCloseTo(original, 1);
    });
  });

  describe("inchesToMm and mmToInches", () => {
    it("should convert inches to millimeters", () => {
      expect(inchesToMm(1)).toBeCloseTo(25.4, 1);
      expect(inchesToMm(8.5)).toBeCloseTo(215.9, 1);
    });

    it("should convert millimeters to inches", () => {
      expect(mmToInches(25.4)).toBeCloseTo(1, 2);
      expect(mmToInches(297)).toBeCloseTo(11.69, 2); // A4 height
    });
  });

  describe("getPageDimensions", () => {
    it("should return correct dimensions for A4 portrait", () => {
      const dims = getPageDimensions("A4", "portrait");
      expect(dims.width).toBe(210);
      expect(dims.height).toBe(297);
    });

    it("should return correct dimensions for A4 landscape", () => {
      const dims = getPageDimensions("A4", "landscape");
      expect(dims.width).toBe(297);
      expect(dims.height).toBe(210);
    });

    it("should return correct dimensions for Letter portrait", () => {
      const dims = getPageDimensions("Letter", "portrait");
      expect(dims.width).toBeCloseTo(215.9, 1);
      expect(dims.height).toBeCloseTo(279.4, 1);
    });

    it("should handle all standard page sizes", () => {
      const sizes: Array<"A4" | "A3" | "Letter" | "Legal" | "Tabloid"> = [
        "A4",
        "A3",
        "Letter",
        "Legal",
        "Tabloid",
      ];

      sizes.forEach((size) => {
        const dims = getPageDimensions(size, "portrait");
        expect(dims.width).toBeGreaterThan(0);
        expect(dims.height).toBeGreaterThan(dims.width);
      });
    });
  });
});
