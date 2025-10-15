import type { PageProps } from "keycloakify/login/pages/PageProps";

import type { I18n } from "../i18n";
import type { KcContext } from "../kcContext";
import {
  Box,
  Button,
  Divider,
  Link,
  Stack,
  TextField,
  Typography,
  useTheme,
} from "@mui/material";

export default function LoginConfigTotp(
  props: PageProps<
    Extract<KcContext, { pageId: "login-config-totp.ftl" }>,
    I18n
  >,
) {
  const theme = useTheme();

  const { kcContext, i18n, doUseDefaultCss, Template, classes } = props;

  const { url, isAppInitiatedAction, totp, mode, messagesPerField } = kcContext;

  const { msg, msgStr } = i18n;

  const algToKeyUriAlg: Record<
    (typeof kcContext)["totp"]["policy"]["algorithm"],
    string
  > = {
    HmacSHA1: "SHA1",
    HmacSHA256: "SHA256",
    HmacSHA512: "SHA512",
  };
  return (
    <Template
      {...{ kcContext, i18n, doUseDefaultCss, classes }}
      headerNode={msg("loginTotpTitle")}
    >
      <>
        <Stack
          direction="column"
          spacing={theme.spacing(4)}
          sx={{
            display: "flex",
            alignItems: "center",
            flexWrap: "wrap",
            justifyContent: "center",
          }}
        >
          {mode && mode == "manual" ? (
            <>
              <Typography variant="body1">
                {msg("loginToptConfigureManually")}
              </Typography>

              <Stack direction="row">
                <Typography variant="subtitle2">
                  {msg("loginTotpType")}: {msg(`loginTotp.${totp.policy.type}`)}
                </Typography>
                <Typography variant="subtitle2">
                  {" , "}
                  {msg("loginTotpAlgorithm")}:{" "}
                  {algToKeyUriAlg?.[totp.policy.algorithm] ??
                    totp.policy.algorithm}
                </Typography>

                <Typography variant="subtitle2">
                  {" , "}
                  {msg("loginTotpDigits")}: {totp.policy.digits}
                </Typography>

                {totp.policy.type === "totp" ? (
                  <Typography variant="subtitle2">
                    {" , "}
                    {msg("loginTotpInterval")}: {totp.policy.period}
                  </Typography>
                ) : (
                  <Typography variant="subtitle2">
                    {" , "}
                    {msg("loginTotpCounter")}: {totp.policy.initialCounter}
                  </Typography>
                )}
              </Stack>
              <Typography variant="body1" fontWeight="900">
                <span id="kc-totp-secret-key">{totp.totpSecretEncoded}</span>
              </Typography>
              <Link underline="hover" href={totp.qrUrl}>
                {msg("scanQrCode")}
              </Link>
            </>
          ) : (
            <>
              <Typography variant="body1">
                {msg("loginTotpScanBarcode")}
              </Typography>
              <img
                height={200}
                id="kc-totp-secret-qr-code"
                src={`data:image/png;base64, ${totp.totpSecretQrCode}`}
                alt="Figure: Barcode"
              />
              <Link underline="hover" href={totp.manualUrl}>
                {msg("loginTotpUnableToScan")}
              </Link>
            </>
          )}
        </Stack>

        <Divider sx={{ my: 5 }}>{msg("then")}</Divider>

        <Box
          component="form"
          action={url.loginAction}
          id="kc-totp-settings-form"
          method="post"
        >
          <Stack spacing={theme.spacing(4)}>
            <TextField
              required
              type="text"
              id="totp"
              name="totp"
              autoComplete="off"
              fullWidth
              label={msg("authenticatorCode")}
              aria-invalid={messagesPerField.existsError("totp")}
              error={messagesPerField.existsError("totp")}
              helperText={
                messagesPerField.existsError("totp") &&
                messagesPerField.get("totp")
              }
            />
            <input
              type="hidden"
              id="totpSecret"
              name="totpSecret"
              value={totp.totpSecret}
            />
            {mode && <input type="hidden" id="mode" value={mode} />}
            <TextField
              required={totp.otpCredentials.length >= 1}
              type="text"
              id="userLabel"
              name="userLabel"
              autoComplete="off"
              fullWidth
              label={msg("loginTotpDeviceName")}
              aria-invalid={messagesPerField.existsError("userLabel")}
              error={messagesPerField.existsError("userLabel")}
              helperText={
                messagesPerField.existsError("userLabel") &&
                messagesPerField.get("userLabel")
              }
            />
          </Stack>
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
                  id="saveTOTPBtn"
                  fullWidth
                  type="submit"
                  defaultValue={msgStr("doSubmit")}
                />

                <Button
                  fullWidth
                  type="submit"
                  id="cancelTOTPBtn"
                  name="cancel-aia"
                  value="true"
                  variant="text"
                >
                  {msg("doCancel")}
                </Button>
              </>
            ) : (
              <Button fullWidth type="submit" id="saveTOTPBtn">
                {msg("doSubmit")}
              </Button>
            )}
          </Box>
        </Box>
      </>
    </Template>
  );
}
