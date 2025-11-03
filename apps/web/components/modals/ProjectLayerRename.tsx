import { LoadingButton } from "@mui/lab";
import {
  Button,
  Checkbox,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControlLabel,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import { useParams } from "next/navigation";
import { useState } from "react";
import { toast } from "react-toastify";
import { mutate } from "swr";

import { useTranslation } from "@/i18n/client";

import { LAYERS_API_BASE_URL, updateDataset, useDataset } from "@/lib/api/layers";
import { updateProjectLayer } from "@/lib/api/projects";
import type { ProjectLayer } from "@/lib/validations/project";

interface ProjectLayerRenameDialogProps {
  open: boolean;
  projectLayer: ProjectLayer;
  onRename?: () => void;
  onClose?: () => void;
}

const ProjectLayerRenameModal: React.FC<ProjectLayerRenameDialogProps> = ({
  open,
  projectLayer,
  onClose,
  onRename,
}) => {
  const { t } = useTranslation("common");
  const { projectId } = useParams() as { projectId: string };
  const [isLoading, setIsLoading] = useState(false);
  const { dataset } = useDataset(projectLayer?.layer_id);
  const [renameSourceLayer, setRenameSourceLayer] = useState(false);
  const [layerName, setLayerName] = useState(projectLayer.name);

  async function handleRename() {
    try {
      setIsLoading(true);
      if (!projectLayer) return;
      const updatedProjectLayer = {
        ...projectLayer,
        name: layerName,
      };
      await updateProjectLayer(projectId, projectLayer.id, updatedProjectLayer);
      if (renameSourceLayer && dataset) {
        await updateDataset(dataset.id, {
          name: layerName,
        });

        // Revalidates the dataset layers cache
        mutate((key) => Array.isArray(key) && key[0] === LAYERS_API_BASE_URL);
        toast.success(t("rename_layer_success"));
      }
      onRename?.();
    } catch (error) {
      toast.error(t("error_renaming_layer"));
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="sm">
      <DialogTitle>{t("rename_project_layer")}</DialogTitle>
      <DialogContent>
        <Stack>
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
            defaultValue={layerName}
            onChange={(e) => {
              setLayerName(e.target.value);
            }}
          />
        </Stack>
        {!projectLayer.in_catalog && (
          <Stack sx={{ mt: 2 }}>
            <FormControlLabel
              control={
                <Checkbox
                  size="small"
                  color="primary"
                  checked={renameSourceLayer}
                  onChange={(e) => {
                    setRenameSourceLayer(e.target.checked);
                  }}
                />
              }
              label={
                <Typography variant="body2" fontWeight="bold">
                  {t("rename_dataset_source")}
                </Typography>
              }
            />
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
          onClick={handleRename}
          loading={isLoading}
          variant="text"
          color="primary"
          disabled={false}
          sx={{ borderRadius: 0 }}>
          <Typography variant="body2" fontWeight="bold" color="inherit">
            {t("rename")}
          </Typography>
        </LoadingButton>
      </DialogActions>
    </Dialog>
  );
};

export default ProjectLayerRenameModal;
