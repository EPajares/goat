/* eslint-disable @typescript-eslint/no-explicit-any */
import { zodResolver } from "@hookform/resolvers/zod";
import KeyboardArrowDownIcon from "@mui/icons-material/KeyboardArrowDown";
import KeyboardArrowRightIcon from "@mui/icons-material/KeyboardArrowRight";
import { LoadingButton } from "@mui/lab";
import {
  Box,
  Button,
  Checkbox,
  Collapse,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  IconButton,
  Radio,
  Stack,
  Step,
  StepLabel,
  Stepper,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from "@mui/material";
import WMSCapabilities from "ol/format/WMSCapabilities";
import WMTSCapabilities from "ol/format/WMTSCapabilities";
import { useCallback, useMemo, useState } from "react";
import React from "react";
import { useForm } from "react-hook-form";
import { useTranslation } from "react-i18next";
import { toast } from "react-toastify";

import { ICON_NAME } from "@p4b/ui/components/Icon";

import { useFolders } from "@/lib/api/folders";
import { useJobs } from "@/lib/api/jobs";
import { createLayer, createRasterLayer } from "@/lib/api/layers";
import { addProjectLayers, useProject, useProjectLayers } from "@/lib/api/projects";
import { setRunningJobIds } from "@/lib/store/jobs/slice";
import { generateLayerGetLegendGraphicUrl, generateWmsUrl } from "@/lib/transformers/wms";
import { convertWmtsToXYZUrl, getWmtsFlatLayers } from "@/lib/transformers/wmts";
import { getBaseUrl } from "@/lib/utils/helpers";
import WFSCapabilities from "@/lib/utils/parser/ol/format/WFSCapabilities";
import type { DataType, GetContentQueryParams } from "@/lib/validations/common";
import { imageryDataType, vectorDataType } from "@/lib/validations/common";
import type { Folder } from "@/lib/validations/folder";
import type { LayerMetadata } from "@/lib/validations/layer";
import {
  createLayerFromDatasetSchema,
  createRasterLayerSchema,
  layerMetadataSchema,
  rasterLayerPropertiesSchema,
} from "@/lib/validations/layer";

import { useAppDispatch, useAppSelector } from "@/hooks/store/ContextHooks";

import { OverflowTypograpy } from "@/components/common/OverflowTypography";
import FolderSelect from "@/components/dashboard/common/FolderSelect";
import NoValuesFound from "@/components/map/common/NoValuesFound";

interface DatasetExternalProps {
  open: boolean;
  onClose?: () => void;
  projectId?: string;
}

interface ExternalDatasetType {
  name: string;
  value: DataType;
  icon: ICON_NAME;
}

interface CapabilitiesType {
  type: DataType;
  directUrl?: string;
  capabilities?: any;
}

const externalDatasetTypes: ExternalDatasetType[] = [
  {
    name: "Web Feature Service (WFS)",
    value: vectorDataType.Enum.wfs,
    icon: ICON_NAME.WFS,
  },
  {
    name: "Web Map Service (WMS)",
    value: imageryDataType.Enum.wms,
    icon: ICON_NAME.WMS,
  },
  {
    name: "Web Map Tile Service (WMTS)",
    value: imageryDataType.Enum.wmts,
    icon: ICON_NAME.WMTS,
  },
  {
    name: "XYZ Tiles",
    value: "xyz",
    icon: ICON_NAME.XYZ,
  },
  {
    name: "Cloud Optimized GeoTIFF (COG)",
    value: imageryDataType.Enum.cog,
    icon: ICON_NAME.LAYERS,
  },
];

const columnsMap = {
  wfs: ["Title", "Name", "Abstract"],
  wms: ["Title", "Name", "Abstract"],
  wmts: ["Title", "Identifier", "Style", "Format", "Abstract"],
  xyz: ["Title", "Identifier"],
  cog: ["Title", "Format"],
};

// Utility function to extract filename from URL
const extractFilenameFromUrl = (url: string): string => {
  try {
    const parsedUrl = new URL(url);
    const pathname = parsedUrl.pathname;
    const filename = pathname.split("/").pop() || "";
    // Remove file extension for display
    return filename.replace(/\.[^/.]+$/, "");
  } catch (error) {
    console.error("Invalid URL", error);
    return "COG Layer";
  }
};

const findExternalDatasetType = (url: string): CapabilitiesType | null => {
  // COG pattern - ends with .tif or .tiff (supports query params and hash fragments)
  const cogPattern = /^https?:\/\/.*\.(tiff?|TIF|TIFF)(\?.*)?(\#.*)?$/;

  // XYZ pattern (Should contain {x}, {y}, {z} and shouldn't contain {TileRow} and {TileCol})
  const xyzPattern = /^(?=.*\{z\})(?=.*\{x\})(?=.*\{y\})(?!.*\{TileRow\})(?!.*\{TileCol\}).*$/;
  const wmtsPattern =
    /^(?=.*\{TileRow\})(?=.*\{TileCol\})(?=.*\{TileMatrix\})(?!.*\{x\})(?!.*\{y\})(?!.*\{z\})(?!.*\{Style\})(?!.*\{TileMatrixSet\}).*$/;

  if (cogPattern.test(url)) {
    return {
      type: imageryDataType.Enum.cog,
      directUrl: url,
    };
  }

  // Check if the URL matches the xyz pattern
  if (xyzPattern.test(url)) {
    // Return the capabilities object for xyz
    return {
      type: "xyz",
      directUrl: url,
    };
  } else if (wmtsPattern.test(url)) {
    // Return the capabilities object for wmts
    return {
      type: "wmts",
      directUrl: url,
    };
  }

  return null;
};

const Row = ({ layer, depth, selectedLayers, handleSelectLayer, getColumns, type }) => {
  const [isExpanded, setIsExpanded] = useState(true);

  const handleToggleExpand = useCallback(
    (e) => {
      e.stopPropagation();
      setIsExpanded(!isExpanded);
    },
    [isExpanded]
  );

  const hasChildren = layer.Layer && layer.Layer.length > 0;
  const isSelected = selectedLayers.includes(layer);

  const handleRowClick = () => {
    if (layer.Name && layer.Style) {
      handleSelectLayer(layer);
    } else {
      if (layer.Layer.length === 0) return;
      setIsExpanded(!isExpanded);
    }
  };

  return (
    <React.Fragment>
      <TableRow
        sx={{
          px: 0,
          cursor: "pointer",
          width: "100%", // Ensure the row takes the full width
        }}
        selected={layer.Name && isSelected}
        onClick={handleRowClick}>
        <TableCell padding="checkbox">
          <Stack direction="row" alignItems="center" sx={{ width: "100%" }}>
            {hasChildren ? (
              <>
                <div style={{ width: depth * 10 }} />
                <IconButton size="small" onClick={handleToggleExpand}>
                  {isExpanded ? <KeyboardArrowDownIcon /> : <KeyboardArrowRightIcon />}
                </IconButton>
              </>
            ) : (
              <div style={{ width: 34 + depth * 10 }} />
            )}
            {layer.Name && layer.Style && (
              <Checkbox
                size="small"
                checked={isSelected}
                onChange={() => handleSelectLayer(layer)}
                onClick={(e) => e.stopPropagation()} // Prevent row click event
              />
            )}
          </Stack>
        </TableCell>
        {getColumns(type).map((column) => (
          <TableCell
            key={column}
            sx={{
              whiteSpace: "nowrap",
              overflow: "hidden",
              textOverflow: "ellipsis",
              maxWidth: 150,
              width: `${95 / getColumns(type).length}%`, // Ensure the cell takes the full width except for the checkbox column
            }}>
            <OverflowTypograpy variant="body2" tooltipProps={{ placement: "top", arrow: true }}>
              {layer[column]}
            </OverflowTypograpy>
          </TableCell>
        ))}
      </TableRow>
      {hasChildren && (
        <TableRow>
          <TableCell sx={{ py: 0, px: 0 }} colSpan={6}>
            <Collapse in={isExpanded} timeout="auto" unmountOnExit>
              {/* {Table Row need to be wrapped in a table tag} */}
              <table style={{ border: "none", borderCollapse: "collapse", width: "100%" }}>
                <tbody style={{ border: "none" }}>
                  {getNestedLayerMultiSelectionTableBody(
                    layer.Layer,
                    depth + 1,
                    selectedLayers,
                    handleSelectLayer,
                    getColumns,
                    type
                  )}
                </tbody>
              </table>
            </Collapse>
          </TableCell>
        </TableRow>
      )}
    </React.Fragment>
  );
};

const getNestedLayerMultiSelectionTableBody = (
  layers,
  depth = 0,
  selectedLayers,
  handleSelectLayer,
  getColumns,
  type
) => {
  if (depth > 4) return null;
  return (
    <React.Fragment>
      {layers.map((layer) => (
        <Row
          key={layer.Name || layer.Title}
          layer={layer}
          depth={depth}
          selectedLayers={selectedLayers}
          handleSelectLayer={handleSelectLayer}
          getColumns={getColumns}
          type={type}
        />
      ))}
    </React.Fragment>
  );
};

const getFlatLayerSingleSelectionTableBody = (
  datasets,
  selectedDatasets,
  handleSelectDataset,
  getColumns,
  type
) => {
  return datasets.map((dataset) => (
    <TableRow
      key={dataset.Name || dataset.Identifier || dataset.Title}
      sx={{
        cursor: "pointer",
      }}
      selected={selectedDatasets.includes(dataset)}
      onClick={() => handleSelectDataset(dataset)}>
      <TableCell padding="checkbox">
        <Radio
          size="small"
          checked={selectedDatasets.includes(dataset)}
          onChange={() => handleSelectDataset(dataset)}
          onClick={(e) => e.stopPropagation()} // Prevent row click event
        />
      </TableCell>
      {getColumns(type).map((column) => (
        <TableCell
          key={column}
          sx={{
            whiteSpace: "nowrap",
            overflow: "hidden",
            textOverflow: "ellipsis",
            maxWidth: 150,
          }}>
          <OverflowTypograpy variant="body2" tooltipProps={{ placement: "top", arrow: true }}>
            {dataset[column]}
          </OverflowTypograpy>
        </TableCell>
      ))}
    </TableRow>
  ));
};

const DatasetsSelectTable = ({ options, type, selectedDatasets, setSelectedDatasets }) => {
  const { t } = useTranslation("common");

  const handleSelectDataset = (dataset) => {
    setSelectedDatasets((prevSelectedDatasets) => {
      if (type === vectorDataType.Enum.wfs || type === imageryDataType.Enum.wmts) {
        return [dataset]; // Allow only one selection
      }
      if (prevSelectedDatasets.includes(dataset)) {
        return prevSelectedDatasets.filter((d) => d !== dataset);
      }
      return [...prevSelectedDatasets, dataset];
    });
  };

  const handleSelectLayer = (layer) => {
    setSelectedDatasets((prevSelectedLayers) => {
      if (prevSelectedLayers.includes(layer)) {
        return prevSelectedLayers.filter((l) => l !== layer);
      }
      return [...prevSelectedLayers, layer];
    });
  };

  const getColumns = (datasetType) => {
    return columnsMap[datasetType] || [];
  };

  return (
    <>
      <Stack direction="row" sx={{ mb: 2 }}>
        <Typography variant="body2">
          <b>{t("type")}:</b> {externalDatasetTypes.find((d) => d.value === type)?.name || type}
        </Typography>
      </Stack>
      <Table size="small" stickyHeader>
        <TableHead>
          <TableRow>
            <TableCell padding="checkbox" />
            {options.length > 0 &&
              getColumns(type).map((column) => <TableCell key={column}>{column}</TableCell>)}
          </TableRow>
        </TableHead>
        <TableBody>
          {type === imageryDataType.enum.wms
            ? getNestedLayerMultiSelectionTableBody(
                options,
                0,
                selectedDatasets,
                handleSelectLayer,
                getColumns,
                type
              )
            : getFlatLayerSingleSelectionTableBody(
                options,
                selectedDatasets,
                handleSelectDataset,
                getColumns,
                type
              )}
        </TableBody>
      </Table>
      {options.length === 0 && (
        <Stack sx={{ mt: 4 }}>
          <NoValuesFound text={t("no_datasets_found")} />
        </Stack>
      )}
      {(type === imageryDataType.Enum.wms || type === imageryDataType.Enum.wmts) && (
        <Stack sx={{ mt: 4 }}>
          <Typography variant="caption" color="textSecondary">
            <b>{t("info")}: </b>
            {type === imageryDataType.Enum.wms ? t("wms_supports_only_epsg_3857") : ""}
            {type === imageryDataType.Enum.wmts ? t("wmts_supports_only_epsg_3857") : ""}
          </Typography>
        </Stack>
      )}
    </>
  );
};

const DatasetExternal: React.FC<DatasetExternalProps> = ({ open, onClose, projectId }) => {
  const { t } = useTranslation("common");
  const dispatch = useAppDispatch();
  const runningJobIds = useAppSelector((state) => state.jobs.runningJobIds);
  const { mutate } = useJobs({
    read: false,
  });
  const { mutate: mutateProjectLayers } = useProjectLayers(projectId);
  const { mutate: mutateProject, project } = useProject(projectId);
  // Step 0: Enter URL
  const steps = [t("enter_url"), t("select_dataset"), t("destination_and_metadata"), t("confirmation")];

  const [activeStep, setActiveStep] = useState(0);
  const [externalUrl, setExternalUrl] = useState<string | null>(null);
  const [capabilities, setCapabilities] = useState<CapabilitiesType | null>(null);

  // Step 1: Select Layer
  // The reason why this is an array is because WMS can have multiple layers.
  // Technically, WFS can have multiple layers too but we only support one layer to be able to use features for analytics.
  const [selectedDatasets, setSelectedDatasets] = useState<any[]>([]);

  const datasetOptions = useMemo(() => {
    const options = [] as any[];
    const _capabilities = capabilities?.capabilities;
    if (capabilities?.type === vectorDataType.Enum.wfs && _capabilities) {
      const version = _capabilities?.version;
      const datasets =
        version === "2.0.0" ? _capabilities?.FeatureTypeList : _capabilities?.FeatureTypeList?.FeatureType;
      if (datasets?.length) {
        datasets.forEach((dataset: any) => {
          options.push(dataset);
        });
      }
    } else if (capabilities?.type === imageryDataType.Enum.wms) {
      const dataset = _capabilities?.Capability?.Layer;
      if (dataset) {
        options.push(dataset);
      }
    } else if (capabilities?.type === imageryDataType.Enum.wmts && _capabilities) {
      const datasets = getWmtsFlatLayers(_capabilities);
      options.push(...datasets);
    }

    return options;
  }, [capabilities]);

  // Step 2: Destination and Metadata
  const queryParams: GetContentQueryParams = {
    order: "descendent",
    order_by: "updated_at",
  };
  const { folders } = useFolders(queryParams);
  const {
    register,
    reset,
    setValue,
    getValues,
    formState: { errors, isValid },
  } = useForm<LayerMetadata>({
    mode: "onChange",
    resolver: zodResolver(layerMetadataSchema),
  });

  const [selectedFolder, setSelectedFolder] = useState<Folder | null>();

  // Other
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isBusy, setIsBusy] = useState(false);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any

  const handleNext = () => {
    // STEP 0: Parse URL.
    if (activeStep === 0) {
      if (!externalUrl) return;
      const urlCapabilities = findExternalDatasetType(externalUrl);
      if (urlCapabilities) {
        setCapabilities(urlCapabilities);
        const homeFolder = folders?.find((folder) => folder.name === "home");
        const projectFolder = folders?.find((folder) => folder.id === project?.folder_id);
        const preselectedFolder = projectFolder || homeFolder;
        if (preselectedFolder) {
          setSelectedFolder(preselectedFolder);
        }

        // For COG type, set default layer name from URL filename
        if (urlCapabilities.type === imageryDataType.Enum.cog) {
          const filename = extractFilenameFromUrl(externalUrl);
          setValue("name", filename || "COG Layer");
        }

        // Skip dataset selection step if it's a direct link and go to destination and metadata step
        setActiveStep((prevActiveStep) => prevActiveStep + 2);
        return;
      }

      setIsBusy(true);
      // Assuming this is a capabilities ogc service
      fetch(externalUrl)
        .then((response) => {
          if (!response.ok) {
            throw new Error(t("error_loading_external_dataset"));
          }
          return response.text();
        })
        .then((text) => {
          const wmsSchema = "opengis.net/wms";
          const wmtsSchema = "opengis.net/wmts";
          const wfsSchema = "opengis.net/wfs";
          let type = null as DataType | null;
          if (text.includes(wmsSchema)) {
            type = imageryDataType.Enum.wms;
          } else if (text.includes(wfsSchema)) {
            type = vectorDataType.Enum.wfs;
          } else if (text.includes(wmtsSchema)) {
            type = imageryDataType.Enum.wmts;
          }
          let parser;
          if (type === vectorDataType.Enum.wfs) {
            parser = new WFSCapabilities();
          } else if (type === imageryDataType.Enum.wms) {
            parser = new WMSCapabilities();
          } else if (type === imageryDataType.Enum.wmts) {
            parser = new WMTSCapabilities();
          } else {
            throw new Error("Could not determine the service type");
          }

          const capabilities = parser.read(text);
          setCapabilities({ type, capabilities });
          setActiveStep((prevActiveStep) => prevActiveStep + 1);
        })
        .catch((_error) => {
          setErrorMessage(t("error_loading_external_dataset"));
        })
        .finally(() => {
          setIsBusy(false);
        });
    }
    // STEP 1: Select Dataset
    else if (activeStep === 1) {
      setActiveStep((prevActiveStep) => prevActiveStep + 1);
      const homeFolder = folders?.find((folder) => folder.name === "home");
      const projectFolder = folders?.find((folder) => folder.id === project?.folder_id);
      const preselectedFolder = projectFolder || homeFolder;
      if (preselectedFolder) {
        setSelectedFolder(preselectedFolder);
      }
      if (
        (capabilities?.type === vectorDataType.Enum.wfs ||
          capabilities?.type === imageryDataType.enum.wmts ||
          capabilities?.type === imageryDataType.enum.wms) &&
        selectedDatasets.length
      ) {
        setValue(
          "name",
          selectedDatasets
            .map((dataset) => dataset.Title || dataset.Name || "")
            .filter((name) => name !== "")
            .join("/")
        );
        if (selectedDatasets.length === 1) {
          setValue("description", selectedDatasets[0].Abstract || "");
        }
      }
    } else if (activeStep === 2) {
      setActiveStep((prevActiveStep) => prevActiveStep + 1);
    }
  };
  const handledBack = () => {
    if (activeStep === 2 && capabilities?.directUrl) {
      // Skip dataset selection step if it's a direct link
      setActiveStep((prevActiveStep) => prevActiveStep - 2);
    } else {
      setActiveStep((prevActiveStep) => prevActiveStep - 1);
    }
  };
  const handleSave = async () => {
    const layerPayload = {
      ...getValues(),
      folder_id: selectedFolder?.id,
    };
    try {
      setIsBusy(true);
      if (capabilities?.type === vectorDataType.Enum.wfs) {
        // Direct WFS import - no intermediate S3 step
        const payload = createLayerFromDatasetSchema.parse({
          ...layerPayload,
          data_type: capabilities.type,
          url: externalUrl,
          other_properties: {
            url: externalUrl,
            layers: [selectedDatasets[0].Name],
            srs: selectedDatasets[0].DefaultCRS,
          },
        });
        const response = await createLayer(payload, projectId);
        const jobId = response?.job_id;
        if (jobId) {
          mutate();
          dispatch(setRunningJobIds([...runningJobIds, jobId]));
        }
      } else if (
        capabilities?.type === imageryDataType.Enum.wms ||
        capabilities?.type === imageryDataType.Enum.wmts ||
        (capabilities?.type === imageryDataType.Enum.xyz && capabilities.directUrl) ||
        capabilities?.type === imageryDataType.Enum.cog
      ) {
        let layers = [] as string[];
        let url = externalUrl;
        const legendUrls = [] as string[];
        if (capabilities.type === imageryDataType.Enum.wms) {
          if (!externalUrl) return;
          const styles = [] as string[];
          const version = capabilities.capabilities?.version;
          const baseUrl = getBaseUrl(externalUrl);
          selectedDatasets.forEach((dataset) => {
            const _layer = dataset.Name;
            const styleName = dataset.Style[0]?.Name; //todo: WMS can have multiple styles. This has to be handled in the future.
            if (!styleName || !_layer) return;
            layers.push(_layer);
            styles.push(styleName);
            const legendGraphicUrl = generateLayerGetLegendGraphicUrl(baseUrl, _layer, styleName, version);
            legendUrls.push(legendGraphicUrl);
          });
          url = generateWmsUrl(baseUrl, layers, styles, version);
        } else if (capabilities.type === imageryDataType.Enum.wmts) {
          if (capabilities.directUrl) {
            url = convertWmtsToXYZUrl(capabilities.directUrl);
          } else {
            layers = selectedDatasets.map((d) => d.Identifier);
            url = convertWmtsToXYZUrl(
              selectedDatasets[0].ResourceURL,
              selectedDatasets[0].Style,
              selectedDatasets[0].TileMatrixSet
            );
          }
        } else if (capabilities.type === imageryDataType.Enum.xyz && capabilities.directUrl) {
          url = capabilities.directUrl;
        } else if (capabilities.type === imageryDataType.Enum.cog) {
          // For COG, save the URL as-is (client will handle cog:// prefix)
          url = externalUrl;
        }

        // Parse default raster properties using the schema
        const defaultRasterProperties = rasterLayerPropertiesSchema.parse({
          visibility: true,
        });

        const payload = createRasterLayerSchema.parse({
          ...layerPayload,
          type: "raster",
          data_type: capabilities.type,
          url,
          properties: defaultRasterProperties,
          other_properties: {
            ...(layers && { layers }),
            ...(legendUrls.length && { legend_urls: legendUrls }),
          },
        });
        const response = await createRasterLayer(payload, projectId);
        if (projectId) {
          await addProjectLayers(projectId, [response.id]);
          mutateProjectLayers();
          mutateProject();
        }
      }
      toast.success(t("success_adding_external_dataset"));
    } catch (_error) {
      toast.error(t("error_adding_external_dataset"));
    } finally {
      setIsBusy(false);
      handleOnClose();
    }
  };
  const handleOnClose = () => {
    setExternalUrl(null);
    setCapabilities(null);
    setSelectedDatasets([]);
    setActiveStep(0);
    cleanDestinationAndMetadata();
    reset();
    onClose && onClose();
  };

  const cleanDestinationAndMetadata = () => {
    setSelectedFolder(null);
    reset();
  };

  const isNextDisabled = useMemo(() => {
    if (activeStep === 0) {
      return !externalUrl;
    }
    if (activeStep === 1) {
      return !selectedDatasets?.length;
    }
    if (activeStep === 2) {
      return !selectedFolder || !isValid;
    }

    return false;
  }, [activeStep, externalUrl, selectedDatasets?.length, selectedFolder, isValid]);

  return (
    <>
      <Dialog open={open} onClose={handleOnClose} fullWidth maxWidth={activeStep === 1 ? "md" : "sm"}>
        <DialogTitle>
          {t("dataset_external")}
          <Box sx={{ width: "100%", pt: 6 }}>
            <Stepper activeStep={activeStep} alternativeLabel>
              {steps.map((label) => (
                <Step key={label}>
                  <StepLabel>{label}</StepLabel>
                </Step>
              ))}
            </Stepper>
          </Box>
        </DialogTitle>
        <DialogContent>
          <Box sx={{ width: "100%" }}>
            {activeStep === 0 && (
              <>
                <TextField
                  id="enter-url"
                  variant="outlined"
                  fullWidth
                  error={!!errorMessage}
                  helperText={errorMessage}
                  placeholder={t("url")}
                  onChange={(e) => {
                    setErrorMessage(null);
                    setExternalUrl(e.target.value);
                    setCapabilities(null);
                    setSelectedDatasets([]);
                    cleanDestinationAndMetadata();
                  }}
                />
                <Typography variant="caption">
                  {t("supported_services")}{" "}
                  {externalDatasetTypes.map((datasetType, index) => (
                    <b key={datasetType.value}>
                      {datasetType.name}
                      {index < externalDatasetTypes.length - 1 ? ", " : ""}
                    </b>
                  ))}
                </Typography>
              </>
            )}
            {activeStep === 1 && (
              <Stack
                direction="column"
                sx={{
                  py: 2,
                }}>
                <DatasetsSelectTable
                  options={datasetOptions}
                  type={capabilities?.type}
                  selectedDatasets={selectedDatasets}
                  setSelectedDatasets={setSelectedDatasets}
                />
              </Stack>
            )}

            {activeStep === 2 && (
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

            {activeStep === 3 && (
              <Stack direction="column" spacing={4}>
                <Typography variant="caption">{t("review_dataset_external")}</Typography>
                <Typography variant="body2">
                  <b>{t("url")}:</b> {externalUrl}
                </Typography>
                <Typography variant="body2">
                  <b>{t("type")}:</b>{" "}
                  {externalDatasetTypes.find((d) => d.value === capabilities?.type)?.name ||
                    capabilities?.type}
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
        </DialogContent>

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
              <LoadingButton
                disabled={isNextDisabled}
                onClick={handleNext}
                loading={isBusy}
                variant="outlined"
                color="primary">
                <Typography variant="body2" fontWeight="bold" color="inherit">
                  {t("next")}
                </Typography>
              </LoadingButton>
            )}

            {activeStep === steps.length - 1 && (
              <LoadingButton onClick={handleSave} variant="outlined" color="primary" loading={isBusy}>
                <Typography variant="body2" fontWeight="bold" color="inherit">
                  {t("save")}
                </Typography>
              </LoadingButton>
            )}
          </Stack>
        </DialogActions>
      </Dialog>
    </>
  );
};

export default DatasetExternal;
