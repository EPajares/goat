import { retrieveParamFromUrl, addParamToUrl, updateSearchBarUrl } from "powerhooks/tools/urlSearchParams";
import { capitalize } from "tsafe/capitalize";

export const { theme, addThemeToQueryParams } = (() => {
  const queryParamName = "theme";

  const value = (() => {
    const unparsedValue = read({ queryParamName });

    if (unparsedValue === undefined) {
      return undefined;
    }

    return unparsedValue;
  })();

  function addToUrlQueryParams(params: { url: string; value: string }): string {
    const { url, value } = params;

    return addParamToUrl({
      url,
      name: queryParamName,
      value: JSON.stringify(value),
    }).newUrl;
  }

  const out = {
    [queryParamName]: value,
    [`add${capitalize(queryParamName)}ToQueryParams` as const]: addToUrlQueryParams,
  } as const;

  return out;
})();


function read(params: { queryParamName: string }): string | undefined {
  // if (kcContext === undefined) {
  //   //NOTE: We do something only if we are really in Keycloak
  //   return undefined;
  // }

  const { queryParamName } = params;

  read_from_url: {
    const result = retrieveParamFromUrl({
      url: window.location.href,
      name: queryParamName,
    });

    if (!result.wasPresent) {
      break read_from_url;
    }

    const { newUrl, value: serializedValue } = result;

    updateSearchBarUrl(newUrl);

    localStorage.setItem(queryParamName, serializedValue);

    return serializedValue;
  }

  //Reading from local storage
  const serializedValue = localStorage.getItem(queryParamName) ?? undefined;

  return serializedValue;
}
