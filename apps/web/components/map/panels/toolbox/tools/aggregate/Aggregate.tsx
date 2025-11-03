import { Box, Divider, Stack, Switch, Typography, useTheme } from "@mui/material";
import { useParams } from "next/navigation";
import { useMemo, useState } from "react";
import { toast } from "react-toastify";

import { ICON_NAME } from "@p4b/ui/components/Icon";

import { useTranslation } from "@/i18n/client";

import { useJobs } from "@/lib/api/jobs";
import { computeAggregatePoint, computeAggregatePolygon } from "@/lib/api/tools";
import { setRunningJobIds } from "@/lib/store/jobs/slice";
import type { LayerFieldType } from "@/lib/validations/layer";
import {
  aggregatePointSchema,
  aggregatePolygonSchema,
  areaTypeEnum,
  maxFeatureCnt,
} from "@/lib/validations/tools";

import type { SelectorItem } from "@/types/map/common";
import type { IndicatorBaseProps } from "@/types/map/toolbox";

import useLayerFields from "@/hooks/map/CommonHooks";
import { useFilteredProjectLayers } from "@/hooks/map/LayerPanelHooks";
import {
  useLayerByGeomType,
  useLayerDatasetId,
  useScenarioItems,
  useStatisticValues,
} from "@/hooks/map/ToolsHooks";
import { useAppDispatch, useAppSelector } from "@/hooks/store/ContextHooks";

import FormLabelHelper from "@/components/common/FormLabelHelper";
import LayerFieldSelector from "@/components/map/common/LayerFieldSelector";
import Container from "@/components/map/panels/Container";
import SectionHeader from "@/components/map/panels/common/SectionHeader";
import SectionOptions from "@/components/map/panels/common/SectionOptions";
import Selector from "@/components/map/panels/common/Selector";
import ToolboxActionButtons from "@/components/map/panels/common/ToolboxActionButtons";
import ToolsHeader from "@/components/map/panels/common/ToolsHeader";
import LayerNumberOfFeaturesAlert from "@/components/map/panels/toolbox/common/LayerNumberOfFeaturesAlert";
import LearnMore from "@/components/map/panels/toolbox/common/LearnMore";

type AggregateProps = IndicatorBaseProps & {
  type: "point" | "polygon";
};

const Aggregate = ({ onBack, onClose, type }: AggregateProps) => {
  const { t } = useTranslation("common");
  const theme = useTheme();
  const [isBusy, setIsBusy] = useState(false);
  const { mutate } = useJobs({
    read: false,
  });
  const dispatch = useAppDispatch();
  const runningJobIds = useAppSelector((state) => state.jobs.runningJobIds);
  const { projectId } = useParams();
  const { filteredLayers: sourceLayers } = useLayerByGeomType(["feature"], [type], projectId as string);

  const { filteredLayers: polygonAreaLayers } = useLayerByGeomType(
    ["feature"],
    ["polygon"],
    projectId as string
  );
  const { layers: projectLayers } = useFilteredProjectLayers(projectId as string);

  const aggregateMaxFeatureCnt = maxFeatureCnt.aggregate_polygon;

  const [sourceLayerItem, setSourceLayerItem] = useState<SelectorItem | undefined>();
  const sourceLayerDatasetId = useLayerDatasetId(
    sourceLayerItem?.value as number | undefined,
    projectId as string
  );

  const sourceLayer = useMemo(() => {
    return projectLayers?.find((layer) => layer.id === sourceLayerItem?.value);
  }, [sourceLayerItem, projectLayers]);

  const [areaType, setAreaType] = useState<SelectorItem | undefined>();
  const [selectedAreaLayerItem, setSelectedAreaLayerItem] = useState<SelectorItem | undefined>(undefined);
  const selectedAreaLayer = useMemo(() => {
    return projectLayers?.find((layer) => layer.id === selectedAreaLayerItem?.value);
  }, [selectedAreaLayerItem, projectLayers]);
  const [selectedAreaH3Grid, setSelectedAreaH3Grid] = useState<SelectorItem | undefined>(undefined);
  const [statisticAdvancedOptions, setStatisticAdvancedOptions] = useState(true);

  const [weightPolygonByIntersectingArea, setWeightPolygonByIntersectingArea] = useState(false);

  const [fieldGroup, setFieldGroup] = useState<LayerFieldType[] | undefined>([]);

  // Scenario
  const { scenarioItems } = useScenarioItems(projectId as string);
  const [selectedScenario, setSelectedScenario] = useState<SelectorItem | undefined>(undefined);

  const areaTypes: SelectorItem[] = useMemo(() => {
    return [
      {
        value: areaTypeEnum.Enum.feature,
        label: t("polygon"),
        icon: ICON_NAME.LAYERS,
      },
      {
        value: areaTypeEnum.Enum.h3_grid,
        label: t("h3_grid"),
        icon: ICON_NAME.HEXAGON,
      },
    ];
  }, [t]);

  const h3GridValues: SelectorItem[] = useMemo(() => {
    return Array.from({ length: 8 }, (_, i) => ({
      value: `${i + 3}`,
      label: `${i + 3}`,
    }));
  }, []);

  const {
    statisticMethods,
    statisticMethodSelected,
    setStatisticMethodSelected,
    statisticField,
    setStatisticField,
  } = useStatisticValues();

  const { layerFields: statisticLayerFields } = useLayerFields(
    sourceLayerDatasetId || "",
    statisticMethodSelected?.value === "count" ? undefined : "number"
  );

  const isStatisticFieldVisible = useMemo(() => {
    return statisticMethodSelected?.value !== "count";
  }, [statisticMethodSelected]);

  const { layerFields: allSourceLayerFields } = useLayerFields(sourceLayerDatasetId || "");

  const isValid = useMemo(() => {
    if (
      (areaType?.value === areaTypeEnum.Enum.feature && !selectedAreaLayerItem) ||
      (areaType?.value === areaTypeEnum.Enum.h3_grid && !selectedAreaH3Grid)
    ) {
      return false;
    }
    if (
      sourceLayer?.filtered_count &&
      sourceLayer.filtered_count > aggregateMaxFeatureCnt &&
      type === "polygon"
    ) {
      return false;
    }
    if (
      areaType?.value === areaTypeEnum.Enum.feature &&
      selectedAreaLayer?.filtered_count &&
      selectedAreaLayer.filtered_count > aggregateMaxFeatureCnt &&
      type === "polygon"
    ) {
      return false;
    }

    if (isStatisticFieldVisible && !statisticField) {
      return false;
    }

    return !!sourceLayerItem && !!areaType && !!statisticMethodSelected;
  }, [
    sourceLayerItem,
    areaType,
    statisticMethodSelected,
    selectedAreaLayerItem,
    selectedAreaH3Grid,
    sourceLayer,
    selectedAreaLayer?.filtered_count,
    aggregateMaxFeatureCnt,
    statisticField,
    isStatisticFieldVisible,
    type,
  ]);

  const handleRun = async () => {
    const payload = {
      source_layer_project_id: sourceLayerItem?.value,
      area_type: areaType?.value,
      ...(areaType?.value === areaTypeEnum.Enum.h3_grid && selectedAreaH3Grid?.value
        ? { h3_resolution: parseInt(selectedAreaH3Grid?.value as string) }
        : {
            aggregation_layer_project_id: selectedAreaLayerItem?.value,
            weigthed_by_intersecting_area: weightPolygonByIntersectingArea,
          }),
      column_statistics: {
        operation: statisticMethodSelected?.value,
        ...(isStatisticFieldVisible &&
          statisticField && {
            field: statisticField?.name,
          }),
      },
    };
    if (fieldGroup && fieldGroup?.length > 0) {
      payload["source_group_by_field"] = fieldGroup.map((field) => field.name);
    }

    if (selectedScenario) {
      payload["scenario_id"] = selectedScenario.value;
    }

    const schema = type === "point" ? aggregatePointSchema : aggregatePolygonSchema;
    const computeApi = type === "point" ? computeAggregatePoint : computeAggregatePolygon;
    try {
      setIsBusy(true);
      const parsedPayload = schema.parse(payload);
      const response = await computeApi(parsedPayload, projectId as string);
      const { job_id } = response;
      if (job_id) {
        toast.info(t("aggregation_computation_started"));
        mutate();
        dispatch(setRunningJobIds([...runningJobIds, job_id]));
      }
    } catch (error) {
      toast.error(t("error_running_aggregation_computation"));
    } finally {
      setIsBusy(false);
      handleReset();
    }
  };

  const handleReset = () => {
    setSourceLayerItem(undefined);
    setAreaType(undefined);
    setSelectedAreaLayerItem(undefined);
    setSelectedAreaH3Grid(undefined);
    setStatisticMethodSelected(undefined);
    setStatisticAdvancedOptions(true);
    setWeightPolygonByIntersectingArea(false);
    setFieldGroup([]);
    setSelectedScenario(undefined);
    setStatisticField(undefined);
  };

  return (
    <>
      <Container
        disablePadding={false}
        header={
          <ToolsHeader
            onBack={onBack}
            title={type === "point" ? t("aggregate_points_header") : t("aggregate_polygons_header")}
          />
        }
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
                {type === "point" ? (
                  <>
                    {t("aggregate_point_description")}
                    <LearnMore docsPath="/toolbox/geoanalysis/aggregate_points" />
                  </>
                ) : (
                  <>
                    {t("aggregate_polygon_description")}
                    <LearnMore docsPath="/toolbox/geoanalysis/aggregate_polygons" />
                  </>
                )}
              </Typography>

              {/* SELECT LAYERS */}
              <SectionHeader
                active={true}
                alwaysActive={true}
                label={t("pick_source_layer")}
                icon={ICON_NAME.LAYERS}
                disableAdvanceOptions={true}
              />
              <SectionOptions
                active={true}
                baseOptions={
                  <>
                    <Selector
                      selectedItems={sourceLayerItem}
                      setSelectedItems={(item: SelectorItem[] | SelectorItem | undefined) => {
                        setSourceLayerItem(item as SelectorItem);
                      }}
                      items={sourceLayers}
                      emptyMessage={t("no_layers_found")}
                      emptyMessageIcon={ICON_NAME.LAYERS}
                      label={t("select_source_layer")}
                      placeholder={t("select_source_layer_placeholder")}
                      tooltip={t("select_source_layer_tooltip")}
                    />
                    {!!aggregateMaxFeatureCnt &&
                      type === "polygon" &&
                      !!sourceLayer?.filtered_count &&
                      sourceLayer.filtered_count > aggregateMaxFeatureCnt && (
                        <LayerNumberOfFeaturesAlert
                          currentFeatures={sourceLayer.filtered_count}
                          maxFeatures={aggregateMaxFeatureCnt}
                          texts={{
                            maxFeaturesText: t("maximum_number_of_features"),
                            filterLayerFeaturesActionText: t("please_filter_layer_features"),
                          }}
                        />
                      )}
                  </>
                }
              />

              {/* SELECT AREA TYPE */}
              <SectionHeader
                active={!!sourceLayerItem}
                alwaysActive={true}
                label={t("summary_areas")}
                icon={ICON_NAME.AGGREGATE}
                disableAdvanceOptions={true}
              />
              <SectionOptions
                active={!!sourceLayerItem}
                baseOptions={
                  <>
                    <Selector
                      selectedItems={areaType}
                      setSelectedItems={(item: SelectorItem[] | SelectorItem | undefined) => {
                        setAreaType(item as SelectorItem);
                      }}
                      items={areaTypes}
                      label={t("select_area_type")}
                      placeholder={t("select_area_type_placeholder")}
                      tooltip={t("select_area_type_tooltip")}
                    />
                    {areaType && (
                      <Selector
                        selectedItems={
                          areaType?.value === areaTypeEnum.Enum.h3_grid
                            ? selectedAreaH3Grid
                            : selectedAreaLayerItem
                        }
                        setSelectedItems={(item: SelectorItem[] | SelectorItem | undefined) => {
                          areaType?.value === areaTypeEnum.Enum.h3_grid
                            ? setSelectedAreaH3Grid(item as SelectorItem)
                            : setSelectedAreaLayerItem(item as SelectorItem);
                        }}
                        items={
                          areaType?.value === areaTypeEnum.Enum.h3_grid ? h3GridValues : polygonAreaLayers
                        }
                        emptyMessage={t("no_layers_found")}
                        emptyMessageIcon={ICON_NAME.LAYERS}
                        label={
                          areaType?.value === areaTypeEnum.Enum.h3_grid
                            ? t("select_h3_grid_resolution")
                            : t("select_area_layer")
                        }
                        placeholder={
                          areaType?.value === areaTypeEnum.Enum.h3_grid
                            ? t("select_h3_grid_resolution_placeholder")
                            : t("select_area_layer_placeholder")
                        }
                        tooltip={
                          areaType?.value === areaTypeEnum.Enum.h3_grid
                            ? t("select_h3_grid_resolution_tooltip")
                            : t("select_area_layer_tooltip")
                        }
                      />
                    )}

                    {areaType?.value === areaTypeEnum.Enum.feature &&
                      !!aggregateMaxFeatureCnt &&
                      type === "polygon" &&
                      !!selectedAreaLayer?.filtered_count &&
                      selectedAreaLayer.filtered_count > aggregateMaxFeatureCnt && (
                        <LayerNumberOfFeaturesAlert
                          currentFeatures={selectedAreaLayer.filtered_count}
                          maxFeatures={aggregateMaxFeatureCnt}
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
                active={!!sourceLayerItem && !!areaType}
                alwaysActive={true}
                label={t("statistics")}
                icon={ICON_NAME.CHART}
                disableAdvanceOptions={false}
                collapsed={statisticAdvancedOptions}
                setCollapsed={setStatisticAdvancedOptions}
              />
              <SectionOptions
                active={!!sourceLayerItem && !!areaType}
                baseOptions={
                  <>
                    <Selector
                      selectedItems={statisticMethodSelected}
                      setSelectedItems={(item: SelectorItem[] | SelectorItem | undefined) => {
                        setStatisticMethodSelected(item as SelectorItem);
                      }}
                      items={statisticMethods}
                      label={t("select_statistic_method")}
                      placeholder={t("select_statistic_method_placeholder")}
                      tooltip={t("select_statistic_method_tooltip")}
                    />
                    {isStatisticFieldVisible && (
                      <LayerFieldSelector
                        fields={statisticLayerFields}
                        selectedField={statisticField}
                        disabled={!statisticMethodSelected}
                        setSelectedField={(field) => {
                          setStatisticField(field);
                        }}
                        label={t("select_field_to_calculate_statistics")}
                        tooltip={t("select_field_to_calculate_statistics_tooltip")}
                      />
                    )}
                  </>
                }
                collapsed={statisticAdvancedOptions}
                advancedOptions={
                  <>
                    <Divider />
                    {type === "polygon" && (
                      <Stack direction="row" alignItems="center" justifyContent="space-between">
                        <FormLabelHelper
                          label={t("aggregation_weight_polygon_by_intersection_area")}
                          color="inherit"
                        />
                        <Switch
                          size="small"
                          checked={weightPolygonByIntersectingArea}
                          onChange={() =>
                            setWeightPolygonByIntersectingArea(!weightPolygonByIntersectingArea)
                          }
                        />
                      </Stack>
                    )}
                    {/* TODO: REFACTOR THIS  */}
                    <LayerFieldSelector
                      fields={allSourceLayerFields}
                      // eslint-disable-next-line @typescript-eslint/no-explicit-any
                      selectedField={fieldGroup as any}
                      disabled={!statisticMethodSelected}
                      setSelectedField={(field) => {
                        // eslint-disable-next-line @typescript-eslint/no-explicit-any
                        setFieldGroup(field as any);
                      }}
                      label={t("select_group_fields")}
                      tooltip={t("select_group_fields_tooltip")}
                      // eslint-disable-next-line @typescript-eslint/no-explicit-any
                      multiple={true as any}
                    />
                  </>
                }
              />

              {/* SCENARIO */}
              <SectionHeader
                active={isValid}
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
    </>
  );
};

export default Aggregate;
