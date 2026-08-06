import { Tooltip } from "@mui/material";
import { useTranslation } from "react-i18next";
import { Marker } from "react-map-gl/maplibre";

import { ICON_NAME, Icon } from "@p4b/ui/components/Icon";

import { setGeocoderResult } from "@/lib/store/map/slice";

import { useAppDispatch, useAppSelector } from "@/hooks/store/ContextHooks";

const GeocoderLayer = () => {
  const { t } = useTranslation("common");
  const dispatch = useAppDispatch();
  const selected = useAppSelector((state) => state.map.geocoderResult);

  if (!selected?.feature?.center) return null;

  return (
    <Marker
      longitude={selected.feature.center[0]}
      latitude={selected.feature.center[1]}
      draggable={false}
      anchor="bottom"
      // The search input's clear button also removes the pin, but it is out of
      // reach once the mobile overlay closes — so the pin dismisses itself.
      onClick={() => dispatch(setGeocoderResult(null))}>
      <Tooltip title={t("remove_pin")} arrow>
        <Icon
          iconName={ICON_NAME.LOCATION}
          htmlColor="red"
          fontSize="large"
          role="button"
          aria-label={t("remove_pin")}
          sx={{ cursor: "pointer" }}
        />
      </Tooltip>
    </Marker>
  );
};

export default GeocoderLayer;
