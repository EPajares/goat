import { Button, Stack, Typography } from "@mui/material";
import { useEffect, useRef } from "react";
import { useTranslation } from "react-i18next";

import {
  addPendingFeature,
  commitFeature,
  markForDeletion,
  pushSnapshot,
  setMode,
  removePendingFeature,
  updatePendingGeometry,
  updatePendingProperties,
} from "@/lib/store/featureEditor/slice";
import { useDraw } from "@/lib/providers/DrawProvider";
import { useAppDispatch, useAppSelector } from "@/hooks/store/ContextHooks";
import useLayerFields from "@/hooks/map/CommonHooks";

import { formatFieldValue } from "@/lib/utils/formatFieldValue";
import type { FieldKind } from "@/lib/validations/layer";
import { resolveDisplayKind } from "@/lib/validations/layer";

import TemporalPicker from "@p4b/ui/components/TemporalPicker";

import {
  BOOLEAN_SELECT_ITEMS,
  booleanToSelectValue,
  parseBooleanInput,
} from "@/lib/utils/fieldInput";

import Container from "@/components/map/panels/Container";
import Selector from "@/components/map/panels/common/Selector";
import TextFieldInput from "@/components/map/panels/common/TextFieldInput";

const FeatureEditPanel: React.FC = () => {
  const { t } = useTranslation("common");
  const dispatch = useAppDispatch();
  const { drawControl } = useDraw();
  const { activeLayerId, activeFeatureId, pendingFeatures, mode, geometryType } = useAppSelector(
    (state) => state.featureEditor
  );
  const isTableLayer = !geometryType;
  const { layerFields } = useLayerFields(activeLayerId || "");

  const pushHistory = () => {
    // Snapshot capture must never block the edit itself: getAll() throws when
    // the draw control has been removed from the map.
    let drawFeatures: GeoJSON.FeatureCollection = { type: "FeatureCollection", features: [] };
    try {
      drawFeatures = drawControl?.getAll() ?? drawFeatures;
    } catch {
      // fall through with an empty collection
    }
    dispatch(pushSnapshot({ drawFeatures }));
  };

  const filteredFields = layerFields.filter(
    (f) => f.type === "string" || f.type === "number" || f.type === "date" || f.type === "boolean"
  );

  // In draw mode, eagerly create a pending feature so user can fill attributes before drawing
  const createdForDrawRef = useRef(false);
  useEffect(() => {
    if (mode === "draw" && activeLayerId && !activeFeatureId && !createdForDrawRef.current) {
      createdForDrawRef.current = true;
      dispatch(
        addPendingFeature({
          id: crypto.randomUUID(),
          drawFeatureId: null,
          geometry: null,
          properties: {},
          committed: false,
          action: "create",
        })
      );
    }
    if (mode !== "draw") {
      createdForDrawRef.current = false;
    }
  }, [mode, activeLayerId, activeFeatureId, dispatch]);

  // Track which fields have had a snapshot pushed (reset on feature change)
  const snapshotPushedFieldsRef = useRef<Set<string>>(new Set());
  useEffect(() => {
    snapshotPushedFieldsRef.current.clear();
  }, [activeFeatureId]);

  // Show panel in draw mode or when a feature is selected
  if (!activeLayerId) return null;
  if (mode === "select" && !activeFeatureId) return null;

  const feature = activeFeatureId ? pendingFeatures[activeFeatureId] : null;
  const hasGeometry = feature?.geometry !== null && feature?.geometry !== undefined;

  // For update features, check if anything actually changed
  const hasChanges = (() => {
    if (!feature) return false;
    // For table layers, new features are always committable (no geometry needed)
    // For geospatial layers, require geometry to be drawn
    if (feature.action === "create") return isTableLayer || hasGeometry;
    // Compare geometry and properties with originals
    const geomChanged = JSON.stringify(feature.geometry) !== JSON.stringify(feature.originalGeometry);
    const filterInternal = (props: Record<string, unknown>) => {
      const f = { ...props }; delete f._fillColor; delete f._fillOpacity; return f;
    };
    const propsChanged = JSON.stringify(filterInternal(feature.properties)) !== JSON.stringify(filterInternal(feature.originalProperties || {}));
    return geomChanged || propsChanged;
  })();

  const handlePropertyChange = (fieldName: string, value: string) => {
    if (!activeFeatureId || !feature) return;

    // Push snapshot on first change per field
    if (!snapshotPushedFieldsRef.current.has(fieldName)) {
      snapshotPushedFieldsRef.current.add(fieldName);
      pushHistory();
    }

    const fieldType = filteredFields.find((f) => f.name === fieldName)?.type;
    const parsedValue =
      fieldType === "number"
        ? (value === "" ? null : Number(value))
        : fieldType === "boolean"
          ? parseBooleanInput(value)
          : (value || null);
    dispatch(
      updatePendingProperties({
        id: activeFeatureId,
        properties: { ...feature.properties, [fieldName]: parsedValue },
      })
    );
  };

  const handleDone = () => {
    if (!activeFeatureId || !feature) return;
    // Remove from MapboxDraw — committed features render via GeoJSON overlay
    if (feature.drawFeatureId && drawControl) {
      const drawFeature = drawControl.get(feature.drawFeatureId);
      if (drawFeature?.geometry) {
        dispatch(updatePendingGeometry({ id: activeFeatureId, geometry: drawFeature.geometry }));
      }
      drawControl.delete(feature.drawFeatureId);
    }
    pushHistory();
    dispatch(commitFeature(activeFeatureId));
    // Return to draw mode only if this was a new feature, otherwise stay in select
    if (feature.action === "create") {
      dispatch(setMode("draw"));
    }
  };

  const handleCancel = () => {
    if (activeFeatureId) {
      if (feature?.drawFeatureId && drawControl) {
        drawControl.delete(feature.drawFeatureId);
      }
      dispatch(removePendingFeature(activeFeatureId));
    }
    dispatch(setMode("select"));
  };

  const handleDelete = () => {
    if (!activeFeatureId || !feature) return;
    if (feature.drawFeatureId && drawControl) {
      drawControl.delete(feature.drawFeatureId);
    }
    pushHistory();
    if (feature.action === "update") {
      dispatch(markForDeletion(activeFeatureId));
    } else {
      dispatch(removePendingFeature(activeFeatureId));
    }
  };

  return (
    <Container
      title={t("feature_attributes")}
      close={handleCancel}
      body={
        <Stack spacing={2}>
          {filteredFields.map((field) => {
            const isComputed = field.is_computed === true;
            let displayValue = "";
            if (isComputed) {
              const raw = feature?.properties[field.name];
              if (raw != null && raw !== "") {
                displayValue = formatFieldValue(
                  raw,
                  (resolveDisplayKind(field) as FieldKind) ?? "number",
                  field.display_config ?? {},
                );
              } else if (mode === "draw") {
                displayValue = t("computed_on_save");
              }
            } else {
              displayValue =
                feature?.properties[field.name] != null
                  ? String(feature.properties[field.name])
                  : "";
            }

            if (!isComputed && field.type === "date") {
              return (
                <TemporalPicker
                  key={field.name}
                  kind="datetime"
                  label={field.name}
                  value={(feature?.properties[field.name] as string) ?? ""}
                  onChange={(value) => handlePropertyChange(field.name, value)}
                />
              );
            }

            if (!isComputed && field.type === "boolean") {
              const current = booleanToSelectValue(feature?.properties[field.name]);
              return (
                <Selector
                  key={field.name}
                  label={field.name}
                  selectedItems={BOOLEAN_SELECT_ITEMS.find((i) => i.value === current)}
                  setSelectedItems={(item) => {
                    const value = Array.isArray(item) ? item[0]?.value : item?.value;
                    handlePropertyChange(field.name, String(value ?? ""));
                  }}
                  items={[...BOOLEAN_SELECT_ITEMS]}
                />
              );
            }

            return (
              <TextFieldInput
                key={field.name}
                label={field.name}
                type={isComputed || field.type !== "number" ? "text" : "number"}
                placeholder={
                  isComputed
                    ? ""
                    : field.type === "number"
                      ? t("enter_a_number")
                      : t("enter_text")
                }
                value={displayValue}
                disabled={isComputed}
                onChange={(value) => {
                  if (isComputed) return;
                  handlePropertyChange(field.name, value);
                }}
                clearable={false}
              />
            );
          })}
        </Stack>
      }
      action={
        <Stack direction="row" alignItems="center" justifyContent="space-between" sx={{ width: "100%" }}>
          {feature?.committed || feature?.action === "update" ? (
            <Button
              variant="text"
              size="small"
              color="error"
              onClick={handleDelete}
              sx={{ textTransform: "none" }}>
              {t("delete")}
            </Button>
          ) : (
            <Typography variant="caption" color="text.secondary">
              {!hasGeometry ? t("draw_geometry_first") : ""}
            </Typography>
          )}
          <Button
            variant="contained"
            size="small"
            disabled={!hasChanges}
            onClick={handleDone}
            sx={{ textTransform: "none", minWidth: 80 }}>
            {t("done")}
          </Button>
        </Stack>
      }
    />
  );
};

export default FeatureEditPanel;
