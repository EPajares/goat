import { Box, IconButton, Paper, Stack, Tooltip, Typography, useTheme } from "@mui/material";
import Fab from "@mui/material/Fab";
import { useMemo, useState } from "react";
import { useMap } from "react-map-gl/maplibre";

import { ICON_NAME, Icon } from "@p4b/ui/components/Icon";

import { useTranslation } from "@/i18n/client";

import { ArrowPopper } from "@/components/ArrowPoper";
import { ListTile } from "@/components/common/ListTile";

interface Item {
  value: string;
  url: string;
  title: string;
  subtitle: string;
  thumbnail: string;
  attributionComponent?: React.ReactNode;
}

interface BasemapSelectorProps {
  styles: Item[];
  active: string;
  basemapChange: (style: string) => void;
}

interface BasemapSelectorListProps extends BasemapSelectorProps {
  onClick: () => void;
  hideHeader?: boolean;
}

interface BasemapSelectorButtonProps {
  open: boolean;
  setOpen: (open: boolean) => void;
}

export function BaseMapSelectorList(props: BasemapSelectorListProps) {
  const theme = useTheme();
  const { t } = useTranslation("common");
  const { styles, active, basemapChange } = props;
  const activeIndex = useMemo(() => {
    return styles.findIndex((style) => style.value === active);
  }, [styles, active]);
  return (
    <Paper sx={{ width: "100%", overflow: "auto" }}>
      {!props.hideHeader && (
        <>
          <Box position="absolute" top={5} right={5}>
            <IconButton onClick={() => props.onClick()}>
              <Icon iconName={ICON_NAME.CLOSE} htmlColor={theme.palette.text.secondary} fontSize="small" />
            </IconButton>
          </Box>

          <Typography variant="body1" fontWeight="bold" sx={{ margin: theme.spacing(3) }}>
            {t("map_style")}
          </Typography>
        </>
      )}
      <ListTile
        items={styles}
        selected={[activeIndex]}
        thumbnailBorder="rounded"
        onChange={(selectedStyleIndex) => {
          const basemapValue = styles[selectedStyleIndex[0]].value;
          basemapChange(basemapValue);
        }}
      />
    </Paper>
  );
}

export function BasemapSelectorButton({ open, setOpen }: BasemapSelectorButtonProps) {
  const { t } = useTranslation("common");
  const theme = useTheme();

  return (
    <Tooltip title={t("basemaps")} arrow placement="left">
      <Fab
        onClick={() => setOpen(!open)}
        size="small"
        sx={{
          my: 1,
          backgroundColor: theme.palette.background.paper,
          color: theme.palette.text.secondary,
          ...(open && {
            color: theme.palette.primary.main,
          }),
          "&:hover": {
            backgroundColor: theme.palette.background.default,
          },
          pointerEvents: "all",
        }}>
        <Icon iconName={ICON_NAME.MAP} fontSize="small" htmlColor="inherit" />
      </Fab>
    </Tooltip>
  );
}

export function BasemapSelector(props: BasemapSelectorProps) {
  const [open, setOpen] = useState(false);

  const theme = useTheme();
  const { map } = useMap();

  return (
    <>
      {map && (
        <Stack
          direction="column"
          sx={{
            alignItems: "flex-end",
            marginTop: theme.spacing(1),
            marginBottom: theme.spacing(1),
          }}>
          <ArrowPopper
            placement="top-end"
            content={
              <Box sx={{ width: 360, pointerEvents: "all" }}>
                <BaseMapSelectorList
                  styles={props.styles}
                  active={props.active}
                  basemapChange={props.basemapChange}
                  onClick={() => setOpen(false)} // Close the popper when the close button is clicked
                />
              </Box>
            }
            open={open}
            arrow={true}
            onClose={() => setOpen(false)}>
            <Box>
              <BasemapSelectorButton open={open} setOpen={setOpen} />
            </Box>
          </ArrowPopper>
        </Stack>
      )}
    </>
  );
}
