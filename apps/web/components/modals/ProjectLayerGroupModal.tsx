import { LoadingButton } from "@mui/lab";
import {
  Alert,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Trans } from "react-i18next";
import { toast } from "react-toastify";

import type { ProjectLayerTreeNode } from "@/lib/validations/project";

type LayerGroupModalMode = "create" | "rename" | "delete";

interface ProjectLayerGroupModalProps {
  open: boolean;
  onClose: () => void;
  mode: LayerGroupModalMode;
  projectId: string;
  existingGroup?: ProjectLayerTreeNode;
  layerTree?: ProjectLayerTreeNode[];
  onSubmit?: (data: { name?: string; groupId?: number }) => Promise<void>;
}

const ProjectLayerGroupModal = ({
  open,
  onClose,
  mode,
  existingGroup,
  layerTree = [],
  onSubmit,
}: ProjectLayerGroupModalProps) => {
  const { t } = useTranslation("common");
  const [isLoading, setIsLoading] = useState(false);
  const [name, setName] = useState("");

  useEffect(() => {
    if (open) {
      if (mode === "rename" && existingGroup) {
        setName(existingGroup.name);
      } else if (mode === "create") {
        setName("");
      }
    }
  }, [open, mode, existingGroup]);

  const handleNameChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setName(e.target.value);
  };

  const handleSubmit = async () => {
    setIsLoading(true);
    try {
      const data: { name?: string; groupId?: number } = {};

      if (mode === "create" || mode === "rename") {
        data.name = name.trim();
      }

      if ((mode === "rename" || mode === "delete") && existingGroup) {
        data.groupId = existingGroup.id;
      }

      if (onSubmit) {
        await onSubmit(data);
      }

      const successMessage =
        mode === "create"
          ? t("group_created_successfully")
          : mode === "rename"
            ? t("group_renamed_successfully")
            : t("group_deleted_successfully");

      toast.success(successMessage);
      handleClose();
    } catch (error) {
      console.error(`Error ${mode}ing group:`, error);
      const errorMessage =
        mode === "create"
          ? t("error_creating_group")
          : mode === "rename"
            ? t("error_renaming_group")
            : t("error_deleting_group");
      toast.error(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const handleClose = () => {
    setName("");
    onClose();
  };

  const getDialogTitle = () => {
    switch (mode) {
      case "create":
        return t("create_group");
      case "rename":
        return t("rename_group");
      case "delete":
        return t("delete_group");
      default:
        return t("group");
    }
  };

  const getSubmitButtonText = () => {
    switch (mode) {
      case "create":
        return t("create");
      case "rename":
        return t("rename");
      case "delete":
        return t("delete");
      default:
        return t("submit");
    }
  };

  // Check if the group has children (layers or subgroups)
  const getGroupChildren = () => {
    if (!existingGroup || mode !== "delete") return { layers: [], groups: [] };

    const children = layerTree.filter((node) => node.parent_id === existingGroup.id);
    const layers = children.filter((node) => node.type === "layer");
    const groups = children.filter((node) => node.type === "group");

    return { layers, groups };
  };

  const { layers: childLayers, groups: childGroups } = getGroupChildren();
  const hasChildren = childLayers.length > 0 || childGroups.length > 0;

  return (
    <Dialog open={open} onClose={handleClose} fullWidth maxWidth="sm">
      <DialogTitle>{getDialogTitle()}</DialogTitle>
      <DialogContent>
        {mode === "delete" ? (
          <>
            <DialogContentText>
              <Trans
                i18nKey="common:are_you_sure_to_delete_group"
                values={{ group: existingGroup?.name }}
                components={{ b: <b /> }}
              />
            </DialogContentText>
            {hasChildren && (
              <Alert severity="warning" sx={{ mt: 2 }}>
                <Stack>
                  <Trans
                    i18nKey="common:group_delete_warning"
                    values={{
                      layerCount: childLayers.length,
                      groupCount: childGroups.length,
                    }}
                    components={{ b: <b /> }}
                  />
                  {childLayers.length > 0 && (
                    <Typography variant="caption" color="text.secondary" sx={{ mt: 1 }}>
                      <b>{t("layers")}:</b> {childLayers.map((layer) => layer.name).join(", ")}
                    </Typography>
                  )}
                  {childGroups.length > 0 && (
                    <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5 }}>
                      <b>{t("subgroups")}:</b> {childGroups.map((group) => group.name).join(", ")}
                    </Typography>
                  )}
                </Stack>
              </Alert>
            )}
          </>
        ) : (
          <Stack spacing={3} sx={{ mt: 1 }}>
            <TextField
              fullWidth
              name="name"
              label={t("group_name")}
              value={name}
              onChange={handleNameChange}
              placeholder={t("enter_group_name")}
              autoFocus
            />
          </Stack>
        )}
      </DialogContent>
      <DialogActions
        disableSpacing
        sx={{
          pb: 2,
        }}>
        <Button onClick={handleClose} variant="text" sx={{ borderRadius: 0 }} disabled={isLoading}>
          <Typography variant="body2" fontWeight="bold">
            {t("cancel")}
          </Typography>
        </Button>
        <LoadingButton
          onClick={handleSubmit}
          loading={isLoading}
          variant="text"
          color={mode === "delete" ? "error" : "primary"}
          sx={{ borderRadius: 0 }}>
          <Typography variant="body2" fontWeight="bold" color="inherit">
            {getSubmitButtonText()}
          </Typography>
        </LoadingButton>
      </DialogActions>
    </Dialog>
  );
};

export default ProjectLayerGroupModal;
