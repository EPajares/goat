import { useCallback, useState } from "react";

import { startEditing } from "@/lib/store/featureEditor/slice";
import { setDataPanelLayerId } from "@/lib/store/map/slice";

import { useAppDispatch, useAppSelector } from "@/hooks/store/ContextHooks";

interface StartEditingPayload {
  layerId: string;
  geometryType: "point" | "line" | "polygon" | null;
  /** layer_project id — when the data panel is open, it follows the edit
   * session to this layer (otherwise the panel guard would end the session
   * immediately for targeting a different layer than the table). */
  projectLayerId?: number;
}

/**
 * Guards `startEditing` dispatches: the reducer resets the whole edit
 * session (including pending features), so switching the edit target while
 * unsaved edits exist must be confirmed instead of silently discarding
 * them. Re-requesting the layer that is already being edited is a no-op.
 *
 * Render a ConfirmModal with the returned state:
 *   const guard = useStartEditingGuard();
 *   <ConfirmModal open={guard.confirmOpen} onConfirm={guard.confirm} onClose={guard.cancel} ... />
 */
export const useStartEditingGuard = () => {
  const dispatch = useAppDispatch();
  const activeLayerId = useAppSelector((state) => state.featureEditor.activeLayerId);
  const hasPendingEdits = useAppSelector(
    (state) => Object.keys(state.featureEditor.pendingFeatures).length > 0
  );
  const isDataPanelOpen = useAppSelector((state) => state.map.isDataPanelOpen);
  const [pendingRequest, setPendingRequest] = useState<StartEditingPayload | null>(null);

  const beginEditing = useCallback(
    (payload: StartEditingPayload) => {
      dispatch(startEditing({ layerId: payload.layerId, geometryType: payload.geometryType }));
      // Keep the open data table in lockstep with the edit session
      if (isDataPanelOpen && payload.projectLayerId !== undefined) {
        dispatch(setDataPanelLayerId(payload.projectLayerId));
      }
    },
    [dispatch, isDataPanelOpen]
  );

  const requestStartEditing = useCallback(
    (payload: StartEditingPayload) => {
      // Already editing this layer — keep the session (and its edits) as-is
      if (activeLayerId === payload.layerId) return;
      if (activeLayerId && hasPendingEdits) {
        setPendingRequest(payload);
        return;
      }
      beginEditing(payload);
    },
    [activeLayerId, hasPendingEdits, beginEditing]
  );

  const confirm = useCallback(() => {
    if (pendingRequest) beginEditing(pendingRequest);
    setPendingRequest(null);
  }, [pendingRequest, beginEditing]);

  const cancel = useCallback(() => setPendingRequest(null), []);

  return { requestStartEditing, confirmOpen: !!pendingRequest, confirm, cancel };
};

export default useStartEditingGuard;
