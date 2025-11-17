import { LoadingButton } from "@mui/lab";
import {
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Grid,
  Pagination,
  Paper,
  Stack,
  Typography,
} from "@mui/material";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { toast } from "react-toastify";

import { useLayers } from "@/lib/api/layers";
import { addProjectLayers, useProject, useProjectLayers } from "@/lib/api/projects";
import type { PaginatedQueryParams } from "@/lib/validations/common";
import type { GetDatasetSchema, Layer } from "@/lib/validations/layer";
import type { Project } from "@/lib/validations/project";

import ContentSearchBar from "@/components/dashboard/common/ContentSearchbar";
import FoldersTreeView from "@/components/dashboard/common/FoldersTreeView";
import TileGrid from "@/components/dashboard/common/TileGrid";

interface DatasetExplorerProps {
  open: boolean;
  onClose?: () => void;
  projectId: string;
}

const DatasetExplorerModal: React.FC<DatasetExplorerProps> = ({ open, onClose, projectId }) => {
  const { t } = useTranslation("common");
  const [queryParams, setQueryParams] = useState<PaginatedQueryParams>({
    order: "descendent",
    order_by: "updated_at",
    size: 10,
    page: 1,
  });
  const [datasetSchema, setDatasetSchema] = useState<GetDatasetSchema>({});

  const {
    layers: datasets,
    isLoading: isDatasetLoading,
    isError: _isDatasetError,
  } = useLayers(queryParams, datasetSchema);
  const [isBusy, setIsBusy] = useState(false);
  const { mutate: mutateProjectLayers } = useProjectLayers(projectId);
  const { mutate: mutateProject } = useProject(projectId);

  const [selectedDataset, setSelectedDataset] = useState<Layer>();

  const handleOnClose = () => {
    onClose && onClose();
  };
  const handleOnAdd = async () => {
    try {
      if (!selectedDataset) return;
      setIsBusy(true);
      await addProjectLayers(projectId, [selectedDataset.id]);
      mutateProjectLayers();
      mutateProject();
    } catch (error) {
      toast.error(t("error_adding_layer"));
    } finally {
      setIsBusy(false);
      handleOnClose();
    }
  };
  return (
    <>
      <Dialog open={open} onClose={handleOnClose} fullWidth maxWidth="md">
        <DialogTitle>{t("dataset_explorer")}</DialogTitle>
        <DialogContent>
          <Box sx={{ width: "100%" }}>
            <Grid container justifyContent="space-between" spacing={4}>
              <Grid item xs={4}>
                <Paper elevation={0} sx={{ backgroundImage: "none" }}>
                  <FoldersTreeView
                    queryParams={datasetSchema}
                    setQueryParams={(params, teamId, organizationId) => {
                      const newQueryParams = { ...queryParams, page: 1 };
                      delete newQueryParams.team_id;
                      delete newQueryParams.organization_id;
                      if (teamId) {
                        newQueryParams.team_id = teamId;
                      } else if (organizationId) {
                        newQueryParams.organization_id = organizationId;
                      }
                      setQueryParams(newQueryParams);
                      setDatasetSchema(params);
                    }}
                  />
                </Paper>
              </Grid>
              <Grid item xs={8}>
                <ContentSearchBar
                  contentType="layer"
                  view="list"
                  queryParams={queryParams}
                  setQueryParams={(queryParams) => {
                    setQueryParams({
                      ...queryParams,
                      page: 1,
                    });
                  }}
                  datasetSchema={datasetSchema}
                  setDatasetSchema={(datasetSchema) => {
                    setDatasetSchema(datasetSchema);
                    setQueryParams({
                      ...queryParams,
                      page: 1,
                    });
                  }}
                />
                <Stack direction="column">
                  <TileGrid
                    view="list"
                    enableActions={false}
                    selected={selectedDataset}
                    onClick={(item: Project | Layer) => {
                      if (item.id === selectedDataset?.id) {
                        setSelectedDataset(undefined);
                      } else {
                        setSelectedDataset(item as Layer);
                      }
                    }}
                    items={datasets?.items ?? []}
                    isLoading={isDatasetLoading}
                    type="layer"
                  />

                  {!isDatasetLoading && datasets && datasets?.items.length > 0 && (
                    <Stack direction="row" justifyContent="center" alignItems="center" sx={{ p: 4 }}>
                      <Pagination
                        count={datasets.pages || 1}
                        size="large"
                        page={queryParams.page || 1}
                        onChange={(_e, page) => {
                          setQueryParams({
                            ...queryParams,
                            page,
                          });
                        }}
                      />
                    </Stack>
                  )}
                </Stack>
              </Grid>
            </Grid>
          </Box>
        </DialogContent>
        <DialogActions
          disableSpacing
          sx={{
            pt: 6,
            pb: 2,
            justifyContent: "flex-end",
          }}>
          <Stack direction="row" spacing={2}>
            <Button onClick={handleOnClose} variant="text">
              <Typography variant="body2" fontWeight="bold">
                {t("cancel")}
              </Typography>
            </Button>
            <LoadingButton
              loading={isBusy}
              variant="contained"
              color="primary"
              onClick={handleOnAdd}
              disabled={!selectedDataset || isDatasetLoading}>
              {t("add_layer")}
            </LoadingButton>
          </Stack>
        </DialogActions>
      </Dialog>
    </>
  );
};

export default DatasetExplorerModal;
