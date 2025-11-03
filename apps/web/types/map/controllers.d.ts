export interface Result {
  feature: Feature;
  label: string;
}

export interface Feature {
  id: string;
  type: string;
  place_type: string[];
  relevance: number;
  properties: Properties;
  text: string;
  place_name: string;
  center: [number, number];
  geometry: Geometry;
  address: string;
  context: Context[];
  bbox?: [number, number, number, number];
}

export interface Context {
  id: string;
  text: string;
  wikidata?: string;
  short_code?: string;
}

export interface Geometry {
  type: string;
  coordinates: [number, number];
  interpolated: boolean;
}

export interface Properties {
  accuracy: string;
}
