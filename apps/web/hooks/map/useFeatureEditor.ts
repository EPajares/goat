import MapboxDraw from "@mapbox/mapbox-gl-draw";
import { DrawHistory } from "@p4b/draw";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useParams } from "next/navigation";
import type { MapRef } from "react-map-gl/maplibre";
import { useTranslation } from "react-i18next";
import { toast } from "react-toastify";
import { mutate as globalMutate } from "swr";

import type { MapLayerMouseEvent } from "react-map-gl/maplibre";

import { COLLECTIONS_API_BASE_URL, createFeaturesBulk, deleteFeature, getFeature, getFeatures, replaceFeature } from "@/lib/api/layers";
import { useProjectLayers } from "@/lib/api/projects";
import {
  addPendingFeature,
  clearPendingFeatures,
  commitFeature,
  pushSnapshot,
  redo,
  removePendingFeature,
  setActiveFeature,
  setDrawFeatureId,
  setIsSaving,
  setMode,
  stopEditing,
  undo,
  updatePendingGeometry,
} from "@/lib/store/featureEditor/slice";
import { setIsMapGetInfoActive, setMapCursor, setPopupInfo } from "@/lib/store/map/slice";
import { useDraw } from "@/lib/providers/DrawProvider";
import { useAppDispatch, useAppSelector } from "@/hooks/store/ContextHooks";
import type { FeatureLayerPointProperties } from "@/lib/validations/layer";
import { getMapboxStyleMarker } from "@/lib/transformers/layer";
import type { ProjectLayer } from "@/lib/validations/project";

/**
 * Hook that wires the feature editor Redux state to MapboxDraw.
 * Handles mode switching, draw events, save, discard, and cleanup.
 */
export function useFeatureEditor(mapRef: React.RefObject<MapRef | null> | null) {
  const { t } = useTranslation("common");
  const dispatch = useAppDispatch();
  const { drawControl } = useDraw();
  const { projectId } = useParams();
  const { layers: projectLayers, mutate: mutateProjectLayers } = useProjectLayers(projectId as string);
  const featureEditor = useAppSelector((state) => state.featureEditor);
  const { activeLayerId, activeFeatureId, geometryType, mode, pendingFeatures, isSaving } = featureEditor;
  const activeLayerIdRef = useRef(activeLayerId);
  activeLayerIdRef.current = activeLayerId;
  const activeFeatureIdRef = useRef(activeFeatureId);
  activeFeatureIdRef.current = activeFeatureId;
  const pendingFeaturesRef = useRef(pendingFeatures);
  pendingFeaturesRef.current = pendingFeatures;
  const modeRef = useRef(mode);
  modeRef.current = mode;

  // Flag to skip mode sync after undo/redo (drawControl is already restored)
  const skipModeSyncRef = useRef(false);
  // Flag to prevent recording history during undo/redo operations
  const isUndoRedoRef = useRef(false);

  // Helper: capture current state snapshot (Redux + MapboxDraw)
  const captureSnapshot = useCallback(() => {
    const drawFeatures = drawControl?.getAll() || { type: "FeatureCollection" as const, features: [] };
    return { drawFeatures };
  }, [drawControl]);

  // Helper: push snapshot before any action
  const pushHistory = useCallback(() => {
    if (isUndoRedoRef.current) return;
    dispatch(pushSnapshot(captureSnapshot()));
  }, [dispatch, captureSnapshot]);

  // Find the project layer's numeric ID (used as MapLibre layer ID in Layers.tsx)
  const editingProjectLayer = projectLayers?.find((l) => l.layer_id === activeLayerId);
  const editingProjectLayerIdRef = useRef(editingProjectLayer?.id);
  editingProjectLayerIdRef.current = editingProjectLayer?.id;

  // Build icon properties for custom_marker layers (used as MapboxDraw user properties)
  const iconProps = useMemo(() => {
    if (!editingProjectLayer?.properties?.["custom_marker"]) return null;
    const props = editingProjectLayer.properties as FeatureLayerPointProperties;
    const markerSize = props.marker_size ?? 100;
    // Resolve icon-image — may be a data-driven expression or a simple string
    const iconImage = getMapboxStyleMarker(editingProjectLayer as ProjectLayer);
    const iconImageName =
      typeof iconImage === "string" ? iconImage : `${editingProjectLayer.id}-${props.marker?.name}`;
    const iconSize = markerSize / 200;

    // The draw styles render the selection as a ring AROUND the icon. Its
    // radius must come from the icon's real rendered size — icon images have
    // arbitrary intrinsic dimensions, so a fixed formula based on _iconSize
    // alone leaves the ring hidden behind larger icons.
    let iconRadius: number | undefined;
    try {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const img = (mapRef?.current?.getMap() as any)?.getImage?.(iconImageName);
      const width = img?.data?.width;
      if (typeof width === "number" && width > 0) {
        const pixelRatio = img.pixelRatio ?? 1;
        const height = img.data.height ?? width;
        const cssSize = Math.max(width, height) / pixelRatio;
        iconRadius = Math.round((cssSize * iconSize) / 2 + 4);
      }
    } catch {
      /* image not registered (yet) — styles fall back to the size formula */
    }

    return {
      _iconImage: iconImageName,
      _iconSize: iconSize,
      _iconAnchor: props.marker_anchor || "center",
      _iconOpacity: props.filled ? (props.opacity ?? 1) : 1,
      _iconColor: "#000000",
      ...(iconRadius !== undefined ? { _iconRadius: iconRadius } : {}),
    };
  }, [editingProjectLayer, mapRef]);

  // Timestamp of last feature create — used to ignore the map click that follows a draw.create
  const lastCreateTimeRef = useRef(0);

  // Confirmation dialog state
  const [discardConfirmOpen, setDiscardConfirmOpen] = useState(false);
  const [stopConfirmOpen, setStopConfirmOpen] = useState(false);

  // Map geometry type to MapboxDraw mode
  const getDrawMode = useCallback(() => {
    switch (geometryType) {
      case "point":
        return "draw_point";
      case "line":
        return "draw_line_string";
      case "polygon":
        return "draw_polygon";
      default:
        return "draw_point";
    }
  }, [geometryType]);

  // Sync draw mode with Redux state
  useEffect(() => {
    if (!drawControl || !activeLayerId) return;

    // Skip after undo/redo — drawControl is already in the correct state
    if (skipModeSyncRef.current) {
      skipModeSyncRef.current = false;
      return;
    }

    // Always disable popups while editing
    dispatch(setIsMapGetInfoActive(false));
    dispatch(setPopupInfo(undefined));

    const currentPending = pendingFeaturesRef.current;
    const activeFeature = activeFeatureId ? currentPending[activeFeatureId] : null;
    if (mode === "draw") {
      // Deselect active feature before entering draw mode
      if (activeFeature?.drawFeatureId && activeFeatureId) {
        // Sync geometry before removing
        const drawFeat = drawControl.get(activeFeature.drawFeatureId);
        if (drawFeat?.geometry) {
          dispatch(updatePendingGeometry({ id: activeFeatureId, geometry: drawFeat.geometry }));
        }
        drawControl.delete(activeFeature.drawFeatureId);

        if (activeFeature.committed) {
          dispatch(setDrawFeatureId({ id: activeFeatureId, drawFeatureId: null }));
          dispatch(setActiveFeature(null));
        } else if (activeFeature.action === "update") {
          // Auto-commit existing feature if changed
          const geomChanged = JSON.stringify(activeFeature.geometry) !== JSON.stringify(activeFeature.originalGeometry);
          const filterInternal = (props: Record<string, unknown>) => {
            const f = { ...props }; delete f._fillColor; delete f._fillOpacity; return f;
          };
          const propsChanged = JSON.stringify(filterInternal(activeFeature.properties)) !== JSON.stringify(filterInternal(activeFeature.originalProperties || {}));
          if (geomChanged || propsChanged) {
            dispatch(commitFeature(activeFeatureId));
          } else {
            dispatch(removePendingFeature(activeFeatureId));
          }
        } else {
          dispatch(removePendingFeature(activeFeatureId));
        }
      }
      // Only activate MapboxDraw for geospatial layers
      if (geometryType) {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        drawControl.changeMode(getDrawMode() as any);
        dispatch(setMapCursor("crosshair"));
      }
    } else if (activeFeature?.drawFeatureId) {
      // Feature is being edited in MapboxDraw
      const drawId = activeFeature.drawFeatureId;
      if (drawControl.get(drawId)) {
        try {
          if (geometryType === "point") {
            // Points use simple_select for dragging (direct_select is for vertex editing)
            drawControl.changeMode(MapboxDraw.constants.modes.SIMPLE_SELECT, {
              featureIds: [drawId],
            });
          } else {
            drawControl.changeMode(MapboxDraw.constants.modes.DIRECT_SELECT, {
              featureId: drawId,
            });
          }
        } catch {
          // ignore
        }
      }
      dispatch(setMapCursor(undefined));
    } else {
      // Select mode — clean up any in-progress drawing and reset
      drawControl?.deleteAll();
      dispatch(setMapCursor(undefined));
    }
  }, [mode, activeLayerId, activeFeatureId, drawControl, dispatch, getDrawMode]);

  // Handle draw.create event — capture drawn geometry as a pending feature
  const handleFeatureCreate = useCallback(
    (e: { features: GeoJSON.Feature[] }) => {
      if (!activeLayerIdRef.current || !drawControl) return;

      // Snapshot before feature creation — use empty draw features since
      // the feature in MapboxDraw is the one being created (not a previous state)
      if (!isUndoRedoRef.current) {
        dispatch(pushSnapshot({
          drawFeatures: { type: "FeatureCollection", features: [] },
        }));
      }

      const drawnFeature = e.features[0];
      if (!drawnFeature?.geometry) return;
      const drawId = drawnFeature.id as string;

      lastCreateTimeRef.current = Date.now();

      // Set icon properties on the draw feature so MapboxDraw symbol styles pick them up
      if (iconProps) {
        for (const [key, value] of Object.entries(iconProps)) {
          drawControl.setFeatureProperty(drawId, key, value);
        }
      }

      // Attach geometry to the active pending feature (or create a new one)
      if (activeFeatureIdRef.current) {
        dispatch(
          updatePendingGeometry({
            id: activeFeatureIdRef.current,
            geometry: drawnFeature.geometry,
          })
        );
        dispatch(
          setDrawFeatureId({
            id: activeFeatureIdRef.current,
            drawFeatureId: drawId,
          })
        );
      } else {
        const featureId = crypto.randomUUID();
        dispatch(
          addPendingFeature({
            id: featureId,
            drawFeatureId: drawId,
            geometry: drawnFeature.geometry,
            properties: {},
            committed: false,
            action: "create",
          })
        );
      }

      // Switch to select so "Done" → "draw" is an actual state change
      dispatch(setMode("select"));
      dispatch(setMapCursor(undefined));

    },
    [drawControl, dispatch, pushHistory]
  );

  // Handle draw.update event — sync geometry changes when user edits vertices
  const handleFeatureUpdate = useCallback(
    (e: { features: GeoJSON.Feature[] }) => {
      if (!activeFeatureIdRef.current) return;
      const updatedFeature = e.features[0];
      if (!updatedFeature?.geometry) return;

      // Snapshot before the geometry update
      pushHistory();

      dispatch(
        updatePendingGeometry({
          id: activeFeatureIdRef.current,
          geometry: updatedFeature.geometry,
        })
      );
    },
    [dispatch, pushHistory]
  );

  // Deselect the currently active feature — sync geometry, remove from MapboxDraw
  const deselectActiveFeature = useCallback(() => {
    const activeId = activeFeatureIdRef.current;
    if (!activeId || !drawControl) return;

    const pending = featureEditor.pendingFeatures[activeId];
    if (!pending) return;

    // Sync latest geometry from MapboxDraw
    if (pending.drawFeatureId) {
      const drawFeat = drawControl.get(pending.drawFeatureId);
      if (drawFeat?.geometry) {
        dispatch(updatePendingGeometry({ id: activeId, geometry: drawFeat.geometry }));
      }
      drawControl.delete(pending.drawFeatureId);
    }

    if (pending.committed) {
      // Already committed via "Done" — move back to overlay
      dispatch(setDrawFeatureId({ id: activeId, drawFeatureId: null }));
      dispatch(setActiveFeature(null));
    } else if (pending.action === "update") {
      // Existing feature — auto-commit if changed, discard if not
      const geomChanged = JSON.stringify(pending.geometry) !== JSON.stringify(pending.originalGeometry);
      // Filter out internal style properties (_fillColor, _fillOpacity) for comparison
      const filterInternal = (props: Record<string, unknown>) => {
        const filtered = { ...props };
        delete filtered._fillColor;
        delete filtered._fillOpacity;
        return filtered;
      };
      const propsChanged = JSON.stringify(filterInternal(pending.properties)) !== JSON.stringify(filterInternal(pending.originalProperties || {}));
      if (geomChanged || propsChanged) {
        dispatch(commitFeature(activeId));
      } else {
        dispatch(removePendingFeature(activeId));
      }
    } else {
      // Uncommitted new feature — discard
      dispatch(removePendingFeature(activeId));
    }
  }, [drawControl, dispatch, featureEditor.pendingFeatures]);

  // Handle map click in select mode — select existing feature or deselect
  const handleMapClick = useCallback(
    async (e: MapLayerMouseEvent) => {
      if (!activeLayerIdRef.current || !drawControl) return;
      if (modeRef.current !== "select") return;
      // Skip if we just finished drawing — the click that completes a draw also fires as a map click
      if (Date.now() - lastCreateTimeRef.current < 200) return;



      const map = mapRef?.current?.getMap();
      if (!map) return;

      // Query rendered features at click point — check both tile layer and pending overlay
      const point = e.point;
      const projectLayerId = String(editingProjectLayerIdRef.current);
      const layerIds: string[] = [];
      // Add main layer if it exists on the map
      if (map.getLayer(projectLayerId)) layerIds.push(projectLayerId);
      if (map.getLayer(`stroke-${projectLayerId}`)) {
        layerIds.push(`stroke-${projectLayerId}`);
      }
      if (map.getLayer(`text-label-${projectLayerId}`)) {
        layerIds.push(`text-label-${projectLayerId}`);
      }
      // Also check pending features overlay layers
      const pendingLayerIds = ["pending-features-fill", "pending-features-line", "pending-features-circle", "pending-features-symbol"];
      for (const id of pendingLayerIds) {
        if (map.getLayer(id)) layerIds.push(id);
      }
      const features = map.queryRenderedFeatures(point, { layers: layerIds });
      const clickedFeature = features[0];

      // Click on empty area → deselect current feature
      if (!clickedFeature) {
        deselectActiveFeature();
        return;
      }

      // Get the feature ID — pending overlay features use _pendingId,
      // tile features use MVT feature.id (rowid+1). Fallback to properties.id for legacy PMTiles.
      const isPendingOverlay = clickedFeature.layer?.id?.startsWith("pending-features");
      const featureId = isPendingOverlay
        ? clickedFeature.properties?._pendingId
        : (clickedFeature.id ?? clickedFeature.properties?.id);
      if (featureId === undefined || featureId === null) return;

      // Capture rendered fill color from the tile feature for MapboxDraw styling
      let renderedFillColor: string | undefined;
      let renderedFillOpacity: number | undefined;
      if (!isPendingOverlay && clickedFeature.layer?.paint) {
        const paint = clickedFeature.layer.paint as Record<string, unknown>;
        if (paint["fill-color"]) renderedFillColor = String(paint["fill-color"]);
        if (paint["fill-opacity"] !== undefined) renderedFillOpacity = Number(paint["fill-opacity"]);
      }

      // If clicking the same feature that's already active, ignore
      if (activeFeatureIdRef.current === String(featureId)) return;

      // Snapshot before deselection + new selection
      pushHistory();

      // Deselect any currently active feature first
      deselectActiveFeature();

      // Check if already in pending features (committed overlay feature)
      const existingPending = Object.values(featureEditor.pendingFeatures).find(
        (f) => f.id === String(featureId)
      );
      if (existingPending) {
        // Re-add to MapboxDraw for geometry editing
        if (existingPending.geometry && !existingPending.drawFeatureId) {
          const drawFeature = {
            type: "Feature" as const,
            id: crypto.randomUUID(),
            geometry: existingPending.geometry,
            properties: { ...existingPending.properties, ...iconProps },
          };
          const drawIds = drawControl.add(drawFeature);
          if (drawIds[0]) {
            dispatch(setDrawFeatureId({ id: existingPending.id, drawFeatureId: drawIds[0] }));
            // Mark as uncommitted so it's editable again
                }
        }
        dispatch(setActiveFeature(existingPending.id));
        return;
      }

      // Fetch full feature from backend
      // Use MVT feature ID (rowid+1) when available, fall back to CQL filter on
      // the "id" property for legacy tiles that don't have MVT feature IDs.
      try {
        const hasMvtId = clickedFeature.id != null;
        let fullFeature: GeoJSON.Feature | null | undefined;
        if (hasMvtId) {
          fullFeature = await getFeature(activeLayerIdRef.current, String(featureId));
        } else {
          // Legacy tiles: fetch by CQL filter on the "id" property
          const fc = await getFeatures(activeLayerIdRef.current, {
            filter: { op: "=", args: [{ property: "id" }, featureId] },
            limit: 1,
          });
          fullFeature = fc.features[0] || null;
        }
        if (!fullFeature?.geometry) return;

        // Use the API-returned feature ID (rowid+1) as the canonical ID.
        // For legacy tiles, this converts from properties.id to the real rowid+1.
        const canonicalId = String(fullFeature.id ?? featureId);

        // Add to MapboxDraw for geometry editing — use a unique draw ID to avoid conflicts
        // Include _fillColor/_fillOpacity as properties so MapboxDraw styles can read them
        const drawFeature = {
          ...fullFeature,
          id: crypto.randomUUID(),
          properties: {
            ...fullFeature.properties,
            ...(renderedFillColor && { _fillColor: renderedFillColor }),
            ...(renderedFillOpacity !== undefined && { _fillOpacity: renderedFillOpacity }),
            ...iconProps,
          },
        };
        const drawIds = drawControl.add(drawFeature);
        const drawId = drawIds[0];

        dispatch(
          addPendingFeature({
            id: canonicalId,
            drawFeatureId: drawId || null,
            geometry: fullFeature.geometry,
            properties: {
              ...fullFeature.properties,
              ...(renderedFillColor && { _fillColor: renderedFillColor }),
              ...(renderedFillOpacity !== undefined && { _fillOpacity: renderedFillOpacity }),
            },
            committed: false,
            action: "update",
            originalGeometry: fullFeature.geometry,
            originalProperties: fullFeature.properties || {},
          })
        );
      } catch (error) {
        console.error("Failed to fetch feature:", error);
      }
    },
    [drawControl, dispatch, deselectActiveFeature, featureEditor.pendingFeatures, mapRef]
  );

  // Register/unregister draw event listeners + map click
  useEffect(() => {
    const map = mapRef?.current?.getMap();
    if (!map || !drawControl || !activeLayerId) return;

    map.on(MapboxDraw.constants.events.CREATE, handleFeatureCreate);
    map.on(MapboxDraw.constants.events.UPDATE, handleFeatureUpdate);
    map.on("click", handleMapClick);

    return () => {
      map.off(MapboxDraw.constants.events.CREATE, handleFeatureCreate);
      map.off(MapboxDraw.constants.events.UPDATE, handleFeatureUpdate);
      map.off("click", handleMapClick);
    };
  }, [mapRef, drawControl, activeLayerId, handleFeatureCreate, handleFeatureUpdate, handleMapClick]);

  // Clean up when editing stops
  useEffect(() => {
    if (!activeLayerId && drawControl) {
      try { drawControl.deleteAll(); } catch { /* map may be unmounted */ }
      try { drawControl.changeMode(MapboxDraw.constants.modes.SIMPLE_SELECT); } catch { /* */ }
      dispatch(setMapCursor(undefined));
      dispatch(setIsMapGetInfoActive(true));
    }
  }, [activeLayerId, drawControl, dispatch]);

  // --- Unified Undo/Redo ---
  const undoStack = useAppSelector((state) => state.featureEditor.undoStack);
  const redoStack = useAppSelector((state) => state.featureEditor.redoStack);
  const hasUndo = undoStack.length > 0 || (DrawHistory.active?.hasUndo ?? false);
  const hasRedo = redoStack.length > 0 || (DrawHistory.active?.hasRedo ?? false);

  const restoreDrawState = useCallback((snapshot: typeof undoStack[0]) => {
    if (!drawControl) return;

    const feature = snapshot.activeFeatureId ? snapshot.pendingFeatures[snapshot.activeFeatureId] : null;
    // Restore MapboxDraw features
    drawControl.deleteAll();
    if (snapshot.drawFeatures.features.length > 0) {
      drawControl.add(snapshot.drawFeatures);
    }

    // Restore the correct MapboxDraw interaction mode
    let directSelectId: string | null = null;

    if (feature?.drawFeatureId && drawControl.get(feature.drawFeatureId)) {
      directSelectId = feature.drawFeatureId;
    } else if (snapshot.drawFeatures.features.length > 0 && snapshot.activeFeatureId) {
      // Feature has no drawFeatureId in snapshot but draw features exist —
      // find the first draw feature and use it
      const firstDrawFeature = snapshot.drawFeatures.features[0];
      if (firstDrawFeature?.id && drawControl.get(firstDrawFeature.id as string)) {
        directSelectId = firstDrawFeature.id as string;
      }
    }

    if (directSelectId) {
      if (geometryType === "point") {
        drawControl.changeMode(MapboxDraw.constants.modes.SIMPLE_SELECT, {
          featureIds: [directSelectId],
        });
      } else {
        drawControl.changeMode(MapboxDraw.constants.modes.DIRECT_SELECT, {
          featureId: directSelectId,
        });
      }
      dispatch(setMapCursor(undefined));
    } else if (snapshot.mode === "draw") {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      drawControl.changeMode(getDrawMode() as any);
      dispatch(setMapCursor("crosshair"));
    } else {
      dispatch(setMapCursor(undefined));
    }
  }, [drawControl, getDrawMode]);

  const performUndo = useCallback(() => {
    if (undoStack.length === 0 || !drawControl) return;

    isUndoRedoRef.current = true;
    skipModeSyncRef.current = true;

    const snapshot = captureSnapshot();
    const previous = undoStack[undoStack.length - 1];
    dispatch(undo(snapshot));
    restoreDrawState(previous);

    // Clear flag after a tick to allow React to process state changes
    setTimeout(() => { isUndoRedoRef.current = false; }, 0);
  }, [undoStack, drawControl, captureSnapshot, dispatch, restoreDrawState]);

  const performRedo = useCallback(() => {
    if (redoStack.length === 0 || !drawControl) return;

    isUndoRedoRef.current = true;
    skipModeSyncRef.current = true;

    const snapshot = captureSnapshot();
    const next = redoStack[redoStack.length - 1];
    dispatch(redo(snapshot));
    restoreDrawState(next);

    setTimeout(() => { isUndoRedoRef.current = false; }, 0);
  }, [redoStack, drawControl, captureSnapshot, dispatch, restoreDrawState]);

  const handleUndo = useCallback(() => {
    // Tier 1: vertex undo during active drawing
    if (modeRef.current === "draw" && DrawHistory.active?.hasUndo) {
      DrawHistory.active.undoVertex();
      return;
    }
    // Tier 2: snapshot undo
    performUndo();
  }, [performUndo]);

  const handleRedo = useCallback(() => {
    // Tier 1: vertex redo during active drawing
    if (modeRef.current === "draw" && DrawHistory.active?.hasRedo) {
      DrawHistory.active.redoVertex();
      return;
    }
    // Tier 2: snapshot redo
    performRedo();
  }, [performRedo]);

  // Keyboard shortcuts for undo/redo
  useEffect(() => {
    if (!activeLayerId) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      const isCtrlOrCmd = e.ctrlKey || e.metaKey;
      if (!isCtrlOrCmd) return;

      const target = e.target as HTMLElement;
      if (target.tagName === "INPUT" || target.tagName === "TEXTAREA" || target.isContentEditable) {
        return;
      }

      const isUndoKey = e.key === "z" && !e.shiftKey;
      const isRedoKey = e.key === "y" || (e.key === "z" && e.shiftKey);
      if (!isUndoKey && !isRedoKey) return;

      e.preventDefault();

      if (isUndoKey) {
        handleUndo();
      } else {
        handleRedo();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [activeLayerId, handleUndo, handleRedo]);

  // --- Save handler ---
  const handleSave = useCallback(async () => {
    if (!activeLayerId || isSaving) return;

    const committed = Object.values(pendingFeatures).filter((f) => f.committed);
    if (committed.length === 0) return;

    const newFeatures = committed.filter((f) => f.action === "create");
    const updatedFeatures = committed.filter((f) => f.action === "update");
    const deletedFeatures = committed.filter((f) => f.action === "delete");

    const cleanProps = (props: Record<string, unknown>) => {
      const clean: Record<string, unknown> = {};
      for (const [key, value] of Object.entries(props)) {
        // Skip internal properties used for MapboxDraw styling
        if (key.startsWith("_")) continue;
        clean[key] = value === undefined || value === "" ? null : value;
      }
      return clean;
    };

    dispatch(setIsSaving(true));
    try {
      // Create new features in bulk
      if (newFeatures.length > 0) {
        await createFeaturesBulk(
          activeLayerId,
          newFeatures.map((f) => ({
            geometry: f.geometry as unknown as Record<string, unknown>,
            properties: cleanProps(f.properties),
          }))
        );
      }

      // Update existing features one by one
      for (const f of updatedFeatures) {
        await replaceFeature(activeLayerId, f.id, {
          geometry: f.geometry as unknown as Record<string, unknown>,
          properties: cleanProps(f.properties),
        });
      }

      // Delete features
      for (const f of deletedFeatures) {
        await deleteFeature(activeLayerId, f.id);
      }

      // Clean up MapboxDraw before clearing Redux state
      drawControl?.deleteAll();
      dispatch(clearPendingFeatures());
      toast.success(t("features_saved"));
      // Refresh tiles by optimistically updating updated_at — the tile URL's
      // v= cache-buster derives from it, so bumping it makes MapLibre refetch.
      const bumpLayerUpdatedAt = () =>
        mutateProjectLayers(
          (current) =>
            current?.map((l) =>
              l.layer_id === activeLayerId ? { ...l, updated_at: new Date().toISOString() } : l
            ),
          { revalidate: false },
        );
      bumpLayerUpdatedAt();
      // Revalidate any SWR cache entry for this layer's collection items
      // (data table feature pages, queryables) so newly written values
      // — including recomputed columns like area/perimeter — show up.
      const itemsPrefix = `${COLLECTIONS_API_BASE_URL}/${activeLayerId}`;
      // Single-argument mutate = revalidate while KEEPING the cached data on
      // screen. Passing (key, undefined, {revalidate: true}) is NOT the same:
      // SWR then treats undefined as new data and clears the cache, which
      // blanks the data table (spinner, lost scroll) on every save.
      const revalidateCollection = () =>
        globalMutate((key) => {
          if (typeof key === "string") return key.startsWith(itemsPrefix);
          if (Array.isArray(key) && typeof key[0] === "string") {
            return key[0].startsWith(itemsPrefix);
          }
          return false;
        });
      revalidateCollection();
      // The read pool serves a pinned DuckLake snapshot whose post-write
      // refresh runs on a background thread (~1s) — the immediate revalidate
      // and tile refetch can race it and get the pre-write snapshot, so do
      // both once more after the pin has had time to advance. Without the
      // second updated_at bump the stale tiles would stick: MapLibre only
      // refetches when the tile URL changes.
      setTimeout(() => {
        revalidateCollection();
        bumpLayerUpdatedAt();
      }, 2500);
    } catch (error) {
      console.error("Failed to save features:", error);
      toast.error(t("error_saving_features"));
    } finally {
      dispatch(setIsSaving(false));
    }
  }, [activeLayerId, isSaving, pendingFeatures, dispatch, t]);

  // --- Discard handler ---
  const handleDiscardRequest = useCallback(() => {
    setDiscardConfirmOpen(true);
  }, []);

  const handleDiscardConfirm = useCallback(() => {
    dispatch(clearPendingFeatures());
    setDiscardConfirmOpen(false);
  }, [dispatch]);

  const handleDiscardCancel = useCallback(() => {
    setDiscardConfirmOpen(false);
  }, []);

  // --- Stop editing handler ---
  const handleStopEditingRequest = useCallback(() => {
    const pendingCount = Object.keys(pendingFeatures).length;
    if (pendingCount > 0) {
      setStopConfirmOpen(true);
    } else {
      dispatch(stopEditing());
    }
  }, [pendingFeatures, dispatch]);

  const handleStopConfirm = useCallback(() => {
    dispatch(stopEditing());
    setStopConfirmOpen(false);
  }, [dispatch]);

  const handleStopCancel = useCallback(() => {
    setStopConfirmOpen(false);
  }, []);

  return {
    handleSave,
    handleDiscardRequest,
    handleDiscardConfirm,
    handleDiscardCancel,
    discardConfirmOpen,
    handleStopEditingRequest,
    handleStopConfirm,
    handleStopCancel,
    stopConfirmOpen,
    handleUndo,
    handleRedo,
    hasUndo,
    hasRedo,
  };
}
