import { Link, Typography } from "@mui/material";
import type { I18n } from "keycloakify/login/i18n";
import type { KcContext } from "keycloakify/login/kcContext";
import type { PageProps } from "keycloakify/login/pages/PageProps";

export default function LoginIdpLinkEmail(
  props: PageProps<
    Extract<KcContext, { pageId: "login-idp-link-email.ftl" }>,
    I18n
  >,
) {
  const { kcContext, i18n, doUseDefaultCss, Template, classes } = props;

  const { url, realm, brokerContext, idpAlias } = kcContext;

  const { msg } = i18n;

  return (
    <Template
      {...{ kcContext, i18n, doUseDefaultCss, classes }}
      headerNode={msg("emailLinkIdpTitle", idpAlias)}
    >
      <Typography id="instruction1">
        {msg(
          "emailLinkIdp1",
          idpAlias,
          brokerContext.username,
          realm.displayName,
        )}
        <br />
        <br />
      </Typography>
      <Typography id="instruction2">
        {msg("emailLinkIdp2")}{" "} <br />
        <Link href={url.loginAction}>{msg("doClickHere")}</Link>{" "}
        {msg("emailLinkIdp3")}
        <br />
        <br />

      </Typography>
      <Typography id="instruction3">
        {msg("emailLinkIdp4")}{" "} <br />
        <Link href={url.loginAction}>{msg("doClickHere")}</Link>{" "}
        {msg("emailLinkIdp5")}
      </Typography>
    </Template>
  );
}
