import { isAuthDisabled } from "@/lib/utils/auth-flag";

export const KEYCLOAK_CLIENT_ID = process.env.NEXT_PUBLIC_KEYCLOAK_CLIENT_ID;
export const KEYCLOAK_ISSUER = process.env.NEXT_PUBLIC_KEYCLOAK_ISSUER;
export const GEOAPI_BASE_URL = process.env.NEXT_PUBLIC_GEOAPI_URL;
export const PROCESSES_BASE_URL = process.env.NEXT_PUBLIC_PROCESSES_URL;
export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL;
export const APP_URL = process.env.NEXT_PUBLIC_APP_URL;
export const AUTH_DISABLED = isAuthDisabled(process.env.NEXT_PUBLIC_AUTH);

export const DOCS_URL = "https://goat.plan4better.de/docs";
export const CONTACT_US_URL = "https://plan4better.de/contact";
export const WEBSITE_URL = "https://plan4better.de";
export const MAPBOX_TOKEN = process.env.NEXT_PUBLIC_MAPBOX_TOKEN ?? "";

export const MAPTILER_KEY = "tffQ1wAu9TKyVMHrc3o3";

export const ORG_DEFAULT_AVATAR = "https://assets.plan4better.de/img/no-org-thumb.jpg";

export const STREET_NETWORK_LAYER_ID = "903ecdca-b717-48db-bbce-0219e41439cf";
export const SYSTEM_LAYERS_IDS = [STREET_NETWORK_LAYER_ID];

export const GEOFENCE_LAYERS_PATH = "https://assets.plan4better.de/other/geofence";
export const DEFAULT_WKT_EXTENT = "POLYGON((-180 -90, -180 90, 180 90, 180 -90, -180 -90))";

export const ASSETS_URL = "https://assets.plan4better.de";

export const MAX_EDITABLE_LAYER_SIZE = 100 * 1024 * 1024; // 100MB

export const THEME_COOKIE_NAME = "client_theme";
export const LANGUAGE_COOKIE_NAME = "client_language";
