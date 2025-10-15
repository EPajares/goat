import type { PageProps } from "keycloakify/login/pages/PageProps";

import type { I18n } from "../i18n";
import type { KcContext } from "../kcContext";
import { Box, Button, Link, Typography, useTheme } from "@mui/material";

export default function LogoutConfirm(
  props: PageProps<Extract<KcContext, { pageId: "logout-confirm.ftl" }>, I18n>,
) {
  const theme = useTheme();

  const { kcContext, i18n, doUseDefaultCss, Template, classes } = props;

  const { url, client, logoutConfirm } = kcContext;

  const { msg, msgStr } = i18n;

  return (
    <Template
      {...{ kcContext, i18n, doUseDefaultCss, classes }}
      displayMessage={false}
      headerNode={msg("logoutConfirmTitle")}
    >
      <Typography variant="body1">{msg("logoutConfirmHeader")}</Typography>
      <Box
        sx={{
          mt: theme.spacing(4),
        }}
        component="form"
        action={url.logoutConfirmAction}
        method="POST"
      >
        <input type="hidden" name="session_code" value={logoutConfirm.code} />
        <Button
          fullWidth
          tabIndex={4}
          name="confirmLogout"
          id="kc-logout"
          type="submit"
        >
          {msgStr("doLogout")}
        </Button>
        {!logoutConfirm.skipLink && client.baseUrl && (
          <Typography
            sx={{
              mt: theme.spacing(4),
            }}
          >
            <Link underline="hover" href={client.baseUrl}>
              {msg("backToApplication")}
            </Link>
          </Typography>
        )}
      </Box>
    </Template>
  );
}
