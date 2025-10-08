import { Delete } from "@mui/icons-material";
import {
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  IconButton,
  Stack,
  Tooltip,
  Typography,
} from "@mui/material";
import type { GridColDef, GridRenderCellParams } from "@mui/x-data-grid";
import { DataGrid } from "@mui/x-data-grid";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { toast } from "react-toastify";

import { ICON_NAME } from "@p4b/ui/components/Icon";

import { deleteAsset, updateAsset } from "@/lib/api/assets";
import type { Marker } from "@/lib/validations/layer";

import NoValuesFound from "@/components/map/common/NoValuesFound";

type ManageIconsDialogProps = {
  open: boolean;
  onClose: () => void;
  markers: Marker[];
  onDelete: (markerId: string) => void;
  onUpdate: (markerId: string) => void;
};

export const ManageIconsDialog = ({ open, onClose, markers, onDelete, onUpdate }: ManageIconsDialogProps) => {
  const { t } = useTranslation("common");
  const [loading, setLoading] = useState(false);

  // Delete custom icon
  const handleDelete = async (assetId: string) => {
    try {
      setLoading(true);
      await deleteAsset(assetId);
      onDelete(assetId);
    } catch (error) {
      toast.error(t("error_deleting_icon"));
    } finally {
      setLoading(false);
    }
  };

  // Update custom icon
  const handleUpdate = async (assetId: string, field: "name" | "category", value: string) => {
    try {
      setLoading(true);
      await updateAsset(assetId, {
        [field === "name" ? "display_name" : "category"]: value,
      });
      onUpdate(assetId);
    } catch (error) {
      toast.error(t("error_updating_icon"));
    } finally {
      setLoading(false);
    }
  };

  const columns: GridColDef[] = [
    {
      field: "icon",
      headerName: "",
      width: 60,
      sortable: false,
      filterable: false,
      renderCell: (params: GridRenderCellParams) => (
        <img
          src={params.row.url}
          alt={params.row.name}
          style={{ width: 24, height: 24, display: "block", margin: "auto" }}
        />
      ),
    },
    {
      field: "name",
      headerName: t("name"),
      flex: 1,
      editable: !loading, // disable editing while loading
    },
    {
      field: "category",
      headerName: t("category"),
      flex: 1,
      editable: !loading,
    },
    {
      field: "actions",
      headerName: "",
      width: 60,
      sortable: false,
      filterable: false,
      renderCell: (params: GridRenderCellParams) => (
        <Tooltip title={t("delete_icon") || "Delete"} placement="top">
          <span>
            <IconButton
              onClick={() => handleDelete(params.row.id || params.row.url)}
              color="error"
              size="small"
              disabled={loading}>
              <Delete fontSize="small" />
            </IconButton>
          </span>
        </Tooltip>
      ),
    },
  ];

  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="sm">
      <DialogTitle>{t("manage_icons")}</DialogTitle>
      <DialogContent sx={{ px: 0 }}>
        {markers.length ? (
          <div style={{ height: 400, width: "100%" }}>
            <DataGrid
              rows={markers}
              columns={columns}
              getRowId={(row) => row.id || row.url}
              disableColumnMenu
              hideFooter
              density="compact"
              loading={loading} // <-- shows LinearProgress automatically
              processRowUpdate={async (newRow, oldRow) => {
                if (loading) return oldRow; // block edits if busy
                if (newRow.name !== oldRow.name) {
                  await handleUpdate(newRow.id || newRow.url, "name", newRow.name);
                }
                if (newRow.category !== oldRow.category) {
                  await handleUpdate(newRow.id || newRow.url, "category", newRow.category);
                }
                return newRow;
              }}
            />
          </div>
        ) : (
          <NoValuesFound text={t("no_custom_icons")} icon={ICON_NAME.IMAGE} />
        )}
      </DialogContent>
      <DialogActions disableSpacing sx={{ pt: 6, pb: 2, justifyContent: "flex-end" }}>
        <Stack direction="row" spacing={2}>
          <Button onClick={onClose} variant="text" disabled={loading}>
            <Typography variant="body2" fontWeight="bold">
              {t("cancel")}
            </Typography>
          </Button>
        </Stack>
      </DialogActions>
    </Dialog>
  );
};
