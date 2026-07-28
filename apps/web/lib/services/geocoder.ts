/* eslint-disable @typescript-eslint/no-explicit-any */
import type { Feature } from "@/types/map/controllers";

const GEOCODER_ENDPOINT = "https://api.mapbox.com";
const GEOCODER_SOURCE = "mapbox.places";

interface GeocodeUrlParams {
  accessToken: string;
  proximity?: { longitude: number; latitude: number };
  bbox?: number[];
  types?: string;
  country?: string;
  limit?: number;
  autocomplete?: boolean;
  language?: string;
}

function buildGeocodeUrl(endpoint: string, source: string, query: string, params: GeocodeUrlParams) {
  const baseUrl = `${endpoint}/geocoding/v5/${source}/${encodeURIComponent(query)}.json`;
  const searchParams = {
    ...(isNotNil(params.accessToken) && { access_token: params.accessToken }),
    ...(isNotNil(params.proximity) && {
      proximity:
        params.proximity && Object.keys(params.proximity).length === 2
          ? `${params.proximity.longitude},${params.proximity.latitude}`
          : null,
    }),
    ...(isNotNil(params.bbox) && {
      bbox: params.bbox && params.bbox.length > 0 ? params.bbox.join(",") : null,
    }),
    ...(isNotNil(params.types) && {
      types: params.types,
    }),
    ...(isNotNil(params.country) && {
      country: params.country,
    }),
    ...(isNotNil(params.limit) && {
      limit: params.limit,
    }),
    ...(isNotNil(params.autocomplete) && {
      autocomplete: params.autocomplete,
    }),
    ...(isNotNil(params.language) && {
      language: params.language,
    }),
  };
  return `${baseUrl}?${toUrlString(searchParams)}`;
}

export async function searchPlaces(
  query: string,
  opts: {
    accessToken: string;
    proximity?: { longitude: number; latitude: number };
    bbox?: number[];
    language?: string;
    limit?: number;
    signal?: AbortSignal;
  }
): Promise<Feature[]> {
  const url = buildGeocodeUrl(GEOCODER_ENDPOINT, GEOCODER_SOURCE, query, opts);
  const res = await fetch(url, { signal: opts.signal });
  if (!res.ok) throw new Error(`Geocoding failed: ${res.status}`);
  const data = await res.json();
  return data?.features ?? [];
}

function toUrlString(params: any) {
  return Object.keys(params)
    .map((key) => encodeURIComponent(key) + "=" + encodeURIComponent(params[key]))
    .join("&");
}

function isNotNil(value: unknown) {
  return value !== undefined && value !== null;
}
