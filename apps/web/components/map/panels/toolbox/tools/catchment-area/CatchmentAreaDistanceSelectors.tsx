import { Stack } from "@mui/material";
import React from "react";

import type { SelectorItem } from "@/types/map/common";

import FormLabelHelper from "@/components/common/FormLabelHelper";
import Selector from "@/components/map/panels/common/Selector";
import SliderInput from "@/components/map/panels/common/SliderInput";
import { getTravelCostConfigValues } from "@/components/map/panels/toolbox/tools/catchment-area/utils";

type CatchmentAreaDistanceSelectorsProps = {
  distance: number | undefined;
  setDistance: (value: number) => void;
  steps: SelectorItem | undefined;
  setSteps: (item: SelectorItem) => void;
  t: (key: string) => string;
};

const CatchmentAreaDistanceSelectors: React.FC<CatchmentAreaDistanceSelectorsProps> = ({
  distance,
  setDistance,
  t,
  steps,
  setSteps,
}) => {
  return (
    <Stack spacing={2}>
      <Stack>
        <FormLabelHelper label={`${t("travel_time_distance")} (Meter)`} color="inherit" />
        <SliderInput
          value={distance || 500}
          min={50}
          max={5000}
          onChange={(value) => setDistance(value as number)}
          isRange={false}
          step={50}
          rootSx={{
            pl: 3,
            pr: 2,
          }}
        />
      </Stack>

      <Selector
        selectedItems={steps}
        setSelectedItems={(item: SelectorItem[] | SelectorItem | undefined) => {
          setSteps(item as SelectorItem);
        }}
        items={getTravelCostConfigValues(1, 9)}
        label={t("travel_time_step") + " (Steps)"}
        tooltip={t("travel_time_step_tooltip")}
      />
    </Stack>
  );
};

export default CatchmentAreaDistanceSelectors;
