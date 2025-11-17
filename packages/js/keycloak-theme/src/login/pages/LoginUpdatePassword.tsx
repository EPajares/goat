import FormControlLabel from "@mui/material/FormControlLabel";
import type { PageProps } from "keycloakify/login/pages/PageProps";

import type { I18n } from "../i18n";
import type { KcContext } from "../kcContext";
import {
  Box,
  Button,
  Checkbox,
  Stack,
  TextField,
  Typography,
  useTheme,
} from "@mui/material";

export default function LoginUpdatePassword(
  props: PageProps<
    Extract<KcContext, { pageId: "login-update-password.ftl" }>,
    I18n
  >,
) {
  const theme = useTheme();
  const { kcContext, i18n, doUseDefaultCss, Template } = props;

  const { msg, msgStr } = i18n;

  const { url, isAppInitiatedAction, username } = kcContext;
  return (
    <Template
      {...{ kcContext, i18n, doUseDefaultCss }}
      headerNode={msg("updatePasswordTitle")}
    >
      <Box
        component="form"
        id="kc-passwd-update-form"
        action={url.loginAction}
        method="post"
      >
        <div style={{ display: "none" }}>
          <TextField
            type="text"
            id="username"
            name="username"
            defaultValue={username}
            disabled={true}
            autoComplete="username"
          />
        </div>

        <div style={{ display: "none" }}>
          <TextField
            type="password"
            id="password"
            name="password"
            autoComplete="current-password"
          />
        </div>
        <Stack spacing={theme.spacing(4)}>
          <TextField
            type="password"
            id="password-new"
            name="password-new"
            aria-label="password-new"
            tabIndex={1}
            label={msg("passwordNew")}
            autoComplete="new-password"
          />

          <TextField
            type="password"
            id="password-confirm"
            name="password-confirm"
            aria-label="password-confirm"
            tabIndex={2}
            label={msg("passwordConfirm")}
            autoComplete="new-password"
          />
        </Stack>

        <div id="kc-form-options">
          {isAppInitiatedAction && (
            <Box
              sx={{
                mt: theme.spacing(2),
                display: "flex",
                alignItems: "center",
                flexWrap: "wrap",
                justifyContent: "space-between",
              }}
            >
              <FormControlLabel
                control={
                  <Checkbox
                    tabIndex={3}
                    id="logout-sessions"
                    name="logout-sessions"
                    defaultChecked={true}
                    color="primary"
                  />
                }
                label={
                  <Typography variant="body2">
                    {msgStr("logoutOtherSessions")}
                  </Typography>
                }
              />
            </Box>
          )}
        </div>

        <Box
          sx={{
            mt: theme.spacing(8),
          }}
          id="kc-form-buttons"
        >
          {isAppInitiatedAction ? (
            <>
              <Button
                fullWidth
                type="submit"
                sx={{
                  mb: theme.spacing(2),
                }}
              >
                {msgStr("doSubmit")}
              </Button>
              <Button fullWidth variant="text" name="cancel-aia" type="submit">
                {msgStr("doCancel")}
              </Button>
            </>
          ) : (
            <Button fullWidth type="submit">
              {msgStr("doSubmit")}
            </Button>
          )}
        </Box>
      </Box>
    </Template>
  );
}
