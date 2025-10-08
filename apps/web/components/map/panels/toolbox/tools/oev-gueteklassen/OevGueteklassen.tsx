import { Box, Typography, useTheme } from "@mui/material";
import { useParams } from "next/navigation";
import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { toast } from "react-toastify";

import { ICON_NAME } from "@p4b/ui/components/Icon";

import { useJobs } from "@/lib/api/jobs";
import { computeOevGueteKlassen } from "@/lib/api/tools";
import { accessibilityIndicatorsStaticPayload } from "@/lib/constants/payloads";
import { setRunningJobIds } from "@/lib/store/jobs/slice";
import { setMaskLayer } from "@/lib/store/map/slice";
import { jobTypeEnum } from "@/lib/validations/jobs";
import {
  oevGueteklassenCatchmentType,
  oevGueteklassenSchema,
  toolboxMaskLayerNames,
} from "@/lib/validations/tools";

import type { SelectorItem } from "@/types/map/common";
import type { IndicatorBaseProps } from "@/types/map/toolbox";

import { useLayerByGeomType, usePTTimeSelectorValues } from "@/hooks/map/ToolsHooks";
import { useAppDispatch, useAppSelector } from "@/hooks/store/ContextHooks";

import Container from "@/components/map/panels/Container";
import SectionHeader from "@/components/map/panels/common/SectionHeader";
import SectionOptions from "@/components/map/panels/common/SectionOptions";
import Selector from "@/components/map/panels/common/Selector";
import ToolboxActionButtons from "@/components/map/panels/common/ToolboxActionButtons";
import ToolsHeader from "@/components/map/panels/common/ToolsHeader";
import LearnMore from "@/components/map/panels/toolbox/common/LearnMore";
import PTTimeSelectors from "@/components/map/panels/toolbox/common/PTTimeSelectors";

const OevGueteklassen = ({ onBack, onClose }: IndicatorBaseProps) => {
  const { t } = useTranslation("common");
  const theme = useTheme();
  const [isBusy, setIsBusy] = useState(false);
  const { mutate } = useJobs({
    read: false,
  });
  const dispatch = useAppDispatch();
  const runningJobIds = useAppSelector((state) => state.jobs.runningJobIds);
  const { projectId } = useParams();
  const { filteredLayers } = useLayerByGeomType(["feature"], ["polygon"], projectId as string);
  const [referenceLayer, setReferenceLayer] = useState<SelectorItem | undefined>(undefined);

  const catchmentAreaTypes: SelectorItem[] = useMemo(() => {
    return [
      {
        value: oevGueteklassenCatchmentType.Enum.buffer,
        label: t("buffer"),
        icon: ICON_NAME.BULLSEYE,
      },
      {
        value: oevGueteklassenCatchmentType.Enum.network,
        label: t("network"),
        icon: ICON_NAME.STREET_NETWORK,
      },
    ];
  }, [t]);
  const [catchmentArea, setCatchmentArea] = useState<SelectorItem | undefined>(catchmentAreaTypes[0]);

  dispatch(setMaskLayer(toolboxMaskLayerNames.pt));

  const {
    // ptModes,
    ptDays,
    ptStartTime,
    setPTStartTime,
    ptEndTime,
    setPTEndTime,
    ptDay,
    setPTDay,
    isPTValid,
    resetPTConfiguration,
  } = usePTTimeSelectorValues();

  const isValid = useMemo(() => {
    if (!referenceLayer || !isPTValid) {
      return false;
    }
    return true;
  }, [isPTValid, referenceLayer]);

  const handleRun = async () => {
    const payload = {
      catchment_type: catchmentArea?.value,
      reference_area_layer_project_id: referenceLayer?.value,
      station_config: accessibilityIndicatorsStaticPayload,
      time_window: {
        weekday: ptDay?.value,
        from_time: ptStartTime,
        to_time: ptEndTime,
      },
    };

    try {
      setIsBusy(true);
      const parsedPayload = oevGueteklassenSchema.parse(payload);
      const response = await computeOevGueteKlassen(parsedPayload, projectId as string);
      const { job_id } = response;
      if (job_id) {
        toast.info(`"${t(jobTypeEnum.Enum.oev_gueteklasse)}" - ${t("job_started")}`);
        mutate();
        dispatch(setRunningJobIds([...runningJobIds, job_id]));
      }
    } catch (error) {
      toast.error(`"${t(jobTypeEnum.Enum.oev_gueteklasse)}" - ${t("job_failed")}`);
    } finally {
      setIsBusy(false);
      handleReset();
    }
  };

  const handleReset = () => {
    setReferenceLayer(undefined);
    setCatchmentArea(catchmentAreaTypes[0]);
    resetPTConfiguration();
  };

  return (
    <>
      <Container
        disablePadding={false}
        header={<ToolsHeader onBack={onBack} title={t("oev_gueteklasse_header")} />}
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
                {t("oev_gueteklasse_description")}
                <LearnMore docsPath="/toolbox/accessibility_indicators/oev_gueteklassen" />
              </Typography>

              {/* CALCULATION TIME */}
              <SectionHeader
                active={true}
                alwaysActive={true}
                label={t("calculation_time")}
                icon={ICON_NAME.CLOCK}
                disableAdvanceOptions={true}
              />
              <SectionOptions
                active={true}
                baseOptions={
                  <>
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

              {/* REFERENCE LAYER */}
              <SectionHeader
                active={true}
                alwaysActive={true}
                label={t("reference_layer")}
                icon={ICON_NAME.LAYERS}
                disableAdvanceOptions={true}
              />
              <SectionOptions
                active={true}
                baseOptions={
                  <>
                    <Selector
                      selectedItems={referenceLayer}
                      setSelectedItems={(item: SelectorItem[] | SelectorItem | undefined) => {
                        setReferenceLayer(item as SelectorItem);
                      }}
                      items={filteredLayers}
                      emptyMessage={t("no_polygon_layer_found")}
                      emptyMessageIcon={ICON_NAME.LAYERS}
                      label={t("select_reference_layer")}
                      placeholder={t("select_reference_layer_placeholder")}
                      tooltip={t("select_reference_layer_tooltip")}
                    />
                  </>
                }
              />

              {/* CONFIGURATION  */}
              <SectionHeader
                active={!!referenceLayer && isPTValid}
                alwaysActive={true}
                label={t("configuration")}
                icon={ICON_NAME.SETTINGS}
                disableAdvanceOptions={true}
              />

              <SectionOptions
                active={!!referenceLayer && isPTValid}
                baseOptions={
                  <>
                    <Selector
                      selectedItems={catchmentArea}
                      setSelectedItems={(item: SelectorItem[] | SelectorItem | undefined) => {
                        setCatchmentArea(item as SelectorItem);
                      }}
                      items={catchmentAreaTypes}
                      label={t("oev_gueteklassen_catchement_area")}
                      tooltip={t("oev_gueteklassen_catchment_area_tooltip")}
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

export default OevGueteklassen;
