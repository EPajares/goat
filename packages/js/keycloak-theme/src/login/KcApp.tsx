/* eslint-disable @typescript-eslint/no-explicit-any */
import Fallback, { type PageProps } from "keycloakify/login";
import { lazy, Suspense } from "react";

import { useI18n } from "./i18n";
import { ColorModeContext, type KcContext } from "./kcContext";
import ThemeProvider from "@p4b/ui/theme/ThemeProvider";
import React from "react";

const Template = lazy(() => import("./Template"));
const RegisterUserProfile = lazy(() => import("./pages/RegisterUserProfile"));
const UpdateUserProfile = lazy(() => import("./pages/UpdateUserProfile"));
const UpdateEmail = lazy(() => import("./pages/UpdateEmail"));
const IdpReviewUserProfile = lazy(() => import("./pages/IdpReviewUserProfile"));
const SelectAuthenticator = lazy(() => import("./pages/SelectAuthenticator"));
const Login = lazy(() => import("./pages/Login"));
const LoginVerifyEmail = lazy(() => import("./pages/LoginVerifyEmail"));
const LoginConfigTotp = lazy(() => import("./pages/LoginConfigTotp"));
const LoginIdpLinkConfirm = lazy(() => import("./pages/LoginIdpLinkConfirm"));
const LoginIdpLinkEmail = lazy(() => import("./pages/LoginIdpLinkEmail"));
const LoginUpdateProfile = lazy(() => import("./pages/LoginUpdateProfile"));
const LoginOtp = lazy(() => import("./pages/LoginOtp"));
const LoginPassword = lazy(() => import("./pages/LoginPassword"));
const LoginUsername = lazy(() => import("./pages/LoginUsername"));
const LoginResetPassword = lazy(() => import("./pages/LoginResetPassword"));
const LoginUpdatePassword = lazy(() => import("./pages/LoginUpdatePassword"));
const LoginPageExpired = lazy(() => import("./pages/LoginPageExpired"));
const LogoutConfirm = lazy(() => import("./pages/LogoutConfirm"));
const Info = lazy(() => import("./pages/Info"));
const Error = lazy(() => import("./pages/Error"));

export default function KcApp(props: { kcContext: KcContext }) {
  const urlParams = new URLSearchParams(window.location.search);
  if (urlParams.get("theme")) {
    localStorage.setItem("theme", urlParams.get("theme") || "light");
  }
  const theme = localStorage.getItem("theme") || "light";
  const [mode, setMode] = React.useState<"light" | "dark">(
    theme as "light" | "dark",
  );
  const colorMode = React.useMemo(
    () => ({
      toggleColorMode: () => {
        setMode((prevMode) => {
          localStorage.setItem(
            "theme",
            prevMode === "light" ? "dark" : "light",
          );
          if (prevMode === "light") {
            return "dark";
          }
          return "light";
        });
      },
    }),
    [],
  );
  const { kcContext } = props;
  const i18n = useI18n({ kcContext });

  if (i18n === null) {
    return null;
  }
  const pageProps: Omit<PageProps<any, typeof i18n>, "kcContext"> = {
    i18n,
    Template,
    doUseDefaultCss: false,
    classes: {},
  };

  return (
    <ColorModeContext.Provider value={colorMode}>
      <Suspense>
        <ThemeProvider
          settings={{
            mode,
          }}
        >
          {(() => {
            switch (kcContext.pageId) {
              case "register-user-profile.ftl":
                return (
                  <RegisterUserProfile kcContext={kcContext} {...pageProps} />
                );
              case "update-user-profile.ftl":
                return (
                  <UpdateUserProfile kcContext={kcContext} {...pageProps} />
                );
              case "update-email.ftl":
                return <UpdateEmail kcContext={kcContext} {...pageProps} />;
              case "idp-review-user-profile.ftl":
                return (
                  <IdpReviewUserProfile kcContext={kcContext} {...pageProps} />
                );
              case "select-authenticator.ftl":
                return (
                  <SelectAuthenticator kcContext={kcContext} {...pageProps} />
                );
              case "login.ftl":
                return <Login kcContext={kcContext} {...pageProps} />;
              case "login-verify-email.ftl":
                return (
                  <LoginVerifyEmail kcContext={kcContext} {...pageProps} />
                );
              case "login-config-totp.ftl":
                return <LoginConfigTotp kcContext={kcContext} {...pageProps} />;
              case "login-idp-link-confirm.ftl":
                return (
                  <LoginIdpLinkConfirm kcContext={kcContext} {...pageProps} />
                );
              case "login-idp-link-email.ftl":
                return (
                  <LoginIdpLinkEmail kcContext={kcContext} {...pageProps} />
                );
              case "login-update-profile.ftl":
                return (
                  <LoginUpdateProfile kcContext={kcContext} {...pageProps} />
                );
              case "login-password.ftl":
                return <LoginPassword kcContext={kcContext} {...pageProps} />;
              case "login-username.ftl":
                return <LoginUsername kcContext={kcContext} {...pageProps} />;
              case "login-otp.ftl":
                return <LoginOtp kcContext={kcContext} {...pageProps} />;
              case "login-reset-password.ftl":
                return (
                  <LoginResetPassword kcContext={kcContext} {...pageProps} />
                );
              case "login-update-password.ftl":
                return (
                  <LoginUpdatePassword kcContext={kcContext} {...pageProps} />
                );
              case "login-page-expired.ftl":
                return (
                  <LoginPageExpired kcContext={kcContext} {...pageProps} />
                );
              case "logout-confirm.ftl":
                return <LogoutConfirm kcContext={kcContext} {...pageProps} />;
              case "info.ftl":
                return <Info kcContext={kcContext} {...pageProps} />;
              case "error.ftl":
                return <Error kcContext={kcContext} {...pageProps} />;
              default:
                return <Fallback kcContext={kcContext} {...pageProps} />;
            }
          })()}
        </ThemeProvider>
      </Suspense>
    </ColorModeContext.Provider>
  );
}
