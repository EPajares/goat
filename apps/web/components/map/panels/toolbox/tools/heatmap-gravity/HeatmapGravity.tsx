import { useParams } from "next/navigation";
import { useMemo, useState } from "react";

import { useTranslation } from "@/i18n/client";

import { computeHeatmapGravity } from "@/lib/api/tools";
import type { LayerFieldType } from "@/lib/validations/layer";
import { heatmapGravitySchema, heatmapImpedanceFunctionEnum } from "@/lib/validations/tools";

import type { SelectorItem } from "@/types/map/common";
import type { IndicatorBaseProps } from "@/types/map/toolbox";

import { useFilteredProjectLayers } from "@/hooks/map/LayerPanelHooks";

import Selector from "@/components/map/panels/common/Selector";
import HeatmapContainer from "@/components/map/panels/toolbox/common/HeatmapContainer";
import HeatmapOpportunitiesSelector from "@/components/map/panels/toolbox/common/HeatmapOpportunitiesSelector";

type Opportunity = {
  layer: SelectorItem | undefined;
  maxTravelTime: SelectorItem | undefined;
  sensitivity: number | undefined;
  destinationPotentialColumn: LayerFieldType | undefined;
};

const HeatmapGravity = ({ onBack, onClose }: IndicatorBaseProps) => {
  const { t } = useTranslation("common");
  const { projectId } = useParams();
  const { layers } = useFilteredProjectLayers(projectId as string);
  const defaultImpedanceFunction = {
    value: heatmapImpedanceFunctionEnum.Enum.gaussian,
    label: t(heatmapImpedanceFunctionEnum.Enum.gaussian),
  };
  const [impedanceFunction, setImpedanceFunction] = useState<SelectorItem | undefined>(
    defaultImpedanceFunction
  );

  const impedanceFunctions = useMemo(() => {
    return heatmapImpedanceFunctionEnum.options.map((value) => {
      return {
        value: value,
        label: t(value),
      } as SelectorItem;
    });
  }, [t]);

  const defaultOpportunities = [
    {
      layer: undefined,
      maxTravelTime: {
        value: 20,
        label: "20 (Min)",
      },
      sensitivity: 300000,
      destinationPotentialColumn: undefined,
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

  const isValid = useMemo(() => {
    return (
      impedanceFunction !== undefined &&
      opportunities.every((opportunity) => {
        return opportunity.layer !== undefined && opportunity.maxTravelTime !== undefined;
      })
    );
  }, [impedanceFunction, opportunities]);

  const handleRun = () => {
    const payload = {
      impedance_function: impedanceFunction?.value,
      opportunities: opportunities.map((opportunity) => {
        return {
          opportunity_layer_project_id:
            layers && layers.find((layer) => layer.id === opportunity.layer?.value)?.id,
          max_traveltime: opportunity.maxTravelTime?.value,
          sensitivity: opportunity.sensitivity,
          destination_potential_column: opportunity.destinationPotentialColumn?.name,
        };
      }),
    };

    return {
      schema: heatmapGravitySchema,
      payload,
      apiCall: computeHeatmapGravity,
      type: "heatmap_gravity",
    };
  };

  const handleReset = () => {
    setImpedanceFunction(defaultImpedanceFunction);
    setOpportunities(defaultOpportunities);
  };

  return (
    <HeatmapContainer
      type="gravity"
      title={t("heatmap_gravity")}
      description={t("heatmap_gravity_description")}
      docsPath="/toolbox/accessibility_indicators/gravity"
      onBack={onBack}
      onClose={onClose}
      handleReset={handleReset}
      handleRun={handleRun}
      isOpportunitiesValid={isValid}
      currentNumberOfFeatures={numberOfSelectedOpportunityFeatures}
      configChildren={
        <>
          <Selector
            selectedItems={impedanceFunction}
            setSelectedItems={(item: SelectorItem[] | SelectorItem | undefined) => {
              setImpedanceFunction(item as SelectorItem);
            }}
            items={impedanceFunctions}
            label={t("impedance_function")}
            tooltip={t("impedance_function_tooltip")}
          />
        </>
      }
      opportunitiesChildren={
        <>
          <HeatmapOpportunitiesSelector
            opportunities={opportunities}
            setOpportunities={setOpportunities}
            heatmapType="gravity"
          />
        </>
      }
    />
  );
};

export default HeatmapGravity;
