import { Stack } from "@mui/material";
import React from "react";

import type { CatchmentAreaRoutingType } from "@/lib/validations/tools";
import { CatchmentAreaRoutingTypeEnum } from "@/lib/validations/tools";

import type { SelectorItem } from "@/types/map/common";

import Selector from "@/components/map/panels/common/Selector";
import PTTimeSelectors from "@/components/map/panels/toolbox/common/PTTimeSelectors";
import { getTravelCostConfigValues } from "@/components/map/panels/toolbox/tools/catchment-area/utils";

type CatchmentAreaTimeSelectorsProps = {
  routingType: CatchmentAreaRoutingType;
  maxTravelTime: SelectorItem | undefined;
  setMaxTravelTime: (item: SelectorItem) => void;
  speed: SelectorItem | undefined;
  setSpeed: (item: SelectorItem) => void;
  steps: SelectorItem | undefined;
  setSteps: (item: SelectorItem) => void;
  areStepsValid: boolean;
  ptStartTime: number | undefined;
  setPTStartTime: (value: number) => void;
  ptEndTime: number | undefined;
  setPTEndTime: (value: number) => void;
  ptDays: SelectorItem[];
  ptDay: SelectorItem | undefined;
  setPTDay: (item: SelectorItem) => void;
  isPTValid: boolean;
  t: (key: string) => string;
};

const CatchmentAreaTimeSelectors: React.FC<CatchmentAreaTimeSelectorsProps> = ({
  routingType,
  maxTravelTime,
  setMaxTravelTime,
  speed,
  setSpeed,
  steps,
  setSteps,
  areStepsValid,
  ptStartTime,
  setPTStartTime,
  ptEndTime,
  setPTEndTime,
  ptDays,
  ptDay,
  setPTDay,
  isPTValid,
  t,
}) => {
  //TODO: move the max travel time value out of the component
  const maxTravelTimeValue =
    routingType === CatchmentAreaRoutingTypeEnum.Enum.pt ||
    routingType === CatchmentAreaRoutingTypeEnum.Enum.car
      ? 90
      : 45;
  return (
    <Stack spacing={2}>
      <Selector
        selectedItems={maxTravelTime}
        setSelectedItems={(item: SelectorItem[] | SelectorItem | undefined) => {
          setMaxTravelTime(item as SelectorItem);
        }}
        items={getTravelCostConfigValues(3, maxTravelTimeValue, "min")}
        label={t("travel_time_limit") + " (Min)"}
        tooltip={t("travel_time_limit_tooltip")}
      />

      {routingType &&
        routingType !== CatchmentAreaRoutingTypeEnum.Enum.pt &&
        routingType !== CatchmentAreaRoutingTypeEnum.Enum.car && (
          <Selector
            selectedItems={speed}
            setSelectedItems={(item: SelectorItem[] | SelectorItem | undefined) => {
              setSpeed(item as SelectorItem);
            }}
            items={getTravelCostConfigValues(1, 25, "Km/h")}
            label={t("travel_time_speed") + " (Km/h)"}
            tooltip={t("travel_time_speed_tooltip")}
          />
        )}

      <Selector
        selectedItems={steps}
        setSelectedItems={(item: SelectorItem[] | SelectorItem | undefined) => {
          setSteps(item as SelectorItem);
        }}
        errorMessage={!areStepsValid ? t("travel_time_step_error") : ""}
        items={getTravelCostConfigValues(1, 9)}
        label={t("travel_time_step") + " (Steps)"}
        tooltip={t("travel_time_step_tooltip")}
      />
      {routingType === CatchmentAreaRoutingTypeEnum.Enum.pt && (
        <PTTimeSelectors
          ptStartTime={ptStartTime}
          setPTStartTime={setPTStartTime}
          ptEndTime={ptEndTime}
          setPTEndTime={setPTEndTime}
          ptDays={ptDays}
          ptDay={ptDay}
          setPTDay={setPTDay}
          isPTValid={isPTValid}
        />
      )}
    </Stack>
  );
};

export default CatchmentAreaTimeSelectors;
