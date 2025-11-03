import { Stack, Typography } from "@mui/material";
import { useTheme } from "@mui/material/styles";
import { useTranslation } from "react-i18next";

import { ICON_NAME, Icon } from "@p4b/ui/components/Icon";

type NoValuesFoundProps = {
  text?: string;
  icon?: ICON_NAME;
};

const NoValuesFound = ({ text, icon }: NoValuesFoundProps) => {
  const { t } = useTranslation("common");
  const theme = useTheme();

  return (
    <Stack
      direction="column"
      spacing={2}
      sx={{
        my: 2,
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
      }}>
      <Icon iconName={icon || ICON_NAME.TABLE} fontSize="small" htmlColor={theme.palette.text.secondary} />
      <Typography variant="body2" fontWeight="bold" color={theme.palette.text.secondary}>
        {text || t("no_values_found")}
      </Typography>
    </Stack>
  );
};

export default NoValuesFound;
