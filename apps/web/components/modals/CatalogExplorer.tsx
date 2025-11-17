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
  Stack,
  Typography,
  debounce,
  useTheme,
} from "@mui/material";
import { useCallback, useState } from "react";
import { useTranslation } from "react-i18next";
import { toast } from "react-toastify";

import { Loading } from "@p4b/ui/components/Loading";

import { useCatalogLayers } from "@/lib/api/layers";
import { addProjectLayers, useProject } from "@/lib/api/projects";
import type { PaginatedQueryParams } from "@/lib/validations/common";
import type { GetDatasetSchema, Layer } from "@/lib/validations/layer";

import { useFilteredProjectLayers } from "@/hooks/map/LayerPanelHooks";

import CatalogDatasetCard from "@/components/dashboard/catalog/CatalogDatasetCard";
import ContentSearchBar from "@/components/dashboard/common/ContentSearchbar";
import NoValuesFound from "@/components/map/common/NoValuesFound";

interface CatalogExplorerProps {
  open: boolean;
  onClose?: () => void;
  projectId: string;
}

const CatalogExplorerModal: React.FC<CatalogExplorerProps> = ({ open, onClose, projectId }) => {
  const { t } = useTranslation("common");
  const theme = useTheme();

  const [queryParams, setQueryParams] = useState<PaginatedQueryParams>({
    order: "descendent",
    order_by: "updated_at",
    size: 10,
    page: 1,
  });

  const [datasetSchema, setDatasetSchema] = useState<GetDatasetSchema>({
    in_catalog: true,
  });

  const { layers: datasets, isLoading: isDatasetLoading } = useCatalogLayers(queryParams, datasetSchema);

  const { mutate: mutateProjectLayers } = useFilteredProjectLayers(projectId);
  const { mutate: mutateProject } = useProject(projectId);
  const [searchText, setSearchText] = useState<string>("");
  const [isBusy, setIsBusy] = useState<boolean>(false);

  const [selectedDataset, setSelectedDataset] = useState<Layer>();

  const resetPage = useCallback(() => {
    setQueryParams({
      ...queryParams,
      page: 1,
    });
  }, [queryParams]);

  const debouncedSetSearchText = debounce((value) => {
    resetPage();
    setSearchText(value || null);
    const newDatasetSchema = { ...datasetSchema };
    if (value) {
      newDatasetSchema.search = value;
    } else {
      delete newDatasetSchema.search;
    }
    setDatasetSchema(newDatasetSchema);
  }, 500);

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
        <DialogTitle>{t("catalog_explorer")}</DialogTitle>

        <ContentSearchBar
          contentType="layer"
          searchText={searchText || ""}
          onSearchTextChange={(text) => {
            debouncedSetSearchText(text);
          }}
        />
        <DialogContent sx={{ backgroundColor: theme.palette.background.default }}>
          {datasets && datasets?.items.length > 0 && (
            <Stack direction="row" sx={{ pb: 2 }}>
              <Typography variant="body1" fontWeight="bold">
                {`${datasets?.total} ${t("datasets")}`}
              </Typography>
            </Stack>
          )}
          <Box
            sx={{
              width: "100%",
            }}>
            <Grid container justifyContent="space-between" spacing={4}>
              <Grid item xs={12}>
                <Stack direction="column" spacing={4}>
                  {!isDatasetLoading &&
                    datasets &&
                    datasets?.items.length > 0 &&
                    datasets.items.map((dataset) => (
                      <CatalogDatasetCard
                        key={dataset.id}
                        dataset={dataset}
                        selected={selectedDataset?.id === dataset.id}
                        onClick={(dataset) => {
                          if (selectedDataset?.id === dataset.id) {
                            setSelectedDataset(undefined);
                            return;
                          }
                          setSelectedDataset(dataset);
                        }}
                      />
                    ))}
                  {isDatasetLoading && (
                    <Box
                      sx={{
                        display: "flex",
                        justifyContent: "center",
                        alignItems: "center",
                      }}>
                      <Loading size={40} />
                    </Box>
                  )}
                  {!isDatasetLoading && datasets?.items?.length === 0 && (
                    <NoValuesFound text={t("no_datasets_found")} />
                  )}
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
            pb: 4,
            justifyContent: "flex-end",
          }}>
          <Stack direction="row" spacing={2} sx={{ pt: 3 }}>
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

export default CatalogExplorerModal;
