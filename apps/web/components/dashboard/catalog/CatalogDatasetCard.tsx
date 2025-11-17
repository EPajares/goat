import { Box, CardMedia, Grid, Paper, Stack, Typography, useTheme } from "@mui/material";
import { useTranslation } from "react-i18next";

import { ICON_NAME, Icon } from "@p4b/ui/components/Icon";

import type { Layer } from "@/lib/validations/layer";
import { datasetMetadataAggregated } from "@/lib/validations/layer";

import { useGetMetadataValueTranslation } from "@/hooks/map/DatasetHooks";

export const METADATA_HEADER_ICONS = {
  type: ICON_NAME.LAYERS,
  data_category: ICON_NAME.DATA_CATEGORY,
  distributor_name: ICON_NAME.ORGANIZATION,
  geographical_code: ICON_NAME.GLOBE,
  language_code: ICON_NAME.LANGUAGE,
  license: ICON_NAME.LICENSE,
};

const CatalogDatasetCard = ({
  dataset,
  onClick,
  selected,
}: {
  dataset: Layer;
  onClick?: (dataset: Layer) => void;
  selected?: boolean;
}) => {
  const theme = useTheme();
  const { t } = useTranslation(["common"]);
  const getMetadataValueTranslation = useGetMetadataValueTranslation();

  return (
    <Paper
      onClick={() => onClick && onClick(dataset)}
      sx={{
        overflow: "hidden",
        "&:hover": {
          cursor: "pointer",
          boxShadow: 10,
          "& img": {
            transform: "scale(1.2)",
          },
        },
        ...(selected && {
          backgroundColor: "rgba(43, 179, 129, 0.2)",
        }),
      }}
      elevation={3}>
      <Grid container justifyContent="flex-start" spacing={2}>
        <Grid item xs={12} sm={6} md={4} lg={3} sx={{ pl: 0 }}>
          <Box
            sx={{
              overflow: "hidden",
              height: "100%",
            }}>
            <CardMedia
              component="img"
              sx={{
                mr: 6,
                height: "100%",
                transition: "transform 300ms cubic-bezier(0.4, 0, 0.2, 1) 0ms",
                transformOrigin: "center center",
                objectFit: "cover",
                backgroundSize: "cover",
              }}
              image={dataset.thumbnail_url}
            />
          </Box>
        </Grid>
        <Grid item xs={12} sm={6} md={8} lg={9}>
          <Stack direction="column" sx={{ p: 2 }} spacing={2}>
            <Stack spacing={2}>
              <Typography variant="h6" fontWeight="bold">
                {dataset.name}
              </Typography>
              <Box
                sx={{
                  height: "60px",
                  overflow: "hidden",
                  textOverflow: "ellipsis",
                  display: "-webkit-box",
                  WebkitBoxOrient: "vertical",
                  WebkitLineClamp: 3,
                }}>
                <Typography variant="body2" color="text.secondary">
                  {dataset.description || t("common:no_description")}
                </Typography>
              </Box>
            </Stack>
            <Grid container justifyContent="flex-start" sx={{ pl: 0 }}>
              {Object.keys(datasetMetadataAggregated.shape).map((key, index) => {
                return (
                  <Grid
                    item
                    {...(index < Object.keys(datasetMetadataAggregated.shape).length - 1 && {
                      xs: 12,
                      sm: 6,
                      md: 4,
                      lg: 3,
                    })}
                    key={key}
                    sx={{ pl: 0 }}>
                    <Stack
                      direction="row"
                      width="100%"
                      alignItems="center"
                      justifyContent="start"
                      sx={{ py: 2, pr: 2 }}
                      spacing={2}>
                      <Icon
                        iconName={METADATA_HEADER_ICONS[key]}
                        style={{ fontSize: 14 }}
                        htmlColor={theme.palette.text.secondary}
                      />
                      <Typography variant="body2" fontWeight="bold">
                        {getMetadataValueTranslation(key, dataset[key])}
                      </Typography>
                    </Stack>
                  </Grid>
                );
              })}
            </Grid>
          </Stack>
        </Grid>
      </Grid>
    </Paper>
  );
};

export default CatalogDatasetCard;
