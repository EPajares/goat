import {
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
  TextField,
  Typography,
} from "@mui/material";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Trans } from "react-i18next";
import { toast } from "react-toastify";
import { mutate } from "swr";

import { FOLDERS_API_BASE_URL, createFolder, deleteFolder, updateFolder } from "@/lib/api/folders";

import type { DialogBaseProps } from "@/types/common/dialog";

export interface SelectedFolderForEdit {
  id: string;
  name: string;
}

interface FolderDialogProps extends DialogBaseProps {
  type: "create" | "update" | "delete";
  selectedFolder?: SelectedFolderForEdit;
  disabled?: boolean;
  onEdit?: () => void;
  existingFolderNames?: string[];
}

const FolderModal: React.FC<FolderDialogProps> = ({
  type,
  selectedFolder,
  open,
  existingFolderNames,
  onClose,
  onEdit,
}) => {
  const [folderName, setFolderName] = useState<string>("");
  const { t } = useTranslation("common");

  const handleFolderEdit = async () => {
    try {
      if (type === "create") {
        await createFolder(folderName);
        toast.success(t("created_successfully"));
      }
      if (selectedFolder?.id) {
        if (type === "delete") {
          await deleteFolder(selectedFolder?.id);
          toast.success(t("deleted_successfully"));
        }

        if (type === "update") {
          await updateFolder(selectedFolder.id, folderName);
          toast.success(t("updated_successfully"));
        }
      }

      mutate((key) => Array.isArray(key) && key[0] === FOLDERS_API_BASE_URL);
    } catch (error) {
      toast.error(error.message);
    }

    setFolderName("");
    onEdit?.();
  };

  return (
    <Dialog
      open={open}
      onClose={() => {
        setFolderName("");
        onClose?.();
      }}>
      <DialogTitle>
        {
          {
            create: t("create_folder"),
            update: t("update_folder"),
            delete: t("delete_folder"),
          }[type]
        }
      </DialogTitle>
      <DialogContent>
        {["update", "create"].includes(type) && (
          <TextField
            autoFocus={true}
            autoComplete="off"
            sx={{ my: 2, minWidth: 300 }}
            id="folder-name"
            defaultValue={selectedFolder?.name || folderName}
            inputProps={{ maxLength: 30 }}
            label={t("folder_name")}
            variant="outlined"
            error={folderName.length > 29 || existingFolderNames?.includes(folderName)}
            helperText={
              folderName.length > 29
                ? t("folder_rule")
                : existingFolderNames?.includes(folderName)
                  ? t("folder_exists")
                  : ""
            }
            onChange={(e) => setFolderName(e.target.value)}
          />
        )}

        {type === "delete" && (
          <DialogContentText>
            <Trans
              i18nKey="common:are_you_sure_to_delete_folder"
              values={{ folder: selectedFolder?.name }}
              components={{ b: <b /> }}
            />
          </DialogContentText>
        )}
      </DialogContent>
      <DialogActions
        disableSpacing
        sx={{
          pb: 2,
        }}>
        <Button
          onClick={() => {
            setFolderName("");
            onClose?.();
          }}
          variant="text"
          sx={{ borderRadius: 0 }}>
          <Typography variant="body2" fontWeight="bold">
            {t("cancel")}
          </Typography>
        </Button>
        <Button
          disabled={folderName === "" && type !== "delete"}
          onClick={handleFolderEdit}
          variant="text"
          color={type === "delete" ? "error" : "primary"}
          sx={{ borderRadius: 0 }}>
          <Typography variant="body2" fontWeight="bold" color="inherit">
            {
              {
                create: t("create"),
                update: t("update"),
                delete: t("delete"),
              }[type]
            }
          </Typography>
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default FolderModal;
