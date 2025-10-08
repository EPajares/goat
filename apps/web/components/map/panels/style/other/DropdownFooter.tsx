import { Box, Button, Stack, Typography } from "@mui/material";
import { useTranslation } from "react-i18next";

type DropdownFooterProps = {
  isValid: boolean;
  onCancel?: () => void;
  onApply?: () => void;
  cancelLabel?: string;
  applyLabel?: string;
};

const DropdownFooter = (props: DropdownFooterProps) => {
  const { t } = useTranslation("common");
  return (
    <>
      <Box sx={{ px: 1 }}>
        <Stack direction="row" alignItems="center" justifyContent="flex-end" sx={{ px: 2 }} spacing={1}>
          <Button variant="text" size="small" sx={{ borderRadius: 0 }} onClick={props.onCancel}>
            <Typography variant="body2" fontWeight="bold">
              {props.cancelLabel || t("common:cancel")}
            </Typography>
          </Button>
          <Button
            variant="text"
            size="small"
            color="primary"
            disabled={!props.isValid}
            sx={{ borderRadius: 0 }}
            onClick={props.onApply}>
            <Typography variant="body2" fontWeight="bold" color="inherit">
              {props.applyLabel || t("common:apply")}
            </Typography>
          </Button>
        </Stack>
      </Box>
    </>
  );
};
export default DropdownFooter;
