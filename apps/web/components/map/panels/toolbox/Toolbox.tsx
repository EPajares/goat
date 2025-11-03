import {
  Box,
  List,
  ListItemButton,
  ListItemSecondaryAction,
  ListItemText,
  Typography,
  useTheme,
} from "@mui/material";
import React, { useState } from "react";

import { ICON_NAME, Icon } from "@p4b/ui/components/Icon";

import { useTranslation } from "@/i18n/client";

import {
  setActiveRightPanel,
  setIsMapGetInfoActive,
  setMapCursor,
  setMaskLayer,
  setToolboxStartingPoints,
} from "@/lib/store/map/slice";

import { useAppDispatch } from "@/hooks/store/ContextHooks";

import AccordionWrapper from "@/components/common/AccordionWrapper";
import Container from "@/components/map/panels/Container";
import Aggregate from "@/components/map/panels/toolbox/tools/aggregate/Aggregate";
import Buffer from "@/components/map/panels/toolbox/tools/buffer/Buffer";
import CatchmentArea from "@/components/map/panels/toolbox/tools/catchment-area/CatchmentArea";
import HeatmapClosestAverage from "@/components/map/panels/toolbox/tools/heatmap-closest-average/HeatmapClosestAverage";
import HeatmapConnectivity from "@/components/map/panels/toolbox/tools/heatmap-connectivity/HeatmapConnectivity";
import HeatmapGravity from "@/components/map/panels/toolbox/tools/heatmap-gravity/HeatmapGravity";
import Join from "@/components/map/panels/toolbox/tools/join/Join";
import NearbyStations from "@/components/map/panels/toolbox/tools/nearby-stations/NearbyStations";
import OevGueteklassen from "@/components/map/panels/toolbox/tools/oev-gueteklassen/OevGueteklassen";
import OriginDestination from "@/components/map/panels/toolbox/tools/origin-destination/OriginDestination";
import TripCount from "@/components/map/panels/toolbox/tools/trip-count/TripCount";

const Tabs = ({ tab, handleChange }) => {
  const { t } = useTranslation("common");

  return (
    <List dense sx={{ pt: 0 }}>
      {tab.children.map((childTab) => (
        <ListItemButton key={childTab} onClick={() => handleChange(childTab)}>
          <ListItemText primary={t(`${childTab}`)} />
          <ListItemSecondaryAction>
            <Icon iconName={ICON_NAME.CHEVRON_RIGHT} sx={{ fontSize: "12px" }} />
          </ListItemSecondaryAction>
        </ListItemButton>
      ))}
    </List>
  );
};

const Toolbox = () => {
  const [value, setValue] = useState<string | undefined>(undefined);

  const { t } = useTranslation("common");
  const theme = useTheme();
  const dispatch = useAppDispatch();

  const handleOnBack = () => {
    setValue(undefined);
    dispatch(setMaskLayer(undefined));
    dispatch(setToolboxStartingPoints(undefined));
    dispatch(setIsMapGetInfoActive(true));
    dispatch(setMapCursor(undefined));
  };

  const handleOnClose = () => {
    setValue(undefined);
    dispatch(setActiveRightPanel(undefined));
  };

  const main_accordions = [
    {
      name: t("accessibility_indicators"),
      value: "accessibility_indicators",
      children: [
        "catchment_area",
        "heatmap_connectivity",
        "heatmap_closest_average",
        "heatmap_gravity",
        "oev_guteklassen",
        "trip_count",
        "nearby_stations",
      ],
      icon: ICON_NAME.BULLSEYE,
    },
    {
      name: t("data_management"),
      value: "data_management",
      children: ["join"],
      icon: ICON_NAME.TABLE,
    },
    {
      name: t("geoanalysis"),
      value: "geoanalysis",
      children: ["aggregate", "aggregate_polygon", "origin_destination"],
      icon: ICON_NAME.CHART,
    },
    {
      name: t("geoprocessing"),
      value: "geoprocessing",
      children: ["buffer"],
      icon: ICON_NAME.SETTINGS,
    },
  ];

  const tabs = {
    join: {
      name: t("join"),
      value: "join",
      element: <Join onBack={handleOnBack} onClose={handleOnClose} />,
    },
    heatmap_connectivity: {
      name: t("heatmap_connectivity"),
      value: "heatmap_connectivity",
      element: <HeatmapConnectivity onBack={handleOnBack} onClose={handleOnClose} />,
    },
    heatmap_closest_average: {
      name: t("heatmap_closest_average"),
      value: "heatmap_closest_average",
      element: <HeatmapClosestAverage onBack={handleOnBack} onClose={handleOnClose} />,
    },
    heatmap_gravity: {
      name: t("heatmap_gravity"),
      value: "heatmap_gravity",
      element: <HeatmapGravity onBack={handleOnBack} onClose={handleOnClose} />,
    },

    aggregate: {
      name: t("aggregate_points"),
      value: "aggregate",
      element: <Aggregate onBack={handleOnBack} onClose={handleOnClose} type="point" />,
    },
    aggregate_polygon: {
      name: t("aggregate_polygons"),
      value: "aggregate_polygon",
      element: <Aggregate onBack={handleOnBack} onClose={handleOnClose} type="polygon" />,
    },
    catchment_area: {
      name: t("catchment_area"),
      value: "catchment_area",
      element: <CatchmentArea onBack={handleOnBack} onClose={handleOnClose} />,
    },
    buffer: {
      name: t("buffer"),
      value: "buffer",
      element: <Buffer onBack={handleOnBack} onClose={handleOnClose} />,
    },
    oev_guteklassen: {
      name: t("oev_guteklassen"),
      value: "oev_guteklassen",
      element: <OevGueteklassen onBack={handleOnBack} onClose={handleOnClose} />,
    },
    trip_count: {
      name: t("trip_count"),
      value: "trip_count",
      element: <TripCount onBack={handleOnBack} onClose={handleOnClose} />,
    },
    nearby_stations: {
      name: t("nearby_stations"),
      value: "nearby_stations",
      element: <NearbyStations onBack={handleOnBack} onClose={handleOnClose} />,
    },
    origin_destination: {
      name: t("origin_destination"),
      value: "origin_destination",
      element: <OriginDestination onBack={handleOnBack} onClose={handleOnClose} />,
    },
  };

  const handleChange = (newValue: string) => {
    setValue(newValue);
  };
  return (
    <Box sx={{ height: "100%" }}>
      {!value && (
        <Container
          title={t("tools")}
          disablePadding={true}
          close={() => dispatch(setActiveRightPanel(undefined))}
          body={
            <>
              {!value &&
                main_accordions.map((tab) => (
                  <AccordionWrapper
                    key={tab.name}
                    header={
                      <Typography
                        variant="body2"
                        fontWeight="bold"
                        sx={{
                          flexShrink: 0,
                          display: "flex",
                          gap: theme.spacing(2),
                          alignItems: "center",
                        }}>
                        <Icon iconName={tab.icon} sx={{ fontSize: "16px" }} htmlColor="inherit" />
                        {tab.name}
                      </Typography>
                    }
                    body={<Tabs tab={tab} handleChange={handleChange} />}
                  />
                ))}
            </>
          }
        />
      )}

      {value ? <>{tabs[value].element}</> : null}
    </Box>
  );
};

export default Toolbox;
