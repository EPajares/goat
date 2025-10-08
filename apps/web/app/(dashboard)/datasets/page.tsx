"use client";

import {
  Box,
  Button,
  ClickAwayListener,
  Container,
  Grid,
  ListItemIcon,
  Menu,
  MenuItem,
  MenuList,
  Pagination,
  Paper,
  Stack,
  Typography,
} from "@mui/material";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

import { ICON_NAME, Icon } from "@p4b/ui/components/Icon";

import { useLayers } from "@/lib/api/layers";
import type { PaginatedQueryParams } from "@/lib/validations/common";
import type { GetDatasetSchema } from "@/lib/validations/layer";

import { AddLayerSourceType } from "@/types/common";

import { useAuthZ } from "@/hooks/auth/AuthZ";
import { useJobStatus } from "@/hooks/jobs/JobStatus";

import ContentSearchBar from "@/components/dashboard/common/ContentSearchbar";
import FoldersTreeView from "@/components/dashboard/common/FoldersTreeView";
import TileGrid from "@/components/dashboard/common/TileGrid";
import DatasetExternal from "@/components/modals/DatasetExternal";
import DatasetUploadModal from "@/components/modals/DatasetUpload";

const Datasets = () => {
  const router = useRouter();
  const { t } = useTranslation("common");
  const [queryParams, setQueryParams] = useState<PaginatedQueryParams>({
    order: "descendent",
    order_by: "updated_at",
    size: 10,
    page: 1,
  });
  const [datasetSchema, setDatasetSchema] = useState<GetDatasetSchema>({});
  const [view, setView] = useState<"list" | "grid">("grid");

  const {
    mutate,
    layers: datasets,
    isLoading: isDatasetLoading,
    isError: _isDatasetError,
  } = useLayers(queryParams, datasetSchema);

  const { isOrgEditor } = useAuthZ();
  useJobStatus(mutate);

  const [addDatasetModal, setAddDatasetModal] = useState<AddLayerSourceType | null>(null);

  const [addDatasetAnchorEl, setAddDatasetAnchorEl] = useState<null | HTMLElement>(null);
  const open = Boolean(addDatasetAnchorEl);
  const handleAddDatasetClick = (event: React.MouseEvent<HTMLButtonElement>) => {
    setAddDatasetAnchorEl(event.currentTarget);
  };
  const handleAddDatasetClose = () => {
    setAddDatasetAnchorEl(null);
  };

  const openAddDatasetModal = (sourceType: AddLayerSourceType) => {
    handleAddDatasetClose();
    setAddDatasetModal(sourceType);
  };

  const closeAddDatasetModal = () => {
    setAddDatasetModal(null);
    mutate();
  };

  const addDatasetMenuItems = [
    {
      sourceType: AddLayerSourceType.DatasourceUpload,
      iconName: ICON_NAME.UPLOAD,
      label: t("dataset_upload"),
    },
    {
      sourceType: AddLayerSourceType.DataSourceExternal,
      iconName: ICON_NAME.LINK,
      label: t("dataset_external"),
    },
  ];

  useEffect(() => {
    if (datasets?.pages && queryParams?.page && datasets?.pages < queryParams?.page) {
      setQueryParams({
        ...queryParams,
        page: datasets.pages,
      });
    }
  }, [datasets, queryParams]);

  return (
    <Container sx={{ py: 10, px: 10 }} maxWidth="xl">
      {addDatasetModal === AddLayerSourceType.DatasourceUpload && (
        <DatasetUploadModal open={true} onClose={closeAddDatasetModal} />
      )}
      {addDatasetModal === AddLayerSourceType.DataSourceExternal && (
        <DatasetExternal open={true} onClose={closeAddDatasetModal} />
      )}
      <Box
        sx={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          mb: 8,
        }}>
        <Typography variant="h6">{t("datasets")}</Typography>
        {isOrgEditor && (
          <Button
            disableElevation={true}
            startIcon={<Icon iconName={ICON_NAME.PLUS} style={{ fontSize: 12 }} />}
            onClick={handleAddDatasetClick}>
            {t("add_dataset")}
          </Button>
        )}
        <Menu
          anchorEl={addDatasetAnchorEl}
          sx={{
            "& .MuiPaper-root": {
              boxShadow: "0px 0px 10px 0px rgba(58, 53, 65, 0.1)",
            },
          }}
          anchorOrigin={{ vertical: "bottom", horizontal: "center" }}
          transformOrigin={{ vertical: -5, horizontal: "center" }}
          open={open}
          MenuListProps={{
            "aria-labelledby": "basic-button",
            sx: { p: 0 },
          }}
          onClose={handleAddDatasetClose}>
          <Box>
            <ClickAwayListener onClickAway={handleAddDatasetClose}>
              <MenuList>
                {addDatasetMenuItems.map((item, index) => (
                  <MenuItem key={index} onClick={() => openAddDatasetModal(item.sourceType)}>
                    <ListItemIcon>
                      <Icon iconName={item.iconName} style={{ fontSize: "15px" }} />
                    </ListItemIcon>
                    <Typography variant="body2">{item.label}</Typography>
                  </MenuItem>
                ))}
              </MenuList>
            </ClickAwayListener>
          </Box>
        </Menu>
      </Box>
      <Grid container justifyContent="space-between" spacing={4}>
        <Grid item xs={12}>
          <ContentSearchBar
            contentType="layer"
            view={view}
            setView={setView}
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
        </Grid>
        <Grid item xs={3}>
          <Paper elevation={3} sx={{ backgroundImage: "none" }}>
            <FoldersTreeView
              queryParams={datasetSchema}
              enableActions={isOrgEditor}
              hideMyContent={!isOrgEditor}
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
        <Grid item xs={9}>
          <TileGrid
            view={view}
            items={datasets?.items ?? []}
            isLoading={isDatasetLoading}
            type="layer"
            enableActions={isOrgEditor}
            onClick={(item) => {
              if (item && item.id) {
                router.push(`/datasets/${item.id}`);
              }
            }}
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
        </Grid>
      </Grid>
    </Container>
  );
};

export default Datasets;
