import {
  Box,
  IconButton,
  List,
  ListItem,
  ListItemButton,
  ListItemText,
  Paper,
  Radio,
  Stack,
  Tooltip,
  Typography,
  useTheme,
} from "@mui/material";
import Fab from "@mui/material/Fab";
import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { useMap } from "react-map-gl/maplibre";

import { ICON_NAME, Icon } from "@p4b/ui/components/Icon";

import { ArrowPopper } from "@/components/ArrowPoper";
import { SkeletonImage } from "@/components/common/SkeletonImage";
import type { Basemap } from "@/types/map/common";

interface BasemapSelectorProps {
  styles: Basemap[];
  active: string;
  basemapChange: (value: string) => void;
  editable?: boolean;
  onAdd?: () => void;
  onEdit?: (id: string) => void;
}

interface BasemapSelectorListProps extends BasemapSelectorProps {
  onClick: () => void;
  hideHeader?: boolean;
  /**
   * Renders without the card surface (no elevation, radius or own background).
   * The mobile bottom sheet already provides the surface — nesting the card in
   * it left a raised, rounded edge where the list ended.
   */
  flat?: boolean;
}

interface BasemapSelectorButtonProps {
  open: boolean;
  setOpen: (open: boolean) => void;
}

function BasemapThumbnail({ basemap }: { basemap: Basemap }) {
  // Built-ins always have a thumbnail.
  if (basemap.source === "builtin") {
    return (
      <SkeletonImage
        width={60}
        height={60}
        src={basemap.thumbnail}
        border="rounded"
      />
    );
  }
  // Customs may carry a thumbnail_url.
  if (basemap.thumbnail_url) {
    return (
      <SkeletonImage
        width={60}
        height={60}
        src={basemap.thumbnail_url}
        border="rounded"
      />
    );
  }
  // Solid → swatch.
  if (basemap.type === "solid") {
    return (
      <Box
        sx={{
          width: 60,
          height: 60,
          borderRadius: 1,
          backgroundColor: basemap.color,
          border: (theme) => `1px solid ${theme.palette.divider}`,
        }}
      />
    );
  }
  // Generic placeholder for vector/raster customs without a thumbnail.
  return (
    <Box
      sx={{
        width: 60,
        height: 60,
        borderRadius: 1,
        backgroundColor: (theme) =>
          theme.palette.mode === "light"
            ? theme.palette.grey[200]
            : "rgba(255, 255, 255, 0.06)",
      }}
    />
  );
}

function BasemapRow({
  basemap,
  selected,
  onSelect,
  editable,
  onEdit,
}: {
  basemap: Basemap;
  selected: boolean;
  onSelect: () => void;
  editable: boolean;
  onEdit?: (id: string) => void;
}) {
  const customId = basemap.source === "custom" ? basemap.id : null;
  const showOverlay = editable && customId !== null;

  const title =
    basemap.source === "builtin" ? basemap.title : basemap.name;
  const subtitle =
    basemap.source === "builtin"
      ? basemap.subtitle
      : basemap.description ?? "";

  return (
    <ListItem disablePadding>
      <ListItemButton onClick={onSelect} sx={{ py: 1 }}>
        <Radio checked={selected} onChange={() => {}} sx={{ mr: 1 }} />
        <ListItemText primary={title} secondary={subtitle} />
        <Box
          sx={{
            position: "relative",
            ml: 2,
            "&:hover .basemap-edit-overlay": showOverlay
              ? { opacity: 1 }
              : undefined,
            "&:hover .basemap-thumb": showOverlay
              ? { filter: "blur(2px) brightness(0.7)" }
              : undefined,
          }}>
          <Box
            className="basemap-thumb"
            sx={{
              transition: "filter 0.15s ease",
            }}>
            <BasemapThumbnail basemap={basemap} />
          </Box>
          {showOverlay && (
            <IconButton
              className="basemap-edit-overlay"
              size="small"
              onClick={(e) => {
                e.stopPropagation();
                if (customId) onEdit?.(customId);
              }}
              sx={{
                position: "absolute",
                top: 0,
                left: 0,
                width: "100%",
                height: "100%",
                borderRadius: 1,
                opacity: 0,
                transition: "opacity 0.15s ease",
                color: "#fff",
                backgroundColor: "rgba(0,0,0,0.0)",
                "&:hover": {
                  backgroundColor: "rgba(0,0,0,0.0)",
                },
              }}>
              <Icon iconName={ICON_NAME.EDIT} fontSize="small" htmlColor="inherit" />
            </IconButton>
          )}
        </Box>
      </ListItemButton>
    </ListItem>
  );
}

export function BaseMapSelectorList(props: BasemapSelectorListProps) {
  const theme = useTheme();
  const { t } = useTranslation("common");
  const { styles, active, basemapChange, editable = false, onAdd, onEdit, flat = false } = props;
  const activeIndex = useMemo(
    () => styles.findIndex((style) => style.value === active),
    [styles, active]
  );

  return (
    <Paper
      elevation={flat ? 0 : undefined}
      sx={{
        width: "100%",
        maxHeight: "100%",
        display: "flex",
        flexDirection: "column",
        overflow: "hidden",
        position: "relative",
        ...(flat && {
          height: "100%",
          borderRadius: 0,
          backgroundColor: "transparent",
          backgroundImage: "none",
          boxShadow: "none",
        }),
      }}>
      {!props.hideHeader && (
        <>
          <Box position="absolute" top={5} right={5} sx={{ zIndex: 1 }}>
            <IconButton onClick={() => props.onClick()}>
              <Icon
                iconName={ICON_NAME.CLOSE}
                htmlColor={theme.palette.action.active}
                fontSize="small"
              />
            </IconButton>
          </Box>
          <Typography
            variant="body1"
            fontWeight="bold"
            sx={{ margin: theme.spacing(3), flexShrink: 0 }}>
            {t("map_style")}
          </Typography>
        </>
      )}
      <Box sx={{ flex: 1, minHeight: 0, overflowY: "auto" }}>
        <List sx={{ pt: 0 }}>
          {styles.map((style, idx) => (
            <BasemapRow
              key={style.value}
              basemap={style}
              selected={idx === activeIndex}
              onSelect={() => basemapChange(style.value)}
              editable={editable}
              onEdit={onEdit}
            />
          ))}
        </List>
      </Box>
      {editable && onAdd && (
        <Box
          sx={{
            display: "flex",
            justifyContent: "flex-end",
            alignItems: "center",
            px: 2,
            py: 2.5,
            flexShrink: 0,
            borderTop: (theme) => `1px solid ${theme.palette.divider}`,
          }}>
          <Stack
            direction="row"
            alignItems="center"
            spacing={1}
            onClick={onAdd}
            sx={{
              cursor: "pointer",
              color: (theme) => theme.palette.primary.main,
              userSelect: "none",
              "&:hover": { opacity: 0.8 },
            }}>
            <Icon iconName={ICON_NAME.PLUS} fontSize="small" htmlColor="inherit" />
            <Typography variant="body2" color="inherit" sx={{ fontWeight: 500 }}>
              {t("add_new_basemap")}
            </Typography>
          </Stack>
        </Box>
      )}
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
          color: theme.palette.action.active,
          ...(open && { color: theme.palette.primary.main }),
          "&:hover": { backgroundColor: theme.palette.background.default },
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
            disablePortal={false}
            popperStyle={{ zIndex: theme.zIndex.modal }}
            content={
              <Box
                sx={{
                  width: 360,
                  maxHeight: "min(calc(100vh - 120px), 560px)",
                  display: "flex",
                  pointerEvents: "all",
                }}>
                <BaseMapSelectorList
                  styles={props.styles}
                  active={props.active}
                  basemapChange={props.basemapChange}
                  editable={props.editable}
                  onAdd={props.onAdd}
                  onEdit={props.onEdit}
                  onClick={() => setOpen(false)}
                />
              </Box>
            }
            open={open}
            arrow
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
