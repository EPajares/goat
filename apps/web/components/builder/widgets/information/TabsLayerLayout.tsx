import { Box, Checkbox, IconButton, Switch, Tab, Tabs, Typography, useTheme } from "@mui/material";
import { useCallback, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { toast } from "react-toastify";

import { Icon, ICON_NAME } from "@p4b/ui/components/Icon";

import { emitInteractionEvent } from "@/lib/store/interaction/slice";
import type { ProjectLayer, ProjectLayerGroup, ProjectLayerTreeUpdate } from "@/lib/validations/project";
import type { LayerInformationSchema } from "@/lib/validations/widget";

import { useAppDispatch } from "@/hooks/store/ContextHooks";

import { MaskedImageIcon } from "@/components/map/panels/style/other/MaskedImageIcon";

import { ProjectLayerTree } from "@/components/map/panels/layer/ProjectLayerTree";

interface TabsLayerLayoutProps {
  projectId: string;
  projectLayers: ProjectLayer[];
  projectLayerGroups: ProjectLayerGroup[];
  config: LayerInformationSchema;
  onTreeUpdate: (payload: ProjectLayerTreeUpdate) => Promise<void>;
  viewOnly?: boolean;
  downloadableLayers?: number[];
  simpleLegendLayerIds?: number[];
  hideLegendHeading?: boolean;
  groupIcons?: Record<string, { url: string; source?: string }>;
  dimOutOfZoom?: boolean;
}

const TabsLayerLayout = ({
  projectId,
  projectLayers,
  projectLayerGroups,
  config,
  onTreeUpdate,
  downloadableLayers,
  simpleLegendLayerIds,
  hideLegendHeading,
  groupIcons,
  dimOutOfZoom,
}: TabsLayerLayoutProps) => {
  const { t } = useTranslation("common");
  const dispatch = useAppDispatch();
  const theme = useTheme();
  const options = config.options;

  const topLevelGroups = useMemo(
    () =>
      projectLayerGroups
        .filter((g) => !g.parent_id)
        .sort((a, b) => (a.order ?? 0) - (b.order ?? 0)),
    [projectLayerGroups]
  );

  const [activeTab, setActiveTab] = useState(0);
  const activeGroup = topLevelGroups[activeTab];

  // Filter layers to active group and strip group ID so they render as root items
  const activeGroupLayers = useMemo(() => {
    const layers = !activeGroup
      ? projectLayers
      : projectLayers.filter((l) => l.layer_project_group_id === activeGroup.id);
    return layers.map((l) => ({ ...l, layer_project_group_id: null }));
  }, [activeGroup, projectLayers]);

  // Wrap onTreeUpdate to restore the original group ID before sending updates
  const handleTreeUpdate = useCallback(
    async (payload: ProjectLayerTreeUpdate) => {
      const fixedPayload: ProjectLayerTreeUpdate = {
        items: payload.items.map((item) => {
          if (item.type === "layer" && activeGroup) {
            return { ...item, parent_id: activeGroup.id };
          }
          return item;
        }),
      };
      await onTreeUpdate(fixedPayload);
    },
    [onTreeUpdate, activeGroup]
  );

  const togglableLayers = useMemo(
    () => activeGroupLayers.filter((l) => l.type !== "table"),
    [activeGroupLayers]
  );

  const allVisible = useMemo(
    () => togglableLayers.every((l) => l.properties?.visibility !== false),
    [togglableLayers]
  );

  // Whether any layer in each top-level group is visible (for tab active state)
  const groupHasVisibleLayer = useMemo(() => {
    const map: Record<number, boolean> = {};
    for (const group of topLevelGroups) {
      map[group.id] = projectLayers.some(
        (l) => l.layer_project_group_id === group.id && l.properties?.visibility !== false
      );
    }
    return map;
  }, [topLevelGroups, projectLayers]);

  const handleToggleAll = useCallback(async () => {
    if (togglableLayers.length === 0) return;
    const newVisibility = !allVisible;
    const payload: ProjectLayerTreeUpdate = {
      items: togglableLayers.map((layer, index) => ({
        id: layer.id,
        type: "layer" as const,
        order: index,
        parent_id: null,
        properties: {
          ...(layer.properties ?? {}),
          visibility: newVisibility,
        },
      })),
    };
    togglableLayers.forEach((layer) => {
      dispatch(emitInteractionEvent({ type: "visibility_changed", sourceId: layer.id, value: newVisibility }));
    });
    try {
      await handleTreeUpdate(payload);
    } catch {
      toast.error(t("error_updating_visibility"));
    }
  }, [togglableLayers, allVisible, dispatch, handleTreeUpdate, t]);

  if (topLevelGroups.length === 0) {
    return (
      <Typography variant="body2" color="text.secondary" sx={{ p: 2, textAlign: "center" }}>
        {t("no_groups_found")}
      </Typography>
    );
  }

  const iconOnly = options?.show_group_name === false;
  const togglePosition = options?.toggle_position ?? "left";
  const showAllToggle = options?.show_all_toggle !== false && togglableLayers.length > 0;

  return (
    <Box>
      <Tabs
        value={activeTab}
        onChange={(_, newValue) => {
          setActiveTab(newValue);
          const group = topLevelGroups[newValue];
          if (group) {
            dispatch(emitInteractionEvent({ type: "group_activated", sourceId: group.id }));
          }
        }}
        variant="scrollable"
        scrollButtons="auto"
        sx={{ borderBottom: 1, borderColor: "divider", minHeight: 32 }}>
        {topLevelGroups.map((group) => {
          const iconColor = groupHasVisibleLayer[group.id]
            ? theme.palette.action.active
            : theme.palette.text.disabled;
          return (
            <Tab
              key={group.id}
              label={
                iconOnly ? undefined : (
                  <Box component="span" sx={{ display: "inline-flex", alignItems: "center" }}>
                    {group.name}
                  </Box>
                )
              }
              icon={
                options?.show_group_icons ? (
                  groupIcons?.[`group_icon_${group.id}`]?.url ? (
                    <MaskedImageIcon
                      imageUrl={groupIcons[`group_icon_${group.id}`].url}
                      dimension="16px"
                      applyMask={groupIcons[`group_icon_${group.id}`].source === "library"}
                      imgColor={iconColor}
                    />
                  ) : (
                    <Icon iconName={ICON_NAME.LAYERS} style={{ fontSize: 14, color: iconColor }} />
                  )
                ) : undefined
              }
              iconPosition="start"
              sx={{
                minHeight: 32,
                textTransform: "none",
                fontSize: "0.8125rem",
                py: 0,
                ...(iconOnly && { minWidth: 40, px: 0.5 }),
              }}
            />
          );
        })}
      </Tabs>
      {/* Reuse ProjectLayerTree — same rendering as tree mode, just filtered to active group */}
      <ProjectLayerTree
        projectId={projectId}
        projectLayers={activeGroupLayers}
        projectLayerGroups={[]}
        viewMode="view"
        isLoading={false}
        onTreeUpdate={handleTreeUpdate}
        toggleStyle={options?.toggle_style}
        togglePosition={options?.toggle_position}
        moreOptionsStyle={options?.more_options_style}
        allowedActions={{
          style: options?.show_style_action ?? true,
          viewData: options?.show_view_data_action ?? true,
          properties: options?.show_properties_action ?? true,
          zoomTo: options?.show_zoom_to_action ?? true,
        }}
        downloadableLayers={downloadableLayers}
        simpleLegendLayerIds={simpleLegendLayerIds}
        hideLegendHeading={hideLegendHeading}
        groupIcons={groupIcons}
        dimOutOfZoom={dimOutOfZoom}
        headerContent={showAllToggle ? (
          <Box
            onClick={handleToggleAll}
            sx={{
              display: "flex",
              alignItems: "center",
              py: 0.25,
              mb: 0.5,
              borderBottom: 1,
              borderColor: "divider",
              cursor: "pointer",
              "&:hover": { bgcolor: "action.hover" },
            }}>
            {togglePosition === "left" && (
              <Box onClick={(e) => e.stopPropagation()} sx={{ display: "flex", alignItems: "center" }}>
                {options?.toggle_style === "checkbox" ? (
                  <Checkbox size="small" checked={allVisible} onChange={handleToggleAll} sx={{ p: 0.25 }} />
                ) : options?.toggle_style === "switch" ? (
                  <Switch size="small" checked={allVisible} onChange={handleToggleAll} sx={{ transform: "scale(0.75)", mx: -0.5 }} />
                ) : (
                  <IconButton size="small" onClick={(e) => { e.stopPropagation(); handleToggleAll(); }} sx={{ p: 0.25 }}>
                    <Icon iconName={allVisible ? ICON_NAME.EYE : ICON_NAME.EYE_SLASH} style={{ fontSize: "15px" }} />
                  </IconButton>
                )}
              </Box>
            )}
            <Typography variant="body2" sx={{ flex: 1, fontWeight: 500 }}>
              {t("show_all")}
            </Typography>
            {togglePosition !== "left" && (
              <Box onClick={(e) => e.stopPropagation()} sx={{ display: "flex", alignItems: "center", pl: 1 }}>
                {options?.toggle_style === "checkbox" ? (
                  <Checkbox size="small" checked={allVisible} onChange={handleToggleAll} sx={{ p: 0.5 }} />
                ) : options?.toggle_style === "switch" ? (
                  <Switch size="small" checked={allVisible} onChange={handleToggleAll} sx={{ transform: "scale(0.75)", mx: -0.5 }} />
                ) : (
                  <IconButton size="small" onClick={(e) => { e.stopPropagation(); handleToggleAll(); }} sx={{ px: 0.5 }}>
                    <Icon iconName={allVisible ? ICON_NAME.EYE : ICON_NAME.EYE_SLASH} style={{ fontSize: "15px" }} />
                  </IconButton>
                )}
              </Box>
            )}
          </Box>
        ) : undefined}
      />
    </Box>
  );
};

export default TabsLayerLayout;
