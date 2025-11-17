import type { DeepPartial } from "keycloakify/tools/DeepPartial";

import KcApp from "./KcApp";
import { getKcContext, type KcContext } from "./kcContext";
import { useDarkMode } from "storybook-dark-mode";
import { useEffect, useState } from "react";

export function createPageStory<PageId extends KcContext["pageId"]>(params: {
  pageId: PageId;
}) {
  const { pageId } = params;

  function PageStory(params: {
    kcContext?: DeepPartial<Extract<KcContext, { pageId: PageId }>>;
  }) {
    const { kcContext } = getKcContext({
      mockPageId: pageId,
      storyPartialKcContext: params.kcContext,
    });
    const dark = useDarkMode();
    const [key, setKey] = useState(0);
    useEffect(() => {
      const url = new URL(window.location.href);
      const params = new URLSearchParams(url.search);
      params.set("theme", dark ? "dark" : "light");
      url.search = params.toString();
      window.history.replaceState(null, "", url.toString());
      setTimeout(() => {
        setKey((prev) => prev + 1);
      }, 100);
    }, [dark]);
    return <KcApp key={key} kcContext={kcContext} />;
  }

  return { PageStory };
}
