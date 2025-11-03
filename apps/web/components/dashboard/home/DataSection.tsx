import { Box, Button, Divider, Grid, Skeleton, Typography } from "@mui/material";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { ICON_NAME, Icon } from "@p4b/ui/components/Icon";

import { useTranslation } from "@/i18n/client";

import type { Layer } from "@/lib/validations/layer";

import type { ContentActions } from "@/types/common";

import { useContentMoreMenu } from "@/hooks/dashboard/ContentHooks";

import EmptyCard from "@/components/dashboard/common/EmptyCard";
import TileCard from "@/components/dashboard/common/TileCard";
import ContentDialogWrapper from "@/components/modals/ContentDialogWrapper";
import DatasetUploadModal from "@/components/modals/DatasetUpload";

interface DataSectionProps {
  layers: Layer[];
  isLoading: boolean;
  hideCreate?: boolean;
}

const DataSection = (props: DataSectionProps) => {
  const { layers, isLoading } = props;
  const { t } = useTranslation("common");
  const router = useRouter();
  const { getMoreMenuOptions, activeContent, moreMenuState, closeMoreMenu, openMoreMenu } =
    useContentMoreMenu();

  const [openDatasetUploadModal, setOpenDatasetUploadModal] = useState(false);
  return (
    <Box>
      {openDatasetUploadModal && (
        <DatasetUploadModal open={openDatasetUploadModal} onClose={() => setOpenDatasetUploadModal(false)} />
      )}
      {activeContent && moreMenuState && (
        <>
          <ContentDialogWrapper
            content={activeContent}
            action={moreMenuState.id as ContentActions}
            onClose={closeMoreMenu}
            onContentDelete={closeMoreMenu}
            type="layer"
          />
        </>
      )}
      <Box
        sx={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          mb: 2,
        }}>
        <Typography variant="h6">{t("recent_datasets")}</Typography>
        <Button
          variant="text"
          size="small"
          endIcon={<Icon iconName={ICON_NAME.CHEVRON_RIGHT} style={{ fontSize: 12 }} />}
          href="/datasets"
          sx={{
            borderRadius: 0,
          }}>
          {t("see_all")}
        </Button>
      </Box>
      <Divider sx={{ mb: 4 }} />
      <Grid container spacing={5}>
        {(isLoading ? Array.from(new Array(4)) : (layers ?? [])).map((item: Layer, index: number) => (
          <Grid
            item
            key={item?.id ?? index}
            xs={12}
            sm={6}
            md={4}
            lg={3}
            display={{
              sm: index > 3 ? "none" : "block",
              md: index > 2 ? "none" : "block",
              lg: index > 3 ? "none" : "block",
            }}
            onClick={() => {
              if (item && item.id) {
                router.push(`/datasets/${item.id}`);
              }
            }}>
            {!item ? (
              <Skeleton variant="rectangular" height={200} />
            ) : (
              <TileCard
                cardType="grid"
                item={item}
                moreMenuOptions={getMoreMenuOptions("layer", item)}
                onMoreMenuSelect={openMoreMenu}
              />
            )}
          </Grid>
        ))}
        <Grid item xs={12} sm={6} md={4} lg={3}>
          {isLoading ? (
            <Skeleton variant="rectangular" height={200} />
          ) : (
            !props.hideCreate && (
              <EmptyCard
                onClick={() => setOpenDatasetUploadModal(true)}
                tooltip={t("create_new_dataset")}
                backgroundImage="https://assets.plan4better.de/img/grid_thumbnail.png"
              />
            )
          )}
        </Grid>
      </Grid>
    </Box>
  );
};

export default DataSection;
