import { Alert, Stack, useTheme } from "@mui/material";
import DarkModeSwitch from "@p4b/ui/components/DarkModeSwitch";
import LanguageDropdown from "@p4b/ui/components/LanguageDropdown";
import AuthLayout from "@p4b/ui/components/AuthLayout";
import AuthContainer from "@p4b/ui/components/AuthContainer";
import type { I18n } from "./i18n";
import { ColorModeContext, type KcContext } from "./kcContext";
import type { TemplateProps } from "keycloakify/login/TemplateProps";
import { useContext } from "react";
export default function Template(props: TemplateProps<KcContext, I18n>) {
  const theme = useTheme();
  const colorMode = useContext(ColorModeContext);
  const {
    displayInfo = false,
    displayMessage = true,
    headerNode,
    infoNode = null,
    kcContext,
    i18n,
    children,
  } = props;
  const { realm, locale, message, isAppInitiatedAction } = kcContext;
  const {
    msgStr,
    changeLocale,
    labelBySupportedLanguageTag,
    currentLanguageTag,
  } = i18n;
  return (
    <AuthLayout
      sx={{
        fontFamily: "'Mulish', sans-serif",
      }}
    >
      <AuthContainer
        headerTitle={headerNode}
        headerAlert={
          displayMessage &&
          message !== undefined &&
          (message.type !== "warning" || !isAppInitiatedAction) && (
            <Alert severity={message.type}>{message.summary}</Alert>
          )
        }
        body={children}
        footer={
          displayInfo && (
            <Stack
              spacing={theme.spacing(2)}
              sx={{
                mt: theme.spacing(4),
                textAlign: "left",
              }}
            >
              {infoNode}
            </Stack>
          )
        }
        otherFooterActions={
          [
            "register-user-profile.ftl",
            "login.ftl",
            "login-username.ftl",
          ].includes(kcContext.pageId) && (
            <>
              {realm.internationalizationEnabled &&
                locale &&
                locale.supported.length > 1 && (
                  <LanguageDropdown
                    toolTipProps={{
                      title: msgStr("changeLanguage"),
                      placement: "top",
                    }}
                    languages={labelBySupportedLanguageTag}
                    selected={currentLanguageTag}
                    onLanguageChange={changeLocale}
                  />
                )}
              <DarkModeSwitch
                sx={{
                  ml: theme.spacing(2),
                }}
                size="small"
                onClick={() => {
                  colorMode.toggleColorMode();
                }}
                toolTipProps={{
                  title: msgStr("changeTheme"),
                  placement: "top",
                }}
                isDarkModeEnabled={theme.palette.mode === "dark"}
              />
            </>
          )
        }
      />
    </AuthLayout>
  );
}
