import type { PageProps } from "keycloakify/login/pages/PageProps";

import type { I18n } from "../i18n";
import type { KcContext } from "../kcContext";
import { Box, Button, Stack, useTheme } from "@mui/material";

export default function LoginIdpLinkConfirm(
  props: PageProps<
    Extract<KcContext, { pageId: "login-idp-link-confirm.ftl" }>,
    I18n
  >,
) {
  const theme = useTheme();
  const { kcContext, i18n, doUseDefaultCss, Template, classes } = props;

  const { url, idpAlias } = kcContext;

  const { msg } = i18n;

  return (
    <Template
      {...{ kcContext, i18n, doUseDefaultCss, classes }}
      headerNode={msg("confirmLinkIdpTitle")}
    >
      <Box
        component="form"
        id="kc-register-form"
        action={url.loginAction}
        method="post"
      >
        <Stack spacing={theme.spacing(4)}>
          <Button
            fullWidth
            type="submit"
            name="submitAction"
            id="updateProfile"
            value="updateProfile"
          >
            {msg("confirmLinkIdpReviewProfile")}
          </Button>
          <Button
            fullWidth
            type="submit"
            name="submitAction"
            id="linkAccount"
            value="linkAccount"
          >
            {msg("confirmLinkIdpContinue", idpAlias)}
          </Button>
        </Stack>
      </Box>
    </Template>
  );
}
