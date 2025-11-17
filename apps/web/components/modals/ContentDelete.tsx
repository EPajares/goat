import {
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
  Typography,
} from "@mui/material";
import { useTranslation } from "react-i18next";
import { Trans } from "react-i18next";
import { toast } from "react-toastify";
import { mutate } from "swr";

import { LAYERS_API_BASE_URL, deleteLayer } from "@/lib/api/layers";
import { PROJECTS_API_BASE_URL, deleteProject } from "@/lib/api/projects";

import type { ContentDialogBaseProps } from "@/types/dashboard/content";

interface ContentDeleteDialogProps extends ContentDialogBaseProps {
  disabled?: boolean;
  onDelete?: () => void;
}

const ContentDeleteModal: React.FC<ContentDeleteDialogProps> = ({
  open,
  disabled,
  onClose,
  onDelete,
  type,
  content,
}) => {
  const { t } = useTranslation("common");
  const handleDelete = async () => {
    try {
      if (!content) return;
      if (type === "layer") {
        await deleteLayer(content?.id);
        mutate((key) => Array.isArray(key) && key[0] === LAYERS_API_BASE_URL);
      } else if (type === "project") {
        await deleteProject(content?.id);
        mutate((key) => Array.isArray(key) && key[0] === PROJECTS_API_BASE_URL);
      }
      toast.success(type === "layer" ? t("delete_layer_success") : t("delete_project_success"));
    } catch {
      toast.error(type === "layer" ? t("delete_layer_error") : t("delete_project_error"));
    }

    onDelete?.();
  };

  return (
    <Dialog open={open} onClose={onClose}>
      <DialogTitle>{type === "layer" ? t("delete_layer") : t("delete_project")}</DialogTitle>
      <DialogContent>
        <DialogContentText>
          {type === "layer" ? (
            <Trans
              i18nKey="common:are_you_sure_to_delete_layer"
              values={{ layer: content?.name }}
              components={{ b: <b /> }}
            />
          ) : (
            <Trans
              i18nKey="common:are_you_sure_to_delete_project"
              values={{ project: content?.name }}
              components={{ b: <b /> }}
            />
          )}
        </DialogContentText>
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
        <Button
          onClick={handleDelete}
          variant="text"
          color="error"
          disabled={disabled}
          sx={{ borderRadius: 0 }}>
          <Typography variant="body2" fontWeight="bold" color="inherit">
            {t("delete")}
          </Typography>
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default ContentDeleteModal;
