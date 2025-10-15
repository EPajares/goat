import type { PageProps } from "keycloakify/login/pages/PageProps";
import { useConstCallback } from "keycloakify/tools/useConstCallback";
import type { FormEventHandler } from "react";
import { useState } from "react";

import type { I18n } from "../i18n";
import type { KcContext } from "../kcContext";
import { Icon, brandColors, ICON_NAME } from "@p4b/ui/components/Icon";

import {
  Box,
  Button,
  Checkbox,
  Divider,
  FormControlLabel,
  IconButton,
  Link,
  Stack,
  TextField,
  Tooltip,
  Typography,
  useTheme,
} from "@mui/material";

export default function LoginUsername(
  props: PageProps<Extract<KcContext, { pageId: "login-username.ftl" }>, I18n>,
) {
  const theme = useTheme();

  const { kcContext, i18n, doUseDefaultCss, Template, classes } = props;

  const { social, realm, url, usernameHidden, login, registrationDisabled } =
    kcContext;

  const { msg, msgStr } = i18n;

  const [isLoginButtonDisabled, setIsLoginButtonDisabled] = useState(false);

  const onSubmit = useConstCallback<FormEventHandler<HTMLFormElement>>((e) => {
    e.preventDefault();

    setIsLoginButtonDisabled(true);

    const formElement = e.target as HTMLFormElement;

    //NOTE: Even if we login with email Keycloak expect username and password in
    //the POST request.
    formElement
      .querySelector("input[name='email']")
      ?.setAttribute("name", "username");

    formElement.submit();
  });

  return (
    <Template
      {...{ kcContext, i18n, doUseDefaultCss, classes }}
      displayInfo={social.displayInfo}
      headerNode={msg("doLogIn")}
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
              }}
            >
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
                  }}
                >
                  {social.providers.map((p) =>
                    social.providers && social.providers.length > 3 ? (
                      <Tooltip
                        key={p.providerId}
                        title={`Log in with ${p.displayName}`}
                        arrow
                        placement="top"
                      >
                        <IconButton href={p.loginUrl} component="a">
                          <Icon
                            htmlColor={
                              p.providerId in brandColors
                                ? brandColors[p.providerId]
                                : "inherit"
                            }
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
                            htmlColor={
                              p.providerId in brandColors
                                ? brandColors[p.providerId]
                                : "inherit"
                            }
                            iconName={
                              p.providerId.toUpperCase() in ICON_NAME
                                ? (p.providerId as ICON_NAME)
                                : ICON_NAME.USERS
                            }
                            fontSize="inherit"
                          />
                        }
                      >
                        Log in with {p.displayName}
                      </Button>
                    ),
                  )}
                </Stack>
              </>
            )}
          </Stack>
        )
      }
    >
      {realm.password && (
        <Box
          component="form"
          id="kc-form-login"
          onSubmit={onSubmit}
          action={url.loginAction}
          method="post"
        >
          {!usernameHidden &&
            (() => {
              const label = !realm.loginWithEmailAllowed
                ? "username"
                : realm.registrationEmailAsUsername
                ? "email"
                : "usernameOrEmail";

              const autoCompleteHelper: typeof label =
                label === "usernameOrEmail" ? "username" : label;

              return (
                <TextField
                  fullWidth
                  tabIndex={1}
                  id={autoCompleteHelper}
                  //NOTE: This is used by Google Chrome auto fill so we use it to tell
                  //the browser how to pre fill the form but before submit we put it back
                  //to username because it is what keycloak expects.
                  name={autoCompleteHelper}
                  defaultValue={login.username ?? ""}
                  label={msg(label)}
                  autoComplete="off"
                  autoFocus={true}
                  type="text"
                />
              );
            })()}

          <Box
            sx={{
              mt: theme.spacing(2),
              display: "flex",
              alignItems: "center",
              flexWrap: "wrap",
              justifyContent: "space-between",
            }}
          >
            {realm.rememberMe && !usernameHidden && (
              <FormControlLabel
                control={
                  <Checkbox
                    tabIndex={3}
                    defaultChecked={!!login.rememberMe}
                    id="rememberMe"
                    name="rememberMe"
                    color="primary"
                    checked={login.rememberMe === "on"}
                  />
                }
                label={
                  <Typography variant="body2">{msg("rememberMe")}</Typography>
                }
              />
            )}
          </Box>
          <Box
            id="kc-form-buttons"
            sx={{
              mt: theme.spacing(4),
            }}
          >
            <Button
              fullWidth
              tabIndex={4}
              name="login"
              id="kc-login"
              type="submit"
              disabled={isLoginButtonDisabled}
            >
              {msgStr("doLogIn")}
            </Button>
          </Box>
        </Box>
      )}
    </Template>
  );
}
