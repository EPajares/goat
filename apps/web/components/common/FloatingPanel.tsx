import { Stack, type SxProps, type Theme, useTheme } from "@mui/material";
import { alpha } from "@mui/material";

interface FloatingPanelProps {
  children: React.ReactNode;
  sx?: SxProps<Theme>;
  width?: number;
}

export const FloatingPanel = ({ children, sx, width = 300 }: FloatingPanelProps) => {
  const theme = useTheme();
  return (
    <Stack
      direction="column"
      sx={[
        {
          direction: "ltr",
          width: `${width}px`,
          minHeight: "400px",
          height: "auto",
          borderRadius: "1rem",
          backgroundColor: alpha(theme.palette.background.paper, 0.9),
          boxShadow: `rgba(0, 0, 0, 0.2) 0px 0px 10px`,
          backdropFilter: "blur(10px)",
          pointerEvents: "all",
          overflow: "hidden",
        },
        ...(Array.isArray(sx) ? sx : [sx]),
      ]}>
      {children}
    </Stack>
  );
};
