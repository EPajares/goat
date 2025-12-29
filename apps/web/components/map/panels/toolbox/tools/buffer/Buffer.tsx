import { Box, Stack, Switch, Typography, useTheme } from "@mui/material";
import { useParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { toast } from "react-toastify";

import { ICON_NAME } from "@p4b/ui/components/Icon";

import { useJobs } from "@/lib/api/jobs";
import { computeBuffer } from "@/lib/api/tools";
import { setRunningJobIds } from "@/lib/store/jobs/slice";
import { bufferDefaults, bufferSchema, maxFeatureCnt } from "@/lib/validations/tools";

import type { SelectorItem } from "@/types/map/common";
import type { IndicatorBaseProps } from "@/types/map/toolbox";

import { useFilteredProjectLayers } from "@/hooks/map/LayerPanelHooks";
import { useLayerByGeomType, useScenarioItems } from "@/hooks/map/ToolsHooks";
import { useProjectLayerFeatureCount } from "@/hooks/map/useProjectLayerFeatureCount";
import { useAppDispatch, useAppSelector } from "@/hooks/store/ContextHooks";

import FormLabelHelper from "@/components/common/FormLabelHelper";
import Container from "@/components/map/panels/Container";
import SectionHeader from "@/components/map/panels/common/SectionHeader";
import SectionOptions from "@/components/map/panels/common/SectionOptions";
import Selector from "@/components/map/panels/common/Selector";
import SliderInput from "@/components/map/panels/common/SliderInput";
import ToolboxActionButtons from "@/components/map/panels/common/ToolboxActionButtons";
import ToolsHeader from "@/components/map/panels/common/ToolsHeader";
import LayerNumberOfFeaturesAlert from "@/components/map/panels/toolbox/common/LayerNumberOfFeaturesAlert";
import LearnMore from "@/components/map/panels/toolbox/common/LearnMore";
import { getTravelCostConfigValues } from "@/components/map/panels/toolbox/tools/catchment-area/utils";

const Buffer = ({ onBack, onClose }: IndicatorBaseProps) => {
  const { projectId } = useParams();
  const theme = useTheme();
  const { t } = useTranslation("common");
  const [isBusy, setIsBusy] = useState(false);
  const { mutate } = useJobs({
    read: false,
  });
  const dispatch = useAppDispatch();
  const runningJobIds = useAppSelector((state) => state.jobs.runningJobIds);

  const [bufferLayerItem, setBufferLayerItem] = useState<SelectorItem | undefined>(undefined);
  const [distance, setDistance] = useState<number>(bufferDefaults.default_distance);
  const [steps, setSteps] = useState<SelectorItem | undefined>({
    value: bufferDefaults.default_steps,
    label: bufferDefaults.default_steps.toString(),
  });

  const [isPolygonUnion, setIsPolygonUnion] = useState<boolean>(true);
  const [isPolygonDifference, setIsPolygonDifference] = useState<boolean>(false);

  // Scenario
  const { scenarioItems } = useScenarioItems(projectId as string);
  const [selectedScenario, setSelectedScenario] = useState<SelectorItem | undefined>(undefined);

  useEffect(() => {
    if (!isPolygonUnion) {
      setIsPolygonDifference(false);
    }
  }, [isPolygonUnion]);

  const { filteredLayers } = useLayerByGeomType(["feature"], undefined, projectId as string);

  const { layers: projectLayers } = useFilteredProjectLayers(projectId as string);

  const bufferLayer = useMemo(() => {
    return projectLayers?.find((layer) => layer.id === bufferLayerItem?.value);
  }, [bufferLayerItem, projectLayers]);

  // Fetch buffer layer feature count on-demand
  const { featureCount: bufferLayerFeatureCount } = useProjectLayerFeatureCount({
    projectLayer: bufferLayer,
  });

  const isValid = useMemo(() => {
    if (
      !!bufferLayerItem &&
      distance > 0 &&
      bufferLayerFeatureCount !== undefined &&
      bufferLayerFeatureCount < maxFeatureCnt.buffer
    ) {
      return true;
    }
    return false;
  }, [bufferLayerItem, distance, bufferLayerFeatureCount]);

  const handleRun = async () => {
    const payload = {
      source_layer_project_id: bufferLayerItem?.value,
      max_distance: distance,
      distance_step: steps?.value,
      polygon_union: isPolygonUnion,
      polygon_difference: isPolygonDifference,
    };

    if (selectedScenario) {
      payload["scenario_id"] = selectedScenario.value;
    }

    try {
      setIsBusy(true);
      const parsedPayload = bufferSchema.parse(payload);
      const response = await computeBuffer(parsedPayload, projectId as string);
      const { job_id } = response;
      if (job_id) {
        toast.info(t("buffer_computation_started"));
        mutate();
        dispatch(setRunningJobIds([...runningJobIds, job_id]));
      }
    } catch (error) {
      toast.error(t("error_running_buffer_computation"));
    } finally {
      setIsBusy(false);
      handleReset();
    }
  };
  const handleReset = () => {
    setBufferLayerItem(undefined);
    setDistance(bufferDefaults.default_distance);
    setIsPolygonUnion(true);
    setIsPolygonDifference(false);
    setSteps({
      value: bufferDefaults.default_steps,
      label: bufferDefaults.default_steps.toString(),
    });
    setSelectedScenario(undefined);
  };
  return (
    <Container
      disablePadding={false}
      header={<ToolsHeader onBack={onBack} title={t("buffer_header")} />}
      close={onClose}
      body={
        <>
          <Box
            sx={{
              display: "flex",
              flexDirection: "column",
            }}>
            <Typography variant="body2" sx={{ fontStyle: "italic", marginBottom: theme.spacing(4) }}>
              {t("buffer_description")}
              <LearnMore docsPath="/toolbox/geoprocessing/buffer" />
            </Typography>
            <SectionHeader
              active={true}
              alwaysActive={true}
              label={t("pick_layer_to_buffer")}
              icon={ICON_NAME.LAYERS}
              disableAdvanceOptions={true}
            />
            <SectionOptions
              active={true}
              baseOptions={
                <>
                  <Selector
                    selectedItems={bufferLayerItem}
                    setSelectedItems={(item: SelectorItem[] | SelectorItem | undefined) => {
                      setBufferLayerItem(item as SelectorItem);
                    }}
                    items={filteredLayers}
                    emptyMessage={t("no_layers_found")}
                    emptyMessageIcon={ICON_NAME.LAYERS}
                    label={t("select_buffer_layer")}
                    placeholder={t("select_buffer_layer_placeholder")}
                    tooltip={t("select_buffer_layer_tooltip")}
                  />
                  {!!maxFeatureCnt.buffer &&
                    bufferLayerFeatureCount !== undefined &&
                    bufferLayerFeatureCount > maxFeatureCnt.buffer && (
                      <LayerNumberOfFeaturesAlert
                        currentFeatures={bufferLayerFeatureCount}
                        maxFeatures={maxFeatureCnt.buffer}
                        texts={{
                          maxFeaturesText: t("maximum_number_of_features"),
                          filterLayerFeaturesActionText: t("please_filter_layer_features"),
                        }}
                      />
                    )}
                </>
              }
            />
            <SectionHeader
              active={!!bufferLayerItem}
              alwaysActive={true}
              label={t("buffer_settings")}
              icon={ICON_NAME.SETTINGS}
              disableAdvanceOptions={true}
            />
            <SectionOptions
              active={!!bufferLayerItem}
              baseOptions={
                <>
                  <Stack>
                    <FormLabelHelper label={`${t("buffer_distance")} (Meter)`} color="inherit" />
                    <SliderInput
                      value={distance}
                      min={bufferDefaults.min_distance}
                      max={bufferDefaults.max_distance}
                      onChange={(value) => setDistance(value as number)}
                      isRange={false}
                      step={bufferDefaults.buffer_step}
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
                    label={t("buffer_steps") + " (Steps)"}
                    tooltip={t("buffer_steps_tooltip")}
                  />
                  <Stack>
                    <Stack direction="row" alignItems="center" justifyContent="space-between">
                      <FormLabelHelper label={t("polygon_union")} color="inherit" />
                      <Switch
                        size="small"
                        checked={isPolygonUnion}
                        onChange={() => setIsPolygonUnion(!isPolygonUnion)}
                      />
                    </Stack>
                    <Stack direction="row" alignItems="center" justifyContent="space-between">
                      <FormLabelHelper label={t("polygon_difference")} color="inherit" />
                      <Switch
                        size="small"
                        disabled={!isPolygonUnion}
                        checked={isPolygonDifference}
                        onChange={() => setIsPolygonDifference(!isPolygonDifference)}
                      />
                    </Stack>
                  </Stack>
                </>
              }
            />

            {/* SCENARIO */}
            <SectionHeader
              active={isValid && !!bufferLayerItem}
              alwaysActive={true}
              label={t("scenario")}
              icon={ICON_NAME.SCENARIO}
              disableAdvanceOptions={true}
            />
            <SectionOptions
              active={isValid && !!bufferLayerItem}
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

export default Buffer;
