import { LoadingButton } from "@mui/lab";
import {
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  MenuItem,
  Select,
  Stack,
  Typography,
} from "@mui/material";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { toast } from "react-toastify";

import { downloadDataset } from "@/lib/api/layers";
import type { FeatureDataExchangeType } from "@/lib/validations/common";
import {
  featureDataExchangeCRS,
  featureDataExchangeType,
  tableDataExchangeType,
} from "@/lib/validations/common";
import type { DatasetDownloadRequest, Layer } from "@/lib/validations/layer";
import type { ProjectLayer } from "@/lib/validations/project";

interface DownloadDatasetDialogProps {
  open: boolean;
  onClose?: () => void;
  disabled?: boolean;
  onDownload?: () => void;
  dataset: ProjectLayer | Layer;
}

const DatsetDownloadModal: React.FC<DownloadDatasetDialogProps> = ({
  open,
  disabled,
  onClose,
  onDownload,
  dataset,
}) => {
  const { t } = useTranslation("common");

  // Support both 'type' (Layer schema) and 'layer_type' (ProjectLayerTreeNode)
  // For ProjectLayerTreeNode, 'type' is "layer" or "group", so we need 'layer_type' for the actual layer type
  const layerType = (dataset as { layer_type?: string }).layer_type || dataset.type;
  const isSpatialLayer = layerType === "feature" || layerType === "raster";

  const [dataDownloadType, setDataDownloadType] = useState<FeatureDataExchangeType>(
    isSpatialLayer ? featureDataExchangeType.Enum.gpkg : tableDataExchangeType.Enum.csv
  );

  const [isBusy, setIsBusy] = useState(false);

  const [dataCrs, setDataCrs] = useState<string | null>(
    isSpatialLayer ? featureDataExchangeCRS.Enum["3857"] : null
  );

  const handleDownload = async () => {
    try {
      if (!dataset) return;
      setIsBusy(true);
      const payload = {
        id: dataset["layer_id"] || dataset["id"],
        file_type: dataDownloadType,
        file_name: dataset.name,
      };
      if (dataCrs) {
        payload["crs"] = `EPSG:${dataCrs}`;
      }
      if (dataset["layer_id"] && dataset["query"] && dataset["query"]["cql"]) {
        payload["query"] = dataset["query"]["cql"];
      }

      const dataBlob = await downloadDataset(payload as DatasetDownloadRequest);
      const url = window.URL.createObjectURL(new Blob([dataBlob]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", `${dataset.name}.zip`);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } catch {
      toast.error(`${t("error_downloading")} ${dataset.name}`);
    } finally {
      setIsBusy(false);
      onClose?.();
    }

    onDownload?.();
  };

  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="xs">
      <DialogTitle>{`${t("download")} "${dataset.name}"`}</DialogTitle>
      <DialogContent>
        <Stack spacing={2} sx={{ py: 2 }}>
          <Box>
            <Typography variant="caption">{t(`download_type`)}</Typography>
            <Select
              fullWidth
              disabled={isBusy}
              sx={{
                my: 2,
              }}
              id="download-simple-select"
              value={dataDownloadType}
              onChange={(e) => setDataDownloadType(e.target.value as FeatureDataExchangeType)}>
              {isSpatialLayer &&
                featureDataExchangeType.options.map((type: string) => (
                  <MenuItem key={type} value={type}>
                    {t(`${type}`)}
                  </MenuItem>
                ))}
              {!isSpatialLayer &&
                tableDataExchangeType.options.map((type: string) => (
                  <MenuItem key={type} value={type}>
                    {t(`${type}`)}
                  </MenuItem>
                ))}
            </Select>
          </Box>
          {isSpatialLayer && (
            <Box>
              <Typography variant="caption">{t(`download_crs`)}</Typography>
              <Select
                fullWidth
                disabled={isBusy}
                sx={{
                  my: 2,
                }}
                id="download-crs-select"
                value={dataCrs}
                onChange={(e) => setDataCrs(e.target.value as string)}>
                {featureDataExchangeCRS.options.map((type: string) => (
                  <MenuItem key={type} value={type}>
                    {t(`${type}`)}
                  </MenuItem>
                ))}
              </Select>
            </Box>
          )}
        </Stack>
      </DialogContent>
      <DialogActions
        disableSpacing
        sx={{
          pb: 2,
        }}>
        <Button onClick={onClose} variant="text">
          <Typography variant="body2" fontWeight="bold">
            {t("cancel")}
          </Typography>
        </Button>
        <LoadingButton loading={isBusy} onClick={handleDownload} disabled={disabled}>
          <Typography variant="body2" fontWeight="bold" color="inherit">
            {t("download")}
          </Typography>
        </LoadingButton>
      </DialogActions>
    </Dialog>
  );
};

export default DatsetDownloadModal;
