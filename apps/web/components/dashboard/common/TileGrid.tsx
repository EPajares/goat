import { Box, Grid, Skeleton } from "@mui/material";
import { useTranslation } from "react-i18next";

import { ICON_NAME } from "@p4b/ui/components/Icon";

import type { Layer } from "@/lib/validations/layer";
import type { Project } from "@/lib/validations/project";

import type { ContentActions } from "@/types/common";

import { useContentMoreMenu } from "@/hooks/dashboard/ContentHooks";

import EmptySection from "@/components/common/EmptySection";
import TileCard from "@/components/dashboard/common/TileCard";
import ContentDialogWrapper from "@/components/modals/ContentDialogWrapper";

interface TileGridProps {
  view: "list" | "grid";
  type: "project" | "layer";
  items: Omit<Project, "layer_order">[] | Layer[];
  isLoading: boolean;
  enableActions?: boolean;
  onClick?: (item: Project | Layer) => void;
  selected?: Project | Layer;
}

const TileGrid = (props: TileGridProps) => {
  const { items, isLoading } = props;
  const { t } = useTranslation("common");
  const listProps = {
    xs: 12,
  };
  const gridProps = {
    xs: 12,
    sm: 6,
    md: 4,
    lg: 3,
  };

  const { getMoreMenuOptions, activeContent, moreMenuState, closeMoreMenu, openMoreMenu } =
    useContentMoreMenu();

  return (
    <>
      {activeContent && moreMenuState && (
        <>
          <ContentDialogWrapper
            content={activeContent}
            action={moreMenuState.id as ContentActions}
            onClose={closeMoreMenu}
            onContentDelete={closeMoreMenu}
            type={props.type}
          />
        </>
      )}

      <Box
        sx={{
          ...(props.view === "list" && {
            boxShadow: props.enableActions ? 3 : 0,
          }),
        }}>
        <Grid container spacing={props.view === "list" ? 0 : 5}>
          {!isLoading && items?.length === 0 && (
            <Grid item xs={12}>
              <EmptySection
                label={props.type === "project" ? t("no_projects_found") : t("no_datasets_found")}
                icon={props.type === "project" ? ICON_NAME.MAP : ICON_NAME.DATABASE}
              />
            </Grid>
          )}
          {(isLoading ? Array.from(new Array(4)) : (items ?? [])).map(
            (item: Project | Layer, index: number) => (
              <Grid
                item
                onClick={() => {
                  if (props.onClick) {
                    props.onClick(item);
                  }
                }}
                key={item?.id ?? index}
                {...(props.view === "list" ? listProps : gridProps)}>
                {!item ? (
                  <Skeleton variant="rectangular" height={props.view === "list" ? 80 : 200} />
                ) : (
                  <TileCard
                    selected={props.selected}
                    enableActions={props.enableActions}
                    cardType={props.view}
                    item={item}
                    moreMenuOptions={getMoreMenuOptions(props.type, item)}
                    onMoreMenuSelect={openMoreMenu}
                  />
                )}
              </Grid>
            )
          )}
        </Grid>
      </Box>
    </>
  );
};

export default TileGrid;
