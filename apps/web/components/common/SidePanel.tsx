"use client";

import type { SxProps, Theme } from "@mui/material";
import { Box, Divider, Stack, Tab, Tabs, Typography } from "@mui/material";
import { styled } from "@mui/material/styles";
import React from "react";

export const SIDE_PANEL_WIDTH = 300;

export const SidePanelContainer = styled(Box)(({ theme }) => ({
  backgroundColor: theme.palette.background.default,
}));

export const SidePanelStack = styled(Stack)({
  width: `${SIDE_PANEL_WIDTH}px`,
  height: "calc(100% - 40px)",
});

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
  id?: string;
}

export const SidePanelTabPanel: React.FC<TabPanelProps> = ({ children, value, index, id = "side-panel" }) => {
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`${id}-tabpanel-${index}`}
      style={{ height: "100%", overflowY: "auto" }}
      aria-labelledby={`${id}-tab-${index}`}>
      {value === index && <>{children}</>}
    </div>
  );
};

interface SidePanelTabsProps {
  value: number;
  onChange: (event: React.SyntheticEvent, newValue: number) => void;
  tabs: Array<{ label: string; id?: string }>;
  ariaLabel?: string;
}

export const SidePanelTabs: React.FC<SidePanelTabsProps> = ({
  value,
  onChange,
  tabs,
  ariaLabel = "side panel tabs",
}) => {
  return (
    <>
      <Tabs
        sx={{ minHeight: "40px" }}
        value={value}
        onChange={onChange}
        aria-label={ariaLabel}
        variant="fullWidth">
        {tabs.map((tab, index) => (
          <Tab
            key={tab.id || index}
            sx={{ minHeight: "40px", height: "40px" }}
            label={
              <Typography variant="body2" fontWeight="bold" sx={{ ml: 2 }} color="inherit">
                {tab.label}
              </Typography>
            }
            id={`${tab.id || "tab"}-${index}`}
            aria-controls={`${tab.id || "tabpanel"}-${index}`}
          />
        ))}
      </Tabs>
      <Divider sx={{ mt: 0 }} />
    </>
  );
};

interface SidePanelProps {
  children: React.ReactNode;
  width?: number;
  sx?: SxProps<Theme>;
}

/**
 * A reusable side panel component that matches the builder's styling.
 * Use with SidePanelTabs and SidePanelTabPanel for tabbed content.
 */
const SidePanel: React.FC<SidePanelProps> = ({ children, width = SIDE_PANEL_WIDTH, sx }) => {
  return (
    <SidePanelContainer sx={sx}>
      <Stack
        sx={{
          width: `${width}px`,
          height: "100%",
        }}>
        {children}
      </Stack>
    </SidePanelContainer>
  );
};

export default SidePanel;
