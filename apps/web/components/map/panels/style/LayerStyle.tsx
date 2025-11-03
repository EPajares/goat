import { Box, Divider, IconButton, Stack, Tooltip, Typography } from "@mui/material";
import { useCallback, useMemo, useState } from "react";
import { useMap } from "react-map-gl/maplibre";
import { useDispatch } from "react-redux";
import { toast } from "react-toastify";

import { ICON_NAME, Icon } from "@p4b/ui/components/Icon";

import { useTranslation } from "@/i18n/client";

import { getLayerClassBreaks, getLayerUniqueValues, updateDataset, useDataset } from "@/lib/api/layers";
import { updateProjectLayer } from "@/lib/api/projects";
import { useUserProfile } from "@/lib/api/users";
import { setActiveRightPanel } from "@/lib/store/map/slice";
import { layerType } from "@/lib/validations/common";
import {
  type ColorMap,
  type FeatureLayerProperties,
  type LayerUniqueValues,
  type MarkerMap,
  classBreaks,
} from "@/lib/validations/layer";
import type { ProjectLayer } from "@/lib/validations/project";

import { LayerStyleActions } from "@/types/common";

import useLayerFields from "@/hooks/map/CommonHooks";
import { useActiveLayer, useFilteredProjectLayers } from "@/hooks/map/LayerPanelHooks";

import AccordionWrapper from "@/components/common/AccordionWrapper";
import type { PopperMenuItem } from "@/components/common/PopperMenu";
import MoreMenu from "@/components/common/PopperMenu";
import Container from "@/components/map/panels/Container";
import ProjectLayerDropdown from "@/components/map/panels/ProjectLayerDropdown";
import SectionHeader from "@/components/map/panels/common/SectionHeader";
import ColorOptions from "@/components/map/panels/style/color/ColorOptions";
import GeneralOptions from "@/components/map/panels/style/general/GeneralOptions";
import InteractionOptions from "@/components/map/panels/style/interaction/InteractionOptions";
import LabelOptions from "@/components/map/panels/style/label/LabelOptions";
import { LegendOptions } from "@/components/map/panels/style/legend/LegendOptions";
import MarkerOptions from "@/components/map/panels/style/marker/MarkerOptions";
import Settings from "@/components/map/panels/style/settings/Settings";

enum LayerStylePanels {
  STYLE = "style",
  LABELS = "labels",
  POPUP = "popup",
  LEGEND = "legend",
}

const LayerStylePanel = ({ projectId }: { projectId: string }) => {
  const { t } = useTranslation("common");
  const { map } = useMap();

  const [expanded, setExpanded] = useState<LayerStylePanels | false>(LayerStylePanels.STYLE);

  const handleAccordionChange =
    (panel: LayerStylePanels) => (_event: React.SyntheticEvent, isExpanded: boolean) => {
      setExpanded(isExpanded ? panel : false);
    };

  const dispatch = useDispatch();
  const { activeLayer } = useActiveLayer(projectId);
  const { dataset, mutate: mutateDataset } = useDataset(activeLayer?.layer_id || "");
  const { layers: projectLayers, mutate: mutateProjectLayers } = useFilteredProjectLayers(projectId);
  const { layerFields } = useLayerFields(activeLayer?.layer_id || "");
  const { userProfile } = useUserProfile();
  const layerProperties = activeLayer?.properties as FeatureLayerProperties;
  const updateLayerStyle = useCallback(
    async (newStyle: FeatureLayerProperties) => {
      if (!activeLayer) return;
      const layers = JSON.parse(JSON.stringify(projectLayers));
      const index = layers.findIndex((l) => l.id === activeLayer.id);
      const layerToUpdate = layers[index] as ProjectLayer;
      if (!layerToUpdate.properties) {
        layerToUpdate.properties = {} as FeatureLayerProperties;
      }

      layerToUpdate.properties = newStyle;
      await mutateProjectLayers(layers, false);
      await updateProjectLayer(projectId, activeLayer.id, layerToUpdate);
    },
    [activeLayer, projectLayers, mutateProjectLayers, projectId]
  );

  const createColorMapFromClassBreaks = useCallback((colors: string[], breakValues: string[]) => {
    const colorMap = [] as ColorMap;
    colors.forEach((color, index) => {
      const breakValue = breakValues[index] || "0";
      colorMap.push([[breakValue], color]);
    });
    return colorMap;
  }, []);

  const updateColorClassificationBreaks = useCallback(
    async (updateType: "color" | "stroke_color", newStyle: FeatureLayerProperties) => {
      if (!activeLayer) return;
      if (!newStyle[`${updateType}_field`]?.name) return;
      let classBreakType = newStyle[`${updateType}_scale`];
      const existingBreaks = layerProperties[`${updateType}_scale_breaks`];
      if (classBreakType === classBreaks.Enum.custom_breaks && existingBreaks) {
        const breakValues = [] as string[];
        if (classBreakType === layerProperties[`${updateType}_scale`]) {
          const colorMap = newStyle[`${updateType}_range`]?.color_map;
          if (colorMap) {
            colorMap.forEach((colorMapItem) => {
              if (colorMapItem?.[0]?.[0] !== undefined) breakValues.push(colorMapItem[0][0]);
            });
          }
        } else {
          if (existingBreaks) {
            breakValues.push(existingBreaks.min.toString());
            existingBreaks.breaks.forEach((value) => {
              breakValues.push(value.toString());
            });
          }
        }
        newStyle[`${updateType}_range`]["color_map"] = createColorMapFromClassBreaks(
          newStyle[`${updateType}_range`]?.colors || [],
          breakValues
        );
        return;
      }
      if (
        newStyle[`${updateType}_scale`] !== layerProperties[`${updateType}_scale`] ||
        newStyle[`${updateType}_field`]?.name !== layerProperties[`${updateType}_field`]?.name ||
        newStyle[`${updateType}_range`]?.colors?.length !==
          layerProperties[`${updateType}_range`]?.colors?.length
      ) {
        if (classBreakType === classBreaks.Enum.custom_breaks) {
          classBreakType = classBreaks.Enum.equal_interval;
        }
        const breaks = await getLayerClassBreaks(
          activeLayer.layer_id,
          classBreakType,
          newStyle[`${updateType}_field`]?.name as string,
          newStyle[`${updateType}_range`]?.colors?.length - 1
        );
        if (breaks && breaks?.breaks?.length === newStyle[`${updateType}_range`]?.colors?.length - 1)
          newStyle[`${updateType}_scale_breaks`] = breaks;
      }
    },
    [activeLayer, createColorMapFromClassBreaks, layerProperties]
  );

  const updateOrdinalValues = useCallback(
    async (updateType: "color" | "stroke_color" | "marker", newStyle: FeatureLayerProperties) => {
      if (!activeLayer) return;
      if (!newStyle[`${updateType}_field`]?.name) return;
      const oldFieldName = layerProperties[`${updateType}_field`]?.name;
      const newFieldName = newStyle[`${updateType}_field`]?.name;
      if (updateType === "marker" && oldFieldName !== newFieldName) {
        const uniqueValues = await getLayerUniqueValues(
          activeLayer.layer_id,
          newStyle[`${updateType}_field`]?.name as string,
          6
        );
        const markerMap = [] as MarkerMap;
        const emptyMarker = {
          name: "",
          url: "",
          source: "custom" as const,
          category: "",
          id: "",
        };
        uniqueValues.items.forEach((item: LayerUniqueValues) => {
          markerMap.push([[item.value], emptyMarker]);
        });
        newStyle[`${updateType}_mapping`] = markerMap;
      } else if (updateType !== "marker") {
        if (
          (newStyle[`${updateType}_scale`] === "ordinal" &&
            newStyle[`${updateType}_range`]?.name !== layerProperties[`${updateType}_range`]?.name) ||
          !newStyle[`${updateType}_range`]?.color_map ||
          oldFieldName !== newFieldName
        ) {
          const colors = newStyle[`${updateType}_range`]?.colors;
          const uniqueValues = await getLayerUniqueValues(
            activeLayer.layer_id,
            newStyle[`${updateType}_field`]?.name as string,
            colors?.length
          );

          const colorMap = [] as ColorMap;
          uniqueValues.items.forEach((item: LayerUniqueValues, index: number) => {
            colorMap.push([[item.value], colors[index]]);
          });
          newStyle[`${updateType}_range`].color_map = colorMap;
        }
      }
      updateLayerStyle(newStyle);
    },
    [activeLayer, updateLayerStyle, layerProperties]
  );

  const onToggleChange = useCallback(
    (event: React.ChangeEvent<HTMLInputElement>, property: string) => {
      const newStyle = JSON.parse(JSON.stringify(layerProperties)) || {};
      newStyle[property] = event.target.checked;
      if (property === "stroked" && layerProperties?.["custom_marker"]) {
        newStyle["custom_marker"] = false;
      }
      if (property === "custom_marker" && layerProperties?.["stroked"]) {
        newStyle["stroked"] = false;
      }

      updateLayerStyle(newStyle);
    },
    [updateLayerStyle, layerProperties]
  );

  const resetStyle = useCallback(async () => {
    if (dataset?.properties) {
      const newStyle = JSON.parse(JSON.stringify(dataset.properties));
      await updateLayerStyle(newStyle);
    }
  }, [dataset, updateLayerStyle]);

  const saveStyleAsDatasetDefault = useCallback(async () => {
    if (dataset?.properties && layerProperties) {
      dataset.properties = JSON.parse(JSON.stringify(layerProperties));
      try {
        await updateDataset(dataset.id, dataset);
        await mutateDataset(dataset, false);
        toast.success(t("style_saved_as_dataset_default_success"));
      } catch (err) {
        toast.error(t("style_saved_as_dataset_default_error"));
      }
    }
  }, [dataset, layerProperties, mutateDataset, t]);
  const layerStyleMoreMenuOptions = useMemo(() => {
    const layerStyleMoreMenuOptions: PopperMenuItem[] = [
      // Save as default is only available to the user who owns the dataset
      ...(userProfile?.id === dataset?.user_id
        ? [
            {
              id: LayerStyleActions.SAVE_AS_DEFAULT,
              label: t("save_as_default"),
              icon: ICON_NAME.SAVE,
            },
          ]
        : []),
      {
        id: LayerStyleActions.RESET,
        label: t("reset"),
        icon: ICON_NAME.REFRESH,
      },
    ];

    return layerStyleMoreMenuOptions;
  }, [t, userProfile, dataset]);

  const markerExists = useMemo(() => {
    return (
      layerProperties["custom_marker"] &&
      (layerProperties["marker"]?.name ||
        (layerProperties["marker_field"] && layerProperties["marker_mapping"]?.length > 0))
    );
  }, [layerProperties]);

  const [collapseFillOptions, setCollapseFillOptions] = useState(true);
  const [collapseStrokeColorOptions, setCollapseStrokeColorOptions] = useState(true);
  const [collapseStrokeWidthOptions, setCollapseStrokeWidthOptions] = useState(true);
  const [collapsedMarkerIconOptions, setCollapsedMarkerIconOptions] = useState(true);
  const [collapseRadiusOptions, setCollapseRadiusOptions] = useState(true);

  return (
    <Container
      title={t("layer_design")}
      disablePadding={true}
      close={() => dispatch(setActiveRightPanel(undefined))}
      body={
        <>
          {(activeLayer?.type === layerType.Values.feature ||
            activeLayer?.type === layerType.Values.raster) && (
            <Stack direction="row" alignItems="center" spacing={2} sx={{ mb: 4, px: 2 }}>
              <ProjectLayerDropdown
                projectId={projectId}
                layerTypes={[layerType.Values.feature, layerType.Values.raster]}
              />
              <MoreMenu
                menuItems={layerStyleMoreMenuOptions}
                menuButton={
                  <Tooltip title={t("more_options")} arrow placement="top">
                    <IconButton>
                      <Icon iconName={ICON_NAME.MORE_VERT} style={{ fontSize: 15 }} />
                    </IconButton>
                  </Tooltip>
                }
                onSelect={async (menuItem: PopperMenuItem) => {
                  if (menuItem.id === LayerStyleActions.RESET) {
                    resetStyle();
                  } else if (menuItem.id === LayerStyleActions.SAVE_AS_DEFAULT) {
                    saveStyleAsDatasetDefault();
                  }
                }}
              />
            </Stack>
          )}
          <Divider />
          <Box
            sx={{
              display: "flex",
              p: 2,
              flexDirection: "column",
            }}>
            {activeLayer && (
              <GeneralOptions
                key={activeLayer.id}
                layer={activeLayer}
                onStyleChange={async (newStyle) => {
                  updateLayerStyle(newStyle);
                }}
              />
            )}
          </Box>
          <Divider sx={{ mb: 0 }} />
          {activeLayer?.type === "feature" && (
            <>
              <AccordionWrapper
                boxShadow="none"
                backgroundColor="transparent"
                disableGutters
                expanded={expanded === LayerStylePanels.STYLE}
                onChange={handleAccordionChange(LayerStylePanels.STYLE)}
                header={
                  <>
                    <Typography variant="body2" fontWeight="bold">
                      {t("style")}
                    </Typography>
                  </>
                }
                accordionSxProps={{
                  "&:before": {
                    display: "none",
                  },
                }}
                body={
                  <>
                    <Box
                      sx={{
                        display: "flex",
                        px: 4,
                        flexDirection: "column",
                      }}>
                      {activeLayer && (
                        <Stack>
                          {/* {FILL COLOR} */}
                          {activeLayer.feature_layer_geometry_type &&
                            ["polygon", "point"].includes(activeLayer.feature_layer_geometry_type) && (
                              <>
                                <SectionHeader
                                  active={layerProperties.filled}
                                  onToggleChange={(event) => {
                                    onToggleChange(event, "filled");
                                  }}
                                  label={
                                    activeLayer?.feature_layer_geometry_type === "line"
                                      ? t("color")
                                      : t("fill_color")
                                  }
                                  collapsed={collapseFillOptions}
                                  setCollapsed={setCollapseFillOptions}
                                />
                                <ColorOptions
                                  type="color"
                                  layerStyle={layerProperties}
                                  active={!!layerProperties.filled}
                                  layerFields={layerFields}
                                  collapsed={collapseFillOptions}
                                  selectedField={layerProperties.color_field}
                                  onStyleChange={async (newStyle: FeatureLayerProperties) => {
                                    if (
                                      newStyle.color_field?.type === "number" &&
                                      newStyle.color_scale !== "ordinal"
                                    ) {
                                      await updateColorClassificationBreaks("color", newStyle);
                                    } else if (newStyle.color_scale === "ordinal") {
                                      await updateOrdinalValues("color", newStyle);
                                    }

                                    updateLayerStyle(newStyle);
                                  }}
                                  layerId={activeLayer?.layer_id}
                                />
                              </>
                            )}

                          {/* {STROKE} */}
                          <SectionHeader
                            active={!!layerProperties.stroked}
                            onToggleChange={(event) => {
                              onToggleChange(event, "stroked");
                            }}
                            alwaysActive={activeLayer?.feature_layer_geometry_type === "line"}
                            label={
                              activeLayer?.feature_layer_geometry_type === "line"
                                ? t("color")
                                : t("stroke_color")
                            }
                            collapsed={collapseStrokeColorOptions}
                            setCollapsed={setCollapseStrokeColorOptions}
                          />

                          <ColorOptions
                            type="stroke_color"
                            layerStyle={layerProperties}
                            active={!!layerProperties.stroked}
                            layerFields={layerFields}
                            collapsed={collapseStrokeColorOptions}
                            selectedField={layerProperties.stroke_color_field}
                            onStyleChange={async (newStyle: FeatureLayerProperties) => {
                              if (
                                newStyle.stroke_color_field?.type === "number" &&
                                newStyle.stroke_color_scale !== "ordinal"
                              ) {
                                await updateColorClassificationBreaks("stroke_color", newStyle);
                              } else if (newStyle.stroke_color_scale === "ordinal") {
                                await updateOrdinalValues("stroke_color", newStyle);
                              }
                              updateLayerStyle(newStyle);
                            }}
                            layerId={activeLayer?.layer_id}
                          />

                          {/* {LINE STROKE} */}
                          {activeLayer.feature_layer_geometry_type &&
                            ["line", "polygon", "point"].includes(
                              activeLayer.feature_layer_geometry_type
                            ) && (
                              <>
                                <SectionHeader
                                  active={!!layerProperties.stroked}
                                  onToggleChange={(event) => {
                                    onToggleChange(event, "stroked");
                                  }}
                                  alwaysActive={activeLayer?.feature_layer_geometry_type === "line"}
                                  label={t("stroke_width")}
                                  collapsed={collapseStrokeWidthOptions}
                                  setCollapsed={setCollapseStrokeWidthOptions}
                                  disableAdvanceOptions={true}
                                />

                                <Settings
                                  type="stroke_width"
                                  layerStyle={layerProperties}
                                  active={!!layerProperties.stroked}
                                  collapsed={collapseStrokeWidthOptions}
                                  onStyleChange={(newStyle: FeatureLayerProperties) => {
                                    updateLayerStyle(newStyle);
                                  }}
                                  layerFields={layerFields}
                                  selectedField={layerProperties["stroke_width_field"]}
                                />
                              </>
                            )}

                          {/* {MARKER ICON} */}
                          {activeLayer.feature_layer_geometry_type &&
                            activeLayer.feature_layer_geometry_type === "point" && (
                              <>
                                <SectionHeader
                                  active={layerProperties["custom_marker"]}
                                  alwaysActive={false}
                                  onToggleChange={(event) => {
                                    onToggleChange(event, "custom_marker");
                                  }}
                                  label={t("custom_marker")}
                                  collapsed={collapsedMarkerIconOptions}
                                  setCollapsed={setCollapsedMarkerIconOptions}
                                />

                                <MarkerOptions
                                  type="marker"
                                  layerStyle={layerProperties}
                                  layerId={activeLayer?.layer_id}
                                  active={!!layerProperties["custom_marker"]}
                                  collapsed={collapsedMarkerIconOptions}
                                  onStyleChange={async (newStyle: FeatureLayerProperties) => {
                                    if (!map) return;
                                    await updateOrdinalValues("marker", newStyle);
                                    updateLayerStyle(newStyle);
                                  }}
                                  layerFields={layerFields}
                                  selectedField={layerProperties["marker_field"]}
                                />
                              </>
                            )}

                          {/* {RADIUS/SIZE} */}
                          {activeLayer?.feature_layer_geometry_type &&
                            activeLayer.feature_layer_geometry_type === "point" && (
                              <>
                                {layerProperties["custom_marker"] && (
                                  <>
                                    <SectionHeader
                                      active={markerExists}
                                      alwaysActive={true}
                                      label={t("marker_settings")}
                                      collapsed={collapseRadiusOptions}
                                      setCollapsed={setCollapseRadiusOptions}
                                      disableAdvanceOptions={true}
                                    />
                                    <Settings
                                      type="marker_size"
                                      layerStyle={layerProperties}
                                      active={markerExists}
                                      collapsed={collapseRadiusOptions}
                                      onStyleChange={(newStyle: FeatureLayerProperties) => {
                                        if (!map) return;
                                        updateLayerStyle(newStyle);
                                      }}
                                      layerFields={layerFields}
                                      selectedField={layerProperties["marker_size_field"]}
                                      activeLayer={activeLayer}
                                    />
                                  </>
                                )}

                                {!layerProperties["custom_marker"] && (
                                  <>
                                    <SectionHeader
                                      active={true}
                                      alwaysActive={true}
                                      label={t("point_settings")}
                                      collapsed={collapseStrokeWidthOptions}
                                      setCollapsed={setCollapseStrokeWidthOptions}
                                      disableAdvanceOptions={true}
                                    />

                                    <Settings
                                      type="radius"
                                      layerStyle={layerProperties}
                                      active={true}
                                      collapsed={collapseRadiusOptions}
                                      onStyleChange={(newStyle: FeatureLayerProperties) => {
                                        updateLayerStyle(newStyle);
                                      }}
                                      layerFields={layerFields}
                                      selectedField={layerProperties["radius_field"]}
                                    />
                                  </>
                                )}
                              </>
                            )}
                        </Stack>
                      )}
                    </Box>
                  </>
                }
              />
              <Divider sx={{ m: 0 }} />
              <AccordionWrapper
                boxShadow="none"
                backgroundColor="transparent"
                disableGutters
                expanded={expanded === LayerStylePanels.LABELS}
                onChange={handleAccordionChange(LayerStylePanels.LABELS)}
                accordionSxProps={{
                  "&:before": {
                    display: "none",
                  },
                }}
                header={
                  <>
                    <Typography variant="body2" fontWeight="bold">
                      {t("labels")}
                    </Typography>
                  </>
                }
                body={
                  <Box
                    sx={{
                      display: "flex",
                      px: 4,
                      flexDirection: "column",
                    }}>
                    {activeLayer && (
                      <LabelOptions
                        layer={activeLayer}
                        onStyleChange={async (newStyle) => {
                          updateLayerStyle(newStyle);
                        }}
                        key={activeLayer.id}
                      />
                    )}
                  </Box>
                }
              />
              <Divider sx={{ m: 0 }} />
              <AccordionWrapper
                boxShadow="none"
                backgroundColor="transparent"
                disableGutters
                expanded={expanded === LayerStylePanels.POPUP}
                onChange={handleAccordionChange(LayerStylePanels.POPUP)}
                header={
                  <Typography variant="body2" fontWeight="bold">
                    {t("popup")}
                  </Typography>
                }
                accordionSxProps={{
                  "&:before": {
                    display: "none",
                  },
                }}
                body={
                  <Box
                    sx={{
                      display: "flex",
                      px: 4,
                      flexDirection: "column",
                    }}>
                    {activeLayer && (
                      <InteractionOptions
                        layer={activeLayer}
                        onStyleChange={async (newStyle) => {
                          updateLayerStyle(newStyle);
                        }}
                        key={activeLayer.id}
                      />
                    )}
                  </Box>
                }
              />
            </>
          )}

          <Divider sx={{ m: 0 }} />
          <AccordionWrapper
            boxShadow="none"
            backgroundColor="transparent"
            disableGutters
            expanded={expanded === LayerStylePanels.LEGEND}
            onChange={handleAccordionChange(LayerStylePanels.LEGEND)}
            header={
              <Typography variant="body2" fontWeight="bold">
                {t("legend")}
              </Typography>
            }
            accordionSxProps={{
              "&:before": {
                display: "none",
              },
            }}
            body={
              <Box
                sx={{
                  display: "flex",
                  px: 4,
                  flexDirection: "column",
                }}>
                {activeLayer && (
                  <LegendOptions
                    layer={activeLayer}
                    onStyleChange={async (newStyle) => {
                      updateLayerStyle(newStyle);
                    }}
                  />
                )}
              </Box>
            }
          />
          <Divider sx={{ mt: 0 }} />
        </>
      }
    />
  );
};

export default LayerStylePanel;
