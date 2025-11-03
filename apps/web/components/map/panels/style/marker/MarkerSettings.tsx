import { useMemo } from "react";

import { useTranslation } from "@/i18n/client";

import type { Layer } from "@/lib/validations/layer";
import { type FeatureLayerProperties } from "@/lib/validations/layer";
import type { ProjectLayer } from "@/lib/validations/project";

import type { SelectorItem } from "@/types/map/common";

import { useSymbolOptions } from "@/hooks/map/LayerDesignHooks";

import Selector from "@/components/map/panels/common/Selector";

const MarkerSettings = ({
  layer,
  onStyleChange,
}: {
  layer: ProjectLayer | Layer;
  onStyleChange?: (newStyle: FeatureLayerProperties) => void;
}) => {
  const { t } = useTranslation("common");
  const { anchorItems } = useSymbolOptions(layer);

  const selectedAnchor = useMemo(() => {
    const anchor = layer.properties?.["marker_anchor"];
    return anchorItems.find((item) => item.value === anchor) || anchorItems[0];
  }, [layer.properties, anchorItems]);

  return (
    <>
      <Selector
        selectedItems={selectedAnchor}
        setSelectedItems={(item: SelectorItem | undefined) => {
          const newStyle = JSON.parse(JSON.stringify(layer.properties)) || {};
          newStyle["marker_anchor"] = item?.value || "center";
          onStyleChange?.(newStyle);
        }}
        items={anchorItems}
        label={t("placement")}
        placeholder={t("select_marker_placement")}
      />
    </>
  );
};

export default MarkerSettings;
