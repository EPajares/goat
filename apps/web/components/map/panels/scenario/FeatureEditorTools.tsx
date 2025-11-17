import MapboxDraw from "@mapbox/mapbox-gl-draw";
import { Stack, ToggleButton, ToggleButtonGroup, Tooltip, useTheme } from "@mui/material";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import type { MapGeoJSONFeature, MapLayerMouseEvent } from "react-map-gl/maplibre";
import { useMap } from "react-map-gl/maplibre";
import { toast } from "react-toastify";
import type { Id as ToastId, TypeOptions } from "react-toastify";

import { ICON_NAME, Icon } from "@p4b/ui/components/Icon";

import { useDraw } from "@/lib/providers/DrawProvider";
import { setIsMapGetInfoActive, setPopupEditor } from "@/lib/store/map/slice";
import type { Layer } from "@/lib/validations/layer";

import { EditorModes } from "@/types/map/popover";

import { useAppDispatch } from "@/hooks/store/ContextHooks";

import FormLabelHelper from "@/components/common/FormLabelHelper";
import { CustomDrawModes } from "@/components/map/controls/draw/Draw";

export type FeatureEditorToolsProps = {
  layer: Layer;
  projectLayerId?: number;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  onFinish?: (payload?: any) => void;
  disabled?: boolean;
};

export const SelectModes = {
  DRAW_CIRCLE: CustomDrawModes.DRAW_CIRCLE,
};

export const toMapDrawModeGeometryType = {
  point: "POINT",
  line: "LINE_STRING",
  polygon: "POLYGON",
};

const FeatureEditorTools = ({
  layer: _layer,
  projectLayerId,
  onFinish,
  disabled,
}: FeatureEditorToolsProps) => {
  const [layer, setLayer] = useState<FeatureEditorToolsProps["layer"] | null>(_layer);
  const { map } = useMap();
  const { t } = useTranslation("common");
  const theme = useTheme();
  const dispatch = useAppDispatch();
  const { drawControl } = useDraw();
  const messageToastId = useRef<ToastId | null>(null);
  const [editType, setEditType] = useState<EditorModes | null>(null);
  const [selectType, setSelectType] = useState<string | null>(null);

  const editTools = useMemo(
    () => [
      { title: t("draw"), mode: EditorModes.DRAW, icon: ICON_NAME.PLUS },
      { title: t("modify_geometry"), mode: EditorModes.MODIFY_GEOMETRY, icon: ICON_NAME.EDIT },
      {
        title: t("modify_attributes"),
        mode: EditorModes.MODIFY_ATTRIBUTES,
        icon: ICON_NAME.TABLE,
      },
      { title: t("delete"), mode: EditorModes.DELETE, icon: ICON_NAME.TRASH },
    ],
    [t]
  );

  const startToastMessages = useCallback(
    (type: EditorModes) => {
      if (type === EditorModes.DELETE) {
        return t("click_on_feature_to_delete");
      } else if (type === EditorModes.MODIFY_ATTRIBUTES) {
        return t("click_on_feature_to_modify_attributes");
      } else if (type === EditorModes.DRAW) {
        if (layer?.feature_layer_geometry_type === "point") {
          return t("click_to_add_point");
        } else if (layer?.feature_layer_geometry_type === "line") {
          return t("click_to_start_drawing_line");
        } else if (layer?.feature_layer_geometry_type === "polygon") {
          return t("click_to_start_drawing_polygon");
        }
      }
    },
    [layer?.feature_layer_geometry_type, t]
  );

  const drawToastMessages = useCallback(
    (geometryType: "line" | "polygon", coordinatesLength: number) => {
      if (geometryType === "line") {
        if (coordinatesLength === 1) {
          return t("click_to_continue_drawing_line");
        } else {
          return t("click_to_continue_double_click_finish_drawing_line");
        }
      } else if (geometryType === "polygon") {
        if (coordinatesLength <= 3) {
          return t("click_to_continue_drawing_polygon");
        } else {
          return t("click_to_continue_double_click_finish_drawing_polygon");
        }
      }
    },
    [t]
  );

  const hideToast = useCallback(() => {
    if (messageToastId.current) {
      toast.dismiss(messageToastId.current);
      messageToastId.current = null;
    }
  }, []);

  const showStartToast = useCallback(
    (editType: EditorModes, toastType: TypeOptions) => {
      hideToast();
      messageToastId.current = toast(startToastMessages(editType), {
        autoClose: false,
        type: toastType,
        position: "bottom-center",
      });
    },
    [hideToast, startToastMessages]
  );

  const updateDrawToast = useCallback(
    (geometryType: "line" | "polygon", coordinatesLength: number) => {
      if (messageToastId.current) {
        toast.update(messageToastId.current, {
          render: drawToastMessages(geometryType, coordinatesLength),
        });
      }
    },
    [drawToastMessages]
  );

  const clean = useCallback(() => {
    setEditType(null);
    setSelectType(null);
    dispatch(setIsMapGetInfoActive(true));
    drawControl?.deleteAll();
    drawControl?.changeMode(MapboxDraw.constants.modes.SIMPLE_SELECT);
    hideToast();
    dispatch(setPopupEditor(undefined));
  }, [dispatch, drawControl, hideToast]);

  useEffect(() => {
    if (layer && layer?.id !== _layer.id) {
      setLayer(_layer);
      clean();
    }
  }, [_layer, clean, editType, layer, layer?.id, selectType]);

  const reenableDraw = useCallback(
    (drawControl: MapboxDraw | null, newEditType: EditorModes | null) => {
      drawControl?.deleteAll();
      const geomType = layer?.feature_layer_geometry_type;
      if (!geomType) {
        return;
      }
      if (newEditType === EditorModes.DRAW) {
        const mapboxDrawMode = `DRAW_${toMapDrawModeGeometryType[geomType]}`;
        drawControl?.changeMode(MapboxDraw.constants.modes[mapboxDrawMode]);
        showStartToast(newEditType, "info");
      }
    },
    [layer?.feature_layer_geometry_type, showStartToast]
  );

  const handleFeatureClick = useCallback(
    (e: MapLayerMouseEvent) => {
      const features = map?.queryRenderedFeatures(e.point);
      const layerId = layer?.id.toString();
      if (!features || !layerId) {
        return;
      }
      const selectedEditFeatures = features?.filter(
        (feature) =>
          layerId === feature?.properties?.layer_id ||
          projectLayerId === feature?.properties?.layer_project_id
      );
      if (selectedEditFeatures?.length && editType) {
        // Hide message toast
        hideToast();
        dispatch(
          setPopupEditor({
            lngLat: [e.lngLat.lng, e.lngLat.lat],
            editMode: editType,
            layer,
            feature: selectedEditFeatures[0] as MapGeoJSONFeature,
            onClose: () => {
              dispatch(setPopupEditor(undefined));
              // Reshow edit type
              showStartToast(editType, "info");
            },
            onConfirm: (payload) => {
              onFinish && onFinish(payload);
              showStartToast(editType, "info");
            },
          })
        );
      }
    },
    [map, layer, editType, projectLayerId, hideToast, dispatch, showStartToast, onFinish]
  );

  const handleFeatureCreate = useCallback(
    (e: { features: object[] }) => {
      const feature = e.features[0] as MapGeoJSONFeature;
      if (feature) {
        hideToast();
        setTimeout(() => {
          dispatch(
            setPopupEditor({
              editMode: editType,
              layer,
              feature: feature,
              onClose: () => {
                drawControl?.deleteAll();
                dispatch(setPopupEditor(undefined));
                reenableDraw(drawControl, editType);
              },
              onConfirm: (payload) => {
                drawControl?.deleteAll();
                onFinish && onFinish(payload);
                reenableDraw(drawControl, editType);
              },
            })
          );
        }, 100);
      }
    },
    [layer, hideToast, dispatch, editType, drawControl, reenableDraw, onFinish]
  );

  const handleFeatureCreateTooltipUpdates = useCallback(() => {
    const drawnFeatures = drawControl?.getAll();
    const geometryType = layer?.feature_layer_geometry_type;
    if (drawnFeatures?.features?.length && (geometryType === "line" || geometryType === "polygon")) {
      // Get the last feature drawn
      const feature = drawnFeatures.features[drawnFeatures.features.length - 1];
      const coordinates = feature.geometry["coordinates"];
      if (coordinates?.length) {
        updateDrawToast(geometryType, coordinates.length);
      }
    }
  }, [drawControl, layer?.feature_layer_geometry_type, updateDrawToast]);

  useEffect(() => {
    if (!map) {
      return;
    }
    if (editType === EditorModes.DELETE || editType === EditorModes.MODIFY_ATTRIBUTES) {
      map.on("click", handleFeatureClick);
      dispatch(setIsMapGetInfoActive(false));
      showStartToast(editType, "info");
      return () => {
        map.off("click", handleFeatureClick);
        dispatch(setIsMapGetInfoActive(true));
        hideToast();
      };
    }
    if (editType === EditorModes.DRAW) {
      map.on(MapboxDraw.constants.events.CREATE, handleFeatureCreate);
      map.on("click", handleFeatureCreateTooltipUpdates);
      return () => {
        map.off(MapboxDraw.constants.events.CREATE, handleFeatureCreate);
        map.off("click", handleFeatureCreateTooltipUpdates);
        hideToast();
      };
    }
  }, [
    map,
    editType,
    handleFeatureClick,
    dispatch,
    handleFeatureCreate,
    t,
    startToastMessages,
    hideToast,
    showStartToast,
    handleFeatureCreateTooltipUpdates,
  ]);

  useEffect(() => {
    return () => {
      clean();
    };
  }, [clean]);

  return (
    <Stack spacing={4}>
      <Stack>
        <FormLabelHelper
          label={t("feature_editor_tools")}
          color={disabled ? theme.palette.secondary.main : "inherit"}
        />
        <ToggleButtonGroup
          value={editType}
          exclusive
          aria-label="feature editor tools"
          onChange={(_event: React.MouseEvent<HTMLElement>, newEditType: EditorModes | null) => {
            setSelectType(null);
            dispatch(setPopupEditor(undefined));
            reenableDraw(drawControl, newEditType);
            setEditType(newEditType);
          }}>
          {editTools.map((tool) => (
            <Tooltip key={tool.mode} title={tool.title} placement="top" arrow>
              <ToggleButton value={tool.mode} disabled={tool.mode === EditorModes.MODIFY_GEOMETRY}>
                <Icon fontSize="inherit" iconName={tool.icon} />
              </ToggleButton>
            </Tooltip>
          ))}
        </ToggleButtonGroup>
      </Stack>
    </Stack>
  );
};

export default FeatureEditorTools;
