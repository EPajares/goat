import type { PageProps } from "keycloakify/login/pages/PageProps";
import { UserProfileFormFields } from "./shared/UserProfileFormFields";
import { useState } from "react";

import type { I18n } from "../i18n";
import type { KcContext } from "../kcContext";
import { Box, Button, useTheme } from "@mui/material";

export default function UpdateUserProfile(
  props: PageProps<
    Extract<KcContext, { pageId: "update-user-profile.ftl" }>,
    I18n
  >,
) {
  const theme = useTheme();
  const { kcContext, i18n, doUseDefaultCss, Template, classes } = props;

  const { msg, msgStr } = i18n;

  const { url, isAppInitiatedAction } = kcContext;

  const [isFomSubmittable, setIsFomSubmittable] = useState(false);

  const getIncrementedTabIndex = (() => {
    let counter = 1;
    return () => counter++;
  })();
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
        <UserProfileFormFields
          kcContext={kcContext}
          onIsFormSubmittableValueChange={setIsFomSubmittable}
          i18n={i18n}
          getIncrementedTabIndex={getIncrementedTabIndex}
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
                formNoValidate
              >
                {msg("doCancel")}
              </Button>
            </>
          ) : (
            <Button fullWidth type="submit" disabled={!isFomSubmittable}>
              {msg("doSubmit")}
            </Button>
          )}
        </Box>
      </Box>
    </Template>
  );
}
