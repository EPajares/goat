import { Box, Typography, useTheme } from "@mui/material";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { toast } from "react-toastify";

import { ICON_NAME } from "@p4b/ui/components/Icon";

import { useJobs } from "@/lib/api/processes";
import { useProjectLayers } from "@/lib/api/projects";
import { computeNearbyStations } from "@/lib/api/tools";
import { STREET_NETWORK_LAYER_ID } from "@/lib/constants";
import { setRunningJobIds } from "@/lib/store/jobs/slice";
import { setIsMapGetInfoActive, setMaskLayer, setToolboxStartingPoints } from "@/lib/store/map/slice";
import { jobTypeEnum } from "@/lib/validations/jobs";
import type { CatchmentAreaRoutingWithoutPTType } from "@/lib/validations/tools";
import { maxFeatureCnt, nearbyStationsSchema, toolboxMaskLayerNames } from "@/lib/validations/tools";

import type { SelectorItem } from "@/types/map/common";
import type { IndicatorBaseProps } from "@/types/map/toolbox";

import {
  usePTTimeSelectorValues,
  useRoutingTypes,
  useScenarioItems,
  useStartingPointMethods,
} from "@/hooks/map/ToolsHooks";
import { useProjectLayerFeatureCount } from "@/hooks/map/useProjectLayerFeatureCount";
import { useAppDispatch, useAppSelector } from "@/hooks/store/ContextHooks";

import Container from "@/components/map/panels/Container";
import SectionHeader from "@/components/map/panels/common/SectionHeader";
import SectionOptions from "@/components/map/panels/common/SectionOptions";
import Selector from "@/components/map/panels/common/Selector";
import ToolboxActionButtons from "@/components/map/panels/common/ToolboxActionButtons";
import ToolsHeader from "@/components/map/panels/common/ToolsHeader";
import LearnMore from "@/components/map/panels/toolbox/common/LearnMore";
import PTTimeSelectors from "@/components/map/panels/toolbox/common/PTTimeSelectors";
import StartingPointSelectors from "@/components/map/panels/toolbox/common/StartingPointsSelectors";
import {
  getDefaultConfigValue,
  getTravelCostConfigValues,
} from "@/components/map/panels/toolbox/tools/catchment-area/utils";

const NearbyStations = ({ onBack, onClose }: IndicatorBaseProps) => {
  const { t } = useTranslation("common");
  const theme = useTheme();
  const [isBusy, setIsBusy] = useState(false);
  const { mutate } = useJobs({
    read: false,
  });
  const dispatch = useAppDispatch();
  const startingPoints = useAppSelector((state) => state.map.toolboxStartingPoints);
  const runningJobIds = useAppSelector((state) => state.jobs.runningJobIds);
  const { projectId } = useParams();
  const { layers: projectLayers } = useProjectLayers((projectId as string) || "");

  useEffect(() => {
    if (projectId) {
      dispatch(setMaskLayer(toolboxMaskLayerNames.pt));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId]);

  // Station access routing
  const { activeMobilityRoutingTypes, selectedRouting, setSelectedRouting } = useRoutingTypes();

  const [maxTravelTime, setMaxTravelTime] = useState<SelectorItem | undefined>(undefined);

  const [speed, setSpeed] = useState<SelectorItem | undefined>(undefined);

  const handleConfigurationReset = useCallback(() => {
    setMaxTravelTime(
      getDefaultConfigValue(
        (selectedRouting?.value as CatchmentAreaRoutingWithoutPTType) || "walking",
        "max_travel_time"
      )
    );
    setSpeed(
      getDefaultConfigValue(
        (selectedRouting?.value as CatchmentAreaRoutingWithoutPTType) || "walking",
        "speed"
      )
    );
  }, [selectedRouting]);

  useEffect(() => {
    handleConfigurationReset();
  }, [handleConfigurationReset, selectedRouting]);

  const isRoutingValid = useMemo(() => {
    return !!selectedRouting && !!maxTravelTime && !!speed;
  }, [maxTravelTime, selectedRouting, speed]);

  // Station configuration
  const {
    ptDays,
    ptStartTime,
    setPTStartTime,
    ptEndTime,
    setPTEndTime,
    ptDay,
    setPTDay,
    isPTValid,
    ptModes,
    selectedPTModes,
    setSelectedPTModes,
  } = usePTTimeSelectorValues();

  // Starting Points
  const { startingPointMethods } = useStartingPointMethods();
  const [startingPointMethod, setStartingPointMethod] = useState<SelectorItem>(startingPointMethods[0]);
  const [startingPointLayerItem, setSelectecStartingPointLayerItem] = useState<SelectorItem | undefined>(
    undefined
  );

  const startingPointLayer = useMemo(() => {
    return projectLayers?.find((layer) => layer.id === startingPointLayerItem?.value);
  }, [projectLayers, startingPointLayerItem?.value]);

  // Fetch starting point layer feature count on-demand
  const { featureCount: startingPointLayerFeatureCount } = useProjectLayerFeatureCount({
    projectLayer: startingPointLayer,
  });

  const maxStartingPoints = maxFeatureCnt.catchment_area_nearby_station_access;

  const isValid = useMemo(() => {
    if (startingPointMethod.value === "browser_layer" && !startingPointLayerItem?.value) return false;

    if (startingPointMethod.value === "map" && (!startingPoints || startingPoints.length === 0)) return false;

    const startingPointCount = startingPoints?.length || startingPointLayerFeatureCount || 0;
    if (startingPointCount > maxStartingPoints) return false;

    return isRoutingValid;
  }, [
    isRoutingValid,
    maxStartingPoints,
    startingPointLayerFeatureCount,
    startingPointLayerItem?.value,
    startingPointMethod.value,
    startingPoints,
  ]);

  // Scenario
  const { scenarioItems } = useScenarioItems(projectId as string);
  const [selectedScenario, setSelectedScenario] = useState<SelectorItem | undefined>(undefined);
  const scenarioNetworkSystemLayer = useMemo(() => {
    if (projectLayers) {
      return projectLayers.find((layer) => layer.layer_id === STREET_NETWORK_LAYER_ID);
    }
    return undefined;
  }, [projectLayers]);

  const handleRun = async () => {
    const payload = {
      access_mode: selectedRouting?.value,
      time_window: {
        from_time: ptStartTime,
        to_time: ptEndTime,
        weekday: ptDay?.value,
      },
      speed: speed?.value,
      max_traveltime: maxTravelTime?.value,
      mode: selectedPTModes?.map((mode) => mode.value),
    };
    if (selectedScenario) {
      payload["scenario_id"] = selectedScenario.value;
      // todo: Set street network layer for scenario.
      // At the moment this is hardcoded.
      // Eventually, users should be able to upload their own street network layer which can be used for scenarios.
      payload["street_network"] = {
        edge_layer_project_id: scenarioNetworkSystemLayer?.id,
      };
    }
    if (startingPointMethod.value === "map") {
      const longitude = startingPoints?.map((point) => point[0]);
      const latitude = startingPoints?.map((point) => point[1]);
      payload["starting_points"] = {
        longitude,
        latitude,
      };
    }
    if (startingPointMethod.value === "browser_layer") {
      payload["starting_points"] = {
        layer_project_id: startingPointLayerItem?.value,
      };
    }
    try {
      setIsBusy(true);
      const parsedPayload = nearbyStationsSchema.parse(payload);
      const response = await computeNearbyStations(parsedPayload, projectId as string);
      const { job_id } = response;
      if (job_id) {
        toast.info(`"${t(jobTypeEnum.Enum.nearby_station_access)}" - ${t("job_started")}`);
        mutate();
        dispatch(setRunningJobIds([...runningJobIds, job_id]));
      }
    } catch {
      toast.error(`"${t(jobTypeEnum.Enum.nearby_station_access)}" - ${t("job_failed")}`);
    } finally {
      setIsBusy(false);
      handleReset();
    }
  };

  const handleReset = () => {
    setSelectedRouting(undefined);
    setMaxTravelTime(undefined);
    setSpeed(undefined);
    setStartingPointMethod(startingPointMethods[0]);
    setSelectecStartingPointLayerItem(undefined);
    setSelectedScenario(undefined);
    dispatch(setToolboxStartingPoints(undefined));
    dispatch(setIsMapGetInfoActive(true));
  };

  return (
    <>
      <Container
        disablePadding={false}
        header={<ToolsHeader onBack={onBack} title={t("nearby_stations_access_header")} />}
        close={onClose}
        body={
          <>
            <Box
              sx={{
                display: "flex",
                flexDirection: "column",
              }}>
              {/* DESCRIPTION */}
              <Typography variant="body2" sx={{ fontStyle: "italic", marginBottom: theme.spacing(4) }}>
                {t("nearby_stations_access_description")}
                <LearnMore docsPath="/toolbox/accessibility_indicators/nearby_stations" />
              </Typography>

              {/* ACCESS_MODE */}
              <SectionHeader
                active={true}
                alwaysActive={true}
                label={t("nearby_station_access")}
                icon={ICON_NAME.ROUTE}
                disableAdvanceOptions={true}
              />
              <SectionOptions
                active={true}
                collapsed={!selectedRouting}
                baseOptions={
                  <>
                    <Selector
                      selectedItems={selectedRouting}
                      setSelectedItems={(item: SelectorItem[] | SelectorItem | undefined) => {
                        const routing = item as SelectorItem;
                        setSelectedRouting(routing);
                      }}
                      items={activeMobilityRoutingTypes}
                      label={t("nearby_station_access")}
                      placeholder={t("select_routing")}
                      tooltip={t("nearby_station_access_tooltip")}
                    />
                  </>
                }
                advancedOptions={
                  <>
                    <Selector
                      selectedItems={maxTravelTime}
                      disabled={!selectedRouting}
                      setSelectedItems={(item: SelectorItem[] | SelectorItem | undefined) => {
                        setMaxTravelTime(item as SelectorItem);
                      }}
                      items={getTravelCostConfigValues(3, 15, "min")}
                      label={t("travel_time_limit") + " (Min)"}
                      tooltip={t("travel_time_limit_tooltip")}
                    />

                    <Selector
                      selectedItems={speed}
                      disabled={!selectedRouting}
                      setSelectedItems={(item: SelectorItem[] | SelectorItem | undefined) => {
                        setSpeed(item as SelectorItem);
                      }}
                      items={getTravelCostConfigValues(1, 25, "Km/h")}
                      label={t("travel_time_speed") + " (Km/h)"}
                      tooltip={t("travel_time_speed_tooltip")}
                    />
                  </>
                }
              />

              {/* STATION CONFIGURATIONS */}
              <SectionHeader
                active={isRoutingValid}
                alwaysActive={true}
                label={t("station_configuration")}
                icon={ICON_NAME.SETTINGS}
                disableAdvanceOptions={true}
              />
              <SectionOptions
                active={isRoutingValid}
                baseOptions={
                  <>
                    <Selector
                      selectedItems={selectedPTModes}
                      setSelectedItems={(item: SelectorItem[] | SelectorItem | undefined) => {
                        setSelectedPTModes(item as SelectorItem[]);
                      }}
                      items={ptModes}
                      multiple
                      label={t("routing_pt_mode")}
                      placeholder={t("select_pt_mode")}
                      tooltip={t("choose_pt_mode")}
                      allSelectedLabel={t("all")}
                    />
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
                  </>
                }
              />

              {/* STARTING POINTS */}
              <SectionHeader
                active={isRoutingValid}
                alwaysActive={true}
                label={t("starting_points")}
                icon={ICON_NAME.LOCATION}
                disableAdvanceOptions={true}
              />
              <SectionOptions
                active={isRoutingValid}
                baseOptions={
                  <>
                    <StartingPointSelectors
                      isActive={isRoutingValid}
                      startingPointMethod={startingPointMethod}
                      setStartingPointMethod={setStartingPointMethod}
                      startingPointMethods={startingPointMethods}
                      startingPointLayer={startingPointLayerItem}
                      setStartingPointLayer={setSelectecStartingPointLayerItem}
                      currentStartingPoints={startingPoints?.length || startingPointLayerFeatureCount || 0}
                      maxStartingPoints={maxStartingPoints}
                    />
                  </>
                }
              />

              {/* SCENARIO */}
              <SectionHeader
                active={isValid && !!scenarioNetworkSystemLayer}
                alwaysActive={true}
                label={t("scenario")}
                icon={ICON_NAME.SCENARIO}
                disableAdvanceOptions={true}
              />
              <SectionOptions
                active={isValid}
                baseOptions={
                  <>
                    <Selector
                      selectedItems={selectedScenario}
                      disabled={!scenarioNetworkSystemLayer}
                      setSelectedItems={(item: SelectorItem[] | SelectorItem | undefined) => {
                        setSelectedScenario(item as SelectorItem);
                      }}
                      items={scenarioItems}
                      label={t("scenario")}
                      placeholder={t("select_scenario")}
                      tooltip={t("choose_scenario")}
                    />
                  </>
                }
              />
            </Box>
          </>
        }
        action={
          <ToolboxActionButtons
            runFunction={handleRun}
            runDisabled={!isValid}
            isBusy={isBusy}
            resetFunction={handleReset}
          />
        }
      />
      ;
    </>
  );
};

export default NearbyStations;
