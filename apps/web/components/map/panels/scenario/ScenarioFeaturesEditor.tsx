import {
  Box,
  IconButton,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Tooltip,
  Typography,
  useTheme,
} from "@mui/material";
import bbox from "@turf/bbox";
import { useCallback, useEffect, useMemo, useRef } from "react";
import { useTranslation } from "react-i18next";
import { useMap } from "react-map-gl/maplibre";
import { toast } from "react-toastify";
import { ZodError } from "zod";

import { ICON_NAME, Icon } from "@p4b/ui/components/Icon";

import { getDataset, useDataset } from "@/lib/api/layers";
import {
  createProjectScenarioFeatures,
  deleteProjectScenarioFeature,
  updateProjectScenarioFeatures,
  useProjectScenarioFeatures,
} from "@/lib/api/projects";
import { setPopupEditor, setSelectedScenarioLayer } from "@/lib/store/map/slice";
import { fitBounds } from "@/lib/utils/map/navigate";
import { stringify as stringifyToWKT } from "@/lib/utils/map/wkt";
import type { ProjectLayer } from "@/lib/validations/project";
import type { ScenarioFeature, ScenarioFeatures } from "@/lib/validations/scenario";
import {
  type Scenario,
  scenarioEditTypeEnum,
  scenarioFeaturePost,
  scenarioFeatureUpdate,
} from "@/lib/validations/scenario";

import type { SelectorItem } from "@/types/map/common";
import { EditorModes } from "@/types/map/popover";

import { useFilteredProjectLayers } from "@/hooks/map/LayerPanelHooks";
import { useAppDispatch, useAppSelector } from "@/hooks/store/ContextHooks";

import SectionHeader from "@/components/map/panels/common/SectionHeader";
import SectionOptions from "@/components/map/panels/common/SectionOptions";
import Selector from "@/components/map/panels/common/Selector";
import { getLayerIcon } from "@/components/map/panels/layer/Layer";
import FeatureEditorTools from "@/components/map/panels/scenario/FeatureEditorTools";

const ScenarioFeaturesTable = ({
  projectId,
  scenarioId,
  projectLayers,
  scenarioFeatures,
  mutateScenarioFeatures,
}: {
  projectId: string;
  scenarioId: string;
  scenarioFeatures: ScenarioFeatures | undefined;
  projectLayers: ProjectLayer[];
  mutateScenarioFeatures: () => void;
}) => {
  const { t } = useTranslation("common");
  const theme = useTheme();
  const { map } = useMap();
  const dispatch = useAppDispatch();

  const handleZoomToFeature = (feature: ScenarioFeature) => {
    if (!map) return;
    const boundingBox = bbox(feature);
    fitBounds(map, boundingBox as [number, number, number, number]);
  };

  const projectLayerIdToName = useMemo(() => {
    return projectLayers.reduce(
      (acc, layer) => {
        acc[layer.id] = layer.name;
        return acc;
      },
      {} as Record<number, string>
    );
  }, [projectLayers]);

  const handleDeleteFeature = async (feature: ScenarioFeature) => {
    const projectLayerId = feature.properties?.layer_project_id;
    const projectLayer = projectLayers.find((layer) => layer.id === projectLayerId);
    if (!projectLayer) return;
    const layerId = projectLayer.layer_id;
    if (!layerId) return;
    const layer = await getDataset(layerId);
    if (!layer) return;
    handleZoomToFeature(feature);
    dispatch(
      setPopupEditor({
        editMode: EditorModes.DELETE,
        layer,
        feature,
        onClose: () => {
          dispatch(setPopupEditor(undefined));
        },
        onConfirm: async () => {
          const properties = feature.properties;
          try {
            await deleteProjectScenarioFeature(
              projectId,
              projectLayerId,
              scenarioId,
              properties.id,
              properties?.h3_3 as number
            );
            toast.success(t("feature_deleted_success"));
          } catch (error) {
            console.error(error);
            toast.error(t("feature_delete_error"));
          } finally {
            dispatch(setPopupEditor(undefined));
            mutateScenarioFeatures();
          }
        },
      })
    );
  };

  const editTypeLabel = (editType: string) => {
    switch (editType) {
      case scenarioEditTypeEnum.Enum.m:
        return t("new");
      case scenarioEditTypeEnum.Enum.d:
        return t("deleted");
      case scenarioEditTypeEnum.Enum.m:
        return t("modified");
      default:
        return editType;
    }
  };
  return (
    <>
      <Table size="small" aria-label="scenario features table" stickyHeader>
        <TableHead>
          <TableRow>
            <TableCell align="left" sx={{ px: 2, width: 100 }}>
              <Typography variant="caption" fontWeight="bold">
                {t("layer")}
              </Typography>
            </TableCell>
            <TableCell align="left" sx={{ px: 2, width: 100 }}>
              <Typography variant="caption" fontWeight="bold">
                {t("type")}
              </Typography>
            </TableCell>
            <TableCell align="left" sx={{ px: 2, width: 60 }}>
              {" "}
            </TableCell>
          </TableRow>
        </TableHead>
      </Table>

      <TableContainer style={{ marginTop: 0, maxHeight: 250 }}>
        <Table size="small" aria-label="scenario features table">
          <TableBody>
            {!scenarioFeatures?.features?.length && (
              <TableRow>
                <TableCell align="center" colSpan={3}>
                  <Typography variant="caption" fontWeight="bold">
                    {t("no_scenario_features")}
                  </Typography>
                </TableCell>
              </TableRow>
            )}
            {/* Scenario Feature Table  */}
            {!scenarioFeatures
              ? null
              : scenarioFeatures.features.map((_feature) => (
                  <TableRow key={_feature.id}>
                    <TableCell align="left" sx={{ px: 2, width: 100 }}>
                      <Typography variant="caption" fontWeight="bold">
                        {/* {_feature.properties?.layer_project_id} */}
                        {projectLayerIdToName[_feature.properties?.layer_project_id] || t("unknown")}
                      </Typography>
                    </TableCell>
                    <TableCell align="left" sx={{ px: 2, width: 100 }}>
                      <Typography variant="caption" fontWeight="bold">
                        {editTypeLabel(_feature.properties?.edit_type)}
                      </Typography>
                    </TableCell>
                    <TableCell align="right" sx={{ px: 2, width: 60 }}>
                      <Stack direction="row" alignItems="center" justifyContent="end" spacing={1}>
                        <Tooltip title={t("zoom_to_feature")} placement="top">
                          <IconButton
                            size="small"
                            onClick={() => handleZoomToFeature(_feature)}
                            sx={{
                              "&:hover": {
                                color: theme.palette.primary.main,
                              },
                            }}>
                            <Icon
                              iconName={ICON_NAME.ZOOM_IN}
                              style={{ fontSize: "12px" }}
                              htmlColor="inherit"
                            />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title={t("delete_feature")} placement="top">
                          <IconButton
                            size="small"
                            sx={{
                              "&:hover": {
                                color: theme.palette.error.main,
                              },
                            }}
                            onClick={async () => await handleDeleteFeature(_feature)}>
                            <Icon
                              iconName={ICON_NAME.TRASH}
                              style={{ fontSize: "12px" }}
                              htmlColor="inherit"
                            />
                          </IconButton>
                        </Tooltip>
                      </Stack>
                    </TableCell>
                  </TableRow>
                ))}
          </TableBody>
        </Table>
      </TableContainer>
    </>
  );
};

const ScenarioFeaturesEditor = ({ scenario, projectId }: { scenario: Scenario; projectId: string }) => {
  const theme = useTheme();
  const { t } = useTranslation("common");
  const dispatch = useAppDispatch();
  const { layers: projectLayers } = useFilteredProjectLayers(projectId, ["table"], []);
  const { scenarioFeatures, mutate: mutateScenarioFeatures } = useProjectScenarioFeatures(
    projectId,
    scenario.id
  );
  const selectedScenarioEditLayer = useAppSelector((state) => state.map.selectedScenarioLayer);
  const popupEditor = useAppSelector((state) => state.map.popupEditor);
  const popupEditorRef = useRef(popupEditor);

  useEffect(() => {
    popupEditorRef.current = popupEditor;
  }, [popupEditor]);

  const scenarioEditLayers = useMemo(() => {
    const scenarioLayers = [] as SelectorItem[];
    if (projectLayers) {
      projectLayers.forEach((layer) => {
        if (layer.type === "feature") {
          layer.feature_layer_geometry_type;
          scenarioLayers.push({
            value: layer.id,
            label: layer.name,
            icon: getLayerIcon(layer),
          });
        }
      });
    }
    return scenarioLayers;
  }, [projectLayers]);

  const selectedScenarioLayer = useMemo(() => {
    if (selectedScenarioEditLayer) {
      return projectLayers?.find((layer) => layer.id === selectedScenarioEditLayer.value);
    }
  }, [selectedScenarioEditLayer, projectLayers]);

  const { dataset: layer } = useDataset(selectedScenarioLayer?.layer_id || "");

  const validateProperties = useCallback(
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    (properties: any) => {
      if (!properties.id) {
        throw new Error("Feature ID is missing");
      }
    },
    []
  );

  const handleSubmit = useCallback(
    async (payload) => {
      dispatch(setPopupEditor(undefined));
      if (popupEditorRef.current && selectedScenarioLayer) {
        const type = popupEditorRef.current.editMode;
        const properties = popupEditorRef.current.feature?.properties;
        if (type === EditorModes.DELETE && popupEditorRef.current.feature && properties) {
          try {
            validateProperties(properties);
            await deleteProjectScenarioFeature(
              projectId,
              selectedScenarioLayer?.id,
              scenario.id,
              properties.id,
              properties.h3_3
            );
            toast.success(t("feature_deleted_success"));
          } catch (error) {
            console.error(error);
            toast.error(t("feature_delete_error"));
          } finally {
            mutateScenarioFeatures();
          }
        } else if (
          (type === EditorModes.MODIFY_ATTRIBUTES || type === EditorModes.MODIFY_GEOMETRY) &&
          payload
        ) {
          try {
            validateProperties(properties);
            const { layer_id: _, ...updatedPayload } = payload;
            const updateFeature = scenarioFeatureUpdate.parse({
              ...updatedPayload,
              edit_type: properties?.edit_type || scenarioEditTypeEnum.Enum.m,
              layer_project_id: selectedScenarioLayer?.id,
            });
            await updateProjectScenarioFeatures(projectId, selectedScenarioLayer?.id, scenario.id, [
              updateFeature,
            ]);
            toast.success(t("feature_updated_success"));
          } catch (error) {
            if (error instanceof ZodError) {
              console.error("Parse error details:", error.errors);
            } else {
              console.error("Unexpected error:", error);
            }
            toast.error(t("feature_update_error"));
          } finally {
            mutateScenarioFeatures();
          }
        } else if (type === EditorModes.DRAW && payload) {
          try {
            const geom = popupEditorRef.current.feature?.geometry;
            if (!geom) {
              throw new Error("Feature geometry is missing");
            }
            const createFeature = scenarioFeaturePost.parse({
              ...payload,
              edit_type: scenarioEditTypeEnum.Enum.n,
              layer_project_id: selectedScenarioLayer?.id,
              geom: stringifyToWKT(geom),
            });
            await createProjectScenarioFeatures(projectId, selectedScenarioLayer?.id, scenario.id, [
              createFeature,
            ]);
            toast.success(t("feature_created_success"));
          } catch (error) {
            if (error instanceof ZodError) {
              console.error("Parse error details:", error.errors);
            } else {
              console.error("Unexpected error:", error);
            }
            toast.error(t("feature_create_error"));
          } finally {
            mutateScenarioFeatures();
          }
        }
      }
    },
    [dispatch, mutateScenarioFeatures, projectId, scenario.id, selectedScenarioLayer, t, validateProperties]
  );

  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: "column",
      }}>
      <Typography variant="body2" sx={{ fontStyle: "italic", marginBottom: theme.spacing(4) }}>
        {t("scenario_features_editor_description")}
      </Typography>
      <SectionHeader
        active={true}
        alwaysActive={true}
        label={t("layer")}
        icon={ICON_NAME.LAYERS}
        disableAdvanceOptions={true}
      />
      <SectionOptions
        active={true}
        baseOptions={
          <>
            <Selector
              selectedItems={selectedScenarioEditLayer}
              setSelectedItems={(item: SelectorItem[] | SelectorItem | undefined) => {
                dispatch(setSelectedScenarioLayer(item as SelectorItem));
              }}
              items={scenarioEditLayers}
              label={t("select_layer")}
              placeholder={t("select_layer")}
              tooltip={t("select_layer_for_scenario")}
            />
          </>
        }
      />

      {/* {EDIT TOOLS} */}
      <SectionHeader
        active={selectedScenarioEditLayer !== undefined}
        alwaysActive={true}
        label={t("edit_tools")}
        icon={ICON_NAME.SCENARIO}
        disableAdvanceOptions={true}
      />
      <SectionOptions
        active={layer !== undefined}
        baseOptions={
          <>
            {layer !== undefined && (
              <FeatureEditorTools
                layer={layer}
                onFinish={handleSubmit}
                projectLayerId={selectedScenarioLayer?.id}
              />
            )}
          </>
        }
      />

      {/* {SCENARIO FEATURES} */}
      <SectionHeader
        active={true}
        alwaysActive={true}
        label={t("scenario_features")}
        icon={ICON_NAME.TABLE}
        disableAdvanceOptions={true}
      />

      <SectionOptions
        active={scenarioFeatures !== undefined}
        baseOptions={
          <>
            <ScenarioFeaturesTable
              projectId={projectId}
              scenarioId={scenario.id}
              scenarioFeatures={scenarioFeatures}
              projectLayers={projectLayers}
              mutateScenarioFeatures={mutateScenarioFeatures}
            />
          </>
        }
      />
    </Box>
  );
};

export default ScenarioFeaturesEditor;
