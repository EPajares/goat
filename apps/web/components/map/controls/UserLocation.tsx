import GpsFixedIcon from "@mui/icons-material/GpsFixed";
import GpsOffIcon from "@mui/icons-material/GpsOff";
import { CircularProgress, Fab, Stack, Tooltip, useTheme } from "@mui/material";
import React, { useCallback, useEffect, useRef, useState } from "react";
import { useMap } from "react-map-gl/maplibre";
import { toast } from "react-toastify";
import useSWR from "swr";

import { setUserLocation } from "@/lib/store/map/slice";

import { useAppDispatch, useAppSelector } from "@/hooks/store/ContextHooks";

type UserLocationProps = {
  tooltip?: string;
};

const USER_LOCATION_ZOOM = 12;
const ERROR_TOAST_ID = "location-error-toast";

const fetchLocation = () =>
  new Promise<GeolocationPosition>((resolve, reject) => {
    navigator.geolocation.getCurrentPosition(resolve, reject);
  });

const fetchPermission = async () => {
  const permission = await navigator.permissions.query({ name: "geolocation" });
  return permission;
};

export function UserLocation(props: UserLocationProps) {
  const theme = useTheme();
  const { map } = useMap();
  const errorToastShown = useRef(false);
  const dispatch = useAppDispatch();
  const [locationRequested, setLocationRequested] = useState(false);
  const locationActive = useAppSelector((state) => state.map?.userLocation?.active);

  const { data: permission, mutate: mutatePermission } = useSWR("locationPermission", fetchPermission, {
    revalidateOnFocus: false,
    shouldRetryOnError: false,
  });

  const {
    data: location,
    error,
    mutate: requestLocation,
    isValidating,
  } = useSWR("userLocation", fetchLocation, {
    revalidateOnFocus: false,
    shouldRetryOnError: false,
  });

  const findLocation = useCallback(() => {
    if (locationActive && !error) {
      // turn off location
      dispatch(
        setUserLocation({
          active: false,
          position: undefined,
        })
      );
      setLocationRequested(false);
      // Additional logic to handle location off can be added here
    } else {
      // turn on location
      if (error) {
        if (!toast.isActive(ERROR_TOAST_ID)) {
          toast.error(
            "Location access is currently disabled. Please review your location permissions and try again.",
            {
              toastId: ERROR_TOAST_ID,
              onClose: () => {
                errorToastShown.current = false;
              },
            }
          );
          errorToastShown.current = true;
        }
      } else {
        requestLocation();
        setLocationRequested(true);
      }
    }
  }, [locationActive, error, dispatch, requestLocation]);

  useEffect(() => {
    if (location && locationRequested && map) {
      map.flyTo({
        center: [location.coords.longitude, location.coords.latitude],
        zoom: USER_LOCATION_ZOOM,
      });
      dispatch(
        setUserLocation({
          active: true,
          position: location,
        })
      );
    }
  }, [dispatch, location, locationRequested, map]);

  useEffect(() => {
    const handlePermissionChange = () => {
      setLocationRequested(false);
      dispatch(
        setUserLocation({
          active: false,
          position: undefined,
        })
      );
      mutatePermission();
      requestLocation();
      errorToastShown.current = false;
      toast.dismiss(ERROR_TOAST_ID);
    };

    if (permission) {
      permission.addEventListener("change", handlePermissionChange);
    }

    return () => {
      if (permission) {
        permission.removeEventListener("change", handlePermissionChange);
      }
    };
  }, [permission, mutatePermission, requestLocation, dispatch]);

  const IconComponent = error ? GpsOffIcon : GpsFixedIcon;

  return (
    <>
      {map && (
        <Stack
          direction="column"
          sx={{
            alignItems: "flex-end",
            my: 1,
          }}>
          <Tooltip title={props.tooltip || "Find location"} arrow placement="left">
            <Fab
              onClick={findLocation}
              size="small"
              sx={{
                pointerEvents: "all",
                backgroundColor: theme.palette.background.paper,
                marginTop: theme.spacing(1),
                marginBottom: theme.spacing(1),
                color: theme.palette.text.secondary,
                "&:hover": {
                  backgroundColor: theme.palette.background.default,
                },
              }}>
              {locationRequested && isValidating ? (
                <CircularProgress size={20} />
              ) : (
                <IconComponent
                  fontSize="small"
                  sx={{ color: locationActive ? theme.palette.primary.main : "inherit" }}
                />
              )}
            </Fab>
          </Tooltip>
        </Stack>
      )}
    </>
  );
}
