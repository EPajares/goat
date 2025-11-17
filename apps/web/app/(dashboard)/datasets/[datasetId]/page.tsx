"use client";

import { Box, Button, Container, Paper, Skeleton, Tab, Tabs, Typography } from "@mui/material";
import { useRouter } from "next/navigation";
import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";

import { ICON_NAME, Icon } from "@p4b/ui/components/Icon";

import { useDataset } from "@/lib/api/layers";

import { CustomTabPanel, a11yProps } from "@/components/common/CustomTabPanel";
import DatasetMapPreview from "@/components/dashboard/dataset/DatasetMapPreview";
import DatasetSummary from "@/components/dashboard/dataset/DatasetSummary";
import DatasetTable from "@/components/dashboard/dataset/DatasetTable";

export default function DatasetDetailPage({ params: { datasetId } }) {
  const router = useRouter();
  const { t } = useTranslation("common");
  const { dataset, isLoading } = useDataset(datasetId);
  const [value, setValue] = useState(0);

  const handleChange = (_event: React.SyntheticEvent, newValue: number) => {
    setValue(newValue);
  };
  const tabItems = useMemo(() => {
    const dataItems = [{ label: t("summary"), value: "summary" }];

    if (dataset?.type === "table" || dataset?.type === "feature") {
      dataItems.push({ label: t("data"), value: "data" });
    }

    if (dataset?.type === "feature" || dataset?.type === "raster") {
      dataItems.push({ label: t("map"), value: "map" });
    }

    return dataItems;
  }, [dataset?.type, t]);

  return (
    <Container sx={{ py: 10, px: 10 }} maxWidth="xl">
      <Box
        sx={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          mb: 8,
        }}>
        <Button
          variant="text"
          startIcon={<Icon iconName={ICON_NAME.CHEVRON_LEFT} style={{ fontSize: 12 }} />}
          sx={{
            borderRadius: 0,
          }}
          onClick={() => router.back()}>
          <Typography variant="body2" color="inherit">
            {t("back")}
          </Typography>
        </Button>
      </Box>
      {isLoading && <Skeleton variant="rectangular" width="100%" height={600} />}
      {!isLoading && dataset && (
        <Box>
          <Paper elevation={3} sx={{ p: 4 }}>
            <Typography variant="h6" fontWeight="bold">
              {dataset.name}
            </Typography>
            <Box sx={{ width: "100%", mt: 8 }}>
              <Box sx={{ borderBottom: 1, borderColor: "divider" }}>
                <Tabs value={value} scrollButtons onChange={handleChange}>
                  {tabItems.map((item) => (
                    <Tab key={item.value} label={item.label} {...a11yProps(item.value)} />
                  ))}
                </Tabs>
              </Box>
              {tabItems.map((item) => (
                <CustomTabPanel
                  key={item.value}
                  value={value}
                  index={tabItems.findIndex((tab) => tab.value === item.value)}>
                  {item.value === "summary" && <DatasetSummary dataset={dataset} />}
                  {item.value === "data" && <DatasetTable dataset={dataset} />}
                  {item.value === "map" && <DatasetMapPreview dataset={dataset} />}
                </CustomTabPanel>
              ))}
            </Box>
          </Paper>
        </Box>
      )}
    </Container>
  );
}
