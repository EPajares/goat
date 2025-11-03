import { LoadingButton } from "@mui/lab";
import {
  Alert,
  Button,
  Checkbox,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
  FormControlLabel,
  Stack,
  Typography,
} from "@mui/material";
import { useParams } from "next/navigation";
import { useState } from "react";
import { Trans } from "react-i18next";
import { toast } from "react-toastify";
import { mutate } from "swr";

import { useTranslation } from "@/i18n/client";

import { LAYERS_API_BASE_URL, deleteLayer, useDataset } from "@/lib/api/layers";
import { deleteProjectLayer } from "@/lib/api/projects";
import type { ProjectLayer } from "@/lib/validations/project";

interface ProjectLayerDeleteDialogProps {
  open: boolean;
  projectLayer: ProjectLayer;
  onDelete?: () => void;
  onClose?: () => void;
}

const ProjectLayerDeleteModal: React.FC<ProjectLayerDeleteDialogProps> = ({
  open,
  projectLayer,
  onClose,
  onDelete,
}) => {
  const { t } = useTranslation("common");
  const { projectId } = useParams() as { projectId: string };
  const [isLoading, setIsLoading] = useState(false);
  const { dataset } = useDataset(projectLayer?.layer_id);
  const [deleteSourceLayer, setDeleteSourceLayer] = useState(false);

  async function handleDelete() {
    try {
      setIsLoading(true);
      if (!projectLayer) return;
      if (deleteSourceLayer && dataset) {
        await deleteLayer(dataset.id);
        // Revalidates the dataset layers cache
        mutate((key) => Array.isArray(key) && key[0] === LAYERS_API_BASE_URL);
      } else {
        await deleteProjectLayer(projectId, projectLayer.id);
      }
      if (deleteSourceLayer && dataset) {
        toast.success(t("delete_layer_success"));
      }
      onDelete?.();
    } catch (error) {
      toast.error(t("error_removing_layer_from_project"));
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="sm">
      <DialogTitle>{t("delete_project_layer")}</DialogTitle>
      <DialogContent>
        <DialogContentText>
          <Trans
            i18nKey="common:are_you_sure_to_delete_layer"
            values={{ layer: projectLayer?.name }}
            components={{ b: <b /> }}
          />
        </DialogContentText>
        {!projectLayer.in_catalog && (
          <Stack sx={{ mt: 2 }}>
            <FormControlLabel
              control={
                <Checkbox
                  size="small"
                  color="warning"
                  checked={deleteSourceLayer}
                  onChange={(e) => {
                    setDeleteSourceLayer(e.target.checked);
                  }}
                />
              }
              label={
                <Typography variant="body2" fontWeight="bold">
                  {t("delete_dataset_source")}
                </Typography>
              }
            />
            {deleteSourceLayer && dataset && (
              <Alert severity="warning" sx={{ mt: 2 }}>
                <Trans
                  i18nKey="common:dataset_delete_warning"
                  values={{ datasetName: dataset?.name }}
                  components={{ b: <b /> }}
                />
              </Alert>
            )}
          </Stack>
        )}
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
          onClick={handleDelete}
          loading={isLoading}
          variant="text"
          color="error"
          disabled={false}
          sx={{ borderRadius: 0 }}>
          <Typography variant="body2" fontWeight="bold" color="inherit">
            {t("delete")}
          </Typography>
        </LoadingButton>
      </DialogActions>
    </Dialog>
  );
};

export default ProjectLayerDeleteModal;
