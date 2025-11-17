import type { Theme } from "@mui/material/styles";

const CssBaseline = (theme: Theme) => {
  return {
    MuiCssBaseline: {
      styleOverrides: {
        ":root": {
          "--toastify-color-dark": theme.palette.background.paper,
          "--toastify-color-light": theme.palette.background.paper,
          "--toastify-color-info": theme.palette.info.main,
          "--toastify-color-success": theme.palette.success.main,
          "--toastify-color-warning": theme.palette.warning.main,
          "--toastify-color-error": theme.palette.error.main,
          "--toastify-icon-color-info": theme.palette.info.main,
          "--toastify-icon-color-success": theme.palette.success.main,
          "--toastify-icon-color-warning": theme.palette.warning.main,
          "--toastify-icon-color-error": theme.palette.error.main,
          "--toastify-font-family": "inherit",
          "--toastify-color-progress-light": theme.palette.primary.main,
          "--toastify-color-progress-dark": theme.palette.primary.main,
          "--toastify-color-progress-info": theme.palette.info.main,
          "--toastify-color-progress-success": theme.palette.success.main,
          "--toastify-color-progress-warning": theme.palette.warning.main,
          "--toastify-color-progress-error": theme.palette.error.main,
          "--toastify-text-color-light": theme.palette.text.primary,
          "--toastify-text-color-dark": theme.palette.text.primary,
        },
        html: {
          "& ::-webkit-scrollbar": {
            width: "5px",
            height: "5px",
          },
          "& ::-webkit-scrollbar-track": {
            background: "transparent",
          },
          "& ::-webkit-scrollbar-thumb": {
            backgroundColor:
              theme.palette.mode === "dark"
                ? "#374A62"
                : theme.palette.grey[400],
            borderRadius: "5px",
          },
        },
        body: {
          overflow: "hidden",
          width: "100%",
          height: "100%",
          margin: 0,
          padding: 0,
          position: "fixed",
        },
      },
    },
  };
};

export default CssBaseline;
