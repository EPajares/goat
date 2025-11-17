import { Link, Stack, Typography, useTheme } from "@mui/material";
import type { PageProps } from "keycloakify/login/pages/PageProps";

import type { I18n } from "../i18n";
import type { KcContext } from "../kcContext";

export default function Error(
  props: PageProps<Extract<KcContext, { pageId: "error.ftl" }>, I18n>,
) {
  const theme = useTheme();
  const { kcContext, i18n, doUseDefaultCss, Template } = props;

  const { message, client } = kcContext;

  const { msg } = i18n;
  return (
    <Template
      {...{ kcContext, i18n, doUseDefaultCss }}
      displayMessage={false}
      headerNode={msg("errorTitle")}
    >
      {client !== undefined && client.baseUrl !== undefined && (
        <Stack spacing={theme.spacing(4)}>
          <Typography variant="body1">{message.summary}</Typography>
          <Link id="backToApplication" href={client.baseUrl}>
            {msg("backToApplication")}
          </Link>
        </Stack>
      )}
    </Template>
  );
}
