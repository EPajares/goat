import { TabContext, TabList, TabPanel } from "@mui/lab";
import { Box, Tab, Typography } from "@mui/material";
import { useTranslation } from "react-i18next";

import { ICON_NAME, Icon } from "@p4b/ui/components/Icon";

interface TabPanelProps {
  value: string;
  children: React.ReactNode;
}

interface CatchmentAreaTypeTabProps {
  catchmentAreaType: string;
  handleCachmentAreaTypeChange: (event: React.SyntheticEvent, newValue: string) => void;
  tabPanels: TabPanelProps[];
}

const CatchmentAreaTypeTab: React.FC<CatchmentAreaTypeTabProps> = ({
  catchmentAreaType,
  handleCachmentAreaTypeChange,
  tabPanels,
}) => {
  const { t } = useTranslation("common");

  return (
    <Box sx={{ width: "100%", typography: "body1" }}>
      <TabContext value={catchmentAreaType}>
        <Box sx={{ borderBottom: 1, borderColor: "divider" }}>
          <TabList
            variant="fullWidth"
            sx={{ minHeight: "40px" }}
            onChange={handleCachmentAreaTypeChange}
            aria-label={t("catchment_area_type")}>
            <Tab
              sx={{ minHeight: "40px", height: "40px" }}
              icon={<Icon iconName={ICON_NAME.CLOCK} sx={{ fontSize: "16px" }} />}
              iconPosition="start"
              label={
                <Typography variant="caption" fontWeight="bold" sx={{ ml: 2 }} color="inherit">
                  {t("time")}
                </Typography>
              }
              value="time"
            />
            <Tab
              sx={{ minHeight: "36px", height: "36px" }}
              icon={<Icon iconName={ICON_NAME.RULER_HORIZONTAL} sx={{ fontSize: "16px" }} />}
              iconPosition="start"
              label={
                <Typography variant="caption" fontWeight="bold" sx={{ ml: 2 }} color="inherit">
                  {t("distance")}
                </Typography>
              }
              value="distance"
            />
          </TabList>
        </Box>
        {tabPanels.map((panel) => (
          <TabPanel sx={{ px: 0 }} key={panel.value} value={panel.value}>
            {panel.children}
          </TabPanel>
        ))}
      </TabContext>
    </Box>
  );
};

export default CatchmentAreaTypeTab;
