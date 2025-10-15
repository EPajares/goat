import type { PageProps } from "keycloakify/login/pages/PageProps";
import { useState } from "react";

import { Box, Button, useTheme } from "@mui/material";
import type { I18n } from "../i18n";
import type { KcContext } from "../kcContext";
import { UserProfileFormFields } from "./shared/UserProfileFormFields";

export default function IdpReviewUserProfile(
  props: PageProps<
    Extract<KcContext, { pageId: "idp-review-user-profile.ftl" }>,
    I18n
  >,
) {
  const theme = useTheme();
  const { kcContext, i18n, doUseDefaultCss, Template } = props;

  const { msg, msgStr } = i18n;

  const { url } = kcContext;

  const [isFomSubmittable, setIsFomSubmittable] = useState(false);

  const getIncrementedTabIndex = (() => {
    let counter = 1;
    return () => counter++;
  })();

  return (
    <Template
      {...{ kcContext, i18n, doUseDefaultCss }}
      headerNode={msg("loginIdpReviewProfileTitle")}
    >
      <Box
        component="form"
        id="kc-idp-review-profile-form"
        action={url.loginAction}
        method="post"
      >
        <UserProfileFormFields
          kcContext={kcContext}
          onIsFormSubmittableValueChange={setIsFomSubmittable}
          i18n={i18n}
          getIncrementedTabIndex={getIncrementedTabIndex}
        />

        <Button
          sx={{
            mt: theme.spacing(4),
          }}
          type="submit"
          fullWidth
          disabled={!isFomSubmittable}
          tabIndex={getIncrementedTabIndex()}
        >
          {msgStr("doSubmit")}
        </Button>
      </Box>
    </Template>
  );
}
