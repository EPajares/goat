import type { PageProps } from "keycloakify/login/pages/PageProps";

import type { I18n } from "../i18n";
import type { KcContext } from "../kcContext";
import { Link, Stack, Typography, useTheme } from "@mui/material";

export default function LoginPageExpired(
  props: PageProps<
    Extract<KcContext, { pageId: "login-page-expired.ftl" }>,
    I18n
  >,
) {
  const theme = useTheme();
  const { kcContext, i18n, doUseDefaultCss, Template, classes } = props;

  const { url } = kcContext;

  const { msg } = i18n;

  return (
    <Template
      {...{ kcContext, i18n, doUseDefaultCss, classes }}
      displayMessage={false}
      headerNode={msg("pageExpiredTitle")}
    >
      <Stack id="instruction1" spacing={theme.spacing(2)}>
        <Typography variant="body1">
          {msg("pageExpiredMsg1")}{": "}
          <Link id="loginRestartLink" href={url.loginRestartFlowUrl}>
            {msg("doClickHere")}
          </Link>
        </Typography>

        <Typography variant="body1">
          {msg("pageExpiredMsg2")}{": "}
          <Link id="loginContinueLink" href={url.loginAction}>
            {msg("doClickHere")}
          </Link>
        </Typography>
      </Stack>
    </Template>
  );
}
