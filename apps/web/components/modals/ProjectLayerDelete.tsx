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
import { useTranslation } from "react-i18next";
import { Trans } from "react-i18next";
import { toast } from "react-toastify";
import { mutate } from "swr";

import { LAYERS_API_BASE_URL, deleteLayer, useDataset } from "@/lib/api/layers";
import { useJobs } from "@/lib/api/processes";
import { deleteProjectLayer, useProjectLayers } from "@/lib/api/projects";
import { setRunningJobIds } from "@/lib/store/jobs/slice";
import type { ProjectLayer } from "@/lib/validations/project";

import { useAppDispatch, useAppSelector } from "@/hooks/store/ContextHooks";

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
  const { mutate: mutateProjectLayers } = useProjectLayers(projectId);
  const [deleteSourceLayer, setDeleteSourceLayer] = useState(false);
  const { mutate: mutateJobs } = useJobs({ read: false });
  const dispatch = useAppDispatch();
  const runningJobIds = useAppSelector((state) => state.jobs.runningJobIds);

  async function handleDelete() {
    try {
      setIsLoading(true);
      if (!projectLayer) return;

      if (deleteSourceLayer && dataset) {
        const job = await deleteLayer(dataset.id);
        // Add job to running jobs for error tracking only
        if (job?.jobID) {
          mutateJobs();
          dispatch(setRunningJobIds([...runningJobIds, job.jobID]));
        }
        // Invalidate dataset layers cache
        mutate(`${LAYERS_API_BASE_URL}`);
      } else {
        await deleteProjectLayer(projectId, projectLayer.id);
        // Only refresh project layers immediately for non-async deletion
        mutateProjectLayers();
        toast.success(t("layer_removed_from_project"));
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
