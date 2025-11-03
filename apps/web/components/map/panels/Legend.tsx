import { useMemo } from "react";

import { useTranslation } from "@/i18n/client";

import { setActiveLeftPanel } from "@/lib/store/map/slice";
import type { ProjectLayer } from "@/lib/validations/project";

import { useAppDispatch, useAppSelector } from "@/hooks/store/ContextHooks";

import { Legend, LegendMapContainer } from "@/components/map/controls/Legend";
import Container from "@/components/map/panels/Container";

interface PanelProps {
  projectLayers?: ProjectLayer[];
  isFloating?: boolean;
  showAllLayers?: boolean;
  onVisibilityChange?: (layer: ProjectLayer) => void;
}

const LegendPanel = ({
  isFloating = false,
  showAllLayers = false,
  projectLayers = [],
  onVisibilityChange,
}: PanelProps) => {
  const { t } = useTranslation("common");
  const dispatch = useAppDispatch();
  const currentZoom = useAppSelector((state) => state.map.currentZoom);
  const _layers = useMemo(
    () =>
      showAllLayers
        ? projectLayers
        : projectLayers?.filter((layer) => {
            const minZoom = layer.properties?.min_zoom;
            const maxZoom = layer.properties?.max_zoom;
            const isVisible = layer.properties?.visibility;
            if (minZoom && maxZoom && currentZoom) {
              return currentZoom >= minZoom && currentZoom <= maxZoom && isVisible;
            }
            return isVisible;
          }),
    [projectLayers, showAllLayers, currentZoom]
  );
  return (
    <>
      {!isFloating && (
        <Container
          title={t("legend")}
          close={() => dispatch(setActiveLeftPanel(undefined))}
          direction="left"
          body={projectLayers && <Legend layers={_layers} hideZoomLevel />}
        />
      )}
      {isFloating && (
        <LegendMapContainer
          layers={_layers}
          enableActions={showAllLayers}
          hideZoomLevel
          onVisibilityChange={async (layer) => {
            onVisibilityChange?.(layer);
          }}
        />
      )}
    </>
  );
};

export default LegendPanel;
