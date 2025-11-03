import { Box, Typography, useTheme } from "@mui/material";
import { useParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { toast } from "react-toastify";

import { ICON_NAME } from "@p4b/ui/components/Icon";

import { useTranslation } from "@/i18n/client";

import { useJobs } from "@/lib/api/jobs";
import { computeJoin } from "@/lib/api/tools";
import { setRunningJobIds } from "@/lib/store/jobs/slice";
import { statisticOperationEnum } from "@/lib/validations/common";
import { jobTypeEnum } from "@/lib/validations/jobs";
import type { LayerFieldType } from "@/lib/validations/layer";
import { joinSchema, maxFeatureCnt } from "@/lib/validations/tools";

import type { SelectorItem } from "@/types/map/common";
import type { IndicatorBaseProps } from "@/types/map/toolbox";

import useLayerFields from "@/hooks/map/CommonHooks";
import { useFilteredProjectLayers } from "@/hooks/map/LayerPanelHooks";
import { useLayerByGeomType, useLayerDatasetId, useStatisticValues } from "@/hooks/map/ToolsHooks";
import { useAppDispatch, useAppSelector } from "@/hooks/store/ContextHooks";

import LayerFieldSelector from "@/components/map/common/LayerFieldSelector";
import Container from "@/components/map/panels/Container";
import SectionHeader from "@/components/map/panels/common/SectionHeader";
import SectionOptions from "@/components/map/panels/common/SectionOptions";
import Selector from "@/components/map/panels/common/Selector";
import ToolboxActionButtons from "@/components/map/panels/common/ToolboxActionButtons";
import ToolsHeader from "@/components/map/panels/common/ToolsHeader";
import LayerNumberOfFeaturesAlert from "@/components/map/panels/toolbox/common/LayerNumberOfFeaturesAlert";
import LearnMore from "@/components/map/panels/toolbox/common/LearnMore";

const Join = ({ onBack, onClose }: IndicatorBaseProps) => {
  const { projectId } = useParams();
  const theme = useTheme();
  const { t } = useTranslation("common");
  const [isBusy, setIsBusy] = useState(false);
  const { mutate } = useJobs({
    read: false,
  });
  const dispatch = useAppDispatch();
  const runningJobIds = useAppSelector((state) => state.jobs.runningJobIds);
  const { filteredLayers } = useLayerByGeomType(["feature", "table"], undefined, projectId as string);
  const { layers: projectLayers } = useFilteredProjectLayers(projectId as string);
  // Target
  const [targetLayerItem, setTargetLayerItem] = useState<SelectorItem | undefined>(undefined);

  const targetLayer = useMemo(() => {
    return projectLayers.find((layer) => layer.id === targetLayerItem?.value);
  }, [targetLayerItem, projectLayers]);

  const [targetSelectedField, setTargetSelectedField] = useState<LayerFieldType | undefined>(undefined);

  const targetLayerDatasetId = useLayerDatasetId(
    targetLayerItem?.value as number | undefined,
    projectId as string
  );

  // Join
  const [joinLayerItem, setJoinLayerItem] = useState<SelectorItem | undefined>(undefined);

  const joinLayer = useMemo(() => {
    return projectLayers.find((layer) => layer.id === joinLayerItem?.value);
  }, [joinLayerItem, projectLayers]);

  const [joinSelectedField, setJoinSelectedField] = useState<LayerFieldType | undefined>(undefined);

  useEffect(() => {
    if (targetLayerItem) {
      setTargetSelectedField(undefined);
    }
  }, [targetLayerItem]);

  const {
    statisticMethods,
    statisticMethodSelected,
    setStatisticMethodSelected,
    statisticField,
    setStatisticField,
  } = useStatisticValues();

  useEffect(() => {
    if (joinLayerItem) {
      setJoinSelectedField(undefined);
      setStatisticField(undefined);
    }
  }, [joinLayerItem, setStatisticField]);

  const joinLayerDatasetId = useLayerDatasetId(
    joinLayerItem?.value as number | undefined,
    projectId as string
  );

  // Fields have to be the same type
  const { layerFields: targetFields } = useLayerFields(
    targetLayerDatasetId || ""
    // joinSelectedField?.type,
  );
  const { layerFields: joinFields } = useLayerFields(
    joinLayerDatasetId || ""
    // targetSelectedField?.type,
  );
  const { layerFields: allJoinFields } = useLayerFields(joinLayerDatasetId || "");

  // List of target and join layer
  const targetLayers = useMemo(() => {
    if (!joinLayerItem) {
      return filteredLayers;
    }
    return filteredLayers.filter((layer) => layer.value !== joinLayerItem.value);
  }, [joinLayerItem, filteredLayers]);

  const joinLayers = useMemo(() => {
    if (!targetLayerItem) {
      return filteredLayers;
    }
    return filteredLayers.filter((layer) => layer.value !== targetLayerItem.value);
  }, [targetLayerItem, filteredLayers]);

  // Filters the join layer fields based on the selected statistic method
  const filteredStatisticFields = useMemo(() => {
    return allJoinFields.filter((field) => {
      if (statisticMethodSelected?.value === statisticOperationEnum.Enum.count) {
        return field.type === "number" || field.type === "string";
      }
      return field.type === "number";
    });
  }, [allJoinFields, statisticMethodSelected]);

  // Validation
  const isValid = useMemo(() => {
    if (
      !targetLayerItem ||
      !joinLayerItem ||
      !targetSelectedField ||
      !joinSelectedField ||
      !statisticMethodSelected
    ) {
      return false;
    }
    if (
      maxFeatureCnt.join &&
      targetLayer?.filtered_count &&
      targetLayer.filtered_count > maxFeatureCnt.join
    ) {
      return false;
    }
    if (maxFeatureCnt.join && joinLayer?.filtered_count && joinLayer.filtered_count > maxFeatureCnt.join) {
      return false;
    }

    return true;
  }, [
    targetLayerItem,
    joinLayerItem,
    targetSelectedField,
    joinSelectedField,
    statisticMethodSelected,
    joinLayer?.filtered_count,
    targetLayer?.filtered_count,
  ]);

  const handleRun = async () => {
    const payload = {
      target_layer_project_id: targetLayerItem?.value,
      target_field: targetSelectedField?.name,
      join_layer_project_id: joinLayerItem?.value,
      join_field: joinSelectedField?.name,
      column_statistics: {
        operation: statisticMethodSelected?.value,
        field: statisticField?.name,
      },
    };
    try {
      setIsBusy(true);
      const parsedPayload = joinSchema.parse(payload);
      const response = await computeJoin(parsedPayload, projectId as string);
      const { job_id } = response;
      if (job_id) {
        toast.info(`"${t(jobTypeEnum.Enum.join)}" - ${t("job_started")}`);
        mutate();
        dispatch(setRunningJobIds([...runningJobIds, job_id]));
      }
    } catch (error) {
      toast.error(`"${t(jobTypeEnum.Enum.join)}" - ${t("job_failed")}`);
    } finally {
      setIsBusy(false);
      handleReset();
    }
  };
  const handleReset = () => {
    setTargetLayerItem(undefined);
    setJoinLayerItem(undefined);
    setTargetSelectedField(undefined);
    setJoinSelectedField(undefined);
    setStatisticMethodSelected(undefined);
    setStatisticField(undefined);
  };

  return (
    <Container
      disablePadding={false}
      header={<ToolsHeader onBack={onBack} title={t("join_header")} />}
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
              {t("join_description")}
              <LearnMore docsPath="/toolbox/data_management/join" />
            </Typography>
            <SectionHeader
              active={true}
              alwaysActive={true}
              label={t("pick_layers_to_join")}
              icon={ICON_NAME.LAYERS}
              disableAdvanceOptions={true}
            />
            <SectionOptions
              active={true}
              baseOptions={
                <>
                  <Selector
                    selectedItems={targetLayerItem}
                    setSelectedItems={(item: SelectorItem[] | SelectorItem | undefined) => {
                      setTargetLayerItem(item as SelectorItem);
                    }}
                    items={targetLayers}
                    emptyMessage={t("no_layers_found")}
                    emptyMessageIcon={ICON_NAME.LAYERS}
                    label={t("select_target_layer")}
                    placeholder={t("select_target_layer_placeholder")}
                    tooltip={t("select_target_layer_tooltip")}
                  />

                  {!!maxFeatureCnt.join &&
                    !!targetLayer?.filtered_count &&
                    targetLayer.filtered_count > maxFeatureCnt.join && (
                      <LayerNumberOfFeaturesAlert
                        currentFeatures={targetLayer.filtered_count}
                        maxFeatures={maxFeatureCnt.join}
                        texts={{
                          maxFeaturesText: t("maximum_number_of_features"),
                          filterLayerFeaturesActionText: t("please_filter_layer_features"),
                        }}
                      />
                    )}
                  <Selector
                    selectedItems={joinLayerItem}
                    setSelectedItems={(item: SelectorItem[] | SelectorItem | undefined) => {
                      setJoinLayerItem(item as SelectorItem);
                    }}
                    items={joinLayers}
                    emptyMessage={t("no_layers_found")}
                    emptyMessageIcon={ICON_NAME.LAYERS}
                    label={t("select_join_layer")}
                    placeholder={t("select_join_layer_placeholder")}
                    tooltip={t("select_join_layer_tooltip")}
                  />

                  {!!maxFeatureCnt.join &&
                    !!joinLayer?.filtered_count &&
                    joinLayer.filtered_count > maxFeatureCnt.join && (
                      <LayerNumberOfFeaturesAlert
                        currentFeatures={joinLayer.filtered_count}
                        maxFeatures={maxFeatureCnt.join}
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
              active={!!targetLayerItem && !!joinLayerItem}
              alwaysActive={true}
              label={t("fields_to_match")}
              icon={ICON_NAME.TABLE}
              disableAdvanceOptions={true}
            />
            <SectionOptions
              active={!!targetLayerItem && !!joinLayerItem}
              baseOptions={
                <>
                  {targetLayerItem && (
                    <LayerFieldSelector
                      fields={targetFields}
                      selectedField={targetSelectedField}
                      disabled={!targetLayerItem}
                      setSelectedField={(field) => {
                        setTargetSelectedField(field);
                      }}
                      label={t("target_field")}
                      tooltip={t("target_field_tooltip")}
                    />
                  )}

                  {joinLayerItem && (
                    <LayerFieldSelector
                      fields={joinFields}
                      selectedField={joinSelectedField}
                      disabled={!joinLayerItem}
                      setSelectedField={(field) => {
                        setJoinSelectedField(field);
                      }}
                      label={t("join_field")}
                      tooltip={t("join_field_tooltip")}
                    />
                  )}
                </>
              }
            />
            <SectionHeader
              active={!!targetSelectedField && !!joinSelectedField}
              alwaysActive={true}
              label={t("statistics")}
              icon={ICON_NAME.CHART}
              disableAdvanceOptions={true}
            />
            <SectionOptions
              active={!!targetSelectedField && !!joinSelectedField}
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

                  <LayerFieldSelector
                    fields={filteredStatisticFields}
                    selectedField={statisticField}
                    disabled={!statisticMethodSelected}
                    setSelectedField={(field) => {
                      setStatisticField(field);
                    }}
                    label={t("select_field_to_calculate_statistics")}
                    tooltip={t("select_field_to_calculate_statistics_tooltip")}
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

export default Join;
