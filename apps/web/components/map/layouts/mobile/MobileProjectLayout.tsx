import { Global } from "@emotion/react";
import type { Theme } from "@mui/material";
import { Box, IconButton, Stack, SwipeableDrawer, Typography, styled, useTheme } from "@mui/material";
import React, { useEffect, useMemo, useRef, useState } from "react";
import "swiper/css";
import "swiper/css/pagination";
import { Pagination } from "swiper/modules";
import { Swiper, SwiperSlide } from "swiper/react";
import { v4 } from "uuid";

import { ICON_NAME, Icon } from "@p4b/ui/components/Icon";

import { useTranslation } from "@/i18n/client";

import { MAPBOX_TOKEN } from "@/lib/constants";
import { setGeocoderResult } from "@/lib/store/map/slice";
import { projectSchema } from "@/lib/validations/project";

import { useBasemap } from "@/hooks/map/MapHooks";
import { useAppDispatch, useAppSelector } from "@/hooks/store/ContextHooks";

import WidgetWrapper from "@/components/builder/widgets/WidgetWrapper";
import Header from "@/components/header/Header";
import AttributionControl from "@/components/map/controls/Attribution";
import { BaseMapSelectorList, BasemapSelectorButton } from "@/components/map/controls/BasemapSelector";
import Geocoder from "@/components/map/controls/Geocoder";
import type { DetailsViewType } from "@/components/map/controls/LayerInfo";
import { LayerInfo } from "@/components/map/controls/LayerInfo";
import Scalebar from "@/components/map/controls/Scalebar";
import { UserLocation } from "@/components/map/controls/UserLocation";
import { Zoom } from "@/components/map/controls/Zoom";
import type { PublicProjectLayoutProps } from "@/components/map/layouts/desktop/PublicProjectLayout";

import "@/styles/swiper.css";

// --- Constants ---
const drawerBleeding = 56;

// --- Types ---
type DrawerView = "default" | "layerInfo" | "basemapSelector";

// --- GlobalSwiperStyles (Unchanged) ---
const GlobalSwiperStyles = ({ open, drawerView }: { open: boolean; drawerView: DrawerView }) => (
  <Global
    styles={(theme: Theme) => ({
      "#swiper-pagination-container": {
        position: "absolute",
        top: "50%", // Centered vertically within the puller area
        transform: "translateY(-50%)",
        left: 0,
        right: 0,
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        zIndex: 1, // Below Puller, above drawer content
        pointerEvents: "auto", // Allow clicking bullets
        transition: "opacity 0.3s ease-in-out, visibility 0.3s ease-in-out",
        // Show only when drawer is open AND in default view
        opacity: open && drawerView === "default" ? 1 : 0,
        visibility: open && drawerView === "default" ? "visible" : "hidden",
        ".swiper-pagination-bullet": {
          backgroundColor: theme.palette.mode === "dark" ? theme.palette.grey[400] : theme.palette.grey[600],
          opacity: 0.7,
          margin: "0 4px !important",
        },
        ".swiper-pagination-bullet-active": {
          backgroundColor: theme.palette.primary.main,
          opacity: 1,
        },
      },
      ".MuiDrawer-root > .MuiPaper-root": {
        // Adjusted height calculation if needed, but 60% seems reasonable
        height: `calc(60% - ${drawerBleeding}px)`,
        overflow: "visible",
      },
    })}
  />
);

// --- Puller (Unchanged) ---
const Puller = styled("div")(({ theme }) => ({
  width: 30,
  height: 6,
  backgroundColor: theme.palette.grey[300],
  borderRadius: 3,
  position: "absolute",
  top: 8,
  left: "calc(50% - 15px)",
  zIndex: 2, // Ensure puller is above pagination
  ...theme.applyStyles("dark", {
    backgroundColor: theme.palette.grey[700],
  }),
}));

// --- InfoHeader (Unchanged) ---
interface InfoHeaderProps {
  title: string;
  onClose: () => void;
  iconName?: ICON_NAME;
}
export const InfoHeader: React.FC<InfoHeaderProps> = ({ title, iconName, onClose }) => {
  return (
    <Stack sx={{ pl: 4, pr: 2, pt: 2 }} direction="row" alignItems="center" justifyContent="space-between">
      <Stack direction="row" spacing={2} alignItems="center" sx={{ width: "90%" }}>
        {iconName && <Icon iconName={iconName} fontSize="small" />}
        <Typography variant="body1" fontWeight="bold" noWrap>
          {title}
        </Typography>
      </Stack>
      <IconButton onClick={onClose} sx={{ pointerEvents: "all" }}>
        <Icon iconName={ICON_NAME.XCLOSE} />
      </IconButton>
    </Stack>
  );
};

// --- MobileProjectLayout component ---
const MobileProjectLayout = ({
  projectLayers = [],
  project: _project,
  onProjectUpdate,
}: PublicProjectLayoutProps) => {
  const { t } = useTranslation("common");
  const theme = useTheme();
  const dispatch = useAppDispatch();
  const project = useMemo(() => {
    const parsedProject = projectSchema.safeParse(_project);
    if (parsedProject.success) {
      return parsedProject.data;
    } else {
      console.error("Invalid project data:", parsedProject.error);
      return undefined;
    }
  }, [_project]);

  // --- State ---
  const [open, setOpen] = useState(false); // Drawer open/closed state
  const [drawerView, setDrawerView] = useState<DrawerView>("default"); // Explicit view state
  const [layerInfoDetailsView, setLayerInfoDetailsView] = useState<DetailsViewType | undefined>(undefined);

  // --- Redux State ---
  const layerInfo = useAppSelector((state) => state.map.popupInfo);
  const highlightedFeature = useAppSelector((state) => state.map.highlightedFeature);

  // --- Hooks ---
  const { translatedBaseMaps, activeBasemap } = useBasemap(project);
  const scrollableContentRef = useRef<HTMLDivElement | null>(null);

  // --- Effects ---
  // Effect to handle changes in layerInfo (feature selection/deselection)
  useEffect(() => {
    if (layerInfo) {
      // When a feature is selected, switch to layerInfo view and open drawer
      setDrawerView("layerInfo");
      setLayerInfoDetailsView(undefined); // Reset details view when feature changes
      setOpen(true);
    } else {
      // When a feature is deselected (layerInfo becomes null)
      // If the current view is 'layerInfo', switch back to 'default'
      // We keep the drawer open, user can swipe down if they want.
      if (drawerView === "layerInfo") {
        setDrawerView("default");
      }
    }
    // Only react to changes in layerInfo itself
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [layerInfo]);

  // --- Handlers ---
  const toggleDrawer = (newOpen: boolean) => () => {
    setOpen(newOpen);
  };

  // Handles clicks on the close ('X') button in the InfoHeader
  const handleCloseView = () => {
    // Always clear map state if layerInfo was active
    if (drawerView === "layerInfo" && layerInfo) {
      layerInfo.onClose(); // This should set layerInfo to null via Redux
    }
    // Reset the view to default
    setDrawerView("default");
    // Keep the drawer open, allowing user to see default view or swipe down
    setOpen(true);
  };

  // Handles clicks on the BasemapSelectorButton
  const handleOpenBasemapSelector = () => {
    // Clear any existing layer info selection first
    if (layerInfo) {
      layerInfo.onClose();
    }
    setDrawerView("basemapSelector");
    setLayerInfoDetailsView(undefined); // Ensure details view is reset
    setOpen(true);
  };

  // Stops propagation for internal scrolling
  const handleContentTouchMove = (event: React.TouchEvent) => {
    event.stopPropagation();
  };

  // --- Derived State ---
  // Determine the title and icon for the current view in the header area
  const currentHeaderInfo = useMemo(() => {
    switch (drawerView) {
      case "layerInfo":
        return layerInfo ? { title: layerInfo.title, icon: ICON_NAME.LAYERS } : null;
      case "basemapSelector":
        return { title: t("map_style"), icon: ICON_NAME.MAP };
      case "default":
      default:
        return null; // No header needed for default view (only pagination)
    }
  }, [drawerView, layerInfo, t]);

  return (
    <>
      {/* Pass drawerView to GlobalSwiperStyles */}
      <GlobalSwiperStyles open={open} drawerView={drawerView} />
      <Box sx={{ height: `calc(100% - 56px)`, width: "100%", display: "flex", flexDirection: "column" }}>
        {/* Header and Map Controls (Unchanged structure) */}
        {project?.builder_config?.settings?.toolbar && (
          <Header showHambugerMenu={false} mapHeader={true} project={project} viewOnly />
        )}
        <Box
          display="flex"
          sx={{
            zIndex: 1,
            position: "relative",
            height: "100%",
            flexGrow: 1,
            justifyContent: "space-between",
            pointerEvents: "none",
          }}>
          {project?.builder_config?.settings.location && (
            <Box
              sx={{
                position: "absolute",
                left: 0,
                top: 0,
                m: 2,
                zIndex: 2,
                pointerEvents: "all",
              }}>
              <Geocoder
                accessToken={MAPBOX_TOKEN}
                placeholder={t("enter_an_address")}
                tooltip={t("search")}
                onSelect={(result) => {
                  dispatch(setGeocoderResult(result));
                }}
              />
            </Box>
          )}
          {/* Top-Right Controls (Unchanged) */}
          <Box
            sx={{
              position: "absolute",
              right: 0,
              top: 0,
              m: 2,
              zIndex: 2,
              pointerEvents: "all",
            }}>
            {project?.builder_config?.settings.zoom_controls && (
              <Zoom tooltipZoomIn={t("zoom_in")} tooltipZoomOut={t("zoom_out")} />
            )}
            {project?.builder_config?.settings.find_my_location && (
              <UserLocation tooltip={t("find_location")} />
            )}
            {project?.builder_config?.settings.basemap && (
              <BasemapSelectorButton
                // Use `open` state derived from drawerView for visual indication (optional)
                open={drawerView === "basemapSelector"}
                // Use specific handler to switch view
                setOpen={handleOpenBasemapSelector}
              />
            )}
          </Box>

          {/* Bottom-Left Controls */}
          <Box
            sx={{
              position: "absolute",
              left: 0,
              zIndex: 2,
              bottom: 0,
              pointerEvents: "all",
            }}>
            {project?.builder_config?.settings.scalebar && (
              <Box sx={{ m: 2 }}>
                <Scalebar />
              </Box>
            )}
            <AttributionControl />
          </Box>
        </Box>

        {/* Drawer */}
        <SwipeableDrawer
          anchor="bottom"
          open={open}
          hideBackdrop={true}
          ModalProps={{
            sx: {
              pointerEvents: "none", // Allow interactions with map behind
              "& .MuiDialog-container": { pointerEvents: "none" },
              "& .MuiPaper-root": { pointerEvents: "auto" }, // Drawer itself is interactive
            },
            keepMounted: true, // Keep content mounted for transitions/state
          }}
          onClose={toggleDrawer(false)}
          onOpen={toggleDrawer(true)}
          swipeAreaWidth={drawerBleeding}
          disableSwipeToOpen={false}
          disableDiscovery={false}>
          {/* Puller Area */}
          <Box
            sx={{
              position: "absolute",
              top: -drawerBleeding,
              borderTopLeftRadius: 8,
              borderTopRightRadius: 8,
              visibility: "visible",
              right: 0,
              left: 0,
              height: drawerBleeding,
              cursor: "grab",
              backgroundColor: theme.palette.background.paper,
              boxShadow: "0 -3px 6px -2px rgba(0,0,0,0.15)",
            }}>
            <Puller />
            {/* Dynamic Header Content */}
            <Box sx={{ pt: currentHeaderInfo ? 1 : 0 }}>
              {currentHeaderInfo && (
                <InfoHeader
                  title={currentHeaderInfo.title}
                  iconName={currentHeaderInfo.icon}
                  onClose={handleCloseView} // Use unified close handler
                />
              )}
              {/* Pagination container, visibility controlled by GlobalSwiperStyles */}
              <div id="swiper-pagination-container" />
            </Box>
          </Box>

          {/* Content Area */}
          <Box
            sx={{
              height: "100%",
              overflow: "auto", // Hide overflow, specific content scrolls internally
              borderTopLeftRadius: 8,
              borderTopRightRadius: 8,
              backgroundColor: theme.palette.background.paper,
            }}
            // Attach touch move handler to prevent drawer swipe when scrolling content
            onTouchMove={handleContentTouchMove}>
            {/* Conditional Rendering based on drawerView */}
            {drawerView === "layerInfo" && layerInfo && (
              <LayerInfo
                // Use key to force re-mount when feature changes, ensuring fresh state
                key={highlightedFeature?.id ?? layerInfo.title ?? v4()}
                {...layerInfo}
                detailsView={layerInfoDetailsView}
                setDetailsView={setLayerInfoDetailsView}
              />
            )}

            {drawerView === "basemapSelector" && (
              <BaseMapSelectorList
                styles={translatedBaseMaps}
                active={activeBasemap.value}
                basemapChange={async (basemap) => {
                  await onProjectUpdate?.("basemap", basemap);
                  // Optionally close drawer or switch back to default view after selection
                  // setOpen(false);
                  // setDrawerView('default');
                }}
                // Close drawer on item click for immediate map feedback
                onClick={() => setOpen(false)}
                hideHeader // Header is now in the puller area
              />
            )}

            {drawerView === "default" && project?.builder_config?.interface && (
              <Swiper
                pagination={{
                  clickable: true,
                  el: "#swiper-pagination-container", // Target the div in puller area
                }}
                modules={[Pagination]}
                style={{ height: "100%", width: "100%" }}
                // Ensure Swiper doesn't conflict with drawer swipe
                touchStartPreventDefault={false} // Let drawer handle swipe if needed
              >
                {project.builder_config.interface.map((item, index) => {
                  if (item.type === "panel" && item?.widgets?.length > 0) {
                    return (
                      <SwiperSlide key={index} style={{ height: "100%", boxSizing: "border-box" }}>
                        {/* Scrollable container for widgets */}
                        <Box
                          ref={scrollableContentRef}
                          sx={{
                            display: "flex",
                            flexDirection: "column",
                            height: "100%",
                            width: "100%",
                            overflowY: "auto", // Enable vertical scrolling for widgets
                            overflowX: "hidden",
                            boxSizing: "border-box",
                            pb: 4, // Padding at the bottom
                            touchAction: "pan-y", // Hint for browser scroll handling
                          }}
                          // No touch handlers needed here anymore, handled by parent Box
                        >
                          {item?.widgets?.map((widget) => (
                            <Box key={widget.id} sx={{ p: 2, width: "100%", flexShrink: 0 }}>
                              <WidgetWrapper widget={widget} projectLayers={projectLayers} viewOnly />
                            </Box>
                          ))}
                        </Box>
                      </SwiperSlide>
                    );
                  }
                  return null;
                })}
              </Swiper>
            )}
          </Box>
        </SwipeableDrawer>
      </Box>
    </>
  );
};

export default MobileProjectLayout;
