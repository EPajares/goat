import { DndContext, closestCenter } from "@dnd-kit/core";
import { restrictToVerticalAxis } from "@dnd-kit/modifiers";
import { SortableContext, arrayMove, useSortable, verticalListSortingStrategy } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { DragIndicator } from "@mui/icons-material";
import {
  Badge,
  Box,
  Button,
  Card,
  ClickAwayListener,
  Grid,
  IconButton,
  ListItemIcon,
  Menu,
  MenuItem,
  MenuList,
  Stack,
  Tooltip,
  Typography,
  useTheme,
} from "@mui/material";
import { useMemo, useState } from "react";
import React from "react";
import { useMap } from "react-map-gl/maplibre";
import { toast } from "react-toastify";

import { ICON_NAME, Icon } from "@p4b/ui/components/Icon";

import { useTranslation } from "@/i18n/client";

import {
  addProjectLayers,
  updateProject,
  updateProjectLayer,
  useProject,
  useProjectScenarioFeatures,
  useProjectScenarios,
} from "@/lib/api/projects";
import { setActiveLayer } from "@/lib/store/layer/slice";
import {
  setActiveLeftPanel,
  setActiveRightPanel,
  setEditingScenario,
  setSelectedScenarioLayer,
} from "@/lib/store/map/slice";
import { zoomToLayer } from "@/lib/utils/map/navigate";
import type { Layer } from "@/lib/validations/layer";
import type { ProjectLayer } from "@/lib/validations/project";

import { AddLayerSourceType, ContentActions, MapLayerActions } from "@/types/common";
import { MapSidebarItemID } from "@/types/map/common";
import type { PanelProps } from "@/types/map/sidebar";

import { useFilteredProjectLayers, useLayerSettingsMoreMenu } from "@/hooks/map/LayerPanelHooks";
import { useAppDispatch, useAppSelector } from "@/hooks/store/ContextHooks";

import { DragHandle } from "@/components/common/DragHandle";
import EmptySection from "@/components/common/EmptySection";
import { OverflowTypograpy } from "@/components/common/OverflowTypography";
import type { PopperMenuItem } from "@/components/common/PopperMenu";
import MoreMenu from "@/components/common/PopperMenu";
import Container from "@/components/map/panels/Container";
import CatalogExplorerModal from "@/components/modals/CatalogExplorer";
import ContentDialogWrapper from "@/components/modals/ContentDialogWrapper";
import DatasetExplorerModal from "@/components/modals/DatasetExplorer";
import DatasetExternalModal from "@/components/modals/DatasetExternal";
import DatasetUploadModal from "@/components/modals/DatasetUpload";
import MapLayerChartModal from "@/components/modals/MapLayerChart";
import ProjectLayerDeleteModal from "@/components/modals/ProjectLayerDelete";
import ProjectLayerRenameModal from "@/components/modals/ProjectLayerRename";

type SortableLayerTileProps = {
  id: number;
  layer: ProjectLayer;
  active: boolean;
  onClick: () => void;
  actions?: React.ReactNode;
  body: React.ReactNode;
};

export const iconMapping = {
  point: ICON_NAME.POINT_FEATURE,
  line: ICON_NAME.LINE_FEATURE,
  polygon: ICON_NAME.POLYGON_FEATURE,
  table: ICON_NAME.TABLE,
  streetNetwork: ICON_NAME.STREET_NETWORK,
};

export function getLayerIcon(layer: ProjectLayer | Layer) {
  if (layer.type === "table") {
    return iconMapping.table;
  }

  if (layer.type === "feature" && layer.feature_layer_type === "street_network") {
    return iconMapping.streetNetwork;
  }

  if (layer.type === "feature" && layer.feature_layer_geometry_type) {
    return iconMapping[layer.feature_layer_geometry_type];
  }

  return ICON_NAME.LAYERS;
}

export function SortableLayerTile(props: SortableLayerTileProps) {
  const theme = useTheme();
  const { attributes, listeners, setNodeRef, transform, transition } = useSortable({ id: props.id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition: `${transition}, border-color 0.2s ease-in-out`,
  };

  return (
    <Card
      onClick={props.onClick}
      sx={{
        cursor: "pointer",
        my: 2,
        pr: 0,
        pl: 1,
        borderLeft: props.active ? `5px ${theme.palette.primary.main} solid` : "5px transparent solid",
        py: 2,
        ":hover": {
          boxShadow: 6,
          ...(!props.active && {
            borderLeft: `5px ${theme.palette.text.secondary} solid`,
          }),
          "& div, & button": {
            opacity: 1,
          },
        },
      }}
      key={props.id}
      ref={setNodeRef}
      style={style}>
      <Grid container alignItems="center" spacing={2}>
        <Grid item xs={1}>
          <DragHandle {...attributes} listeners={listeners}>
            <DragIndicator fontSize="small" />
          </DragHandle>
        </Grid>
        <Grid item xs={8} zeroMinWidth>
          <Stack spacing={1}>{props.body}</Stack>
        </Grid>
        <Grid item xs={3}>
          {props.actions}
        </Grid>
      </Grid>
    </Card>
  );
}

const AddLayerSection = ({ projectId }: { projectId: string }) => {
  const { t } = useTranslation("common");
  const [anchorEl, setAnchorEl] = React.useState<null | HTMLElement>(null);
  const open = Boolean(anchorEl);
  const handleClick = (event: React.MouseEvent<HTMLButtonElement>) => {
    setAnchorEl(event.currentTarget);
  };
  const handleClose = () => {
    setAnchorEl(null);
  };

  const [addLayerSourceOpen, setAddSourceOpen] = useState<AddLayerSourceType | null>(null);
  const openAddLayerSourceDialog = (addType: AddLayerSourceType) => {
    handleClose();
    setAddSourceOpen(addType);
  };

  const closeAddLayerSourceModal = () => {
    setAddSourceOpen(null);
  };

  const menuItems = [
    {
      sourceType: AddLayerSourceType.DatasourceExplorer,
      iconName: ICON_NAME.DATABASE,
      label: t("dataset_explorer"),
    },
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
    {
      sourceType: AddLayerSourceType.CatalogExplorer,
      iconName: ICON_NAME.GLOBE,
      label: t("catalog_explorer"),
    },
  ];

  return (
    <>
      <Stack spacing={4} sx={{ width: "100%" }}>
        <Stack direction="row" spacing={2} alignItems="center">
          <Icon iconName={ICON_NAME.DATABASE} style={{ fontSize: "15px" }} />
          <Typography variant="body2" fontWeight="bold" color="inherit">
            {t("common:source")}
          </Typography>
        </Stack>
        <Button
          onClick={handleClick}
          fullWidth
          size="small"
          startIcon={<Icon iconName={ICON_NAME.PLUS} style={{ fontSize: "15px" }} />}>
          <Typography variant="body2" fontWeight="bold" color="inherit">
            {t("common:add_layer")}
          </Typography>
        </Button>
        <Menu
          anchorEl={anchorEl}
          sx={{
            "& .MuiPaper-root": {
              boxShadow: "0px 0px 10px 0px rgba(58, 53, 65, 0.1)",
            },
          }}
          anchorOrigin={{ vertical: "top", horizontal: "center" }}
          transformOrigin={{ vertical: "bottom", horizontal: "center" }}
          open={open}
          MenuListProps={{
            "aria-labelledby": "basic-button",
            sx: { width: anchorEl && anchorEl.offsetWidth - 10, p: 0 },
          }}
          onClose={handleClose}>
          <Box>
            <ClickAwayListener onClickAway={handleClose}>
              <MenuList>
                {menuItems.map((item, index) => (
                  <MenuItem key={index} onClick={() => openAddLayerSourceDialog(item.sourceType)}>
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
      </Stack>
      {addLayerSourceOpen === AddLayerSourceType.DatasourceExplorer && (
        <DatasetExplorerModal open={true} onClose={closeAddLayerSourceModal} projectId={projectId} />
      )}
      {addLayerSourceOpen === AddLayerSourceType.DatasourceUpload && (
        <DatasetUploadModal open={true} onClose={closeAddLayerSourceModal} projectId={projectId} />
      )}
      {addLayerSourceOpen === AddLayerSourceType.DataSourceExternal && (
        <DatasetExternalModal open={true} onClose={closeAddLayerSourceModal} projectId={projectId} />
      )}
      {addLayerSourceOpen === AddLayerSourceType.CatalogExplorer && (
        <CatalogExplorerModal open={true} onClose={closeAddLayerSourceModal} projectId={projectId} />
      )}
    </>
  );
};

export const LayerVisibilityToggle = ({ layer, toggleLayerVisibility }) => {
  const { t } = useTranslation("common");
  if (layer.type === "table") {
    return null;
  }

  return (
    <Tooltip
      key={layer.id}
      title={layer.properties?.visibility ? t("hide_layer") : t("show_layer")}
      arrow
      placement="top">
      <IconButton
        size="small"
        onClick={(event) => {
          event.stopPropagation();
          toggleLayerVisibility(layer);
        }}>
        <Icon
          iconName={!layer.properties?.visibility ? ICON_NAME.EYE_SLASH : ICON_NAME.EYE}
          style={{
            fontSize: 15,
          }}
        />
      </IconButton>
    </Tooltip>
  );
};

const LayerPanel = ({ projectId }: PanelProps) => {
  const { t } = useTranslation("common");
  const { map } = useMap();
  const dispatch = useAppDispatch();
  const [previousRightPanel, setPreviousRightPanel] = useState<MapSidebarItemID | undefined>(undefined);
  const activeLayerId = useAppSelector((state) => state.layers.activeLayerId);
  const activeRightPanel = useAppSelector((state) => state.map.activeRightPanel);
  const selectedScenarioLayer = useAppSelector((state) => state.map.selectedScenarioLayer);
  const { scenarios } = useProjectScenarios(projectId);
  const { project, mutate: mutateProject } = useProject(projectId);
  const { layers: projectLayers, mutate: mutateProjectLayers } = useFilteredProjectLayers(projectId);
  const { scenarioFeatures } = useProjectScenarioFeatures(projectId, project?.active_scenario_id);
  const scenarioFeaturesCount = useMemo(() => {
    const count = {};
    scenarioFeatures?.features.forEach((feature) => {
      if (!count[feature.properties.layer_project_id]) {
        count[feature.properties.layer_project_id] = 0;
      }
      count[feature.properties.layer_project_id]++;
    });
    return count;
  }, [scenarioFeatures]);

  const {
    getLayerMoreMenuOptions,
    openMoreMenu,
    closeMoreMenu,
    moreMenuState,
    activeLayer: activeLayerMoreMenu,
  } = useLayerSettingsMoreMenu();
  async function toggleLayerVisibility(layer: ProjectLayer) {
    const layers = JSON.parse(JSON.stringify(projectLayers));
    const index = layers.findIndex((l) => l.id === layer.id);
    const layerToUpdate = layers[index];
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    let properties = layerToUpdate.properties as any;
    if (!properties) {
      properties = {};
    }

    properties.visibility = !properties.visibility;

    layerToUpdate.properties = properties;
    await mutateProjectLayers(layers, false);
    await updateProjectLayer(projectId, layer.id, layerToUpdate);
  }
  async function handleDragEnd(event) {
    if (!project) return;
    const { active, over } = event;
    const projectToUpdate = JSON.parse(JSON.stringify(project));
    const layerOrder = projectToUpdate.layer_order;
    const oldIndex = layerOrder.indexOf(active.id);

    const newIndex = layerOrder.indexOf(over.id);
    const newOrderArray = arrayMove(layerOrder, oldIndex, newIndex);
    const updatedProject = {
      ...projectToUpdate,
      layer_order: newOrderArray,
    };
    if (projectLayers) {
      const oldLayer = projectLayers.find((l) => l.id === active.id);
      const newLayer = projectLayers.find((l) => l.id === over.id);
      if (oldLayer && newLayer) {
        // force a re-render of the map layers (can find a better way to do this later)
        oldLayer.updated_at = new Date().toISOString();
        newLayer.updated_at = new Date().toISOString() + "1";
      }
    }
    try {
      mutateProject(updatedProject, false);
      await updateProject(projectId, updatedProject);
    } catch (error) {
      toast.error(t("error_updating_project_layer_order"));
    }
  }

  async function duplicateLayer(layer: ProjectLayer) {
    try {
      await addProjectLayers(projectId, [layer.layer_id]);
      mutateProjectLayers();
      mutateProject();
    } catch (error) {
      toast.error(t("error_duplicating_layer"));
    }
  }

  function openPropertiesPanel(layer: ProjectLayer) {
    if (layer.id !== activeLayerId) {
      dispatch(setActiveLayer(layer.id));
    }
    dispatch(setActiveRightPanel(MapSidebarItemID.PROPERTIES));
  }

  function getActionLayerWidthOffset(layer: ProjectLayer) {
    // todo: find a better way to calculate the width offset without hardcoding the values (maybe using the ref of the action section and get the width)
    let width = 0;
    const offset = 24;
    if (layer.query?.cql && layer.query?.cql["args"]?.length) {
      width += offset;
    }
    if (scenarioFeaturesCount && scenarioFeaturesCount[layer.id]) {
      width += offset;
    }

    return width;
  }

  return (
    <Container
      title={t("layers")}
      close={() => dispatch(setActiveLeftPanel(undefined))}
      direction="left"
      body={
        <>
          {(moreMenuState?.id === ContentActions.DOWNLOAD || moreMenuState?.id === ContentActions.TABLE) &&
            activeLayerMoreMenu && (
              <ContentDialogWrapper
                content={activeLayerMoreMenu}
                action={moreMenuState.id as ContentActions}
                onClose={closeMoreMenu}
                onContentDelete={closeMoreMenu}
                type="layer"
              />
            )}
          {moreMenuState?.id === ContentActions.DELETE && activeLayerMoreMenu && (
            <ProjectLayerDeleteModal
              open={true}
              onClose={closeMoreMenu}
              projectLayer={activeLayerMoreMenu}
              onDelete={() => {
                mutateProjectLayers(projectLayers?.filter((l) => l.id !== activeLayerMoreMenu.id));
                if (activeLayerMoreMenu.id === activeLayerId) {
                  dispatch(setActiveLayer(null));
                }
                mutateProject();
                closeMoreMenu();
              }}
            />
          )}

          {moreMenuState?.id === MapLayerActions.RENAME && activeLayerMoreMenu && (
            <ProjectLayerRenameModal
              open={true}
              onClose={closeMoreMenu}
              projectLayer={activeLayerMoreMenu}
              onRename={() => {
                mutateProjectLayers(
                  projectLayers?.map((l) => (l.id === activeLayerMoreMenu.id ? activeLayerMoreMenu : l))
                );
                mutateProject();
                closeMoreMenu();
              }}
            />
          )}

          {moreMenuState?.id === MapLayerActions.CHART && activeLayerMoreMenu && (
            <MapLayerChartModal
              open={true}
              onClose={closeMoreMenu}
              layer={activeLayerMoreMenu}
              projectId={projectId}
            />
          )}
          <Box>
            {projectLayers && projectLayers?.length > 0 && (
              <DndContext
                collisionDetection={closestCenter}
                modifiers={[restrictToVerticalAxis]}
                onDragEnd={handleDragEnd}
                autoScroll={false}>
                <SortableContext
                  items={projectLayers.map((layer) => layer.id)}
                  strategy={verticalListSortingStrategy}>
                  {projectLayers?.map((layer) => (
                    <SortableLayerTile
                      key={layer.id}
                      id={layer.id}
                      active={activeLayerId === layer.id}
                      onClick={() => {
                        const rightPanelIds = [
                          MapSidebarItemID.PROPERTIES,
                          MapSidebarItemID.FILTER,
                          MapSidebarItemID.STYLE,
                        ];
                        const isActiveRightPanelInIds =
                          activeRightPanel && rightPanelIds.includes(activeRightPanel);

                        dispatch(setActiveLayer(layer.id));
                        setPreviousRightPanel(undefined);

                        if (layer.id === activeLayerId && isActiveRightPanelInIds) {
                          setPreviousRightPanel(activeRightPanel);
                          dispatch(setActiveRightPanel(undefined));
                        }

                        if (layer.id !== activeLayerId) {
                          if (activeRightPanel && !isActiveRightPanelInIds) {
                            setActiveRightPanel(undefined);
                          }

                          if (previousRightPanel) {
                            dispatch(setActiveRightPanel(previousRightPanel));
                          }
                        }
                      }}
                      layer={layer}
                      body={
                        <>
                          <Stack direction="row" spacing={2} alignItems="center">
                            <Typography variant="caption" fontWeight="bold" noWrap>
                              {t(`common:${layer.type}`)}
                            </Typography>
                          </Stack>

                          <Stack
                            direction="row"
                            sx={{
                              width: `calc(100% - ${
                                getActionLayerWidthOffset(layer) ? getActionLayerWidthOffset(layer) : 0
                              }px)`,
                            }}>
                            <OverflowTypograpy
                              variant="body2"
                              fontWeight="bold"
                              tooltipProps={{
                                placement: "bottom",
                                arrow: true,
                              }}>
                              {layer.name}
                            </OverflowTypograpy>
                          </Stack>
                        </>
                      }
                      actions={
                        <Stack direction="row" justifyContent="flex-end" sx={{ pr: 2 }}>
                          <LayerVisibilityToggle
                            layer={layer}
                            toggleLayerVisibility={toggleLayerVisibility}
                          />

                          {scenarioFeaturesCount && scenarioFeaturesCount[layer.id] && (
                            <Tooltip
                              key={layer.id + "_scenario"}
                              title={
                                selectedScenarioLayer && selectedScenarioLayer.value === layer.id
                                  ? t("hide_scenario_features")
                                  : t("show_scenario_features")
                              }
                              arrow
                              placement="top">
                              <IconButton
                                size="small"
                                sx={{ pr: 2 }}
                                color={
                                  selectedScenarioLayer && selectedScenarioLayer.value === layer.id
                                    ? "primary"
                                    : "default"
                                }
                                onClick={(event) => {
                                  event.stopPropagation();
                                  if (selectedScenarioLayer?.value === layer.id) {
                                    dispatch(setSelectedScenarioLayer(undefined));
                                  } else {
                                    const _scenario = scenarios?.items?.find(
                                      (scenario) => scenario.id === project?.active_scenario_id
                                    );
                                    dispatch(setActiveRightPanel(MapSidebarItemID.SCENARIO));
                                    dispatch(setEditingScenario(_scenario));
                                    dispatch(
                                      setSelectedScenarioLayer({
                                        label: layer.name,
                                        value: layer.id,
                                        icon: getLayerIcon(layer),
                                      })
                                    );
                                  }
                                }}>
                                <Badge
                                  badgeContent={scenarioFeaturesCount[layer.id]}
                                  color="primary"
                                  sx={{
                                    "& .MuiBadge-badge": {
                                      fontSize: 9,
                                      height: 15,
                                      minWidth: 15,
                                    },
                                  }}>
                                  <Icon
                                    htmlColor="inherit"
                                    iconName={ICON_NAME.SCENARIO}
                                    style={{
                                      fontSize: 15,
                                    }}
                                  />
                                </Badge>
                              </IconButton>
                            </Tooltip>
                          )}

                          {layer.query?.cql && layer.query?.cql["args"]?.length && (
                            <Tooltip
                              key={layer.id + "_filter"}
                              title={
                                activeLayerId === layer.id && activeRightPanel === MapSidebarItemID.FILTER
                                  ? t("hide_applied_filters")
                                  : t("show_applied_filters")
                              }
                              placement="top"
                              arrow>
                              <IconButton
                                size="small"
                                color={
                                  activeLayerId === layer.id && activeRightPanel === MapSidebarItemID.FILTER
                                    ? "primary"
                                    : "default"
                                }
                                sx={{ pr: 2 }}
                                onClick={(event) => {
                                  event.stopPropagation();
                                  if (
                                    activeLayerId === layer.id &&
                                    activeRightPanel === MapSidebarItemID.FILTER
                                  ) {
                                    dispatch(setActiveRightPanel(undefined));
                                  } else {
                                    if (layer.id !== activeLayerId) {
                                      dispatch(setActiveLayer(layer.id));
                                    }
                                    dispatch(setActiveRightPanel(MapSidebarItemID.FILTER));
                                  }
                                }}>
                                <Badge
                                  badgeContent={layer.query?.cql?.["args"]?.length}
                                  color="primary"
                                  sx={{
                                    "& .MuiBadge-badge": {
                                      fontSize: 9,
                                      height: 15,
                                      minWidth: 15,
                                    },
                                  }}>
                                  <Icon
                                    htmlColor="inherit"
                                    iconName={ICON_NAME.FILTER}
                                    style={{
                                      fontSize: 15,
                                    }}
                                  />
                                </Badge>
                              </IconButton>
                            </Tooltip>
                          )}
                          <MoreMenu
                            menuItems={getLayerMoreMenuOptions(layer.type, !!layer.charts, layer.in_catalog)}
                            menuButton={
                              <Tooltip title={t("more_options")} arrow placement="top">
                                <IconButton size="small">
                                  <Icon iconName={ICON_NAME.MORE_VERT} style={{ fontSize: 15 }} />
                                </IconButton>
                              </Tooltip>
                            }
                            onSelect={async (menuItem: PopperMenuItem) => {
                              if (menuItem.id === MapLayerActions.PROPERTIES) {
                                openPropertiesPanel(layer);
                              } else if (menuItem.id === MapLayerActions.DUPLICATE) {
                                await duplicateLayer(layer);
                              } else if (menuItem.id === MapLayerActions.ZOOM_TO) {
                                if (map) {
                                  zoomToLayer(map, layer.extent);
                                }
                              } else {
                                openMoreMenu(menuItem, layer);
                              }
                            }}
                          />
                        </Stack>
                      }
                    />
                  ))}
                </SortableContext>
              </DndContext>
            )}
          </Box>
          {projectLayers?.length === 0 && (
            <EmptySection label={t("no_layers_added")} icon={ICON_NAME.LAYERS} />
          )}
        </>
      }
      action={<AddLayerSection projectId={projectId} />}
    />
  );
};

export default LayerPanel;
