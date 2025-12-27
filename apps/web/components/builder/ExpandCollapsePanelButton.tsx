import { IconButton } from "@mui/material";
import React, { useMemo } from "react";

import { ICON_NAME, Icon } from "@p4b/ui/components/Icon";

export interface ExpandCollapseButtonProps {
  position: "top" | "bottom" | "left" | "right";
  expanded: boolean;
  onClick: () => void;
  isVisible: boolean;
}

const ExpandCollapseButton: React.FC<ExpandCollapseButtonProps> = ({
  position,
  expanded,
  onClick,
  isVisible,
}) => {
  const iconName = useMemo<ICON_NAME>(() => {
    switch (position) {
      case "left":
        return expanded ? ICON_NAME.CHEVRON_LEFT : ICON_NAME.CHEVRON_RIGHT;
      case "right":
        return expanded ? ICON_NAME.CHEVRON_RIGHT : ICON_NAME.CHEVRON_LEFT;
      case "top":
        return expanded ? ICON_NAME.CHEVRON_UP : ICON_NAME.CHEVRON_DOWN;
      case "bottom":
        return expanded ? ICON_NAME.CHEVRON_DOWN : ICON_NAME.CHEVRON_UP;
    }
  }, [position, expanded]);

  const styles = {
    left: { right: 4, top: "50%", transform: "translateY(-50%)" },
    right: { left: 4, top: "50%", transform: "translateY(-50%)" },
    top: { bottom: 4, left: "50%", transform: "translateX(-50%)" },
    bottom: { top: 4, left: "50%", transform: "translateX(-50%)" },
  };

  return (
    <IconButton
      sx={{
        ...styles[position],
        position: "absolute",
        pointerEvents: isVisible ? "all" : "none",
        transition: "opacity 0.3s, transform 0.3s",
        opacity: isVisible ? 1 : 0,
        zIndex: 10,
      }}
      onClick={(event) => {
        event.stopPropagation();
        onClick();
      }}>
      <Icon
        iconName={iconName}
        style={{
          fontSize: 17,
        }}
        htmlColor="inherit"
      />
    </IconButton>
  );
};

export default ExpandCollapseButton;
