import type { SxProps } from "@mui/material";
import { Box, useTheme } from "@mui/material";
import Grid from "@mui/material/Unstable_Grid2";

export default function AuthLayout({
  children,
  sx,
}: {
  children: React.ReactNode;
  sx?: SxProps;
}) {
  const theme = useTheme();

  return (
    <Box
      component="main"
      sx={{
        display: "flex",
        flex: "1 1 auto",
        ...sx,
      }}
    >
      <Grid
        container
        sx={{
          flex: "1 1 auto",
        }}
      >
        <Grid
          xs={12}
          lg={6}
          sx={{
            height: "100vh",
            display: "flex",
            flexDirection: "column",
            position: "relative",
          }}
        >
          <Box
            component="header"
            sx={{
              left: 0,
              p: 3,
              position: "fixed",
              top: 0,
              width: "100%",
            }}
          >
            <Box
              component="a"
              href="https://www.plan4better.de/"
              target="_blank"
              sx={{
                display: "inline-flex",
                width: 160,
              }}
            >
              <img
                width="100%"
                src={`https://assets.plan4better.de/img/logo/plan4better_${
                  theme.palette.mode === "light" ? "standard" : "white"
                }.svg`}
                alt="Plan4Better Logo"
              />
            </Box>
          </Box>
          <Box
            component="div"
            sx={{
              flex: "1 1 auto",
              display: "flex",
              flexDirection: "column",
              justifyContent: "center",
              alignItems: "center",
            }}
          >
            {children}
          </Box>
        </Grid>
        <Grid
          xs={12}
          lg={6}
          sx={{
            alignItems: "center",
            background:
              "radial-gradient(50% 50% at 50% 50%, rgba(40,54,72,0.8) 0%, rgba(40,54,72,0.9) 100%), url(https://assets.plan4better.de/img/login/artwork_1.png) no-repeat center",
            backgroundSize: "cover",
            display: "flex",
            justifyContent: "center",
            "& img": {
              maxWidth: "100%",
            },
          }}
        >
          <Box sx={{ p: 3, width: 350 }} component="div">
            <img
              width="100%"
              src="https://assets.plan4better.de/img/logo/goat_white.svg"
              alt="Plan4Better Logo"
            />
          </Box>
        </Grid>
      </Grid>
    </Box>
  );
}
