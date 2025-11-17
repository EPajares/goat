import {
  Box,
  Link,
  Step,
  StepLabel,
  Stepper,
  Typography,
  useTheme,
} from "@mui/material";
import type { PageProps } from "keycloakify/login/pages/PageProps";

import { Button } from "@mui/material";
import type { I18n } from "../i18n";
import type { KcContext } from "../kcContext";

export default function LoginVerifyEmail(
  props: PageProps<
    Extract<KcContext, { pageId: "login-verify-email.ftl" }>,
    I18n
  >,
) {
  const theme = useTheme();

  const { kcContext, i18n, doUseDefaultCss, Template } = props;

  const { msg, msgStr } = i18n;

  const { url } = kcContext;

  return (
    <Template
      {...{ kcContext, i18n, doUseDefaultCss }}
      displayMessage={false}
      headerNode={msg("verifyEmail")}
    >
      <Stepper
        activeStep={2}
        sx={{
          mb: theme.spacing(4),
        }}
      >
        {[1, 2, 3].map((label) => (
          <Step sx={{ paddingRight: 0 }} key={label}>
            <StepLabel> </StepLabel>
          </Step>
        ))}
      </Stepper>

      <Typography variant="body1">{msg("emailVerifyInstruction")}</Typography>

      <Box
        sx={{
          mt: theme.spacing(8),
        }}
      >
        {(() => {
          const button = (
            <Link href={url.loginAction}>
              <Button fullWidth type="submit">
                {msgStr("resendEmail")}
              </Button>
            </Link>
          );

          return button;
        })()}
      </Box>
    </Template>
  );
}
