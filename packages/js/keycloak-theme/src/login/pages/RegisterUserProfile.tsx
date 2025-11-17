import {
  Box,
  Button,
  Stack,
  Tooltip,
  Typography,
  useTheme,
} from "@mui/material";
import Link from "@mui/material/Link";
import type { PageProps } from "keycloakify/login/pages/PageProps";
import { useRef, useState } from "react";
// eslint-disable-next-line @typescript-eslint/ban-ts-comment
// @ts-ignore
import ReCAPTCHA from "react-google-recaptcha";

import type { I18n } from "../i18n";
import type { KcContext } from "../kcContext";
import { UserProfileFormFields } from "./shared/UserProfileFormFields";

interface Steps {
  [key: number]: string[];
}

const steps: Steps = {
  1: ["firstName", "lastName", "country", "profession", "domain"],
  2: [
    "email",
    "password",
    "password-confirm",
    "terms_and_conditions",
    "subscribe_to_newsletter",
  ],
  3: [""], // verify email (last step). This step is not used in this form even though it's shown in the stepper
};

export default function RegisterUserProfile(
  props: PageProps<
    Extract<KcContext, { pageId: "register-user-profile.ftl" }>,
    I18n
  >,
) {
  const theme = useTheme();
  const { kcContext, i18n, doUseDefaultCss, Template } = props;
  const { url, messagesPerField, recaptchaRequired, recaptchaSiteKey } =
    kcContext;
  const { msg, msgStr } = i18n;
  const [activeStep, setActiveStep] = useState(0);
  const [isFormSubmittable, setIsFormSubmittable] = useState(false);
  const [isCaptchaValid, setIsCaptchaValid] = useState(false);
  const captchaRef = useRef(null);
  const getIncrementedTabIndex = (() => {
    let counter = 1;
    return () => counter++;
  })();

  const handleNext = () => {
    setActiveStep((prevActiveStep) => prevActiveStep + 1);
  };

  const handleBack = () => {
    setActiveStep((prevActiveStep) => prevActiveStep - 1);
  };

  return (
    <Template
      {...{ kcContext, i18n, doUseDefaultCss }}
      displayInfo={true}
      displayMessage={messagesPerField.exists("global")}
      displayRequiredFields={false}
      i18n={i18n}
      infoNode={
        <Stack
          spacing={theme.spacing(4)}
          sx={{
            textAlign: "center",
          }}
        >
          <Typography variant="body2">
            {msg("alreadyHaveAccount")}{" "}
            <Link href={url.loginUrl}>{msg("doLogIn")}</Link>
          </Typography>
        </Stack>
      }
      headerNode={msg("doRegister")}
    >
      <Box component="form" action={url.registrationAction} method="post">
        <UserProfileFormFields
          kcContext={kcContext}
          onIsFormSubmittableValueChange={setIsFormSubmittable}
          activeStep={activeStep}
          steps={steps}
          i18n={i18n}
          getIncrementedTabIndex={getIncrementedTabIndex}
        />

        {recaptchaRequired && (
          <ReCAPTCHA
            id="recaptcha"
            hl={i18n.currentLanguageTag}
            theme={theme.palette.mode == "dark" ? "dark" : "light"}
            style={{
              display: activeStep == 1 ? "block" : "none",
            }}
            sx={{
              mt: theme.spacing(4),
            }}
            sitekey={recaptchaSiteKey}
            onChange={() => setIsCaptchaValid(true)}
            onExpired={() => setIsCaptchaValid(false)}
            onErrored={() => setIsCaptchaValid(false)}
            ref={captchaRef}
          />
        )}
        <div>
          {(() => {
            const button = (
              <Button
                sx={{
                  mt: theme.spacing(4),
                }}
                fullWidth
                disabled={
                  !isFormSubmittable || (recaptchaRequired && !isCaptchaValid)
                }
                type="submit"
                tabIndex={getIncrementedTabIndex()}
              >
                {msgStr("getStarted")}
              </Button>
            );

            return activeStep == 1 ? (
              isFormSubmittable ? (
                button
              ) : (
                <Tooltip title={msg("formNotFilledProperly")}>
                  <span>{button}</span>
                </Tooltip>
              )
            ) : null;
          })()}
        </div>
      </Box>
      {activeStep == 0 && (
        <Button
          fullWidth
          sx={{
            mt: theme.spacing(4),
          }}
          onClick={handleNext}
        >
          {msgStr("next")}
        </Button>
      )}
      {activeStep == 1 && (
        <Button
          sx={{
            mt: theme.spacing(2),
          }}
          fullWidth
          onClick={handleBack}
          variant="text"
        >
          {msgStr("back")}
        </Button>
      )}
    </Template>
  );
}
