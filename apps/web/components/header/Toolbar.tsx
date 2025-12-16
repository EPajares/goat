"use client";

import { AppBar, Box, Divider, IconButton, Toolbar as MUIToolbar, Stack, useTheme } from "@mui/material";
import React from "react";

import { ICON_NAME, Icon } from "@p4b/ui/components/Icon";

export type MapToolbarProps = {
  LeftToolbarChild?: React.ReactNode;
  CenterToolbarChild?: React.ReactNode;
  RightToolbarChild?: React.ReactNode;
  height: number;
  showHambugerMenu?: boolean;
  onMenuIconClick?: () => void;
};

export function Toolbar(props: MapToolbarProps) {
  const {
    LeftToolbarChild,
    CenterToolbarChild,
    RightToolbarChild,
    height,
    showHambugerMenu,
    onMenuIconClick,
  } = props;

  const theme = useTheme();

  return (
    <AppBar
      position="relative"
      elevation={0}
      color="primary"
      sx={{
        zIndex: (theme) => theme.zIndex.drawer + 2,
        borderBottom: "1px solid rgba(58, 53, 65, 0.12)",
      }}>
      <MUIToolbar
        variant="dense"
        sx={{
          minHeight: height,
          height: height,
          boxShadow: "0px 0px 10px 0px rgba(58, 53, 65, 0.1)",
        }}>
        {showHambugerMenu && (
          <>
            <IconButton onClick={onMenuIconClick}>
              <Icon iconName={ICON_NAME.HAMBURGER_MENU} fontSize="inherit" />
            </IconButton>

            <Divider orientation="vertical" flexItem sx={{ ml: 2, mr: 3 }} />
          </>
        )}

        <Stack
          direction="row"
          alignItems="center"
          sx={{
            gap: theme.spacing(2),
          }}>
          {LeftToolbarChild}
        </Stack>
        <Box sx={{ flexGrow: 1 }} />

        {CenterToolbarChild && (
          <Stack
            direction="row"
            alignItems="center"
            justifyContent="center"
            sx={{
              position: "absolute",
              left: "50%",
              transform: "translateX(-50%)",
            }}>
            {CenterToolbarChild}
          </Stack>
        )}

        <Box sx={{ flexGrow: 1 }} />

        {RightToolbarChild}
      </MUIToolbar>
    </AppBar>
  );
}
