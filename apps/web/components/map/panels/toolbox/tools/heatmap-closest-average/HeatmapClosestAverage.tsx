import { useParams } from "next/navigation";
import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";

import { computeHeatmapClosestAverage } from "@/lib/api/tools";
import { heatmapClosestAverageSchema } from "@/lib/validations/tools";

import type { IndicatorBaseProps } from "@/types/map/toolbox";

import { useFilteredProjectLayers } from "@/hooks/map/LayerPanelHooks";

import HeatmapContainer from "@/components/map/panels/toolbox/common/HeatmapContainer";
import type { Opportunity } from "@/components/map/panels/toolbox/common/HeatmapOpportunitiesSelector";
import HeatmapOpportunitiesSelector from "@/components/map/panels/toolbox/common/HeatmapOpportunitiesSelector";

const HeatmapClosestAverage = ({ onBack, onClose }: IndicatorBaseProps) => {
  const { t } = useTranslation("common");
  const { projectId } = useParams();
  const { layers } = useFilteredProjectLayers(projectId as string);

  const defaultOpportunities: Opportunity[] = [
    {
      layer: undefined,
      maxTravelTime: {
        value: 20,
        label: "20 (Min)",
      },
      numberOfDestinations: {
        value: 1,
        label: "1",
      },
    },
  ];
  const [opportunities, setOpportunities] = useState<Opportunity[]>(defaultOpportunities);
  const numberOfSelectedOpportunityFeatures = useMemo(() => {
    return opportunities.reduce((acc, opportunity) => {
      if (!opportunity.layer) return acc;
      const layer = layers?.find((layer) => layer.id === opportunity.layer?.value);
      return acc + (layer?.filtered_count || 0);
    }, 0);
  }, [opportunities, layers]);

  const handleReset = () => {
    setOpportunities(defaultOpportunities);
  };

  const handleRun = () => {
    const payload = {
      opportunities: opportunities.map((opportunity) => {
        return {
          opportunity_layer_project_id:
            layers && layers.find((layer) => layer.id === opportunity.layer?.value)?.id,
          max_traveltime: opportunity.maxTravelTime?.value,
          number_of_destinations: opportunity.numberOfDestinations?.value,
        };
      }),
    };

    return {
      schema: heatmapClosestAverageSchema,
      payload,
      apiCall: computeHeatmapClosestAverage,
      type: "heatmap_closest_average",
    };
  };

  const isValid = useMemo(() => {
    return opportunities.every((opportunity) => opportunity.layer !== undefined);
  }, [opportunities]);
  return (
    <HeatmapContainer
      type="closest_average"
      title={t("heatmap_closest_average")}
      description={t("heatmap_closest_average_description")}
      docsPath="/toolbox/accessibility_indicators/closest_average"
      onBack={onBack}
      onClose={onClose}
      handleReset={handleReset}
      handleRun={handleRun}
      isOpportunitiesValid={isValid}
      currentNumberOfFeatures={numberOfSelectedOpportunityFeatures}
      opportunitiesChildren={
        <HeatmapOpportunitiesSelector
          opportunities={opportunities}
          setOpportunities={setOpportunities}
          heatmapType="closest_average"
        />
      }
    />
  );
};

export default HeatmapClosestAverage;
