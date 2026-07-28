import { act, renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { searchLayerFeatures } from "@/lib/api/processes";
import { searchPlaces } from "@/lib/services/geocoder";

import { type SearchSource, useUnifiedSearch } from "@/hooks/map/useUnifiedSearch";

vi.mock("@/lib/api/processes", () => ({ searchLayerFeatures: vi.fn() }));
vi.mock("@/lib/services/geocoder", () => ({ searchPlaces: vi.fn() }));

const source = { mode: "public", projectId: "p1", placesEnabled: true, hasLayers: true } as const;
const baseOpts = {
  source,
  accessToken: "tok",
  getMapCenter: () => ({ lng: 9.5, lat: 48.9 }),
};

describe("useUnifiedSearch", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.mocked(searchPlaces).mockResolvedValue([]);
    vi.mocked(searchLayerFeatures).mockResolvedValue({ groups: [] });
  });
  afterEach(() => {
    vi.useRealTimers();
    vi.clearAllMocks();
  });

  it("does not search under 2 characters", async () => {
    const { result } = renderHook(() => useUnifiedSearch(baseOpts));
    act(() => result.current.setQuery("m"));
    act(() => void vi.advanceTimersByTime(500));
    expect(searchLayerFeatures).not.toHaveBeenCalled();
    expect(searchPlaces).not.toHaveBeenCalled();
  });

  it("debounces and fires both sources with map center", async () => {
    const { result } = renderHook(() => useUnifiedSearch(baseOpts));
    act(() => result.current.setQuery("mu"));
    act(() => result.current.setQuery("mur"));
    act(() => void vi.advanceTimersByTime(399));
    expect(searchLayerFeatures).not.toHaveBeenCalled();
    act(() => void vi.advanceTimersByTime(1));
    expect(searchLayerFeatures).toHaveBeenCalledTimes(1);
    expect(searchLayerFeatures).toHaveBeenCalledWith(
      expect.objectContaining({ query: "mur", project_id: "p1", map_center: [9.5, 48.9] }),
      expect.any(AbortSignal)
    );
    expect(searchPlaces).toHaveBeenCalledTimes(1);
  });

  it("aborts the previous in-flight layer request on new input", async () => {
    const seenSignals: AbortSignal[] = [];
    vi.mocked(searchLayerFeatures).mockImplementation(async (_inputs, signal) => {
      if (signal) seenSignals.push(signal);
      return { groups: [] };
    });
    const { result } = renderHook(() => useUnifiedSearch(baseOpts));
    act(() => result.current.setQuery("murr"));
    act(() => void vi.advanceTimersByTime(400));
    act(() => result.current.setQuery("murrh"));
    act(() => void vi.advanceTimersByTime(400));
    expect(seenSignals).toHaveLength(2);
    expect(seenSignals[0].aborted).toBe(true);
    expect(seenSignals[1].aborted).toBe(false);
  });

  it("layer-search failure degrades silently to empty groups", async () => {
    vi.mocked(searchLayerFeatures).mockRejectedValue(new Error("429"));
    vi.mocked(searchPlaces).mockResolvedValue([{ id: "place.1" } as never]);
    const { result } = renderHook(() => useUnifiedSearch(baseOpts));
    act(() => result.current.setQuery("murr"));
    await act(async () => void (await vi.advanceTimersByTimeAsync(400)));
    expect(result.current.places).toHaveLength(1);
    expect(result.current.layerGroups).toEqual([]);
  });

  it("skips places when disabled", async () => {
    const { result } = renderHook(() =>
      useUnifiedSearch({ ...baseOpts, source: { ...source, placesEnabled: false } })
    );
    act(() => result.current.setQuery("murr"));
    await act(async () => void (await vi.advanceTimersByTimeAsync(400)));
    expect(searchPlaces).not.toHaveBeenCalled();
    expect(searchLayerFeatures).toHaveBeenCalled();
  });

  it("skips places when accessToken is empty", async () => {
    const { result } = renderHook(() => useUnifiedSearch({ ...baseOpts, accessToken: "" }));
    act(() => result.current.setQuery("murr"));
    await act(async () => void (await vi.advanceTimersByTimeAsync(400)));
    expect(searchPlaces).not.toHaveBeenCalled();
    expect(searchLayerFeatures).toHaveBeenCalled();
  });

  it("skips layer search in public mode when hasLayers is false", async () => {
    const { result } = renderHook(() =>
      useUnifiedSearch({ ...baseOpts, source: { ...source, hasLayers: false } })
    );
    act(() => result.current.setQuery("murr"));
    await act(async () => void (await vi.advanceTimersByTimeAsync(400)));
    expect(searchLayerFeatures).not.toHaveBeenCalled();
    expect(searchPlaces).toHaveBeenCalled();
  });

  it("skips layer search in editor mode when layers is empty", async () => {
    const editorSource: SearchSource = { mode: "editor", placesEnabled: true, layers: [] };
    const { result } = renderHook(() => useUnifiedSearch({ ...baseOpts, source: editorSource }));
    act(() => result.current.setQuery("murr"));
    await act(async () => void (await vi.advanceTimersByTimeAsync(400)));
    expect(searchLayerFeatures).not.toHaveBeenCalled();
    expect(searchPlaces).toHaveBeenCalled();
  });

  it("places-search failure degrades silently to empty places", async () => {
    vi.mocked(searchPlaces).mockRejectedValue(new Error("network"));
    const { result } = renderHook(() => useUnifiedSearch(baseOpts));
    act(() => result.current.setQuery("murr"));
    await act(async () => void (await vi.advanceTimersByTimeAsync(400)));
    expect(result.current.places).toEqual([]);
  });

  it("aborts the in-flight layer request on unmount", async () => {
    let capturedSignal: AbortSignal | undefined;
    vi.mocked(searchLayerFeatures).mockImplementation((_inputs, signal) => {
      capturedSignal = signal;
      return new Promise<never>(() => undefined);
    });
    const { result, unmount } = renderHook(() => useUnifiedSearch(baseOpts));
    act(() => result.current.setQuery("murr"));
    act(() => void vi.advanceTimersByTime(400));
    expect(capturedSignal?.aborted).toBe(false);
    unmount();
    expect(capturedSignal?.aborted).toBe(true);
  });

  it("uses the latest source across rerenders (no stale closure)", async () => {
    const emptyLayers: SearchSource = { mode: "editor", placesEnabled: true, layers: [] };
    const oneLayer: SearchSource = {
      mode: "editor",
      placesEnabled: true,
      layers: [{ layer_id: "l1", columns: ["name"] }],
    };
    const { result, rerender } = renderHook(
      ({ src }: { src: SearchSource }) => useUnifiedSearch({ ...baseOpts, source: src }),
      { initialProps: { src: emptyLayers } }
    );
    act(() => result.current.setQuery("murr"));
    rerender({ src: oneLayer });
    act(() => void vi.advanceTimersByTime(400));
    expect(searchLayerFeatures).toHaveBeenCalledWith(
      expect.objectContaining({ layers: oneLayer.layers }),
      expect.any(AbortSignal)
    );
  });

  it("re-fires the same query when editor layers arrive after the debounce", async () => {
    const emptyLayers: SearchSource = { mode: "editor", placesEnabled: true, layers: [] };
    const oneLayer: SearchSource = {
      mode: "editor",
      placesEnabled: true,
      layers: [{ layer_id: "l1", columns: ["name"] }],
    };
    const { result, rerender } = renderHook(
      ({ src }: { src: SearchSource }) => useUnifiedSearch({ ...baseOpts, source: src }),
      { initialProps: { src: emptyLayers } }
    );
    act(() => result.current.setQuery("murr"));
    act(() => void vi.advanceTimersByTime(400));
    expect(searchLayerFeatures).not.toHaveBeenCalled();
    rerender({ src: oneLayer });
    act(() => void vi.advanceTimersByTime(400));
    expect(searchLayerFeatures).toHaveBeenCalledTimes(1);
    expect(searchLayerFeatures).toHaveBeenCalledWith(
      expect.objectContaining({ query: "murr", layers: oneLayer.layers }),
      expect.any(AbortSignal)
    );
  });

  it("caps the query at 100 characters", async () => {
    const { result } = renderHook(() => useUnifiedSearch(baseOpts));
    act(() => result.current.setQuery("m".repeat(150)));
    act(() => void vi.advanceTimersByTime(400));
    expect(searchLayerFeatures).toHaveBeenCalledWith(
      expect.objectContaining({ query: "m".repeat(100) }),
      expect.any(AbortSignal)
    );
    expect(searchPlaces).toHaveBeenCalledWith("m".repeat(100), expect.anything());
  });

  it("does not re-fetch when an edit leaves the trimmed query unchanged", async () => {
    const { result } = renderHook(() => useUnifiedSearch(baseOpts));
    act(() => result.current.setQuery("murr"));
    await act(async () => void (await vi.advanceTimersByTimeAsync(400)));
    expect(searchLayerFeatures).toHaveBeenCalledTimes(1);
    expect(searchPlaces).toHaveBeenCalledTimes(1);

    act(() => result.current.setQuery("murr "));
    await act(async () => void (await vi.advanceTimersByTimeAsync(400)));
    expect(searchLayerFeatures).toHaveBeenCalledTimes(1);
    expect(searchPlaces).toHaveBeenCalledTimes(1);
    expect(result.current.searching).toBe(false);
  });

  it("reports searching from keystroke until the debounced requests settle", async () => {
    const { result } = renderHook(() => useUnifiedSearch(baseOpts));
    expect(result.current.searching).toBe(false);
    act(() => result.current.setQuery("murr"));
    expect(result.current.searching).toBe(true);
    await act(async () => void (await vi.advanceTimersByTimeAsync(400)));
    expect(result.current.searching).toBe(false);
    act(() => result.current.setQuery("m"));
    expect(result.current.searching).toBe(false);
  });

  it("clear() resets state and aborts an in-flight request", async () => {
    let capturedSignal: AbortSignal | undefined;
    vi.mocked(searchLayerFeatures).mockImplementation((_inputs, signal) => {
      capturedSignal = signal;
      return new Promise<never>(() => undefined);
    });
    const { result } = renderHook(() => useUnifiedSearch(baseOpts));
    act(() => result.current.setQuery("murr"));
    act(() => void vi.advanceTimersByTime(400));
    act(() => result.current.clear());
    expect(result.current.query).toBe("");
    expect(result.current.places).toEqual([]);
    expect(result.current.layerGroups).toEqual([]);
    expect(capturedSignal?.aborted).toBe(true);
  });
});
