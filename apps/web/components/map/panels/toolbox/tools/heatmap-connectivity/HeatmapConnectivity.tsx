import { useParams } from "next/navigation";
import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";

import { ICON_NAME } from "@p4b/ui/components/Icon";

import { computeHeatmapConnectivity } from "@/lib/api/tools";
import { heatmapConnectivitySchema } from "@/lib/validations/tools";

import type { SelectorItem } from "@/types/map/common";
import type { IndicatorBaseProps } from "@/types/map/toolbox";

import { useFilteredProjectLayers } from "@/hooks/map/LayerPanelHooks";
import { useLayerByGeomType } from "@/hooks/map/ToolsHooks";
import { useProjectLayerFeatureCount } from "@/hooks/map/useProjectLayerFeatureCount";

import Selector from "@/components/map/panels/common/Selector";
import HeatmapContainer from "@/components/map/panels/toolbox/common/HeatmapContainer";
import { getTravelCostConfigValues } from "@/components/map/panels/toolbox/tools/catchment-area/utils";

const HeatmapConnectivity = ({ onBack, onClose }: IndicatorBaseProps) => {
  const { t } = useTranslation("common");
  const { projectId } = useParams();
  const { layers: projectLayers } = useFilteredProjectLayers(projectId as string);
  const defaultMaxTravelTime = {
    value: 20,
    label: "20 (Min)",
  };
  const [maxTravelTime, setMaxTravelTime] = useState<SelectorItem | undefined>(defaultMaxTravelTime);
  const { filteredLayers } = useLayerByGeomType(["feature"], ["polygon"], projectId as string);
  const [referenceLayerItem, setReferenceLayerItem] = useState<SelectorItem | undefined>(undefined);

  const referenceLayer = useMemo(() => {
    return projectLayers?.find((layer) => layer.id === referenceLayerItem?.value);
  }, [projectLayers, referenceLayerItem?.value]);

  // Fetch reference layer feature count on-demand
  const { featureCount: referenceLayerFeatureCount } = useProjectLayerFeatureCount({
    projectLayer: referenceLayer,
  });

  const isValid = useMemo(() => {
    return maxTravelTime !== undefined && referenceLayerItem !== undefined;
  }, [maxTravelTime, referenceLayerItem]);

  const handleRun = () => {
    const payload = {
      reference_area_layer_project_id: referenceLayerItem?.value,
      max_traveltime: maxTravelTime?.value,
    };

    return {
      schema: heatmapConnectivitySchema,
      payload,
      apiCall: computeHeatmapConnectivity,
      type: "heatmap_connectivity",
    };
  };
  const handleReset = () => {
    setMaxTravelTime(defaultMaxTravelTime);
    setReferenceLayerItem(undefined);
  };

  return (
    <HeatmapContainer
      type="connectivity"
      title={t("heatmap_connectivity")}
      description={t("heatmap_connectivity_description")}
      docsPath="/toolbox/accessibility_indicators/connectivity"
      onBack={onBack}
      onClose={onClose}
      handleReset={handleReset}
      handleRun={handleRun}
      isConfigurationValid={isValid}
      disableScenario
      currentNumberOfFeatures={referenceLayerFeatureCount}
      configChildren={
        <>
          {/* MAX TRAVEL TIME */}
          <Selector
            selectedItems={maxTravelTime}
            setSelectedItems={(item: SelectorItem[] | SelectorItem | undefined) => {
              setMaxTravelTime(item as SelectorItem);
            }}
            items={getTravelCostConfigValues(3, 30, "min")}
            label={t("travel_time_limit") + " (Min)"}
            tooltip={t("travel_time_limit_tooltip")}
          />
          <Selector
            selectedItems={referenceLayerItem}
            setSelectedItems={(item: SelectorItem[] | SelectorItem | undefined) => {
              setReferenceLayerItem(item as SelectorItem);
            }}
            items={filteredLayers}
            emptyMessage={t("no_polygon_layer_found")}
            emptyMessageIcon={ICON_NAME.LAYERS}
            label={t("select_reference_layer")}
            placeholder={t("select_reference_layer_placeholder")}
            tooltip={t("select_reference_layer_tooltip")}
          />
        </>
      }
    />
  );
};

export default HeatmapConnectivity;
