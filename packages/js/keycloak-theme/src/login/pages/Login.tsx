import {
  Box,
  Button,
  Checkbox,
  Divider,
  FormControl,
  IconButton,
  InputAdornment,
  InputLabel,
  OutlinedInput,
  Stack,
  TextField,
  Tooltip,
  Typography,
  useTheme,
} from "@mui/material";
import FormControlLabel from "@mui/material/FormControlLabel";
import Link from "@mui/material/Link";
import type { PageProps } from "keycloakify/login/pages/PageProps";
import { useConstCallback } from "keycloakify/tools/useConstCallback";
import type { MouseEvent } from "react";
import { type FormEventHandler, useState } from "react";

import { ICON_NAME, Icon, brandColors } from "@p4b/ui/components/Icon";

import type { I18n } from "../i18n";
import type { KcContext } from "../kcContext";

export default function Login(props: PageProps<Extract<KcContext, { pageId: "login.ftl" }>, I18n>) {
  const theme = useTheme();
  const { kcContext, i18n, doUseDefaultCss, Template, classes: classes_props } = props;

  const { social, realm, url, usernameHidden, login, auth, registrationDisabled } = kcContext;

  const { msg, msgStr } = i18n;

  const [isLoginButtonDisabled, setIsLoginButtonDisabled] = useState(false);

  const onSubmit = useConstCallback<FormEventHandler<HTMLFormElement>>((e) => {
    e.preventDefault();

    setIsLoginButtonDisabled(true);

    const formElement = e.target as HTMLFormElement;

    //NOTE: Even if we login with email Keycloak expect username and password in
    //the POST request.
    formElement.querySelector("input[name='email']")?.setAttribute("name", "username");

    formElement.submit();
  });

  const [showPassword, setShowPassword] = useState(false);
  const handleMouseEvents = (event: MouseEvent) => {
    event.preventDefault();
  };
  return (
    <Template
      {...{ kcContext, i18n, doUseDefaultCss }}
      classes={classes_props}
      displayInfo={social.displayInfo}
      displayWide={realm.password && social.providers !== undefined}
      headerNode={msg("doLogIn")}
      i18n={i18n}
      infoNode={
        realm.password &&
        realm.registrationAllowed &&
        !registrationDisabled && (
          <Stack direction="column" spacing={theme.spacing(4)}>
            <Stack
              direction="row"
              spacing={1}
              sx={{
                display: "flex",
                alignItems: "center",
                flexWrap: "wrap",
                justifyContent: "center",
              }}>
              <Typography variant="body2">{msg("noAccount")}</Typography>
              <Typography variant="body2">
                <Link href={url.registrationUrl}>{msg("doRegister")}</Link>
              </Typography>
            </Stack>
            {realm.password && social.providers !== undefined && (
              <>
                <Divider sx={{ my: 5 }}>{msg("or")}</Divider>
                <Stack
                  direction={social.providers.length > 3 ? "row" : "column"}
                  spacing={2}
                  sx={{
                    alignItems: "center",
                    flexWrap: "wrap",
                    justifyContent: "center",
                  }}>
                  {social.providers.map((p) =>
                    social.providers && social.providers.length > 3 ? (
                      <Tooltip
                        key={p.providerId}
                        title={`Log in with ${p.displayName}`}
                        arrow
                        placement="top">
                        <IconButton href={p.loginUrl} component="a">
                          <Icon
                            htmlColor={p.providerId in brandColors ? brandColors[p.providerId] : "inherit"}
                            iconName={
                              p.providerId.toUpperCase() in ICON_NAME
                                ? (p.providerId as ICON_NAME)
                                : ICON_NAME.ORGANIZATION
                            }
                            fontSize="inherit"
                          />
                        </IconButton>
                      </Tooltip>
                    ) : (
                      <Button
                        key={p.providerId}
                        href={p.loginUrl}
                        component="a"
                        variant="outlined"
                        fullWidth
                        sx={{
                          "& .MuiButton-startIcon": {
                            position: "absolute",
                            left: "2rem",
                          },
                          textTransform: "none",
                        }}
                        startIcon={
                          <Icon
                            htmlColor={p.providerId in brandColors ? brandColors[p.providerId] : "inherit"}
                            iconName={
                              p.providerId.toUpperCase() in ICON_NAME
                                ? (p.providerId as ICON_NAME)
                                : ICON_NAME.USERS
                            }
                            fontSize="inherit"
                          />
                        }>
                        Log in with {p.displayName}
                      </Button>
                    )
                  )}
                </Stack>
              </>
            )}
          </Stack>
        )
      }>
      {realm.password && (
        <Box id="kc-form-login" component="form" onSubmit={onSubmit} action={url.loginAction} method="post">
          <Stack spacing={theme.spacing(4)}>
            <TextField
              fullWidth
              disabled={usernameHidden}
              defaultValue={login.username ?? ""}
              id="username"
              name="username"
              tabIndex={1}
              spellCheck={false}
              label={
                !realm.loginWithEmailAllowed
                  ? msg("username")
                  : !realm.registrationEmailAsUsername
                    ? msg("usernameOrEmail")
                    : msg("email")
              }
              autoComplete="off"
            />
            <FormControl fullWidth>
              <InputLabel htmlFor="password">{msg("password")}</InputLabel>
              <OutlinedInput
                label={msg("password")}
                defaultValue=""
                id="password"
                name="password"
                tabIndex={2}
                type={showPassword ? "text" : "password"}
                autoComplete="off"
                endAdornment={
                  <InputAdornment position="end">
                    <IconButton
                      edge="end"
                      onClick={() => setShowPassword(!showPassword)}
                      onMouseDown={handleMouseEvents}
                      onMouseUp={handleMouseEvents}
                      aria-label="toggle password visibility">
                      {showPassword ? (
                        <Icon iconName={ICON_NAME.EYE_SLASH} />
                      ) : (
                        <Icon iconName={ICON_NAME.EYE} />
                      )}
                    </IconButton>
                  </InputAdornment>
                }
              />
            </FormControl>
          </Stack>
          <Box
            sx={{
              mt: theme.spacing(2),
              display: "flex",
              alignItems: "center",
              flexWrap: "wrap",
              justifyContent: "space-between",
            }}>
            {realm.rememberMe && !usernameHidden && (
              <FormControlLabel
                control={
                  <Checkbox
                    tabIndex={3}
                    defaultChecked={!!login.rememberMe}
                    id="rememberMe"
                    name="rememberMe"
                    color="primary"
                  />
                }
                label={<Typography variant="body2">{msg("rememberMe")}</Typography>}
              />
            )}

            {realm.resetPasswordAllowed && (
              <Typography variant="body2">
                <Link href={url.loginResetCredentialsUrl} underline="hover">
                  {msg("doForgotPassword")}
                </Link>
              </Typography>
            )}
          </Box>

          <Box
            sx={{
              mt: theme.spacing(8),
            }}>
            <input
              type="hidden"
              name="credentialId"
              {...(auth?.selectedCredential !== undefined
                ? {
                    value: auth.selectedCredential,
                  }
                : {})}
            />
            <Button fullWidth name="login" type="submit" disabled={isLoginButtonDisabled}>
              {msgStr("continue")}
            </Button>
          </Box>
        </Box>
      )}
    </Template>
  );
}
