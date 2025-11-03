import { Layer, Source } from "react-map-gl/maplibre";

import { useAppSelector } from "@/hooks/store/ContextHooks";

type UserLocationLayerProps = {
  beforeId?: string;
};

const UserLocationLayer = (props: UserLocationLayerProps) => {
  const userLocation = useAppSelector((state) => state.map?.userLocation);
  return (
    <>
      {userLocation?.position?.coords && (
        <Source
          type="geojson"
          data={{
            type: "Feature",
            properties: {},
            geometry: {
              type: "Point",
              coordinates: [userLocation.position.coords.longitude, userLocation.position.coords.latitude],
            },
          }}>
          <Layer
            id="user-location-layer"
            type="symbol"
            beforeId={props.beforeId}
            layout={{
              "icon-image": "geolocation-pulsing-dot",
            }}
          />
        </Source>
      )}
    </>
  );
};

export default UserLocationLayer;
