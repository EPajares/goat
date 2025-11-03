import { Alert } from "@mui/material";
import { Stack } from "@mui/material";

import { Loading } from "@p4b/ui/components/Loading";

import { useTranslation } from "@/i18n/client";

interface WidgetStatusContainerProps {
  isLoading?: boolean;
  isNotConfigured?: boolean;
  isError?: boolean;
  height?: number | string;
  isNotConfiguredMessage?: string;
  errorMessage?: string;
}

export const WidgetStatusContainer = ({
  isLoading,
  isNotConfigured,
  isError,
  height = 120,
  isNotConfiguredMessage,
  errorMessage,
}: WidgetStatusContainerProps) => {
  const { t } = useTranslation("common");

  // Default states that apply to all charts
  const defaultStates = [
    {
      condition: isLoading,
      element: <Loading />,
    },
    {
      condition: isNotConfigured,
      element: <Alert severity="warning">{isNotConfiguredMessage ?? t("please_configure_widget")}</Alert>,
    },
    {
      condition: isError,
      element: <Alert severity="error">{errorMessage ?? t("cannot_render_this_widget")}</Alert>,
    },
  ];

  const content = defaultStates.find((state) => state.condition)?.element;

  if (!content) {
    return null;
  }

  return (
    <Stack alignItems="center" justifyContent="center" width="100%" height={height}>
      {content}
    </Stack>
  );
};
