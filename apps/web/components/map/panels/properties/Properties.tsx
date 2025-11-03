import { Divider, Stack, Typography } from "@mui/material";
import { formatDistance } from "date-fns";

import { useDateFnsLocale, useTranslation } from "@/i18n/client";

import { setActiveRightPanel } from "@/lib/store/map/slice";
import type { ProjectLayer } from "@/lib/validations/project";

import { useActiveLayer } from "@/hooks/map/LayerPanelHooks";
import { useAppDispatch } from "@/hooks/store/ContextHooks";

import AccordionWrapper from "@/components/common/AccordionWrapper";
import DatasetSummary from "@/components/dashboard/dataset/DatasetSummary";
import { Legend } from "@/components/map/controls/Legend";
import Container from "@/components/map/panels/Container";
import ProjectLayerDropdown from "@/components/map/panels/ProjectLayerDropdown";

const AccordionHeader = ({ title }: { title: string }) => {
  return (
    <Stack spacing={2} direction="row" alignItems="center">
      <Typography variant="body2" fontWeight="bold">
        {title}
      </Typography>
    </Stack>
  );
};

const LayerInfo = ({ layer }: { layer: ProjectLayer }) => {
  const { t } = useTranslation("common");
  const dateLocale = useDateFnsLocale();

  return (
    <AccordionWrapper
      header={<AccordionHeader title={t("layer_info")} />}
      body={
        <Stack spacing={4} sx={{ p: 2 }}>
          {layer.updated_at && (
            <Stack>
              <Typography variant="body2">{t("last_updated")}</Typography>
              <Divider />
              <Typography variant="caption" noWrap>
                {formatDistance(new Date(layer.updated_at), new Date(), {
                  addSuffix: true,
                  locale: dateLocale,
                })}
              </Typography>
            </Stack>
          )}
          <Stack>
            <Typography variant="body2">{t("source")}</Typography>
            <Divider />
            <DatasetSummary dataset={layer} hideEmpty={true} />
          </Stack>
        </Stack>
      }
    />
  );
};

const Symbology = ({ layer }: { layer: ProjectLayer }) => {
  const { t } = useTranslation("common");
  return (
    <AccordionWrapper
      header={<AccordionHeader title={t("symbology")} />}
      body={<Stack sx={{ p: 2 }}>{layer && <Legend layers={[layer]} />}</Stack>}
    />
  );
};

const PropertiesPanel = ({ projectId }: { projectId: string }) => {
  const dispatch = useAppDispatch();
  const { t } = useTranslation("common");
  const { activeLayer } = useActiveLayer(projectId);
  return (
    <Container
      title={t("properties")}
      direction="right"
      disablePadding={true}
      close={() => dispatch(setActiveRightPanel(undefined))}
      body={
        <>
          {activeLayer && (
            <>
              <ProjectLayerDropdown projectId={projectId} />
              <LayerInfo layer={activeLayer} />
              {(activeLayer.type === "feature" || activeLayer.type === "raster") && (
                <Symbology layer={activeLayer} />
              )}
            </>
          )}
        </>
      }
    />
  );
};

export default PropertiesPanel;
