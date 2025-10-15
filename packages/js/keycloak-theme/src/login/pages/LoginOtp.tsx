/* eslint-disable @typescript-eslint/no-explicit-any */
import { pathJoin } from "keycloakify/bin/tools/pathJoin";
import type { PageProps } from "keycloakify/login/pages/PageProps";
import { headInsert } from "keycloakify/tools/headInsert";
import { useEffect } from "react";

import type { I18n } from "../i18n";
import type { KcContext } from "../kcContext";
import { Box, Button, TextField, useTheme } from "@mui/material";

export default function LoginOtp(
  props: PageProps<Extract<KcContext, { pageId: "login-otp.ftl" }>, I18n>,
) {
  const theme = useTheme();
  const { kcContext, i18n, doUseDefaultCss, Template, classes } = props;

  const { url } = kcContext;

  const { msg, msgStr } = i18n;

  useEffect(() => {
    let isCleanedUp = false;

    const { prLoaded, remove } = headInsert({
      type: "javascript",
      src: pathJoin(
        kcContext.url.resourcesCommonPath,
        "node_modules/jquery/dist/jquery.min.js",
      ),
    });

    (async () => {
      await prLoaded;

      if (isCleanedUp) {
        return;
      }

      evaluateInlineScript();
    })();

    return () => {
      isCleanedUp = true;
      remove();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <Template
      {...{ kcContext, i18n, doUseDefaultCss, classes }}
      headerNode={msg("doLogIn")}
    >
      <Box
        component="form"
        id="kc-otp-login-form"
        action={url.loginAction}
        method="post"
      >
        <TextField
          type="text"
          fullWidth
          id="otp"
          name="otp"
          label={msg("loginOtpOneTime")}
          autoComplete="off"
          autoFocus
        />

        <Box
          sx={{
            mt: theme.spacing(8),
          }}
        >
          <Button fullWidth name="login" id="kc-login" type="submit">
            {msgStr("doLogIn")}
          </Button>
        </Box>
      </Box>
    </Template>
  );
}

declare const $: any;

function evaluateInlineScript() {
  $(document).ready(function () {
    // Card Single Select
    $(".card-pf-view-single-select").click(function (this: any) {
      if ($(this).hasClass("active")) {
        $(this).removeClass("active");
        $(this).children().removeAttr("name");
      } else {
        $(".card-pf-view-single-select").removeClass("active");
        $(".card-pf-view-single-select").children().removeAttr("name");
        $(this).addClass("active");
        $(this).children().attr("name", "selectedCredentialId");
      }
    });

    const defaultCred = $(".card-pf-view-single-select")[0];
    if (defaultCred) {
      defaultCred.click();
    }
  });
}
