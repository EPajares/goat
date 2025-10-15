import type { PageProps } from "keycloakify/login/pages/PageProps";

import type { I18n } from "../i18n";
import type { KcContext } from "../kcContext";
import { Box, Button, Stack, TextField, useTheme } from "@mui/material";

export default function LoginUpdateProfile(
  props: PageProps<
    Extract<KcContext, { pageId: "login-update-profile.ftl" }>,
    I18n
  >,
) {
  const theme = useTheme();

  const { kcContext, i18n, doUseDefaultCss, Template, classes } = props;

  const { msg, msgStr } = i18n;

  const { url, user, messagesPerField, isAppInitiatedAction } = kcContext;

  return (
    <Template
      {...{ kcContext, i18n, doUseDefaultCss, classes }}
      headerNode={msg("loginProfileTitle")}
    >
      <Box
        component="form"
        id="kc-update-profile-form"
        action={url.loginAction}
        method="post"
      >
        <Stack spacing={theme.spacing(4)}>
          {user.editUsernameAllowed && (
            <TextField
              error={messagesPerField.existsError("username")}
              fullWidth
              type="text"
              id="username"
              name="username"
              defaultValue={user.username ?? ""}
              label={msg("username")}
              helperText={
                messagesPerField.existsError("username") &&
                messagesPerField.get("username")
              }
            />
          )}

          <TextField
            error={messagesPerField.existsError("email")}
            fullWidth
            type="text"
            id="email"
            name="email"
            defaultValue={user.email ?? ""}
            label={msg("email")}
            helperText={
              messagesPerField.existsError("email") &&
              messagesPerField.get("email")
            }
          />

          <TextField
            error={messagesPerField.existsError("firstName")}
            fullWidth
            type="text"
            id="firstName"
            name="firstName"
            defaultValue={user.firstName ?? ""}
            label={msg("firstName")}
            helperText={
              messagesPerField.existsError("firstName") &&
              messagesPerField.get("firstName")
            }
          />

          <TextField
            error={messagesPerField.existsError("lastName")}
            fullWidth
            type="text"
            id="lastName"
            name="lastName"
            defaultValue={user.lastName ?? ""}
            label={msg("lastName")}
            helperText={
              messagesPerField.existsError("lastName") &&
              messagesPerField.get("lastName")
            }
          />
        </Stack>

        <Box
          id="kc-form-buttons"
          sx={{
            mt: theme.spacing(8),
          }}
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
