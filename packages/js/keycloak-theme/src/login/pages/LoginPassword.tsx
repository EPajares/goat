import type { PageProps } from "keycloakify/login/pages/PageProps";
import { useConstCallback } from "keycloakify/tools/useConstCallback";
import { useState } from "react";
import type { FormEventHandler } from "react";

import type { I18n } from "../i18n";
import type { KcContext } from "../kcContext";
import { Box, Button, Link, Stack, TextField, useTheme } from "@mui/material";

export default function LoginPassword(
  props: PageProps<Extract<KcContext, { pageId: "login-password.ftl" }>, I18n>,
) {
  const theme = useTheme();
  const { kcContext, i18n, doUseDefaultCss, Template, classes } = props;

  const { realm, url, login } = kcContext;

  const { msg, msgStr } = i18n;

  const [isLoginButtonDisabled, setIsLoginButtonDisabled] = useState(false);

  const onSubmit = useConstCallback<FormEventHandler<HTMLFormElement>>((e) => {
    e.preventDefault();

    setIsLoginButtonDisabled(true);

    const formElement = e.target as HTMLFormElement;

    formElement.submit();
  });

  return (
    <Template
      {...{ kcContext, i18n, doUseDefaultCss, classes }}
      headerNode={msg("doLogIn")}
    >
      <Box
        component="form"
        id="kc-form-login"
        onSubmit={onSubmit}
        action={url.loginAction}
        method="post"
      >
        <Stack spacing={theme.spacing(2)}>
          <TextField
            fullWidth
            tabIndex={2}
            id="password"
            name="password"
            type="password"
            autoFocus={true}
            autoComplete="on"
            defaultValue={login.password ?? ""}
            label={msg("password")}
          />

          {realm.resetPasswordAllowed && (
            <Link href={url.loginResetCredentialsUrl}>
              {msg("doForgotPassword")}
            </Link>
          )}
        </Stack>

        <Button
          tabIndex={4}
          name="login"
          id="kc-login"
          disabled={isLoginButtonDisabled}
          fullWidth
          type="submit"
          sx={{
            mt: theme.spacing(8),
          }}
        >
          {msgStr("doLogIn")}
        </Button>
      </Box>
    </Template>
  );
}
