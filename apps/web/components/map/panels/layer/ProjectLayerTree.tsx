// Icons
import AddIcon from "@mui/icons-material/Add";
// MUI
import {
  Badge,
  Box,
  Button,
  IconButton,
  ListItemIcon,
  ListItemText,
  Menu,
  MenuItem,
  Stack,
  Tooltip,
  Typography,
  useTheme,
} from "@mui/material";
import React, { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { useMap } from "react-map-gl/maplibre";
import { toast } from "react-toastify";

import { ICON_NAME, Icon } from "@p4b/ui/components/Icon";

// ----------------------------------------------------------------------
// 3. MAIN COMPONENT
// ----------------------------------------------------------------------
// Redux
import { setSelectedLayers } from "@/lib/store/layer/slice";
import { setActiveRightPanel } from "@/lib/store/map/slice";
import { rgbToHex } from "@/lib/utils/helpers";
import { zoomToLayer } from "@/lib/utils/map/navigate";
// API & Store
import type {
  ProjectLayer,
  ProjectLayerGroup,
  ProjectLayerTreeNode,
  ProjectLayerTreeUpdate,
} from "@/lib/validations/project";

import { AddLayerSourceType, ContentActions, MapLayerActions } from "@/types/common";
import { MapSidebarItemID } from "@/types/map/common";

import { useLayerSettingsMoreMenu } from "@/hooks/map/LayerPanelHooks";
import { useAppDispatch, useAppSelector } from "@/hooks/store/ContextHooks";

// Common Components
import MoreMenu from "@/components/common/PopperMenu";
import type { PopperMenuItem } from "@/components/common/PopperMenu";
// Modals
import CatalogExplorerModal from "@/components/modals/CatalogExplorer";
import ContentDialogWrapper from "@/components/modals/ContentDialogWrapper";
import DatasetExplorerModal from "@/components/modals/DatasetExplorer";
import DatasetExternalModal from "@/components/modals/DatasetExternal";
import DatasetUploadModal from "@/components/modals/DatasetUpload";
import MapLayerChartModal from "@/components/modals/MapLayerChart";
import ProjectLayerDeleteModal from "@/components/modals/ProjectLayerDelete";
import ProjectLayerGroupModal from "@/components/modals/ProjectLayerGroupModal";
import ProjectLayerRenameModal from "@/components/modals/ProjectLayerRename";

// Tree Components
import type { BaseTreeItem } from "./DraggableTreeView";
import { DraggableTreeView } from "./DraggableTreeView";
import { LayerIcon } from "./legend/LayerIcon";
import { LayerLegendPanel } from "./legend/LayerLegend";

// Extended tree item interface to include project layer data
interface ProjectTreeItem extends BaseTreeItem {
  data: ProjectLayerTreeNode;
  canExpand?: boolean;
}

// 1. HELPER COMPONENTS

const AddLayerButton = ({
  projectId,
  variant = "outlined",
  startIcon = true,
}: {
  projectId: string;
  variant?: "text" | "outlined" | "contained";
  startIcon?: boolean;
}) => {
  const { t } = useTranslation("common");
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [addSourceType, setAddSourceType] = useState<AddLayerSourceType | null>(null);
  const open = Boolean(anchorEl);
  const menuItems = [
    { type: AddLayerSourceType.DatasourceExplorer, icon: ICON_NAME.DATABASE, label: t("dataset_explorer") },
    { type: AddLayerSourceType.DatasourceUpload, icon: ICON_NAME.UPLOAD, label: t("dataset_upload") },
    { type: AddLayerSourceType.DataSourceExternal, icon: ICON_NAME.LINK, label: t("dataset_external") },
    { type: AddLayerSourceType.CatalogExplorer, icon: ICON_NAME.GLOBE, label: t("catalog_explorer") },
  ];
  return (
    <>
      <Button
        variant={variant}
        size="small"
        startIcon={startIcon ? <AddIcon fontSize="small" /> : undefined}
        onClick={(e) => setAnchorEl(e.currentTarget)}
        sx={{ borderRadius: 4, textTransform: "none", fontWeight: "bold", whiteSpace: "nowrap" }}>
        {t("add_layer")}
      </Button>
      <Menu
        anchorEl={anchorEl}
        open={open}
        onClose={() => setAnchorEl(null)}
        anchorOrigin={{ vertical: "bottom", horizontal: "right" }}
        transformOrigin={{ vertical: "top", horizontal: "right" }}>
        {menuItems.map((item) => (
          <MenuItem
            key={item.type}
            onClick={() => {
              setAddSourceType(item.type);
              setAnchorEl(null);
            }}>
            <ListItemIcon>
              <Icon iconName={item.icon} style={{ fontSize: 15 }} />
            </ListItemIcon>
            <ListItemText primaryTypographyProps={{ variant: "body2" }}>{item.label}</ListItemText>
          </MenuItem>
        ))}
      </Menu>
      {addSourceType === AddLayerSourceType.DatasourceExplorer && (
        <DatasetExplorerModal open={true} onClose={() => setAddSourceType(null)} projectId={projectId} />
      )}
      {addSourceType === AddLayerSourceType.DatasourceUpload && (
        <DatasetUploadModal open={true} onClose={() => setAddSourceType(null)} projectId={projectId} />
      )}
      {addSourceType === AddLayerSourceType.DataSourceExternal && (
        <DatasetExternalModal open={true} onClose={() => setAddSourceType(null)} projectId={projectId} />
      )}
      {addSourceType === AddLayerSourceType.CatalogExplorer && (
        <CatalogExplorerModal open={true} onClose={() => setAddSourceType(null)} projectId={projectId} />
      )}
    </>
  );
};

// --- Empty State ---
const EmptyLayerState = ({ projectId, isEditMode }: { projectId: string; isEditMode: boolean }) => {
  const { t } = useTranslation("common");
  const theme = useTheme();
  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        flexGrow: 1,
        p: 4,
        textAlign: "center",
        height: "100%",
        color: theme.palette.text.secondary,
      }}>
      <Box sx={{ mb: 2 }}>
        <Icon
          iconName={ICON_NAME.LAYERS}
          style={{ fontSize: "48px", color: theme.palette.action.disabled }}
        />
      </Box>
      <Typography variant="body1" fontWeight="bold" gutterBottom>
        {t("no_layers_added")}
      </Typography>
      <Typography variant="caption" sx={{ mb: 4, maxWidth: 200 }}>
        {isEditMode ? t("start_building_map_desc") : t("no_active_layers")}
      </Typography>
      {isEditMode && (
        <Stack spacing={2} direction="column" alignItems="center" sx={{ width: "100%" }}>
          <Box sx={{ width: "100%", maxWidth: 200, display: "flex", justifyContent: "center" }}>
            <AddLayerButton projectId={projectId} variant="contained" />
          </Box>
        </Stack>
      )}
    </Box>
  );
};

// ----------------------------------------------------------------------
// 2. UTILS
// ----------------------------------------------------------------------
function formatApiDataForDnd(nodes: ProjectLayerTreeNode[]): ProjectTreeItem[] {
  // First, identify which groups are invisible
  const invisibleGroupIds = new Set(
    nodes
      .filter((node) => node.type === "group" && !(node.properties?.visibility ?? true))
      .map((node) => node.id)
  );

  // Function to check if a node should be hidden (invisible group or child of invisible group)
  const shouldHideNode = (node: ProjectLayerTreeNode): boolean => {
    const nodeVisibility = node.properties?.visibility ?? true;
    if (node.type === "group" && !nodeVisibility) {
      return false; // Show invisible groups themselves, but hide their children
    }

    // Check if this node is a child of an invisible group
    let currentParentId = node.parent_id;
    while (currentParentId) {
      if (invisibleGroupIds.has(currentParentId)) {
        return true; // Hide children of invisible groups
      }
      // Find the parent node to check its parent
      const parentNode = nodes.find((n) => n.id === currentParentId && n.type === "group");
      currentParentId = parentNode?.parent_id || null;
    }

    return false;
  };

  return nodes
    .filter((node) => !shouldHideNode(node))
    .map((node) => ({
      id: `${node.type}-${node.id}`,
      parentId: node.parent_id ? `group-${node.parent_id}` : null,
      label: node.name,
      collapsed:
        node.type === "group"
          ? !(node.properties?.expanded ?? true) // For groups, use expanded property
          : (node.properties?.legend?.collapsed ?? false), // For layers, use legend.collapsed property
      isGroup: node.type === "group",
      data: node,
      // Hide expand/collapse functionality for invisible groups
      canExpand: node.type === "group" ? (node.properties?.visibility ?? true) : undefined,
    }));
}

function formatDndDataForApi(flatItems: ProjectTreeItem[]): ProjectLayerTreeUpdate {
  const items = flatItems.map((item, index) => {
    const parts = item.id.split("-");
    const id = parseInt(parts[1], 10);
    const type = parts[0] as "group" | "layer";
    let parent_id: number | null = null;
    if (item.parentId) {
      parent_id = parseInt(item.parentId.split("-")[1], 10);
    }

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const updateItem: any = {
      id,
      type,
      order: index,
      parent_id,
      properties: {},
    };

    // Handle properties based on item type
    if (type === "group") {
      // For groups: include collapsed state, visibility, and expanded state
      if (item.data.properties) {
        updateItem.properties = { ...item.data.properties };
      }

      // Include expanded state (opposite of collapsed for groups)
      updateItem.properties.expanded = !item.collapsed;

      // Include visibility if it exists (get from properties)
      const nodeVisibility = item.data.properties?.visibility;
      if (nodeVisibility !== undefined) {
        updateItem.properties.visibility = nodeVisibility;
      }
    } else if (type === "layer") {
      // For layers: create a deep copy to avoid read-only property errors
      if (item.data.properties) {
        updateItem.properties = JSON.parse(JSON.stringify(item.data.properties));
      }

      // Include visibility if it exists (get from properties)
      const nodeVisibility = item.data.properties?.visibility;
      if (nodeVisibility !== undefined) {
        updateItem.properties.visibility = nodeVisibility;
      }

      // Update legend collapsed state from the tree item's collapsed property
      if (!updateItem.properties.legend) {
        updateItem.properties.legend = {};
      }
      updateItem.properties.legend.collapsed = item.collapsed;
    }

    return updateItem;
  });
  return { items };
}

const castNodeToProjectLayer = (node: ProjectLayerTreeNode): ProjectLayer => {
  return {
    ...node,
    layer_id: node.layer_id || "",
    id: node.id,
    name: node.name,
    properties: node.properties || {},
  } as unknown as ProjectLayer;
};

// Helper function to filter menu options for view mode
const filterMenuForViewMode = (menuOptions: PopperMenuItem[]): PopperMenuItem[] => {
  const excludedActions = [ContentActions.DELETE, MapLayerActions.RENAME, MapLayerActions.DUPLICATE];
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  return menuOptions.filter((option) => !excludedActions.includes(option.id as any));
};

// ----------------------------------------------------------------------

// ----------------------------------------------------------------------

interface ProjectLayerTreeProps {
  projectId: string;
  projectLayers?: ProjectLayer[];
  projectLayerGroups?: ProjectLayerGroup[];
  onTreeUpdate?: (updatePayload: ProjectLayerTreeUpdate) => Promise<void>;
  onCreateGroup?: (groupData: { name: string; parent_id?: number }) => Promise<void>;
  onUpdateGroup?: (groupData: { name?: string; groupId?: number }) => Promise<void>;
  onDeleteGroup?: (groupData: { groupId?: number }) => Promise<void>;
  onLayerDuplicate?: (layerId: string) => Promise<void>;
  isLoading?: boolean;
  viewMode?: "edit" | "view";
}

export const ProjectLayerTree = ({
  projectId,
  projectLayers = [],
  projectLayerGroups = [],
  onTreeUpdate,
  onCreateGroup,
  onUpdateGroup,
  onDeleteGroup,
  onLayerDuplicate,
  isLoading,
  viewMode = "edit",
}: ProjectLayerTreeProps) => {
  const { t } = useTranslation("common");
  const theme = useTheme();
  const { map } = useMap();
  const dispatch = useAppDispatch();
  const currentZoom = useAppSelector((state) => state.map.currentZoom);

  const [items, setItems] = useState<ProjectTreeItem[]>([]);
  const [groupModal, setGroupModal] = useState<{
    open: boolean;
    mode: "create" | "rename" | "delete";
    group?: ProjectLayerTreeNode;
  }>({ open: false, mode: "create" });

  const activeLayerId = useAppSelector((state) => state.layers.activeLayerId);
  const activeRightPanel = useAppSelector((state) => state.map.activeRightPanel);
  const selectedLayerIds = useAppSelector((state) => state.layers.selectedLayerIds || []);

  const {
    getLayerMoreMenuOptions,
    openMoreMenu,
    closeMoreMenu,
    moreMenuState,
    activeLayer: activeLayerMoreMenu,
  } = useLayerSettingsMoreMenu();

  const isEditMode = viewMode === "edit";

  // Combine layers and groups into tree nodes
  const treeData = useMemo(() => {
    const nodes: ProjectLayerTreeNode[] = [];

    // Add groups as tree nodes
    projectLayerGroups.forEach((group) => {
      nodes.push({
        id: group.id,
        type: "group",
        name: group.name,
        parent_id: group.parent_id,
        order: group.order ?? 0, // Provide default value for order
        extent: "", // Groups don't have extent, use empty string as default
        properties: group.properties, // Include properties for groups
      });
    });

    // Add layers as tree nodes
    projectLayers.forEach((layer) => {
      nodes.push({
        id: layer.id,
        type: "layer",
        name: layer.name,
        parent_id: layer.layer_project_group_id,
        order: layer.order ?? 0, // Provide default value for order
        extent: layer.extent || "", // Provide default value for extent
        layer_id: layer.layer_id,
        layer_type: layer.type,
        geometry_type: layer.feature_layer_geometry_type,
        properties: layer.properties,
        query: layer.query,
        other_properties: layer.other_properties,
      });
    });

    return nodes.sort((a, b) => a.order - b.order);
  }, [projectLayers, projectLayerGroups]);

  useEffect(() => {
    if (treeData) setItems(formatApiDataForDnd(treeData));
  }, [treeData]);

  const treeSelectedIds = useMemo(() => {
    if (selectedLayerIds.length === 0) return [];
    return items
      .filter((item) => {
        const node = item.data;
        // Safety check for node existence
        return node && selectedLayerIds.includes(node.id);
      })
      .map((item) => item.id);
  }, [selectedLayerIds, items]);

  // --- Handlers ---

  const handleVisibilityToggle = async (node: ProjectLayerTreeNode, e: React.MouseEvent) => {
    e.stopPropagation();

    const currentVisibility = node.properties?.visibility ?? true;

    // Update local UI state optimistically - create deep copies to avoid read-only errors
    const newItems = items.map((i) => {
      if (i.data.id === node.id && i.data.type === node.type) {
        const updatedData = {
          ...i.data,
          properties: {
            ...i.data.properties,
            visibility: !currentVisibility,
          },
        };
        return { ...i, data: updatedData };
      }
      return i;
    });
    setItems(newItems);

    try {
      // Create update payload for this visibility change
      const updatePayload = formatDndDataForApi(newItems);
      if (onTreeUpdate) {
        await onTreeUpdate(updatePayload);
      }
    } catch (err) {
      // Revert local state on error
      setItems(items);
      toast.error(t("error_updating_visibility"));
      console.error("Error in handleVisibilityToggle:", err);
    }
  };

  const handleProperties = (layer: ProjectLayer) => {
    dispatch(setSelectedLayers([layer.id]));
    dispatch(setActiveRightPanel(MapSidebarItemID.PROPERTIES));
  };

  const handleStyle = (layer: ProjectLayer) => {
    dispatch(setSelectedLayers([layer.id]));
    dispatch(setActiveRightPanel(MapSidebarItemID.STYLE));
  };

  const handleDuplicate = async (layer: ProjectLayer) => {
    try {
      if (onLayerDuplicate) {
        await onLayerDuplicate(layer.layer_id);
      }
    } catch (error) {
      toast.error(t("error_duplicating_layer"));
    }
  };

  const handleNodeClick = (compositeIds: string[]) => {
    const realIds = compositeIds
      .map((cId) => {
        const item = items.find((i) => i.id === cId);
        return item?.data?.id;
      })
      .filter((id) => id !== undefined);
    dispatch(setSelectedLayers(realIds));

    if (isEditMode && realIds.length > 0) {
      // Get the first selected layer to determine default panel
      const firstSelectedItem = items.find((i) => {
        const node = i.data;
        return node && realIds.includes(node.id);
      });

      if (firstSelectedItem) {
        const node = firstSelectedItem.data;
        const layerType = node.layer_type;

        // Set default panel based on layer type
        if (layerType === "raster") {
          dispatch(setActiveRightPanel(MapSidebarItemID.STYLE));
        } else if (layerType === "table") {
          dispatch(setActiveRightPanel(MapSidebarItemID.FILTER));
        } else {
          // Vector layers default to Style
          dispatch(setActiveRightPanel(MapSidebarItemID.STYLE));
        }
      }
    } else {
      dispatch(setActiveRightPanel(undefined));
    }
  };

  const handleCreateGroup = () => {
    setGroupModal({ open: true, mode: "create" });
  };

  const handleGroupModalSubmit = async (data: { name?: string; groupId?: number }) => {
    try {
      if (groupModal.mode === "create" && data.name && onCreateGroup) {
        await onCreateGroup({ name: data.name });
      } else if (groupModal.mode === "rename" && onUpdateGroup) {
        await onUpdateGroup(data);
      } else if (groupModal.mode === "delete" && onDeleteGroup) {
        await onDeleteGroup(data);
      }

      setGroupModal({ open: false, mode: "create" });
    } catch (error) {
      throw error;
    }
  };

  // --- ROW ACTIONS ---
  const RenderRowActions = ({ item }: { item: ProjectTreeItem }) => {
    const node = item.data as ProjectLayerTreeNode;
    const nodeVisibility = node.properties?.visibility ?? true;
    const [anchorEl] = useState<null | HTMLElement>(null);
    const isOpen = Boolean(anchorEl);

    // Prepare Menu Options
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    let menuOptions: PopperMenuItem[] = [];
    if (node.type === "group") {
      menuOptions = [
        ...(node.extent
          ? [
              {
                id: MapLayerActions.ZOOM_TO,
                label: t("zoom_to") || "Zoom To",
                icon: ICON_NAME.ZOOM_IN,
              },
            ]
          : []),
        { id: MapLayerActions.RENAME, label: t("rename") || "Rename", icon: ICON_NAME.EDIT },
        {
          id: ContentActions.DELETE,
          label: t("delete") || "Delete",
          icon: ICON_NAME.TRASH,
          color: "error.main",
        },
      ];
    } else {
      menuOptions = getLayerMoreMenuOptions(
        (node.layer_type as "table" | "feature" | "raster") || "feature",
        !!node.query,
        false
      );
    }

    // Filter menu options based on view mode
    if (viewMode === "view") {
      menuOptions = filterMenuForViewMode(menuOptions);
    }

    const hasFilter = node.query?.cql?.["args"]?.length;
    const isFilterActive = activeLayerId === node.id && activeRightPanel === MapSidebarItemID.FILTER;

    return (
      <Stack
        direction="row"
        alignItems="center"
        spacing={1}
        // Class for parent CSS to keep opacity 1 when menu open
        className={isOpen ? "menu-open" : ""}>
        {/* Filter Badge - Only show in edit mode */}
        {isEditMode && node.type === "layer" && hasFilter && (
          <Tooltip
            title={isFilterActive ? t("hide_applied_filters") : t("show_applied_filters")}
            placement="top">
            <IconButton
              size="small"
              color={isFilterActive ? "primary" : "default"}
              onClick={(e) => {
                e.stopPropagation();
                if (isFilterActive) dispatch(setActiveRightPanel(undefined));
                else {
                  if (node.id !== activeLayerId) dispatch(setSelectedLayers([node.id]));
                  dispatch(setActiveRightPanel(MapSidebarItemID.FILTER));
                }
              }}
              sx={{ p: 0.5 }}>
              <Badge
                badgeContent={hasFilter}
                color="primary"
                sx={{ "& .MuiBadge-badge": { fontSize: 9, height: 15, minWidth: 15 } }}>
                <Icon htmlColor="inherit" iconName={ICON_NAME.FILTER} style={{ fontSize: "15px" }} />
              </Badge>
            </IconButton>
          </Tooltip>
        )}

        {/* Visibility - Don't show for table layers */}
        {node.layer_type !== "table" && (
          <Tooltip title={nodeVisibility ? t("hide") : t("show")} placement="top">
            <IconButton size="small" onClick={(e) => handleVisibilityToggle(node, e)} sx={{ px: 0.5 }}>
              <Icon
                iconName={!nodeVisibility ? ICON_NAME.EYE_SLASH : ICON_NAME.EYE}
                style={{ fontSize: "15px" }}
              />
            </IconButton>
          </Tooltip>
        )}

        {/* More Menu - Show if we have menu options */}
        {menuOptions.length > 0 && (
          <MoreMenu
            menuItems={menuOptions}
            disablePortal={false}
            menuButton={
              <Tooltip title={t("more_options")} placement="top">
                <IconButton size="small" sx={{ px: 0.5 }}>
                  <Icon iconName={ICON_NAME.MORE_VERT} style={{ fontSize: "15px" }} />
                </IconButton>
              </Tooltip>
            }
            onSelect={async (menuItem: PopperMenuItem) => {
              // Handle Zoom To for both layers and groups
              if (menuItem.id === MapLayerActions.ZOOM_TO) {
                if (map && node.extent) zoomToLayer(map, node.extent);
                return;
              }
              // Handle layer-specific actions
              if (node.type === "layer") {
                const target = castNodeToProjectLayer(node);
                if (menuItem.id === MapLayerActions.PROPERTIES) {
                  handleProperties(target);
                } else if (menuItem.id === MapLayerActions.STYLE) {
                  handleStyle(target);
                } else if (menuItem.id === MapLayerActions.DUPLICATE) {
                  handleDuplicate(target);
                } else {
                  openMoreMenu(menuItem, target);
                }
              } else {
                // Handle group-specific actions (rename, delete)
                if (menuItem.id === MapLayerActions.RENAME && node.type === "group") {
                  setGroupModal({ open: true, mode: "rename", group: node });
                } else if (menuItem.id === ContentActions.DELETE && node.type === "group") {
                  setGroupModal({ open: true, mode: "delete", group: node });
                } else {
                  // Cast group node to ProjectLayer format for compatibility with existing modals
                  const groupAsLayer = castNodeToProjectLayer(node);
                  openMoreMenu(menuItem, groupAsLayer);
                }
              }
            }}
          />
        )}
      </Stack>
    );
  };

  // --- ICONS & LEGEND ---
  const itemsWithIcons = useMemo(() => {
    return items.map((item) => {
      const node = item.data;
      const nodeVisibility = node.properties?.visibility ?? true; // Get visibility state

      // Check zoom-based visibility for layers in view mode
      let isZoomVisible = true;
      if (viewMode === "view" && node.type === "layer" && currentZoom !== undefined) {
        const minZoom = node.properties?.min_zoom;
        const maxZoom = node.properties?.max_zoom;
        if (minZoom !== undefined && maxZoom !== undefined) {
          isZoomVisible = currentZoom >= minZoom && currentZoom <= maxZoom;
        }
      }

      // 1. Group Icon
      if (node.type === "group") {
        // Check if legend should be shown based on viewMode
        const shouldShowLegend = viewMode === "view" ? node.properties?.legend?.show !== false : true;
        const legendCaption = shouldShowLegend ? node.properties?.legend?.caption : undefined;

        return {
          ...item,
          icon: (
            <Icon
              iconName={ICON_NAME.LAYERS}
              style={{ fontSize: "1rem", color: theme.palette.text.secondary }}
            />
          ),
          // Pass visibility to DraggableTreeView for row styling
          isVisible: nodeVisibility,
          // Make groups non-selectable
          isSelectable: false,
          // Add legend caption
          labelInfo: legendCaption,
        };
      }

      const props = node.properties || {};
      const geomType = node.geometry_type?.toLowerCase() || "polygon";
      const hasComplexLegend = props.color_field || props.stroke_color_field || props.marker_field;
      // Combine visibility with zoom-based visibility
      const isVisible = nodeVisibility && isZoomVisible;
      let iconNode: React.ReactNode = null;
      let legendNode: React.ReactNode = undefined;
      let isSelectable = true; // Default to selectable

      // 2. Table Icon (System Icon)
      if (node.layer_type === "table") {
        iconNode = (
          <Icon
            iconName={ICON_NAME.TABLE}
            style={{ fontSize: "1rem", color: theme.palette.text.secondary }}
          />
        );
      }
      // 3. Raster Icon (System Icon)
      else if (node.layer_type === "raster") {
        iconNode = (
          <Icon
            iconName={ICON_NAME.IMAGE}
            fontSize="small"
            style={{ fontSize: "1rem", color: theme.palette.text.secondary }}
          />
        );
      }
      // 4. Complex Legend - Only show legend if layer is visible
      else if (hasComplexLegend) {
        if (isVisible) {
          // Show legend content for visible layers
          // TODO: Add collapse/expand functionality to LayerLegendPanel component
          legendNode = <LayerLegendPanel properties={props} geometryType={geomType} />;
        } else {
          // If not visible, don't show anything and make it non-selectable
          isSelectable = false;
        }
      }
      // 5. Simple Feature (Geometry Preview) - for layers without complex legends
      else {
        const baseColor = props.color
          ? Array.isArray(props.color) && props.color.length >= 3
            ? rgbToHex(props.color as [number, number, number])
            : Array.isArray(props.color)
              ? `rgb(${props.color.join(",")})`
              : props.color
          : "#ccc";
        const strokeColor = props.stroke_color
          ? Array.isArray(props.stroke_color) && props.stroke_color.length >= 3
            ? rgbToHex(props.stroke_color as [number, number, number])
            : Array.isArray(props.stroke_color)
              ? `rgb(${props.stroke_color.join(",")})`
              : props.stroke_color
          : undefined;
        iconNode = (
          <LayerIcon
            type={geomType} // Use geometry type for vector preview
            color={baseColor}
            strokeColor={strokeColor}
            filled={props.filled !== false}
            iconUrl={!props.marker_field && props.marker?.url ? props.marker.url : undefined}
          />
        );
      }
      // Check if legend should be shown based on viewMode
      const shouldShowLegend = viewMode === "view" ? node.properties?.legend?.show !== false : true;
      const legendCaption = shouldShowLegend ? node.properties?.legend?.caption : undefined;

      return {
        ...item,
        icon: iconNode,
        legendContent: legendNode,
        isSelectable,
        // Pass visibility to DraggableTreeView for row styling
        isVisible,
        // Add legend caption
        labelInfo: legendCaption,
      };
    });
  }, [items, theme, currentZoom, viewMode]);

  // --- RENDER ---
  if (isLoading && items.length === 0) {
    return <Box sx={{ p: 2, color: "text.secondary" }}>Loading layers...</Box>;
  }

  if (!isLoading && items.length === 0) {
    return <EmptyLayerState projectId={projectId} isEditMode={isEditMode} />;
  }

  return (
    <Box sx={{ width: "100%", height: "100%", display: "flex", flexDirection: "column", overflow: "hidden" }}>
      {/* 1. Header */}
      {isEditMode && (
        <Box
          sx={{
            px: 2,
            py: 2,
            flexShrink: 0,
            borderBottom: items.length > 0 ? "1px solid" : "none",
            borderColor: "divider",
            zIndex: 1,
          }}>
          <Stack direction="row" alignItems="center" justifyContent="space-between">
            <Typography variant="body1" fontWeight="bold">
              {t("layers")}
            </Typography>
            <Stack direction="row" spacing={1} alignItems="center">
              <Tooltip title={t("create_group") || "Create Group"}>
                <IconButton
                  size="small"
                  onClick={handleCreateGroup}
                  sx={{ color: theme.palette.action.active }}>
                  <Icon iconName={ICON_NAME.LAYERS} />
                </IconButton>
              </Tooltip>
              <AddLayerButton projectId={projectId} />
            </Stack>
          </Stack>
        </Box>
      )}

      {/* 2. Modals - Show download/table modals in both edit and view mode */}
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
        {/* Edit-only modals */}
        {isEditMode && (
          <>
            {moreMenuState?.id === ContentActions.DELETE && activeLayerMoreMenu && (
              <ProjectLayerDeleteModal
                open={true}
                onClose={closeMoreMenu}
                projectLayer={activeLayerMoreMenu}
                onDelete={closeMoreMenu}
              />
            )}
            {moreMenuState?.id === MapLayerActions.RENAME && activeLayerMoreMenu && (
              <ProjectLayerRenameModal
                open={true}
                onClose={closeMoreMenu}
                projectLayer={activeLayerMoreMenu}
                onRename={closeMoreMenu}
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
            {groupModal.open && (
              <ProjectLayerGroupModal
                open={groupModal.open}
                onClose={() => setGroupModal({ open: false, mode: "create" })}
                mode={groupModal.mode}
                projectId={projectId}
                layerTree={treeData}
                existingGroup={groupModal.group}
                onSubmit={handleGroupModalSubmit}
              />
            )}
          </>
        )}
      </>

      {/* 3. Tree */}
      <Box sx={{ flexGrow: 1, overflowY: "auto", overflowX: "hidden", px: 1, pt: 1 }}>
        <DraggableTreeView
          items={itemsWithIcons}
          onItemsChange={(newItems) => {
            setItems(newItems);
            if (onTreeUpdate) {
              const updatePayload = formatDndDataForApi(newItems);
              onTreeUpdate(updatePayload);
            }
          }}
          renderActions={(item) => <RenderRowActions item={item} />}
          enableSelection={isEditMode}
          selectedIds={treeSelectedIds}
          onSelect={handleNodeClick}
          sx={{ width: "100%" }}
        />
      </Box>
    </Box>
  );
};
