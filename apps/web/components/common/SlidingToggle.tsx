import { Box, Typography } from "@mui/material";
import { alpha, styled } from "@mui/material/styles";
import React from "react";

interface Option {
  label: string;
  value: string;
}

interface SlidingToggleProps {
  options: [Option, Option]; // A tuple containing two options
  activeOption: string; // The currently active option
  onToggle: (selected: string) => void; // Callback for when the toggle changes
}

const SwitchContainer = styled(Box)(({ theme }) => ({
  position: "relative",
  display: "flex",
  width: "200px",
  height: "30px",
  backgroundColor: "transparent",
  border: `1px solid ${alpha(theme.palette.primary.main, 0.5)}`,
  borderRadius: "25px",
  overflow: "hidden",
  cursor: "pointer",
}));

const SlidingIndicator = styled(Box)(({ theme }) => ({
  position: "absolute",
  width: "50%",
  height: "100%",
  backgroundColor: theme.palette.primary.main,
  borderRadius: "25px",
  transition: "transform 0.3s ease-in-out",
  zIndex: 1,
}));

const ToggleItem = styled(Box)(({ theme }) => ({
  flex: 1,
  display: "flex",
  justifyContent: "center",
  alignItems: "center",
  zIndex: 2, // Text stays above the sliding indicator
  color: theme.palette.common.white,
}));

const SlidingToggle: React.FC<SlidingToggleProps> = ({ options, activeOption, onToggle }) => {
  const handleSwitchClick = (option: Option) => {
    onToggle(option.value); // Call the onToggle callback
  };

  return (
    <SwitchContainer>
      {/* Sliding Indicator */}
      <SlidingIndicator
        style={{
          transform: activeOption === options[0].value ? "translateX(0)" : "translateX(100%)",
        }}
      />
      {/* Option 1 */}
      <ToggleItem onClick={() => handleSwitchClick(options[0])}>
        <Typography
          color={activeOption === options[0].value ? "inherit" : "primary"}
          variant="body2"
          sx={{ fontWeight: "bold", transition: "color 0.3s ease-in-out" }}>
          {options[0].label}
        </Typography>
      </ToggleItem>
      {/* Option 2 */}
      <ToggleItem onClick={() => handleSwitchClick(options[1])}>
        <Typography
          color={activeOption === options[1].value ? "inherit" : "primary"}
          variant="body2"
          sx={{ fontWeight: "bold", transition: "color 0.3s ease-in-out" }}>
          {options[1].label}
        </Typography>
      </ToggleItem>
    </SwitchContainer>
  );
};

export default SlidingToggle;
