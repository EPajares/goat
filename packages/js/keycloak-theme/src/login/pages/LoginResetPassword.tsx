import { Box, Link, TextField, Typography, useTheme } from "@mui/material";
import type { PageProps } from "keycloakify/login/pages/PageProps";

import { Button } from "@mui/material";
import type { I18n } from "../i18n";
import type { KcContext } from "../kcContext";

export default function LoginResetPassword(
  props: PageProps<
    Extract<KcContext, { pageId: "login-reset-password.ftl" }>,
    I18n
  >,
) {
  const theme = useTheme();
  const { kcContext, i18n, doUseDefaultCss, Template } = props;

  const { url, auth } = kcContext;

  const { msg, msgStr } = i18n;

  return (
    <Template
      {...{ kcContext, i18n, doUseDefaultCss }}
      displayMessage={false}
      headerNode={msg("emailForgotTitle")}
    >
      <Typography
        variant="body1"
        sx={{
          mb: theme.spacing(6),
        }}
      >
        {msg("emailForgotInstruction")}
      </Typography>
      <Box
        component="form"
        id="kc-reset-password-form"
        action={url.loginAction}
        method="post"
      >
        <TextField
          fullWidth
          defaultValue={
            auth !== undefined && auth.showUsername
              ? auth.attemptedUsername
              : undefined
          }
          id="username"
          name="username"
          aria-label="username"
          tabIndex={1}
          autoFocus={true}
          spellCheck={false}
          label={msg("email")}
          autoComplete="off"
        />
        <Box
          sx={{
            mt: theme.spacing(8),
          }}
        >
          <Button
            fullWidth
            type="submit"
            sx={{
              mb: theme.spacing(4),
            }}
          >
            {msgStr("doSubmit")}
          </Button>
          <Link underline="hover" href={url.loginUrl}>
            {msg("backToLogin")}
          </Link>
        </Box>
      </Box>
    </Template>
  );
}
