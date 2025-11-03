import { Box, Typography, debounce } from "@mui/material";
import { styled } from "@mui/material/styles";
import React, { useCallback, useEffect, useState } from "react";
import { useMap } from "react-map-gl/maplibre";

interface AttributionControlProps {
  compact?: boolean;
  customAttribution?: string | Array<string>;
}

const Container = styled(Box)(({}) => ({
  padding: "0px 4px",
  borderRadius: "2px",
  fontSize: "10px",
  zIndex: 1,
  pointerEvents: "all",
  backgroundColor: "hsla(0,0%,100%,.5)",
}));

const AttributionControl: React.FC<AttributionControlProps> = ({
  customAttribution = [
    '<a href="https://www.plan4better.de/en/goat" target="_blank">Made with GOAT</a>',
    '<a href="https://maplibre.org/" target="_blank">&#169;	MapLibre</a>',
  ],
}) => {
  const [attributions, setAttributions] = useState<string[]>([]);
  const { map } = useMap();

  const updateAttributions = useCallback(() => {
    let attributions: string[] = [];
    if (customAttribution) {
      if (Array.isArray(customAttribution)) {
        attributions = attributions.concat(customAttribution);
      } else {
        attributions.push(customAttribution);
      }
    }
    const sourceCaches = map?.getStyle()?.sources;
    for (const id in sourceCaches) {
      const source = sourceCaches[id];
      if (source["attribution"] && attributions.indexOf(source["attribution"]) < 0) {
        attributions.push(source["attribution"]);
      }
    }
    attributions = attributions.filter((e) => String(e).trim());
    attributions.sort((a, b) => a.length - b.length);
    attributions = attributions.filter((attrib, i) => {
      for (let j = i + 1; j < attributions.length; j++) {
        if (attributions[j].includes(attrib)) {
          return false;
        }
      }
      return true;
    });
    setAttributions(attributions);
  }, [map, customAttribution]);

  // Debounced version of `updateAttributions` using MUI `debounce`
  // eslint-disable-next-line react-hooks/exhaustive-deps
  const debouncedUpdateAttributions = useCallback(debounce(updateAttributions, 200), [updateAttributions]);

  useEffect(() => {
    if (!map) return;

    // Attach debounced update function to map events
    map.on("styledata", debouncedUpdateAttributions);
    map.on("sourcedata", debouncedUpdateAttributions);
    map.on("terrain", debouncedUpdateAttributions);

    // Initial attribution update
    updateAttributions();

    return () => {
      map.off("styledata", debouncedUpdateAttributions);
      map.off("sourcedata", debouncedUpdateAttributions);
      map.off("terrain", debouncedUpdateAttributions);

      // Clear debounced function when component unmounts
      debouncedUpdateAttributions.clear();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [map]);

  return (
    <Container>
      {attributions.length > 0 ? (
        <Typography
          sx={{
            color: "rgba(0,0,0,.75)",
            "& a": {
              color: "inherit",
              textDecoration: "none",
              "&:hover": {
                textDecoration: "underline",
              },
            },
          }}
          variant="caption"
          component="div"
          dangerouslySetInnerHTML={{ __html: attributions.join(" | ") }}
        />
      ) : (
        <Typography variant="caption" component="div">
          No attributions available
        </Typography>
      )}
    </Container>
  );
};

export default AttributionControl;
