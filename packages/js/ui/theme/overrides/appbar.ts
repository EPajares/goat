import type { Theme } from "@mui/material/styles";

const AppBar = (theme: Theme) => {
  return {
    MuiAppBar: {
      styleOverrides: {
        colorPrimary: {
          backgroundColor: theme.palette.background.paper
        },
      },
    },
  };
};

export default AppBar;
