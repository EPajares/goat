import { useCallback, useMemo } from "react";

import type { Basemap } from "@/types/map/common";

import { useAppDispatch, useAppSelector } from "@/hooks/store/ContextHooks";
import { useTranslation } from "@/i18n/client";
import { setActiveBasemap as setActiveBasemapAction } from "@/lib/store/map/slice";

export const useBasemap = (project) => {
  const { t, i18n } = useTranslation("common");

  const basemaps = useAppSelector((state) => state.map.basemaps);
  const localBasemap = useAppSelector((state) => state.map.activeBasemap);
  const dispatch = useAppDispatch();

  const activeBasemap: Basemap = useMemo(() => {
    if (!project) {
      return basemaps[0];
    }
    if (localBasemap) {
      return localBasemap;
    }
    if (project.basemap?.startsWith("http")) {
      const obj = {
        url: project.basemap,
        value: "custom",
        title: "Custom",
        subtitle: "User defined basemap",
        thumbnail: basemaps[0].thumbnail,
      };

      return obj;
    } else {
      const found = basemaps.find((b) => b.value === project.basemap);
      if (found) {
        return found;
      }
    }
    return basemaps[0];
  }, [basemaps, localBasemap, project]);


  const translatedBaseMaps = useMemo(() => {
    return basemaps.map((basemap) => ({
      ...basemap,
      title: i18n.exists(`common:basemap_types.${basemap.value}.title`)
        ? t(`basemap_types.${basemap.value}.title`)
        : t(basemap.title),
      subtitle: i18n.exists(`common:basemap_types.${basemap.value}.subtitle`)
        ? t(`basemap_types.${basemap.value}.subtitle`)
        : t(basemap.subtitle),
    }));
  }, [basemaps, i18n, t]);

  const setActiveBasemap = useCallback((value: string) => {
    const found = basemaps.find((b) => b.value === value);
    if (found) {
      dispatch(setActiveBasemapAction(found));
    } else if (value.startsWith("http")) {
      const customBasemap = {
        url: value,
        value: "custom",
        title: "Custom",
        subtitle: "User defined basemap",
        thumbnail: basemaps[0].thumbnail,
      }
      dispatch(setActiveBasemapAction(customBasemap));
    }
  }, [basemaps, dispatch]);

  return {
    basemaps,
    translatedBaseMaps,
    activeBasemap,
    setActiveBasemap,
  };
};
