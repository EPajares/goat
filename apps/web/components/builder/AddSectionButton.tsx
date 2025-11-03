import type { FabProps } from "@mui/material";
import { Fab } from "@mui/material";
import { styled } from "@mui/material/styles";
import { useState } from "react";

import { ICON_NAME, Icon } from "@p4b/ui/components/Icon";

interface CustomFabProps extends FabProps {
  position?: "top" | "bottom" | "left" | "right";
  isHovered?: boolean;
}

interface CustomContainerProps {
  position?: "top" | "bottom" | "left" | "right";
  isHovered?: boolean;
}

interface CustomPanelProps {
  position?: "top" | "bottom" | "left" | "right";
  isHovered?: boolean;
}

interface AddSectionButtonProps {
  position?: "top" | "bottom" | "left" | "right";
  onClick?: () => void;
}

// Prevent forwarding of custom props (isHovered and position) to the DOM element.
const Container = styled("div", {
  shouldForwardProp: (prop) => prop !== "isHovered" && prop !== "position",
})<CustomContainerProps>(({ position }) => ({
  display: "flex",
  position: "absolute",
  justifyContent: "center",
  alignItems: "center",
  padding: "10px",
  ...(position === "top" && { top: "20px", width: "100%" }),
  ...(position === "bottom" && { bottom: "20px", width: "100%" }),
  ...(position === "left" && { left: "20px", height: "100%" }),
  ...(position === "right" && { right: "20px", height: "100%" }),
}));

const Panel = styled("div", {
  shouldForwardProp: (prop) => prop !== "isHovered" && prop !== "position",
})<CustomPanelProps>(({ position, isHovered }) => ({
  backdropFilter: "blur(10px)",
  backgroundColor: `hsla(0, 0%, 100%, 0.3)`,
  position: "absolute",
  transition: "all .3s cubic-bezier(.19,1,.22,1)",
  borderRadius: "8px",
  ...(position === "top" && {
    width: isHovered ? "calc(100% - 20px)" : "8px",
    height: isHovered ? "300px" : "8px",
    top: "-10px",
  }),
  ...(position === "bottom" && {
    width: isHovered ? "calc(100% - 20px)" : "8px",
    height: isHovered ? "300px" : "8px",
    bottom: "-10px",
  }),
  ...(position === "left" && {
    width: isHovered ? "300px" : "8px",
    height: isHovered ? "calc(100% - 20px)" : "8px",
    left: "-10px",
  }),
  ...(position === "right" && {
    width: isHovered ? "300px" : "8px",
    height: isHovered ? "calc(100% - 20px)" : "8px",
    right: "-10px",
  }),
}));

const StyledFab = styled(Fab, {
  shouldForwardProp: (prop) => prop !== "isHovered" && prop !== "position",
})<CustomFabProps>(({ theme, position }) => ({
  backgroundColor: `hsla(0, 0%, 100%, 0.3)`,

  color: theme.palette.primary.main,
  transition: "all .3s cubic-bezier(.19,1,.22,1)",
  pointerEvents: "all",
  backdropFilter: "blur(10px)",
  position: "absolute",
  borderRadius: "50%",
  "&:hover": {
    backdropFilter: "none",
    backgroundColor: "transparent",
    boxShadow: "none",
    ...(position === "top" && { transform: "scale(1.3) translateY(0.25rem)" }),
    ...(position === "bottom" && { transform: "scale(1.3) translateY(-0.25rem)" }),
    ...(position === "left" && { transform: "scale(1.3) translateX(0.25rem)" }),
    ...(position === "right" && { transform: "scale(1.3) translateX(-0.25rem)" }),
  },
}));

const AddSectionButton = ({ position = "top", onClick }: AddSectionButtonProps) => {
  const [isHovered, setIsHovered] = useState(false);

  const handleMouseEnter = () => setIsHovered(true);
  const handleMouseLeave = () => setIsHovered(false);

  return (
    <Container position={position} isHovered={isHovered}>
      <StyledFab
        position={position}
        isHovered={isHovered}
        onClick={onClick}
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
        size="small"
        aria-label="add-panel">
        <Icon iconName={ICON_NAME.PLUS} htmlColor="inherit" fontSize="small" />
      </StyledFab>
      <Panel position={position} isHovered={isHovered} />
    </Container>
  );
};

export default AddSectionButton;
