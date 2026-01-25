import { Divider, Stack, Typography } from "@mui/material";
import { formatDistance } from "date-fns";
import { useTranslation } from "react-i18next";

import { useDateFnsLocale } from "@/i18n/utils";

import type { ProjectLayer } from "@/lib/validations/project";

import DatasetSummary from "@/components/dashboard/dataset/DatasetSummary";

const PropertiesPanel = ({ activeLayer }: { activeLayer: ProjectLayer }) => {
  const { t } = useTranslation("common");
  const dateLocale = useDateFnsLocale();
  return (
    <>
      <Stack spacing={4} sx={{ p: 2 }}>
        <DatasetSummary dataset={activeLayer} hideEmpty={true} hideMainSection={true} />
        {activeLayer.updated_at && (
          <Stack>
            <Typography variant="body2" fontWeight="bold">
              {t("last_updated")}
            </Typography>
            <Divider />
            <Typography variant="caption" noWrap>
              {formatDistance(new Date(activeLayer.updated_at), new Date(), {
                addSuffix: true,
                locale: dateLocale,
              })}
            </Typography>
          </Stack>
        )}
      </Stack>
    </>
  );
};

export default PropertiesPanel;
