import { Box, Divider, IconButton, Paper, Stack, Typography, useTheme } from "@mui/material";
import React from "react";

import { ICON_NAME, Icon } from "@p4b/ui/components/Icon";

import type { MapSidebarItem } from "@/types/map/sidebar";

interface ContainerProps {
  header?: React.ReactNode;
  title?: string;
  direction?: "left" | "right";
  body?: React.ReactNode;
  action?: React.ReactNode;
  close?: (item: MapSidebarItem | undefined) => void;
  disablePadding?: boolean;
  backgroundColor?: string;
  disableClose?: boolean;
}

export default function Container(props: ContainerProps) {
  const { header, body, action, close, title, backgroundColor, disableClose } = props;

  const theme = useTheme();

  return (
    <Stack
      sx={{
        backgroundColor: backgroundColor || theme.palette.background.default,
        height: "100%",
      }}>
      {(header || title) && (
        <>
          <Stack
            sx={{
              paddingTop: theme.spacing(2),
              paddingLeft: theme.spacing(3),
              paddingRight: theme.spacing(3),
              justifyContent: "space-between",
              alignItems: "center",
            }}
            direction="row">
            {header ? (
              <Box
                sx={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  gap: "20px",
                  width: "100%",
                }}>
                {header}
                {disableClose !== true && close && (
                  <IconButton onClick={() => close(undefined)}>
                    <Icon iconName={ICON_NAME.CLOSE} fontSize="small" />
                  </IconButton>
                )}
              </Box>
            ) : (
              <Box
                sx={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  gap: "20px",
                  width: "100%",
                }}>
                <Typography
                  variant="body1"
                  fontWeight="bold"
                  sx={{
                    display: "flex",
                  }}>
                  {title}
                </Typography>
                {disableClose !== true && close && (
                  <IconButton onClick={() => close(undefined)}>
                    <Icon iconName={ICON_NAME.CLOSE} fontSize="small" />
                  </IconButton>
                )}
              </Box>
            )}
          </Stack>
          <Divider />
        </>
      )}
      {body && (
        <Stack
          direction="column"
          sx={{
            pt: 2,
            pb: 7,
            ...(!props.disablePadding && {
              px: 3,
            }),
            overflowY: "auto",
            height: "100%",
            "&::-webkit-scrollbar": {
              width: "6px",
            },
            "&::-webkit-scrollbar-thumb": {
              background: "#2836484D",
              borderRadius: "3px",
              "&:hover": {
                background: "#28364880",
              },
            },
          }}>
          {body}
        </Stack>
      )}
      {action && (
        <Paper
          sx={{
            borderRadius: "0",
            boxShadow: "0px -5px 10px -5px rgba(58, 53, 65, 0.1)",
          }}
          elevation={6}>
          <Stack
            direction="row"
            sx={{
              paddingTop: theme.spacing(4),
              paddingBottom: theme.spacing(4),
              paddingLeft: theme.spacing(3),
              paddingRight: theme.spacing(3),
              overflowY: "auto",
              scrollbarGutter: "stable both-edges",
              "&::-webkit-scrollbar": {
                width: "6px",
              },
              "&::-webkit-scrollbar-thumb": {
                background: "#2836484D",
                borderRadius: "3px",
                "&:hover": {
                  background: "#28364880",
                },
              },
            }}>
            {action}
          </Stack>
        </Paper>
      )}
    </Stack>
  );
}
