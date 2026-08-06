// Icons
import AddIcon from "@mui/icons-material/Add";
// MUI
import {
  Badge,
  Box,
  Button,
  Checkbox,
  IconButton,
  ListItemIcon,
  ListItemText,
  Menu,
  MenuItem,
  Stack,
  Switch,
  Tooltip,
  Typography,
  useTheme,
} from "@mui/material";
import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { useMap } from "react-map-gl/maplibre";
import { toast } from "react-toastify";

import { ICON_NAME, Icon } from "@p4b/ui/components/Icon";

// ----------------------------------------------------------------------
// 3. MAIN COMPONENT
// ----------------------------------------------------------------------
// Redux
import { useUserProfile } from "@/lib/api/users";
import { MAX_EDITABLE_LAYER_SIZE } from "@/lib/constants";
import { startEditing } from "@/lib/store/featureEditor/slice";
import { emitInteractionEvent } from "@/lib/store/interaction/slice";
import { setSelectedLayers } from "@/lib/store/layer/slice";
import { setActiveRightPanel, setDataPanelLayerId, setIsDataPanelOpen } from "@/lib/store/map/slice";
import { rgbToHex } from "@/lib/utils/helpers";
import { zoomToLayer, zoomToProjectLayer } from "@/lib/utils/map/navigate";
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
import CreateLayerModal from "@/components/modals/CreateLayer";
import DatasetUploadModal from "@/components/modals/DatasetUpload";
import MapLayerChartModal from "@/components/modals/MapLayerChart";
import ProjectLayerDeleteModal from "@/components/modals/ProjectLayerDelete";
import ProjectLayerGroupModal from "@/components/modals/ProjectLayerGroupModal";
import ProjectLayerRenameModal from "@/components/modals/ProjectLayerRename";

// Tree Components
import type { BaseTreeItem } from "./DraggableTreeView";
import { DraggableTreeView } from "./DraggableTreeView";
import { LayerIcon } from "./legend/LayerIcon";
import { MaskedImageIcon } from "@/components/map/panels/style/other/MaskedImageIcon";
import { LayerLegendPanel } from "./legend/LayerLegend";
import { getLegendColorMap, getLegendMarkerMap } from "@/lib/utils/map/legend";
import PopupContentRenderer from "@/components/builder/widgets/common/PopupContentRenderer";

// Extended tree item interface to include project layer data
interface ProjectTreeItem extends BaseTreeItem {
  data: ProjectLayerTreeNode;
  canExpand?: boolean;
}

// 1. HELPER COMPONENTS

export const AddLayerButton = ({
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
    { type: AddLayerSourceType.CreateEmptyLayer, icon: ICON_NAME.PLUS, label: t("create_layer") },
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
      {addSourceType === AddLayerSourceType.CreateEmptyLayer && (
        <CreateLayerModal open={true} onClose={() => setAddSourceType(null)} projectId={projectId} />
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

// --- Visibility Toggle ---
// Single source for the three toggle styles. Used as the row prefix
// (togglePosition "left"), inside the row actions ("right"), and by the
// dashboard widget's "show all" row.
//
// On coarse pointers the hit area is grown to 44px. The desktop target is
// ~24px, which is fine for a mouse but easy to miss with a finger — that is
// what made layers feel unresponsive in the mobile dashboard. Only the
// padding grows; the glyph itself stays the same size.
const COARSE_POINTER = "@media (pointer: coarse)";
const COARSE_TARGET = { p: 1.5, minWidth: 44, minHeight: 44 };

export const VisibilityToggle = ({
  toggleStyle,
  visible,
  compact,
  onToggle,
}: {
  toggleStyle: "eye" | "checkbox" | "switch";
  visible: boolean;
  /** Tighter desktop padding, used where the toggle sits inline before the label */
  compact?: boolean;
  onToggle: (e: React.MouseEvent) => void;
}) => {
  const { t } = useTranslation("common");
  const padding = compact ? 0.25 : 0.5;

  if (toggleStyle === "checkbox") {
    return (
      <Checkbox
        size="small"
        checked={visible}
        onChange={(e) => onToggle(e as unknown as React.MouseEvent)}
        sx={{ p: padding, [COARSE_POINTER]: COARSE_TARGET }}
      />
    );
  }

  if (toggleStyle === "switch") {
    return (
      <Switch
        size="small"
        checked={visible}
        onChange={(e) => onToggle(e as unknown as React.MouseEvent)}
        sx={{
          transform: "scale(0.75)",
          mx: -0.5,
          // Undo the shrink on touch — the scaled switch is only ~28px tall
          [COARSE_POINTER]: { transform: "none", mx: 0 },
        }}
      />
    );
  }

  return (
    <Tooltip title={visible ? t("hide") : t("show")} placement="top">
      <IconButton size="small" onClick={onToggle} sx={{ p: padding, [COARSE_POINTER]: COARSE_TARGET }}>
        <Icon iconName={visible ? ICON_NAME.EYE : ICON_NAME.EYE_SLASH} style={{ fontSize: "15px" }} />
      </IconButton>
    </Tooltip>
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
    // Map geometry_type from tree node to feature_layer_geometry_type expected by ProjectLayer
    feature_layer_geometry_type: node.geometry_type as "point" | "line" | "polygon" | undefined,
  } as unknown as ProjectLayer;
};

// Helper function to filter menu options for view mode
const filterMenuForViewMode = (
  menuOptions: PopperMenuItem[],
  allowedActions?: { style?: boolean },
): PopperMenuItem[] => {
  const excludedActions: string[] = [
    ContentActions.DELETE,
    MapLayerActions.RENAME,
    MapLayerActions.DUPLICATE,
    MapLayerActions.EDIT_FEATURES,
  ];
  // Only remove the Style action when the widget has not explicitly allowed it.
  // allowedActions.style === true means the dashboard builder configured this
  // layer-tree widget to expose styling to public/view-mode users.
  if (allowedActions?.style !== true) {
    excludedActions.push(MapLayerActions.STYLE);
  }
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  return menuOptions.filter((option) => !excludedActions.includes(option.id as any));
};

// Catalogue layers cannot be renamed, duplicated, or have features edited
const filterMenuForCatalogLayer = (menuOptions: PopperMenuItem[]): PopperMenuItem[] => {
  const excludedActions = [MapLayerActions.RENAME, MapLayerActions.DUPLICATE, MapLayerActions.EDIT_FEATURES];
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
  /** Callback when a layer starts being dragged (for workflow canvas integration) */
  onLayerDragStart?: (event: React.DragEvent, layer: ProjectLayer) => void;
  isLoading?: boolean;
  viewMode?: "edit" | "view";
  hideActions?: boolean;
  // New configurable props for dashboard widget
  toggleStyle?: "eye" | "checkbox" | "switch";
  togglePosition?: "left" | "right";
  moreOptionsStyle?: "compact" | "direct_actions";
  allowedActions?: {
    style?: boolean;
    viewData?: boolean;
    properties?: boolean;
    zoomTo?: boolean;
  };
  /** Layer IDs that should show download action (view mode only) */
  downloadableLayers?: number[];
  /** Hide attribute/field name headings in legend */
  hideLegendHeading?: boolean;
  /** Custom group icons keyed by group ID */
  groupIcons?: Record<string, { url: string; source?: string }>;
  /** Whether to dim layers that are outside the current zoom range (default: true for backward compat) */
  dimOutOfZoom?: boolean;
  /** Content rendered inside the scroll container, above the tree (e.g. a "show all" toggle row) */
  headerContent?: React.ReactNode;
  /** Per-group info text (keyed by group ID string) shown as an ⓘ button on the group row */
  groupInfo?: Record<string, string>;
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
  onLayerDragStart,
  isLoading,
  viewMode = "edit",
  hideActions = false,
  toggleStyle = "eye",
  togglePosition = "right",
  moreOptionsStyle = "compact",
  allowedActions,
  downloadableLayers,
  hideLegendHeading,
  groupIcons,
  dimOutOfZoom = true,
  headerContent,
  groupInfo,
}: ProjectLayerTreeProps) => {
  const { t } = useTranslation("common");
  const theme = useTheme();
  const { map } = useMap();
  const mapRef = useRef(map);
  mapRef.current = map;
  const dispatch = useAppDispatch();
  const { userProfile } = useUserProfile();
  // Only subscribe to currentZoom when dimming is enabled and in view mode
  const currentZoom = useAppSelector((state) => (dimOutOfZoom && viewMode === "view" ? state.map.currentZoom : undefined));

  const [items, setItems] = useState<ProjectTreeItem[]>([]);
  const itemsRef = useRef<ProjectTreeItem[]>([]);
  useEffect(() => { itemsRef.current = items; }, [items]);
  const [groupModal, setGroupModal] = useState<{
    open: boolean;
    mode: "create" | "rename" | "delete";
    group?: ProjectLayerTreeNode;
  }>({ open: false, mode: "create" });
  const [groupInfoDialog, setGroupInfoDialog] = useState<{ id: number; anchorEl: HTMLElement } | null>(null);

  const activeLayerId = useAppSelector((state) => state.layers.activeLayerId);
  const activeRightPanel = useAppSelector((state) => state.map.activeRightPanel);
  const selectedLayerIds = useAppSelector((state) => state.layers.selectedLayerIds || []);
  const mapMode = useAppSelector((state) => state.map.mapMode);
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
        user_id: layer.user_id,
      });
    });

    return nodes.sort((a, b) => a.order - b.order);
  }, [projectLayers, projectLayerGroups]);

  useEffect(() => {
    if (treeData) {
      setItems((prevItems) => {
        const newItems = formatApiDataForDnd(treeData);
        if (prevItems.length === 0) return newItems;
        // For items that already existed, preserve their collapsed state.
        // Newly appearing layer items (e.g. inside a group that was just toggled visible)
        // are expanded so their legends are immediately visible.
        const prevById = new Map(prevItems.map((item) => [item.id, item]));
        return newItems.map((item) => {
          const prev = prevById.get(item.id);
          if (prev) {
            return { ...item, collapsed: prev.collapsed };
          }
          // New layer items: expand legend so attribute-based styling is shown
          if (!item.isGroup) {
            return { ...item, collapsed: false };
          }
          return item;
        });
      });
    }
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

  const handleVisibilityToggle = useCallback(async (node: ProjectLayerTreeNode, e: React.MouseEvent) => {
    e.stopPropagation();

    const currentVisibility = node.properties?.visibility ?? true;
    const newVisibility = !currentVisibility;

    // Compute updated items from the current snapshot (via ref to avoid stale closure)
    const newItems = itemsRef.current.map((i) => {
      if (i.data.id === node.id && i.data.type === node.type) {
        return {
          ...i,
          data: {
            ...i.data,
            properties: { ...i.data.properties, visibility: newVisibility },
          },
          collapsed: !newVisibility,
        };
      }
      return i;
    });

    setItems(newItems);

    // Emit interaction events based on visibility toggle
    if (node.type === "layer") {
      dispatch(emitInteractionEvent({
        type: "visibility_changed",
        sourceId: node.id,
        value: newVisibility,
      }));
    }
    // When turning a group ON, activate it (switch tab). Turning OFF is just hiding.
    if (node.type === "group" && newVisibility) {
      dispatch(emitInteractionEvent({ type: "group_activated", sourceId: node.id }));
    }

    try {
      const updatePayload = formatDndDataForApi(newItems);
      if (onTreeUpdate) {
        await onTreeUpdate(updatePayload);
      }
    } catch (err) {
      // Revert to the snapshot captured before the optimistic update
      setItems(itemsRef.current);
      toast.error(t("error_updating_visibility"));
      console.error("Error in handleVisibilityToggle:", err);
    }
  }, [dispatch, onTreeUpdate, t]);

  const handleProperties = useCallback((layer: ProjectLayer) => {
    dispatch(setSelectedLayers([layer.id]));
    dispatch(setActiveRightPanel(MapSidebarItemID.PROPERTIES));
  }, [dispatch]);

  const handleStyle = useCallback((layer: ProjectLayer) => {
    dispatch(setSelectedLayers([layer.id]));
    dispatch(setActiveRightPanel(MapSidebarItemID.STYLE));
  }, [dispatch]);

  const handleDuplicate = useCallback(async (layer: ProjectLayer) => {
    try {
      if (onLayerDuplicate) {
        await onLayerDuplicate(layer.layer_id);
      }
    } catch (error) {
      toast.error(t("error_duplicating_layer"));
    }
  }, [onLayerDuplicate, t]);

  const handleNodeClick = (compositeIds: string[]) => {
    const realIds = compositeIds
      .map((cId) => {
        const item = items.find((i) => i.id === cId);
        return item?.data?.id;
      })
      .filter((id) => id !== undefined);

    // Emit interaction event for group activation (works in all modes)
    if (realIds.length === 1) {
      const clickedItem = items.find((i) => i.id === compositeIds[0]);
      if (clickedItem?.data?.type === "group") {
        dispatch(emitInteractionEvent({ type: "group_activated", sourceId: realIds[0] }));
        // Groups should not be selected or open panels — only emit the interaction event
        return;
      }
    }

    // In view mode, only emit interaction events — don't change selection or panels
    if (!isEditMode) return;

    dispatch(setSelectedLayers(realIds));

    // Always sync data panel layer — if the panel is closed, this is a no-op
    if (realIds.length === 1) {
      dispatch(setDataPanelLayerId(realIds[0]));
    }

    if (realIds.length > 0) {
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
  // Defined as a useCallback (not a nested component) so its reference stays stable
  // across re-renders that don't change relevant deps. A nested component definition
  // would get a new identity on every render, causing React to unmount/remount the
  // PopperMenu and reset its open state — closing the three-dots menu unexpectedly.
  const renderRowActions = useCallback((item: ProjectTreeItem) => {
    const node = item.data as ProjectLayerTreeNode;
    const nodeVisibility = node.properties?.visibility ?? true;

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
        !!node.in_catalog,
        false,
        node.user_id === userProfile?.id,
        isEditMode,
      );
    }

    // Filter menu options based on view mode
    if (viewMode === "view") {
      menuOptions = filterMenuForViewMode(menuOptions, allowedActions);
    }

    // Catalogue layers cannot be renamed, duplicated, or have features edited
    if (node.in_catalog) {
      menuOptions = filterMenuForCatalogLayer(menuOptions);
    }

    // Edit features only available in data (map) mode
    if (mapMode !== "data") {
      menuOptions = menuOptions.filter((opt) => opt.id !== MapLayerActions.EDIT_FEATURES);
    }

    // Edit features only allowed for layers under 100MB
    if (node.type === "layer" && node.layer_id) {
      const layerSize = projectLayers.find((l) => l.layer_id === node.layer_id)?.size;
      if (layerSize && layerSize > MAX_EDITABLE_LAYER_SIZE) {
        menuOptions = menuOptions.filter((opt) => opt.id !== MapLayerActions.EDIT_FEATURES);
      }
    }

    // Filter menu options based on allowedActions
    if (allowedActions) {
      menuOptions = menuOptions.filter((opt) => {
        if (opt.id === MapLayerActions.STYLE && allowedActions.style === false) return false;
        if (opt.id === ContentActions.TABLE && allowedActions.viewData === false) return false;
        if (opt.id === MapLayerActions.PROPERTIES && allowedActions.properties === false) return false;
        if (opt.id === MapLayerActions.ZOOM_TO && allowedActions.zoomTo === false) return false;
        return true;
      });
    }

    // Filter download action based on downloadableLayers
    if (downloadableLayers && node.type === "layer") {
      menuOptions = menuOptions.filter((opt) => {
        if (opt.id === ContentActions.DOWNLOAD) {
          return downloadableLayers.includes(node.id);
        }
        return true;
      });
    }

    const hasFilter = node.query?.cql?.["args"]?.length;
    const isFilterActive = activeLayerId === node.id && activeRightPanel === MapSidebarItemID.FILTER;

    return (
      <Stack
        direction="row"
        alignItems="center"
        spacing={1}>
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

        {/* Actions: direct buttons or compact three-dot menu */}
        {!hideActions && menuOptions.length > 0 && (
          moreOptionsStyle === "direct_actions" ? (
            <>
              {menuOptions.map((opt) => (
                opt.icon && (
                  <Tooltip key={opt.id} title={opt.label} placement="top">
                    <IconButton
                      size="small"
                      sx={{ p: 0.25 }}
                      onClick={async (e) => {
                        e.stopPropagation();
                        const handleAction = async () => {
                          if (opt.id === MapLayerActions.ZOOM_TO) {
                            const currentMap = mapRef.current;
                            if (currentMap) {
                              if (node.type === "layer") {
                                const target = castNodeToProjectLayer(node);
                                await zoomToProjectLayer(currentMap, target);
                              } else if (node.extent) {
                                zoomToLayer(currentMap, node.extent);
                              }
                            }
                          } else if (node.type === "layer") {
                            const target = castNodeToProjectLayer(node);
                            if (opt.id === MapLayerActions.PROPERTIES) handleProperties(target);
                            else if (opt.id === MapLayerActions.STYLE) handleStyle(target);
                            else if (opt.id === MapLayerActions.DUPLICATE) handleDuplicate(target);
                            else if (opt.id === ContentActions.TABLE) {
                              if (mapMode === "data") {
                                dispatch(setDataPanelLayerId(target.id));
                                dispatch(setIsDataPanelOpen(true));
                              } else {
                                openMoreMenu(opt, target);
                              }
                            } else openMoreMenu(opt, target);
                          }
                        };
                        await handleAction();
                      }}>
                      <Icon iconName={opt.icon} style={{ fontSize: "13px" }} htmlColor={opt.color} />
                    </IconButton>
                  </Tooltip>
                )
              ))}
            </>
          ) : (
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
                if (menuItem.id === MapLayerActions.ZOOM_TO) {
                  const currentMap = mapRef.current;
                  if (currentMap) {
                    if (node.type === "layer") {
                      const target = castNodeToProjectLayer(node);
                      await zoomToProjectLayer(currentMap, target);
                    } else if (node.extent) {
                      zoomToLayer(currentMap, node.extent);
                    }
                  }
                  return;
                }
                if (node.type === "layer") {
                  const target = castNodeToProjectLayer(node);
                  if (menuItem.id === MapLayerActions.PROPERTIES) {
                    handleProperties(target);
                  } else if (menuItem.id === MapLayerActions.STYLE) {
                    handleStyle(target);
                  } else if (menuItem.id === MapLayerActions.DUPLICATE) {
                    handleDuplicate(target);
                  } else if (menuItem.id === MapLayerActions.EDIT_FEATURES) {
                    dispatch(startEditing({
                      layerId: target.layer_id,
                      geometryType: target.feature_layer_geometry_type ?? null,
                    }));
                  } else if (menuItem.id === ContentActions.TABLE) {
                    if (mapMode === "data") {
                      dispatch(setDataPanelLayerId(target.id));
                      dispatch(setIsDataPanelOpen(true));
                    } else {
                      openMoreMenu(menuItem, target);
                    }
                  } else {
                    openMoreMenu(menuItem, target);
                  }
                } else {
                  if (menuItem.id === MapLayerActions.RENAME && node.type === "group") {
                    setGroupModal({ open: true, mode: "rename", group: node });
                  } else if (menuItem.id === ContentActions.DELETE && node.type === "group") {
                    setGroupModal({ open: true, mode: "delete", group: node });
                  } else {
                    const groupAsLayer = castNodeToProjectLayer(node);
                    openMoreMenu(menuItem, groupAsLayer);
                  }
                }
              }}
            />
          )
        )}

        {/* Group info ⓘ button */}
        {node.type === "group" && groupInfo?.[String(node.id)] && (
          <Tooltip title={t("properties")} placement="top">
            <IconButton
              size="small"
              onClick={(e) => { e.stopPropagation(); setGroupInfoDialog({ id: node.id, anchorEl: e.currentTarget as HTMLElement }); }}
              sx={{ p: 0.25 }}>
              <Icon iconName={ICON_NAME.CIRCLEINFO} style={{ fontSize: "15px" }} />
            </IconButton>
          </Tooltip>
        )}

        {/* Visibility toggle - very right when position is "right" */}
        {togglePosition !== "left" && !hideActions && node.layer_type !== "table" && (
          <VisibilityToggle
            toggleStyle={toggleStyle}
            visible={nodeVisibility}
            onToggle={(e) => handleVisibilityToggle(node, e)}
          />
        )}
      </Stack>
    );
  }, [
    t,
    getLayerMoreMenuOptions, openMoreMenu,
    handleVisibilityToggle, handleProperties, handleStyle, handleDuplicate,
    setGroupModal, setGroupInfoDialog,
    mapRef,
    viewMode, hideActions, toggleStyle, togglePosition, moreOptionsStyle,
    allowedActions, downloadableLayers, projectLayers,
    isEditMode, groupInfo,
    mapMode, userProfile,
    dispatch,
    activeLayerId, activeRightPanel,
  ]);

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

        const customIcon = groupIcons?.[`group_icon_${node.id}`];
        return {
          ...item,
          icon: customIcon?.url ? (
            <MaskedImageIcon
              imageUrl={customIcon.url}
              dimension="16px"
              applyMask={customIcon.source === "library"}
              imgColor={theme.palette.action.active}
            />
          ) : (
            <Icon
              iconName={ICON_NAME.LAYERS}
              style={{ fontSize: "1rem", color: theme.palette.action.active }}
            />
          ),
          isVisible: nodeVisibility,
          isSelectable: false,
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
            style={{ fontSize: "1rem", color: theme.palette.action.active }}
          />
        );
      }
      // 3. Raster Icon (System Icon)
      else if (node.layer_type === "raster") {
        iconNode = (
          <Icon
            iconName={ICON_NAME.IMAGE}
            fontSize="small"
            style={{ fontSize: "1rem", color: theme.palette.action.active }}
          />
        );

        // Check if raster has categories or color_range style for legend
        const rasterStyle = props.style as {
          style_type?: string;
          categories?: unknown[];
          color_map?: unknown[];
        };
        const hasRasterLegend =
          (rasterStyle?.style_type === "categories" &&
            Array.isArray(rasterStyle.categories) &&
            rasterStyle.categories.length > 0) ||
          (rasterStyle?.style_type === "color_range" &&
            Array.isArray(rasterStyle.color_map) &&
            rasterStyle.color_map.length > 0);

        if (hasRasterLegend && isVisible) {
          legendNode = <LayerLegendPanel properties={props} geometryType="raster" hideHeading={hideLegendHeading} />;
        }
      }
      // 4. Complex Legend - Only show legend if layer is visible
      else if (hasComplexLegend) {
        // Check if legend panel will actually have content to show
        const colorMap = getLegendColorMap(props, "color");
        const strokeMap = getLegendColorMap(props, "stroke_color");
        const markerMap = getLegendMarkerMap(props);
        const hasLegendContent = colorMap.length > 1 || strokeMap.length > 1 || markerMap.length > 1;

        if (isVisible && hasLegendContent) {
          // Show legend content for visible layers
          // TODO: Add collapse/expand functionality to LayerLegendPanel component
          legendNode = <LayerLegendPanel properties={props} geometryType={geomType} hideHeading={hideLegendHeading} />;
        } else if (!isVisible) {
          // If not visible, don't show anything and make it non-selectable
          isSelectable = false;
        }

        // Fallback icon when legend panel has no content (e.g. fill/stroke disabled)
        if (!hasLegendContent) {
          if (props.marker_field && props.custom_marker) {
            // Attribute-based markers with no colors: generic location marker icon
            iconNode = (
              <Icon
                iconName={ICON_NAME.LOCATION_MARKER}
                style={{ fontSize: "1rem", color: theme.palette.action.active }}
              />
            );
          } else {
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
            // When fill is disabled and custom marker is active, use black to match map behavior
            const iconColor = props.filled === false && props.custom_marker ? "#000000" : baseColor;
            iconNode = (
              <LayerIcon
                type={geomType}
                color={iconColor}
                strokeColor={props.stroked !== false ? strokeColor : undefined}
                filled={props.filled !== false}
                iconUrl={
                  !props.marker_field && props.custom_marker && props.marker?.url ? props.marker.url : undefined
                }
                iconSource={
                  !props.marker_field && props.custom_marker && props.marker?.source
                    ? props.marker.source
                    : "library"
                }
              />
            );
          }
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
        // When fill is disabled and custom marker is active, use black to match map behavior
        const iconColor = props.filled === false && props.custom_marker ? "#000000" : baseColor;
        iconNode = (
          <LayerIcon
            type={geomType} // Use geometry type for vector preview
            color={iconColor}
            strokeColor={props.stroked !== false ? strokeColor : undefined}
            filled={props.filled !== false}
            iconUrl={
              !props.marker_field && props.custom_marker && props.marker?.url ? props.marker.url : undefined
            }
            iconSource={
              !props.marker_field && props.custom_marker && props.marker?.source
                ? props.marker.source
                : "library"
            }
          />
        );
      }
      // Check if legend should be shown based on viewMode
      const shouldShowLegend = viewMode === "view" ? node.properties?.legend?.show !== false : true;
      const legendCaption = shouldShowLegend ? node.properties?.legend?.caption : undefined;

      return {
        ...item,
        icon: iconNode,
        legendContent: shouldShowLegend ? legendNode : undefined,
        isSelectable,
        isVisible,
        labelInfo: legendCaption,
      };
    });
  }, [items, theme, currentZoom, viewMode, hideLegendHeading, groupIcons]);

  const renderPrefix = useCallback(togglePosition === "left" ? (item: ProjectTreeItem) => {
    const node = item.data as ProjectLayerTreeNode;
    if (hideActions || node.layer_type === "table") return null;
    const nodeVisibility = node.properties?.visibility ?? true;
    return (
      <Box onClick={(e) => e.stopPropagation()} sx={{ display: "flex", alignItems: "center" }}>
        <VisibilityToggle
          toggleStyle={toggleStyle}
          visible={nodeVisibility}
          compact
          onToggle={(e) => handleVisibilityToggle(node, e)}
        />
      </Box>
    );
  } : () => null, [togglePosition, hideActions, toggleStyle, handleVisibilityToggle]);

  // --- RENDER ---
  if (isLoading && items.length === 0) {
    return <Box sx={{ p: 2, color: "text.secondary" }}>Loading layers...</Box>;
  }

  if (!isLoading && items.length === 0) {
    return <EmptyLayerState projectId={projectId} isEditMode={isEditMode} />;
  }

  return (
    <Box sx={{ width: "100%", height: "100%", display: "flex", flexDirection: "column", overflow: "hidden", pointerEvents: "all" }}>
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
        {headerContent}
        <DraggableTreeView
          items={itemsWithIcons}
          onItemsChange={(newItems) => {
            // Always update local state so expand/collapse arrows work in view mode.
            // Persist to the API only in edit mode.
            setItems(newItems);
            if (!isEditMode) return;
            if (onTreeUpdate) {
              const updatePayload = formatDndDataForApi(newItems);
              onTreeUpdate(updatePayload);
            }
          }}
          renderActions={renderRowActions}
          renderPrefix={togglePosition === "left" ? renderPrefix : undefined}
          enableSelection
          disableDrag={!isEditMode}
          selectedIds={treeSelectedIds}
          onSelect={handleNodeClick}
          onExternalDragStart={
            onLayerDragStart
              ? (event, item) => {
                  // Only allow dragging layers, not groups
                  if (item.data.type === "layer") {
                    const layer = castNodeToProjectLayer(item.data);
                    onLayerDragStart(event, layer);
                  }
                }
              : undefined
          }
          sx={{ width: "100%" }}
        />
      </Box>
      {groupInfoDialog !== null && groupInfo?.[String(groupInfoDialog.id)] && (
        <PopupContentRenderer
          open
          onClose={() => setGroupInfoDialog(null)}
          popup_type="dialog"
          placement="auto"
          anchorEl={groupInfoDialog.anchorEl}
          title={projectLayerGroups.find((g) => g.id === groupInfoDialog.id)?.name ?? ""}
          content={groupInfo[String(groupInfoDialog.id)]}
        />
      )}
    </Box>
  );
};
