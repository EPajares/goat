import { zodResolver } from "@hookform/resolvers/zod";
import LoadingButton from "@mui/lab/LoadingButton";
import {
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Stack,
  Step,
  StepLabel,
  Stepper,
  TextField,
  Typography,
} from "@mui/material";
import { useEffect, useMemo, useState } from "react";
import { useForm } from "react-hook-form";
import { useTranslation } from "react-i18next";
import { toast } from "react-toastify";

import { requestDatasetUpload } from "@/lib/api/datasets";
import { useFolders } from "@/lib/api/folders";
import { useJobs } from "@/lib/api/jobs";
import { createLayer } from "@/lib/api/layers";
import { useProject } from "@/lib/api/projects";
import { uploadFileToS3 } from "@/lib/services/s3";
import { setRunningJobIds } from "@/lib/store/jobs/slice";
import type { GetContentQueryParams } from "@/lib/validations/common";
import type { Folder } from "@/lib/validations/folder";
import type { LayerMetadata } from "@/lib/validations/layer";
import { createLayerFromDatasetSchema, layerMetadataSchema } from "@/lib/validations/layer";

import { useAppDispatch, useAppSelector } from "@/hooks/store/ContextHooks";

import { MuiFileInput } from "@/components/common/FileInput";
import FolderSelect from "@/components/dashboard/common/FolderSelect";

interface DatasetUploadDialogProps {
  open: boolean;
  onClose?: () => void;
  projectId?: string;
}

const DatasetUploadModal: React.FC<DatasetUploadDialogProps> = ({ open, onClose, projectId }) => {
  const { t } = useTranslation("common");
  const dispatch = useAppDispatch();
  const runningJobIds = useAppSelector((state) => state.jobs.runningJobIds);

  const { project } = useProject(projectId);
  const steps = [t("select_file"), t("destination_and_metadata"), t("confirmation")];
  const { mutate } = useJobs({
    read: false,
  });
  const queryParams: GetContentQueryParams = {
    order: "descendent",
    order_by: "updated_at",
  };
  const { folders } = useFolders(queryParams);
  const [activeStep, setActiveStep] = useState(0);
  const [fileValue, setFileValue] = useState<File>();
  const [fileUploadError, setFileUploadError] = useState<string>();
  const [selectedFolder, setSelectedFolder] = useState<Folder | null>();
  const [isBusy, setIsBusy] = useState(false);
  useEffect(() => {
    const homeFolder = folders?.find((folder) => folder.name === "home");
    const projectFolder = folders?.find((folder) => folder.id === project?.folder_id);
    const preSelectedFolder = projectFolder || homeFolder;
    if (preSelectedFolder) {
      setSelectedFolder(preSelectedFolder);
    }
  }, [folders, project?.folder_id]);

  const {
    register,
    getValues,
    reset,
    formState: { errors, isValid },
  } = useForm<LayerMetadata>({
    mode: "onChange",
    resolver: zodResolver(layerMetadataSchema),
  });

  const handleNext = () => {
    setActiveStep((prevActiveStep) => prevActiveStep + 1);
  };

  const handledBack = () => {
    setActiveStep((prevActiveStep) => prevActiveStep - 1);
  };

  const acceptedFileTypes = useMemo(() => {
    return [".gpkg", ".geojson", ".zip", ".kml", ".csv", ".xlsx"];
  }, []);

  const handleChange = (file) => {
    setFileUploadError(undefined);
    setFileValue(undefined);
    if (file && file.name) {
      const isAcceptedType = acceptedFileTypes.some((type) => file.name.endsWith(type));
      if (!isAcceptedType) {
        setFileUploadError("Invalid file type. Please select a file of type");
        return;
      }

      // Autodetect dataset type (for UI feedback only - backend does actual detection)
      const isFeatureLayer =
        file.name.endsWith(".gpkg") ||
        file.name.endsWith(".geojson") ||
        file.name.endsWith(".shp") ||
        file.name.endsWith(".kml");
      const isTable = file.name.endsWith(".csv") || file.name.endsWith(".xlsx");
      if (!isFeatureLayer && !isTable) {
        setFileUploadError("Invalid file type");
        return;
      }
      setFileValue(file);
    }
  };

  const handleOnClose = () => {
    setFileValue(undefined);
    setActiveStep(0);
    setFileUploadError(undefined);
    setIsBusy(false);
    reset();
    onClose?.();
  };

  const fileName = useMemo(() => {
    if (fileValue) {
      // remove extension if in accepted file types
      const fileExtension = fileValue.name.split(".").pop();
      if (fileExtension && acceptedFileTypes.includes(`.${fileExtension}`)) {
        return fileValue.name.replace(`.${fileExtension}`, "");
      }
      return fileValue.name;
    }
    return "";
  }, [acceptedFileTypes, fileValue]);

  const handleUpload = async () => {
    try {
      if (!fileValue) return;
      setIsBusy(true);

      // Request backend for presigned URL
      const presigned = await requestDatasetUpload({
        filename: fileValue.name,
        content_type: fileValue.type || "application/octet-stream",
        file_size: fileValue.size,
      });

      // Upload file to S3 directly
      await uploadFileToS3(fileValue, presigned);

      // Tell backend to promote → dataset
      const payload = createLayerFromDatasetSchema.parse({
        ...getValues(),
        folder_id: selectedFolder?.id,
        s3_key: presigned.fields.key,
      });

      // Kick off layer creation (type is auto-detected by backend)
      const response = await createLayer(payload, projectId);

      const jobId = response?.job_id;
      if (jobId) {
        mutate();
        dispatch(setRunningJobIds([...runningJobIds, jobId]));
      }
    } catch (error) {
      toast.error(t("error_uploading_dataset"));
      console.error("error", error);
    } finally {
      handleOnClose();
    }
  };

  return (
    <Dialog open={open} onClose={handleOnClose} fullWidth maxWidth="sm">
      <DialogTitle>{t("upload_dataset")}</DialogTitle>
      <DialogContent>
        <Box sx={{ width: "100%" }}>
          <Stepper activeStep={activeStep} alternativeLabel>
            {steps.map((label) => (
              <Step key={label}>
                <StepLabel>{label}</StepLabel>
              </Step>
            ))}
          </Stepper>
        </Box>
      </DialogContent>
      <Box sx={{ px: 4 }}>
        {activeStep === 0 && (
          <>
            <Typography variant="caption">{t("select_file_to_upload")}</Typography>

            <MuiFileInput
              sx={{
                my: 2,
              }}
              inputProps={{
                accept: acceptedFileTypes.join(","),
              }}
              fullWidth
              error={!!fileUploadError}
              helperText={fileUploadError}
              value={fileValue}
              multiple={false}
              onChange={handleChange}
              placeholder={`${t("eg")} file.gpkg, file.geojson, shapefile.zip`}
            />
            <Typography variant="caption">
              {t("supported")} <b>GeoPackage</b>, <b>GeoJSON</b>, <b>Shapefile (.zip)</b>, <b>KML</b>,{" "}
              <b>CSV</b>, <b>XLSX</b>
            </Typography>
          </>
        )}
        {activeStep === 1 && (
          <>
            <Stack direction="column" spacing={4}>
              <FolderSelect
                folders={folders}
                selectedFolder={selectedFolder}
                setSelectedFolder={setSelectedFolder}
              />

              <TextField
                fullWidth
                required
                defaultValue={fileName}
                label={t("name")}
                {...register("name")}
                error={!!errors.name}
                helperText={errors.name?.message}
              />
              <TextField
                fullWidth
                multiline
                rows={4}
                label={t("description")}
                {...register("description")}
                error={!!errors.description}
                helperText={errors.description?.message}
              />
            </Stack>
          </>
        )}
        {activeStep === 2 && (
          <Stack direction="column" spacing={4}>
            <Typography variant="caption">{t("review")}</Typography>
            <Typography variant="body2">
              <b>{t("file")}:</b> {fileValue?.name}
            </Typography>
            <Typography variant="body2">
              <b>{t("destination")}:</b> {selectedFolder?.name}
            </Typography>
            <Typography variant="body2">
              <b>{t("name")}:</b> {getValues("name")}
            </Typography>
            <Typography variant="body2">
              <b>{t("description")}:</b> {getValues("description")}
            </Typography>
          </Stack>
        )}
      </Box>
      <DialogActions
        disableSpacing
        sx={{
          pt: 6,
          pb: 2,
          justifyContent: "space-between",
        }}>
        <Stack direction="row" spacing={2} justifyContent="flex-start">
          {activeStep > 0 && (
            <Button variant="text" onClick={handledBack}>
              <Typography variant="body2" fontWeight="bold">
                {t("back")}
              </Typography>
            </Button>
          )}
        </Stack>
        <Stack direction="row" spacing={2} justifyContent="flex-end">
          <Button onClick={handleOnClose} variant="text">
            <Typography variant="body2" fontWeight="bold">
              {t("cancel")}
            </Typography>
          </Button>
          {activeStep < steps.length - 1 && (
            <Button
              disabled={
                (activeStep === 0 && !fileValue) ||
                (activeStep === 1 && (isValid !== true || selectedFolder === null))
              }
              onClick={handleNext}
              variant="outlined"
              color="primary">
              <Typography variant="body2" fontWeight="bold" color="inherit">
                {t("next")}
              </Typography>
            </Button>
          )}
          {activeStep === steps.length - 1 && (
            <LoadingButton
              onClick={handleUpload}
              disabled={isBusy}
              loading={isBusy}
              variant="contained"
              color="primary">
              <Typography variant="body2" fontWeight="bold" color="inherit">
                {t("upload")}
              </Typography>
            </LoadingButton>
          )}
        </Stack>
      </DialogActions>
    </Dialog>
  );
};

export default DatasetUploadModal;
