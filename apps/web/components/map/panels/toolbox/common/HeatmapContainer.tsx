import { Box, Typography, useTheme } from "@mui/material";
import { useParams } from "next/navigation";
import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { toast } from "react-toastify";
import type { ZodObject } from "zod";

import { ICON_NAME } from "@p4b/ui/components/Icon";

import { useJobs } from "@/lib/api/processes";
import { setRunningJobIds } from "@/lib/store/jobs/slice";
import { setMaskLayer } from "@/lib/store/map/slice";
import { HeatmapRoutingTypeEnum, maxFeatureCnt, toolboxMaskLayerNames } from "@/lib/validations/tools";

import type { SelectorItem } from "@/types/map/common";
import type { IndicatorBaseProps } from "@/types/map/toolbox";

import { useRoutingTypes, useScenarioItems } from "@/hooks/map/ToolsHooks";
import { useAppDispatch, useAppSelector } from "@/hooks/store/ContextHooks";

import Container from "@/components/map/panels/Container";
import SectionHeader from "@/components/map/panels/common/SectionHeader";
import SectionOptions from "@/components/map/panels/common/SectionOptions";
import Selector from "@/components/map/panels/common/Selector";
import ToolboxActionButtons from "@/components/map/panels/common/ToolboxActionButtons";
import ToolsHeader from "@/components/map/panels/common/ToolsHeader";
import LayerNumberOfFeaturesAlert from "@/components/map/panels/toolbox/common/LayerNumberOfFeaturesAlert";
import LearnMore from "@/components/map/panels/toolbox/common/LearnMore";

type HeatmapType = "connectivity" | "closest_average" | "gravity";

type HeatmapContainerProps = IndicatorBaseProps & {
  type: HeatmapType;
  handleConfigurationReset?: () => void;
  handleRun?: () => {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    schema: ZodObject<any>;
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    payload: any;
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    apiCall: (payload: any, projectId: string) => Promise<any>;
    type: string;
  };
  handleReset?: () => void;
  isConfigurationValid?: boolean;
  isOpportunitiesValid?: boolean;
  title: string;
  description: string;
  docsPath?: string;
  configChildren?: React.ReactNode;
  opportunitiesChildren?: React.ReactNode;
  disableScenario?: boolean;
  currentNumberOfFeatures?: number;
};

const HeatmapContainer = ({
  type,
  onBack,
  onClose,
  handleConfigurationReset,
  handleRun,
  handleReset,
  isConfigurationValid = true,
  isOpportunitiesValid = true,
  title,
  description,
  docsPath,
  configChildren,
  opportunitiesChildren,
  disableScenario = false,
  currentNumberOfFeatures,
}: HeatmapContainerProps) => {
  const { t } = useTranslation("common");
  const theme = useTheme();
  // Routing
  const {
    activeMobilityHeatmapRoutingTypes,
    motorizedHeatmapRoutingTypes,
    selectedRouting,
    setSelectedRouting,
  } = useRoutingTypes();
  const routingTypes = useMemo(() => {
    return activeMobilityHeatmapRoutingTypes.concat(motorizedHeatmapRoutingTypes);
  }, [activeMobilityHeatmapRoutingTypes, motorizedHeatmapRoutingTypes]);
  const [isBusy, setIsBusy] = useState(false);

  const { mutate } = useJobs({
    read: false,
  });
  const dispatch = useAppDispatch();
  const runningJobIds = useAppSelector((state) => state.jobs.runningJobIds);
  const { projectId } = useParams();

  // Scenario
  const { scenarioItems } = useScenarioItems(projectId as string);
  const [selectedScenario, setSelectedScenario] = useState<SelectorItem | undefined>(undefined);

  const _handleReset = () => {
    dispatch(setMaskLayer(undefined));
    setSelectedRouting(undefined);
    setSelectedScenario(undefined);
    handleConfigurationReset && handleConfigurationReset();
    handleReset && handleReset();
  };

  const _handleRun = async () => {
    setIsBusy(true);
    if (!handleRun) {
      return;
    }
    const { schema, payload, apiCall, type } = handleRun();
    const _payload = {
      routing_type: selectedRouting?.value,
      ...payload,
    };
    if (selectedScenario && selectedScenario.value && !disableScenario) {
      _payload.scenario_id = selectedScenario.value;
    }

    let heatmap_type = `${type}_active_mobility`;
    if (selectedRouting?.value === HeatmapRoutingTypeEnum.Enum.public_transport) {
      heatmap_type = `${type}_pt`;
    }

    try {
      const parsedPayload = schema.parse(_payload);
      const response = await apiCall(parsedPayload, projectId as string);
      const { job_id } = response;
      if (job_id) {
        toast.info(`"${t(heatmap_type)}" - ${t("job_started")}`);
        mutate();
        dispatch(setRunningJobIds([...runningJobIds, job_id]));
      }
    } catch (error) {
      toast.error(`"${t(heatmap_type)}" - ${t("job_failed")}`);
    } finally {
      setIsBusy(false);
      _handleReset();
    }
  };

  const maxNumberOfFeatures = useMemo(() => {
    let routingType = "active_mobility";
    if (
      selectedRouting?.value === HeatmapRoutingTypeEnum.Enum.public_transport ||
      selectedRouting?.value === HeatmapRoutingTypeEnum.Enum.car
    ) {
      routingType = "motorized_mobility";
    }

    return maxFeatureCnt[`heatmap_${type}_${routingType}`];
  }, [selectedRouting, type]);

  const _isValid = useMemo(() => {
    if (!selectedRouting || !isConfigurationValid || !isOpportunitiesValid) {
      return false;
    }
    if (maxNumberOfFeatures && currentNumberOfFeatures && currentNumberOfFeatures > maxNumberOfFeatures) {
      return false;
    }

    return true;
  }, [
    isConfigurationValid,
    isOpportunitiesValid,
    selectedRouting,
    currentNumberOfFeatures,
    maxNumberOfFeatures,
  ]);

  return (
    <Container
      disablePadding={false}
      header={<ToolsHeader onBack={onBack} title={title} />}
      close={onClose}
      body={
        <>
          <Box
            sx={{
              display: "flex",
              flexDirection: "column",
            }}>
            <Typography variant="body2" sx={{ fontStyle: "italic", marginBottom: theme.spacing(4) }}>
              {description}
              {docsPath && <LearnMore docsPath={docsPath} />}
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
              collapsed={true}
              baseOptions={
                <>
                  <Selector
                    selectedItems={selectedRouting}
                    setSelectedItems={(item: SelectorItem[] | SelectorItem | undefined) => {
                      const routing = item as SelectorItem;
                      setSelectedRouting(routing);
                      dispatch(setMaskLayer(toolboxMaskLayerNames.heatmap));
                    }}
                    items={routingTypes}
                    label={t("routing_type")}
                    placeholder={t("select_routing")}
                    tooltip={t("choose_heatmap_routing")}
                  />
                </>
              }
            />

            {/* CONFIGURATION */}
            {configChildren && (
              <>
                <SectionHeader
                  active={!!selectedRouting}
                  alwaysActive={true}
                  label={t("configuration")}
                  icon={ICON_NAME.SETTINGS}
                  disableAdvanceOptions={true}
                />
                <SectionOptions active={!!selectedRouting} baseOptions={<>{configChildren}</>} />
              </>
            )}

            {/* OPPORTUNITIES */}
            {opportunitiesChildren && (
              <>
                <SectionHeader
                  active={!!selectedRouting && isConfigurationValid}
                  alwaysActive={true}
                  label={t("opportunities")}
                  icon={ICON_NAME.LOCATION_MARKER}
                  disableAdvanceOptions={true}
                />
                <SectionOptions
                  active={!!selectedRouting && isConfigurationValid}
                  baseOptions={
                    <>
                      {opportunitiesChildren}
                      {!!maxNumberOfFeatures &&
                        !!currentNumberOfFeatures &&
                        currentNumberOfFeatures > maxNumberOfFeatures && (
                          <LayerNumberOfFeaturesAlert
                            currentFeatures={currentNumberOfFeatures}
                            maxFeatures={maxNumberOfFeatures}
                            texts={{
                              maxFeaturesText: t("maximum_number_of_opportunity_features"),
                              filterLayerFeaturesActionText: t("please_filter_opportunity_layer_features"),
                            }}
                          />
                        )}
                    </>
                  }
                />
              </>
            )}

            {/* SCENARIO */}
            {!disableScenario && (
              <>
                <SectionHeader
                  active={_isValid}
                  alwaysActive={true}
                  label={t("scenario")}
                  icon={ICON_NAME.SCENARIO}
                  disableAdvanceOptions={true}
                />
                <SectionOptions
                  active={_isValid}
                  baseOptions={
                    <>
                      <Selector
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
              </>
            )}
          </Box>
        </>
      }
      action={
        <ToolboxActionButtons
          runFunction={_handleRun}
          runDisabled={!_isValid}
          isBusy={isBusy}
          resetFunction={_handleReset}
        />
      }
    />
  );
};

export default HeatmapContainer;
