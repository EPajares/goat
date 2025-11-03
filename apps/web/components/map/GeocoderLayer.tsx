import { Marker } from "react-map-gl/maplibre";

import { ICON_NAME, Icon } from "@p4b/ui/components/Icon";

import { useAppSelector } from "@/hooks/store/ContextHooks";

const GeocoderLayer = () => {
  const selected = useAppSelector((state) => state.map.geocoderResult);

  if (!selected?.feature?.center) return null;

  return (
    <Marker
      longitude={selected.feature.center[0]}
      latitude={selected.feature.center[1]}
      draggable={false}
      anchor="bottom">
      <Icon iconName={ICON_NAME.LOCATION} htmlColor="red" fontSize="large" />
    </Marker>
  );
};

export default GeocoderLayer;
