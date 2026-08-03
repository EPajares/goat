import { useCallback, useEffect, useRef, useState } from "react";

import { type LayerSearchGroup, searchLayerFeatures } from "@/lib/api/processes";
import { searchPlaces } from "@/lib/services/geocoder";

import type { Feature } from "@/types/map/controllers";

const DEBOUNCE_MS = 400;
const MIN_CHARS = 2;
/** Matches the `layer-search` process input limit. */
const MAX_CHARS = 100;

export type SearchSource =
  | { mode: "public"; projectId: string; placesEnabled: boolean; hasLayers: boolean }
  | {
      mode: "editor";
      placesEnabled: true;
      layers: { layer_id: string; columns: string[]; label_column?: string }[];
    };

export function useUnifiedSearch(options: {
  source: SearchSource;
  accessToken: string;
  getMapCenter: () => { lng: number; lat: number } | undefined;
  bbox?: number[];
  language?: string;
}) {
  const { source, accessToken, getMapCenter, bbox, language } = options;
  const [query, setQuery] = useState("");
  const [places, setPlaces] = useState<Feature[]>([]);
  const [layerGroups, setLayerGroups] = useState<LayerSearchGroup[]>([]);
  const [placesLoading, setPlacesLoading] = useState(false);
  const [layersLoading, setLayersLoading] = useState(false);
  // True from a (valid) keystroke until its debounced requests fire, so
  // consumers can tell "not searched yet" apart from "searched, no results".
  const [debouncePending, setDebouncePending] = useState(false);
  const abortRef = useRef<AbortController | undefined>(undefined);
  const seqRef = useRef(0);
  const paramsRef = useRef({ source, accessToken, getMapCenter, bbox, language });
  paramsRef.current = { source, accessToken, getMapCenter, bbox, language };
  // Stable signature of the search scope: re-runs the current query when the
  // scope changes (e.g. the editor's layer columns arrive after the first
  // debounced request already fired).
  const sourceKey =
    source.mode === "editor"
      ? `editor:${source.layers.map((layer) => layer.layer_id).join(",")}`
      : `public:${source.projectId}:${source.hasLayers}:${source.placesEnabled}`;
  // The exact string the requests are built from. Keying the debounce effect on
  // this (instead of the raw `query`) makes edits that don't change it — e.g. a
  // trailing space, or typing past the 100-char cap — a no-op rather than a
  // full re-fetch of a byte-identical query.
  const trimmedQuery = query.trim().slice(0, MAX_CHARS);

  const clear = useCallback(() => {
    abortRef.current?.abort();
    seqRef.current += 1;
    setQuery("");
    setPlaces([]);
    setLayerGroups([]);
    setPlacesLoading(false);
    setLayersLoading(false);
    setDebouncePending(false);
  }, []);

  useEffect(() => {
    if (trimmedQuery.length < MIN_CHARS) {
      abortRef.current?.abort();
      seqRef.current += 1;
      setPlaces([]);
      setLayerGroups([]);
      setDebouncePending(false);
      return;
    }
    setDebouncePending(true);
    const timer = setTimeout(() => {
      setDebouncePending(false);
      const seq = (seqRef.current += 1);
      const q = trimmedQuery;
      const params = paramsRef.current;
      abortRef.current?.abort();
      const controller = new AbortController();
      abortRef.current = controller;
      const center = params.getMapCenter();

      if (params.source.placesEnabled && params.accessToken) {
        setPlacesLoading(true);
        searchPlaces(q, {
          accessToken: params.accessToken,
          proximity: center ? { longitude: center.lng, latitude: center.lat } : undefined,
          bbox: params.bbox,
          language: params.language,
          signal: controller.signal,
        })
          .then((features) => {
            if (seqRef.current === seq) setPlaces(features);
          })
          .catch((err) => {
            if (seqRef.current === seq && (err as Error)?.name !== "AbortError") {
              setPlaces([]);
            }
          })
          .finally(() => {
            if (seqRef.current === seq) setPlacesLoading(false);
          });
      } else {
        setPlaces([]);
      }

      const wantsLayers =
        params.source.mode === "public" ? params.source.hasLayers : params.source.layers.length > 0;
      if (wantsLayers) {
        setLayersLoading(true);
        searchLayerFeatures(
          {
            query: q,
            ...(center && { map_center: [center.lng, center.lat] as [number, number] }),
            ...(params.source.mode === "public"
              ? { project_id: params.source.projectId }
              : { layers: params.source.layers }),
          },
          controller.signal
        )
          .then((output) => {
            if (seqRef.current === seq) setLayerGroups(output.groups);
          })
          .catch((err) => {
            if (seqRef.current === seq && (err as Error)?.name !== "AbortError") {
              console.warn("layer search unavailable:", err);
              setLayerGroups([]);
            }
          })
          .finally(() => {
            if (seqRef.current === seq) setLayersLoading(false);
          });
      } else {
        setLayerGroups([]);
      }
    }, DEBOUNCE_MS);
    return () => clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [trimmedQuery, sourceKey]);

  useEffect(() => {
    return () => {
      seqRef.current += 1;
      abortRef.current?.abort();
    };
  }, []);

  return {
    query,
    setQuery,
    places,
    layerGroups,
    placesLoading,
    layersLoading,
    searching: debouncePending || placesLoading || layersLoading,
    clear,
  };
}
