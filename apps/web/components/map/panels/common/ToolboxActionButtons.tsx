import { LoadingButton } from "@mui/lab";
import { Button, Stack, Typography } from "@mui/material";
import React from "react";
import { useTranslation } from "react-i18next";

interface ToolboxActionButtonsProps {
  resetFunction: () => void;
  resetDisabled?: boolean;
  runFunction: () => void;
  runDisabled?: boolean;
  isBusy?: boolean;
}

const ToolboxActionButtons = (props: ToolboxActionButtonsProps) => {
  const { resetFunction, resetDisabled, runFunction, runDisabled } = props;
  const { t } = useTranslation("common");

  return (
    <Stack direction="row" justifyContent="space-between" spacing={2} sx={{ width: "100%" }}>
      <Button
        color="error"
        size="small"
        variant="outlined"
        sx={{ flexGrow: "1" }}
        onClick={resetFunction}
        disabled={resetDisabled}>
        {t("reset")}
      </Button>
      <LoadingButton
        size="small"
        variant="contained"
        loading={props.isBusy}
        sx={{ flexGrow: "1" }}
        onClick={runFunction}
        disabled={runDisabled}>
        <Typography variant="body2" fontWeight="bold" color="inherit">
          {t("run")}
        </Typography>
      </LoadingButton>
    </Stack>
  );
};

export default ToolboxActionButtons;
