import { Box, Divider, Stack, Switch, Typography, useTheme } from "@mui/material";
import { useParams } from "next/navigation";
import React, { useCallback, useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { toast } from "react-toastify";

import { ICON_NAME } from "@p4b/ui/components/Icon";

import {
  computeActiveMobilityCatchmentArea,
  computeCarCatchmentArea,
  computePTCatchmentArea,
} from "@/lib/api/catchmentArea";
import { useJobs } from "@/lib/api/jobs";
import { useProjectLayers } from "@/lib/api/projects";
import { STREET_NETWORK_LAYER_ID } from "@/lib/constants";
import { setRunningJobIds } from "@/lib/store/jobs/slice";
import {
  setIsMapGetInfoActive,
  setMapCursor,
  setMaskLayer,
  setToolboxStartingPoints,
} from "@/lib/store/map/slice";
import { jobTypeEnum } from "@/lib/validations/jobs";
import type { CatchmentAreaRoutingType } from "@/lib/validations/tools";
import {
  CatchmentAreaRoutingTypeEnum,
  PTAccessModes,
  PTEgressModes,
  activeMobilityAndCarCatchmentAreaSchema,
  catchmentAreaShapeEnum,
  ptCatchmentAreaSchema,
  toolboxMaskLayerNames,
} from "@/lib/validations/tools";

import type { SelectorItem } from "@/types/map/common";
import type { IndicatorBaseProps } from "@/types/map/toolbox";

import {
  useCatchmeMaxStartingPoints,
  useCatchmentAreaShapeTypes,
  usePTTimeSelectorValues,
  useRoutingTypes,
  useScenarioItems,
  useStartingPointMethods,
} from "@/hooks/map/ToolsHooks";
import { useAppDispatch, useAppSelector } from "@/hooks/store/ContextHooks";

import FormLabelHelper from "@/components/common/FormLabelHelper";
import Container from "@/components/map/panels/Container";
import SectionHeader from "@/components/map/panels/common/SectionHeader";
import SectionOptions from "@/components/map/panels/common/SectionOptions";
import Selector from "@/components/map/panels/common/Selector";
import ToolboxActionButtons from "@/components/map/panels/common/ToolboxActionButtons";
import ToolsHeader from "@/components/map/panels/common/ToolsHeader";
import LearnMore from "@/components/map/panels/toolbox/common/LearnMore";
import StartingPointSelectors from "@/components/map/panels/toolbox/common/StartingPointsSelectors";
import CatchmentAreaDistanceSelectors from "@/components/map/panels/toolbox/tools/catchment-area/CatchmentAreaDistanceSelectors";
import CatchmentAreaTypeTab from "@/components/map/panels/toolbox/tools/catchment-area/CatchmentAreaTabs";
import CatchmentAreaTimeSelectors from "@/components/map/panels/toolbox/tools/catchment-area/CatchmentAreaTimeSelectors";
import { getDefaultConfigValue } from "@/components/map/panels/toolbox/tools/catchment-area/utils";

const CatchmentArea = ({ onBack, onClose }: IndicatorBaseProps) => {
  const { t } = useTranslation("common");
  const theme = useTheme();
  const { projectId } = useParams();
  const startingPoints = useAppSelector((state) => state.map.toolboxStartingPoints);
  const { mutate } = useJobs({
    read: false,
  });
  const dispatch = useAppDispatch();
  const runningJobIds = useAppSelector((state) => state.jobs.runningJobIds);
  const [isBusy, setIsBusy] = useState(false);

  const { layers: projectLayers } = useProjectLayers((projectId as string) || "");

  // Routing
  const { routingTypes, selectedRouting, setSelectedRouting } = useRoutingTypes();

  // PT Values
  const {
    ptModes,
    ptDays,
    ptStartTime,
    setPTStartTime,
    ptEndTime,
    setPTEndTime,
    ptDay,
    setPTDay,
    isPTValid,
    selectedPTModes,
    setSelectedPTModes,
    resetPTConfiguration,
  } = usePTTimeSelectorValues();

  const { catchmentAreaShapeTypes: allCatchmentShapeTypes } = useCatchmentAreaShapeTypes();
  const catchmentAreaShapeTypes = useMemo(() => {
    if (!allCatchmentShapeTypes) return [];
    // for pt routing only polygon shape is allowed
    if (selectedRouting?.value === CatchmentAreaRoutingTypeEnum.Enum.pt) {
      return allCatchmentShapeTypes.filter((shape) => shape.value === catchmentAreaShapeEnum.Enum.polygon);
    } else {
      return allCatchmentShapeTypes;
    }
  }, [allCatchmentShapeTypes, selectedRouting?.value]);

  const { startingPointMethods } = useStartingPointMethods();

  const isRoutingValid = useMemo(() => {
    if (
      !selectedRouting ||
      (selectedRouting.value === CatchmentAreaRoutingTypeEnum.Enum.pt && selectedPTModes?.length === 0)
    )
      return false;
    return true;
  }, [selectedPTModes?.length, selectedRouting]);

  const [catchmentAreaType, setCatchmentAreaType] = useState<"time" | "distance">("time");

  // Configuration
  const [advanceConfig, setAdvanceConfig] = useState(true);

  const handleCachmentAreaTypeChange = (_event: React.SyntheticEvent, newValue: "time" | "distance") => {
    setCatchmentAreaType(newValue);
  };

  // Active catchment area configuration
  const [maxTravelTime, setMaxTravelTime] = useState<SelectorItem | undefined>(undefined);
  const [speed, setSpeed] = useState<SelectorItem | undefined>(undefined);
  const [distance, setDistance] = useState<number | undefined>(undefined);
  const [steps, setSteps] = useState<SelectorItem | undefined>(undefined);

  const areStepsValid = useMemo(() => {
    if (steps && maxTravelTime && maxTravelTime.value >= steps.value) {
      return true;
    }
    return false;
  }, [maxTravelTime, steps]);

  // Advanced settings
  const [catchmentAreaShapeType, setCatchmentAreaShapeType] = useState<SelectorItem>(
    catchmentAreaShapeTypes[0]
  );

  const [isPolygonDifference, setIsPolygonDifference] = useState(false);
  useEffect(() => {
    // Only show polygon difference for polygon shape
    if (catchmentAreaShapeType.value !== catchmentAreaShapeEnum.Enum.polygon) {
      setIsPolygonDifference(false);
    } else {
      setIsPolygonDifference(true);
    }
  }, [catchmentAreaShapeType]);

  // Reset values
  const handleConfigurationReset = useCallback(() => {
    setCatchmentAreaType("time");
    setAdvanceConfig(true);
    setMaxTravelTime(
      getDefaultConfigValue(
        (selectedRouting?.value as CatchmentAreaRoutingType) || "walking",
        "max_travel_time"
      )
    );
    if (selectedRouting?.value !== CatchmentAreaRoutingTypeEnum.Enum.pt) {
      setSpeed(
        getDefaultConfigValue((selectedRouting?.value as CatchmentAreaRoutingType) || "walking", "speed")
      );
    }
    const distance = getDefaultConfigValue(
      (selectedRouting?.value as CatchmentAreaRoutingType) || "walking",
      "max_distance"
    );
    setDistance(distance.value);
    const steps = getDefaultConfigValue(
      (selectedRouting?.value as CatchmentAreaRoutingType) || "walking",
      "steps"
    );
    setSteps(steps);
    setCatchmentAreaShapeType(catchmentAreaShapeTypes[0]);
    resetPTConfiguration();

    // Reset starting method
    setStartingPointMethod(startingPointMethods[0]);
    setSelectedStartingPointLayerItem(undefined);

    // Reset scenario
    setSelectedScenario(undefined);
  }, [catchmentAreaShapeTypes, resetPTConfiguration, selectedRouting?.value, startingPointMethods]);

  useEffect(() => {
    handleConfigurationReset();
  }, [handleConfigurationReset, selectedRouting]);

  // Starting point
  const [startingPointMethod, setStartingPointMethod] = useState<SelectorItem>(startingPointMethods[0]);

  const [startingPointLayerItem, setSelectedStartingPointLayerItem] = useState<SelectorItem | undefined>(
    undefined
  );

  const startingPointLayer = useMemo(() => {
    return projectLayers?.find((layer) => layer.id === startingPointLayerItem?.value);
  }, [projectLayers, startingPointLayerItem?.value]);

  const { maxStartingPoints } = useCatchmeMaxStartingPoints(selectedRouting);

  const isValid = useMemo(() => {
    if (!isRoutingValid || (!areStepsValid && catchmentAreaType === "time")) return false;
    if (selectedRouting?.value === CatchmentAreaRoutingTypeEnum.Enum.pt && !isPTValid) return false;
    if (startingPointMethod.value === "browser_layer" && !startingPointLayerItem?.value) return false;

    if (startingPointMethod.value === "map" && (!startingPoints || startingPoints.length === 0)) return false;

    const startingPointCount = startingPoints?.length || startingPointLayer?.filtered_count || 0;
    if (startingPointCount > maxStartingPoints) return false;

    return true;
  }, [
    areStepsValid,
    catchmentAreaType,
    isPTValid,
    isRoutingValid,
    maxStartingPoints,
    selectedRouting?.value,
    startingPointLayer?.filtered_count,
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

  const handleReset = () => {
    dispatch(setMaskLayer(undefined));
    dispatch(setToolboxStartingPoints(undefined));
    dispatch(setIsMapGetInfoActive(true));
    dispatch(setMapCursor(undefined));
    setSelectedRouting(undefined);
    handleConfigurationReset();
  };

  const handleRun = async () => {
    const payload = {
      catchment_area_type: catchmentAreaShapeType.value,
    };
    if (selectedScenario?.value) {
      payload["scenario_id"] = selectedScenario?.value;
      // todo: Set street network layer for scenario.
      // At the moment this is hardcoded.
      // Eventually, users should be able to upload their own street network layer which can be used for scenarios.
      payload["street_network"] = {
        edge_layer_project_id: scenarioNetworkSystemLayer?.id,
      };
    }

    if (isPolygonDifference) {
      payload["polygon_difference"] = true;
    }

    // Set polygon difference to false if the shape is polygon
    if (!isPolygonDifference && catchmentAreaShapeType.value === catchmentAreaShapeEnum.Enum.polygon) {
      payload["polygon_difference"] = false;
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

    if (selectedRouting?.value === CatchmentAreaRoutingTypeEnum.Enum.pt) {
      payload["routing_type"] = {
        mode: selectedPTModes?.map((mode) => mode.value),
        egress_mode: PTEgressModes.Enum.walk,
        access_mode: PTAccessModes.Enum.walk,
      };
      payload["travel_cost"] = {
        max_traveltime: maxTravelTime?.value,
        steps: steps?.value,
      };
      payload["time_window"] = {
        from_time: ptStartTime,
        to_time: ptEndTime,
        weekday: ptDay?.value,
      };
      try {
        setIsBusy(true);
        const parsedPayload = ptCatchmentAreaSchema.parse(payload);
        const response = await computePTCatchmentArea(parsedPayload, projectId as string);
        const { job_id } = response;
        if (job_id) {
          toast.info(`"${t(jobTypeEnum.Enum.catchment_area_pt)}" ${t("job_started")}`);
          mutate();
          dispatch(setRunningJobIds([...runningJobIds, job_id]));
        }
      } catch {
        toast.error(`"${t(jobTypeEnum.Enum.catchment_area_pt)}" ${t("job_failed")}`);
      } finally {
        setIsBusy(false);
        handleReset();
        return;
      }
    }
    const travelTimeCost = {
      max_traveltime: maxTravelTime?.value,
      steps: steps?.value,
      speed: speed?.value,
    };
    const distanceCost = {
      max_distance: distance,
      steps: steps?.value,
    };
    payload["travel_cost"] = catchmentAreaType === "time" ? travelTimeCost : distanceCost;
    payload["routing_type"] = selectedRouting?.value;

    if (selectedRouting?.value !== CatchmentAreaRoutingTypeEnum.Enum.car) {
      try {
        setIsBusy(true);
        const parsedPayload = activeMobilityAndCarCatchmentAreaSchema.parse(payload);
        const response = await computeActiveMobilityCatchmentArea(parsedPayload, projectId as string);
        const { job_id } = response;
        if (job_id) {
          toast.info(`"${t(jobTypeEnum.Enum.catchment_area_active_mobility)}" - ${t("job_started")}`);
          mutate();
          dispatch(setRunningJobIds([...runningJobIds, job_id]));
        }
      } catch {
        toast.error(`"${t(jobTypeEnum.Enum.catchment_area_active_mobility)}" - ${t("job_failed")}`);
      } finally {
        setIsBusy(false);
        handleReset();
        return;
      }
    }

    if (selectedRouting?.value === CatchmentAreaRoutingTypeEnum.Enum.car) {
      try {
        setIsBusy(true);
        const parsedPayload = activeMobilityAndCarCatchmentAreaSchema.parse(payload);
        const response = await computeCarCatchmentArea(parsedPayload, projectId as string);
        const { job_id } = response;
        if (job_id) {
          toast.info(`"${t(jobTypeEnum.Enum.catchment_area_car)}" - ${t("job_started")}`);
          mutate();
          dispatch(setRunningJobIds([...runningJobIds, job_id]));
        }
      } catch {
        toast.error(`"${t(jobTypeEnum.Enum.catchment_area_car)}" - ${t("job_failed")}`);
      } finally {
        setIsBusy(false);
        handleReset();
        return;
      }
    }
  };

  const travelTimeProps = {
    maxTravelTime,
    setMaxTravelTime,
    speed,
    setSpeed,
    steps,
    setSteps,
    ptStartTime,
    setPTStartTime,
    ptEndTime,
    setPTEndTime,
    ptDays,
    ptDay,
    setPTDay,
    areStepsValid,
    isPTValid,
  };

  return (
    <Container
      disablePadding={false}
      header={<ToolsHeader onBack={onBack} title={t("catchment_area")} />}
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
              {t("catchment_area_description")}

              <LearnMore docsPath="/toolbox/accessibility_indicators/catchments" />
            </Typography>

            {/* ROUTING */}
            <SectionHeader
              active={true}
              alwaysActive={true}
              label={t("routing")}
              icon={ICON_NAME.ROUTE}
              disableAdvanceOptions={true}
            />
            <SectionOptions
              active={true}
              collapsed={selectedRouting?.value !== CatchmentAreaRoutingTypeEnum.Enum.pt}
              baseOptions={
                <>
                  <Selector
                    selectedItems={selectedRouting}
                    setSelectedItems={(item: SelectorItem[] | SelectorItem | undefined) => {
                      const routing = item as SelectorItem;
                      setSelectedRouting(routing);
                      if (routing.value === CatchmentAreaRoutingTypeEnum.Enum.pt) {
                        dispatch(setToolboxStartingPoints(undefined));
                        dispatch(setMaskLayer(toolboxMaskLayerNames.pt));
                      }
                      if (routing.value !== CatchmentAreaRoutingTypeEnum.Enum.pt) {
                        // same mask layer for active mobility and car.
                        // it can be changed in the future
                        dispatch(setMaskLayer(toolboxMaskLayerNames.active_mobility));
                      }
                    }}
                    items={routingTypes}
                    label={t("routing_type")}
                    placeholder={t("select_routing")}
                    tooltip={t("choose_routing")}
                  />
                </>
              }
              advancedOptions={
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
                </>
              }
            />
            {/* CONFIGURATION */}
            <SectionHeader
              active={isRoutingValid}
              alwaysActive={true}
              label={t("configuration")}
              icon={ICON_NAME.SETTINGS}
              disableAdvanceOptions={false}
              setCollapsed={setAdvanceConfig}
              collapsed={advanceConfig}
            />
            <SectionOptions
              active={isRoutingValid}
              collapsed={advanceConfig}
              baseOptions={
                <>
                  {selectedRouting?.value !== CatchmentAreaRoutingTypeEnum.Enum.pt && (
                    <CatchmentAreaTypeTab
                      catchmentAreaType={catchmentAreaType}
                      handleCachmentAreaTypeChange={handleCachmentAreaTypeChange}
                      tabPanels={[
                        {
                          value: "time",
                          children: (
                            <>
                              <CatchmentAreaTimeSelectors
                                routingType={selectedRouting?.value as CatchmentAreaRoutingType}
                                {...travelTimeProps}
                                t={t}
                              />
                            </>
                          ),
                        },
                        {
                          value: "distance",
                          children: (
                            <>
                              <CatchmentAreaDistanceSelectors
                                distance={distance}
                                setDistance={setDistance}
                                steps={steps}
                                setSteps={setSteps}
                                t={t}
                              />
                            </>
                          ),
                        },
                      ]}
                    />
                  )}
                  {selectedRouting?.value === CatchmentAreaRoutingTypeEnum.Enum.pt && (
                    <CatchmentAreaTimeSelectors
                      routingType={selectedRouting?.value as CatchmentAreaRoutingType}
                      {...travelTimeProps}
                      t={t}
                    />
                  )}
                </>
              }
              advancedOptions={
                <>
                  <Divider />
                  <Stack spacing={4}>
                    <Selector
                      selectedItems={catchmentAreaShapeType}
                      setSelectedItems={(item: SelectorItem[] | SelectorItem | undefined) => {
                        setCatchmentAreaShapeType(item as SelectorItem);
                      }}
                      items={catchmentAreaShapeTypes}
                      label={t("catchment_area_shape")}
                      placeholder={t("select_catchment_area_shape")}
                      tooltip={t("catchment_area_shape_tooltip")}
                    />
                    <Stack direction="row" alignItems="center" justifyContent="space-between">
                      <FormLabelHelper label={t("polygon_difference")} color="inherit" />
                      <Switch
                        disabled={catchmentAreaShapeType.value !== "polygon"}
                        size="small"
                        checked={isPolygonDifference}
                        onChange={() => setIsPolygonDifference(!isPolygonDifference)}
                      />
                    </Stack>
                  </Stack>
                </>
              }
            />

            {/* STARTING */}
            <SectionHeader
              active={isRoutingValid}
              alwaysActive={true}
              label={t("starting")}
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
                    setStartingPointLayer={setSelectedStartingPointLayerItem}
                    currentStartingPoints={startingPoints?.length || startingPointLayer?.filtered_count || 0}
                    maxStartingPoints={maxStartingPoints}
                  />
                </>
              }
            />
            {/* SCENARIO */}
            <SectionHeader
              active={isRoutingValid && !!scenarioNetworkSystemLayer}
              alwaysActive={true}
              label={t("scenario")}
              icon={ICON_NAME.SCENARIO}
              disableAdvanceOptions={true}
            />
            <SectionOptions
              active={isRoutingValid}
              baseOptions={
                <>
                  <Selector
                    disabled={!scenarioNetworkSystemLayer}
                    selectedItems={selectedScenario}
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
  );
};

export default CatchmentArea;
