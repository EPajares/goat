import { describe, expect, it } from "vitest";

import { formatFieldValue } from "../formatFieldValue";

describe("formatFieldValue", () => {
  describe("string kind", () => {
    it("returns the value as-is", () => {
      expect(formatFieldValue("hello", "string", {})).toBe("hello");
    });
    it("renders null as empty string", () => {
      expect(formatFieldValue(null, "string", {})).toBe("");
    });
  });

  describe("datetime kind", () => {
    it("formats an ISO datetime to YYYY-MM-DD HH:mm by default", () => {
      expect(formatFieldValue("2024-06-15T14:30:00", "datetime", {})).toBe(
        "2024-06-15 14:30"
      );
    });
    it("formats a date-only value at midnight", () => {
      expect(formatFieldValue("2024-06-15", "datetime", {})).toBe(
        "2024-06-15 00:00"
      );
    });
    it("honors a custom format", () => {
      expect(
        formatFieldValue("2024-06-15T14:30:00", "datetime", { format: "DD.MM.YYYY" })
      ).toBe("15.06.2024");
    });
    it("returns the raw value when unparseable", () => {
      expect(formatFieldValue("not-a-date", "datetime", {})).toBe("not-a-date");
    });
    it("renders booleans as True/False", () => {
      expect(formatFieldValue(true, "boolean", {})).toBe("True");
      expect(formatFieldValue(false, "boolean", {})).toBe("False");
    });
    it("renders UTC instants in UTC, not the local timezone", () => {
      expect(formatFieldValue("2024-06-15T14:30:00.000000Z", "datetime", {})).toBe(
        "2024-06-15 14:30"
      );
      expect(formatFieldValue("2024-06-15T14:30:00+02:00", "datetime", {})).toBe(
        "2024-06-15 12:30"
      );
    });
  });

  describe("number kind", () => {
    it("uses auto decimals (2) by default", () => {
      expect(formatFieldValue(3.14159, "number", { decimals: "auto" })).toBe(
        "3.14"
      );
    });
    it("respects explicit decimals", () => {
      expect(formatFieldValue(3.14159, "number", { decimals: 4 })).toBe(
        "3.1416"
      );
    });
    it("inserts thousands separator when requested", () => {
      expect(
        formatFieldValue(1234567.89, "number", {
          decimals: 2,
          thousands_separator: true,
        })
      ).toBe("1,234,567.89");
    });
    it("abbreviates large numbers", () => {
      expect(formatFieldValue(1500000, "number", { abbreviate: true })).toBe(
        "1.5M"
      );
    });
    it("always shows sign when requested", () => {
      expect(formatFieldValue(42, "number", { always_show_sign: true })).toBe(
        "+42"
      );
      expect(formatFieldValue(-3, "number", { always_show_sign: true })).toBe(
        "-3"
      );
    });
  });

  describe("area kind", () => {
    it("auto-picks m² for medium values", () => {
      expect(formatFieldValue(1234, "area", { unit: "auto" })).toBe(
        "1234.00 m²"
      );
    });
    it("auto-picks ha for ≥10 000 m²", () => {
      expect(formatFieldValue(50000, "area", { unit: "auto" })).toBe("5.00 ha");
    });
    it("auto-picks km² for ≥1 000 000 m²", () => {
      expect(formatFieldValue(2_500_000, "area", { unit: "auto" })).toBe(
        "2.50 km²"
      );
    });
    it("respects explicit ha unit", () => {
      // 50 000 m² = 5 ha (1 ha = 10 000 m²)
      expect(
        formatFieldValue(50000, "area", { unit: "ha", decimals: 2 })
      ).toBe("5.00 ha");
    });
  });

  describe("length / perimeter kind", () => {
    it("auto-picks m for medium values", () => {
      expect(formatFieldValue(123, "length", { unit: "auto" })).toBe(
        "123.00 m"
      );
    });
    it("auto-picks km for ≥1000 m", () => {
      expect(formatFieldValue(2500, "length", { unit: "auto" })).toBe(
        "2.50 km"
      );
    });
    it("respects explicit km unit", () => {
      expect(
        formatFieldValue(2500, "perimeter", { unit: "km", decimals: 1 })
      ).toBe("2.5 km");
    });
  });
});
