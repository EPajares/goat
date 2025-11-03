import { getSession } from "next-auth/react";

export const fetcher = async (params) => {
  let queryParams, url, payload;
  const urlSearchParams = new URLSearchParams();
  if (Array.isArray(params)) {
    url = params[0];
    queryParams = params[1];
    payload = params[2];
    if (queryParams) {
      for (const key in queryParams) {
        if (Array.isArray(queryParams[key])) {
          queryParams[key].forEach((value) => {
            urlSearchParams.append(key, value);
          });
        } else {
          urlSearchParams.append(key, queryParams[key]);
        }
      }
    }
  } else {
    url = params;
  }
  const urlWithParams = queryParams ? `${url}?${new URLSearchParams(queryParams)}` : url;
  const options = {};
  if (payload) {
    options["method"] = "POST";
    options["body"] = JSON.stringify(payload);
    options["headers"] = {
      "Content-Type": "application/json",
    };
  }
  const session = await getSession();

  if (session?.access_token) {
    if (!options["headers"]) {
      options["headers"] = {};
    }
    options["headers"]["Authorization"] = `Bearer ${session.access_token}`;
  }

  const res = await fetch(urlWithParams, options);
  // If the status code is not in the range 200-299,
  // we still try to parse and throw it.
  if (!res.ok) {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const error: any = new Error("An error occurred while fetching the data.");
    // Attach extra info to the error object.
    error.info = await res.json();
    error.status = res.status;
    throw error;
  }

  return res.json();
};

export const apiRequestAuth = async (url: string, options?: RequestInit): Promise<Response> => {
  const session = await getSession();
  if (session?.access_token) {
    if (!options) {
      options = {};
    }
    if (!options.headers) {
      options.headers = {};
    }
    options.headers["Authorization"] = `Bearer ${session.access_token}`;
  }
  return fetch(url, options);
};

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export const updateRessource = async (url: string, { arg }: { arg: any }) => {
  return fetch(url, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(arg),
  });
};
