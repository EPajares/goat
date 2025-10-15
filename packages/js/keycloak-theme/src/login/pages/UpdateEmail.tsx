import type { PageProps } from "keycloakify/login/pages/PageProps";

import type { I18n } from "../i18n";
import type { KcContext } from "../kcContext";
import { Box, Button, TextField, useTheme } from "@mui/material";

export default function UpdateEmail(
  props: PageProps<Extract<KcContext, { pageId: "update-email.ftl" }>, I18n>,
) {
  const theme = useTheme();
  const { kcContext, i18n, doUseDefaultCss, Template, classes } = props;

  const { msg, msgStr } = i18n;

  const { url, messagesPerField, isAppInitiatedAction, email } = kcContext;

  return (
    <Template
      {...{ kcContext, i18n, doUseDefaultCss, classes }}
      headerNode={msg("updateEmailTitle")}
    >
      <Box
        component="form"
        id="kc-update-email-form"
        action={url.loginAction}
        method="post"
      >
        <TextField
          fullWidth
          type="text"
          id="email"
          name="email"
          defaultValue={email.value ?? ""}
          aria-invalid={messagesPerField.existsError("email")}
        />

        <Box
          sx={{
            mt: theme.spacing(8),
          }}
        >
          {isAppInitiatedAction ? (
            <>
              <Button
                sx={{
                  mb: theme.spacing(2),
                }}
                fullWidth
                type="submit"
                defaultValue={msgStr("doSubmit")}
              />
              <Button
                fullWidth
                type="submit"
                name="cancel-aia"
                value="true"
                variant="text"
              >
                {msg("doCancel")}
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
