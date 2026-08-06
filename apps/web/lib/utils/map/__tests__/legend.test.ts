import { describe, expect, it } from "vitest";

import { resolveFeatureMarker } from "@/lib/utils/map/legend";

const baseMarker = { name: "base-sign", url: "https://assets/base.svg", source: "custom" };
const availableMarker = { name: "avail", url: "https://assets/avail.svg", source: "custom" };
const busyMarker = { name: "busy", url: "https://assets/busy.svg", source: "library" };

const mappedProps = {
  custom_marker: true,
  marker: baseMarker,
  marker_field: { name: "display_status" },
  marker_mapping: [
    [["AVAILABLE"], availableMarker],
    [["OCCUPIED", "CHARGING"], busyMarker],
  ],
};

describe("resolveFeatureMarker", () => {
  it("returns undefined when custom_marker is off", () => {
    expect(resolveFeatureMarker({ marker: baseMarker })).toBeUndefined();
  });

  it("returns the static marker when no marker_field is set", () => {
    expect(resolveFeatureMarker({ custom_marker: true, marker: baseMarker })).toEqual({
      url: "https://assets/base.svg",
      source: "custom",
    });
  });

  it("resolves the mapped marker for the feature's value", () => {
    expect(resolveFeatureMarker(mappedProps, { display_status: "AVAILABLE" })).toEqual({
      url: "https://assets/avail.svg",
      source: "custom",
    });
  });

  it("matches any value of a multi-value mapping row", () => {
    expect(resolveFeatureMarker(mappedProps, { display_status: "CHARGING" })).toEqual({
      url: "https://assets/busy.svg",
      source: "library",
    });
  });

  it("coerces non-string feature values like the map's to-string match", () => {
    const props = {
      ...mappedProps,
      marker_mapping: [[["42"], availableMarker]],
    };
    expect(resolveFeatureMarker(props, { display_status: 42 })).toEqual({
      url: "https://assets/avail.svg",
      source: "custom",
    });
  });

  it("falls back to the base marker for unmapped values, mirroring the match default", () => {
    expect(resolveFeatureMarker(mappedProps, { display_status: "OUT_OF_ORDER" })).toEqual({
      url: "https://assets/base.svg",
      source: "custom",
    });
  });

  it("falls back to the base marker when no feature properties are given", () => {
    expect(resolveFeatureMarker(mappedProps)).toEqual({
      url: "https://assets/base.svg",
      source: "custom",
    });
  });

  it("returns undefined for unmapped values when there is no base marker", () => {
    const props = { ...mappedProps, marker: { name: "", url: "", source: "custom" } };
    expect(resolveFeatureMarker(props, { display_status: "OUT_OF_ORDER" })).toBeUndefined();
  });

  it("defaults the marker source to library when unset", () => {
    const props = {
      custom_marker: true,
      marker: { name: "bus", url: "https://assets/bus.svg" },
    };
    expect(resolveFeatureMarker(props)).toEqual({
      url: "https://assets/bus.svg",
      source: "library",
    });
  });
});
