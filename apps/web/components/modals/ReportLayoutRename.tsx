import { LoadingButton } from "@mui/lab";
import {
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

interface ReportLayoutRenameDialogProps {
  open: boolean;
  layoutName: string;
  onRename?: (newName: string) => Promise<void>;
  onClose?: () => void;
}

const ReportLayoutRenameModal: React.FC<ReportLayoutRenameDialogProps> = ({
  open,
  layoutName,
  onClose,
  onRename,
}) => {
  const { t } = useTranslation("common");
  const [isLoading, setIsLoading] = useState(false);
  const [name, setName] = useState(layoutName);

  // Reset name when modal opens with a new layout
  useEffect(() => {
    setName(layoutName);
  }, [layoutName, open]);

  async function handleRename() {
    try {
      setIsLoading(true);
      await onRename?.(name);
      onClose?.();
    } catch (error) {
      console.error("Failed to rename layout:", error);
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="sm">
      <DialogTitle>{t("rename_layout")}</DialogTitle>
      <DialogContent>
        <Stack sx={{ pt: 1 }}>
          <TextField
            autoFocus
            size="small"
            fullWidth
            inputProps={{
              style: {
                fontSize: "0.875rem",
                fontWeight: "bold",
              },
            }}
            value={name}
            onChange={(e) => {
              setName(e.target.value);
            }}
          />
        </Stack>
      </DialogContent>
      <DialogActions
        disableSpacing
        sx={{
          pb: 2,
        }}>
        <Button onClick={onClose} variant="text" sx={{ borderRadius: 0 }}>
          <Typography variant="body2" fontWeight="bold">
            {t("cancel")}
          </Typography>
        </Button>
        <LoadingButton
          onClick={handleRename}
          loading={isLoading}
          variant="text"
          color="primary"
          disabled={!name.trim()}
          sx={{ borderRadius: 0 }}>
          <Typography variant="body2" fontWeight="bold" color="inherit">
            {t("rename")}
          </Typography>
        </LoadingButton>
      </DialogActions>
    </Dialog>
  );
};

export default ReportLayoutRenameModal;
