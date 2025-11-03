import { Box, ClickAwayListener, Fade, Popper, type PopperProps } from "@mui/material";
import React from "react";

import type { Marker } from "@/lib/validations/layer";

import MarkerGallery from "@/components/map/panels/style/marker/MarkerGallery";

interface MarkerPopperProps {
  open: boolean;
  anchorEl: HTMLElement | null;
  onClose: () => void;
  selectedMarker?: Marker | undefined;
  onSelectMarker: (marker: Marker) => void;
  popperProps?: Partial<PopperProps>; // 🔹 allow any Popper props
}

const MarkerPopper: React.FC<MarkerPopperProps> = ({
  open,
  anchorEl,
  onClose,
  selectedMarker,
  onSelectMarker,
  popperProps,
}) => {
  return (
    <Popper
      open={open}
      anchorEl={anchorEl}
      transition
      placement="left"
      modifiers={[
        {
          name: "offset",
          options: { offset: [0, 50] },
        },
      ]}
      sx={{ zIndex: 1000 }}
      {...popperProps} // 🔹 allow overwriting placement, modifiers, etc.
    >
      {({ TransitionProps }) => (
        <Fade {...TransitionProps}>
          <Box
            sx={{
              bgcolor: "background.paper",
              borderRadius: 1,
              width: "370px",
              boxShadow: "0px 0px 10px 0px rgba(58, 53, 65, 0.1)",
              overflowY: "auto",
            }}>
            <ClickAwayListener onClickAway={onClose}>
              <Box>
                <MarkerGallery selectedMarker={selectedMarker} onSelectMarker={onSelectMarker} />
              </Box>
            </ClickAwayListener>
          </Box>
        </Fade>
      )}
    </Popper>
  );
};

export default MarkerPopper;
