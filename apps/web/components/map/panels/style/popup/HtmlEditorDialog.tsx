import {
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Stack,
  Typography,
  useTheme,
} from "@mui/material";
import { alpha } from "@mui/material/styles";
import dynamic from "next/dynamic";
import { type ReactNode, useState } from "react";
import { useTranslation } from "react-i18next";

import type { PopupProperties } from "@/lib/validations/layer";

import useLayerFields from "@/hooks/map/CommonHooks";

import type { LayerField } from "@/components/map/popover/formatFeatureProperties";
import { PopupContent, PopupHeader } from "@/components/map/popover/MapFeaturePopover";
import { PopupHtmlStyles } from "@/components/map/popover/popupStyles";
import { useSampleFeature } from "@/components/map/popover/sampleFeature";

const HtmlModeEditor = dynamic(() => import("./HtmlModeEditor").then((m) => m.HtmlModeEditor), { ssr: false });
import { PopupAppearanceSettings } from "./PopupAppearanceSettings";

interface Props {
  open: boolean;
  layerId: string;
  layerName: string;
  layerIcon?: ReactNode;
  popup: PopupProperties;
  onChange: (patch: Partial<PopupProperties>) => void;
  onClose: () => void;
}

export function HtmlEditorDialog({
  open,
  layerId,
  layerName,
  layerIcon,
  popup,
  onChange,
  onClose,
}: Props) {
  const { t } = useTranslation("common");
  const theme = useTheme();
  const { layerFields } = useLayerFields(layerId);
  const { feature } = useSampleFeature(layerId, open);

  // Local draft so Cancel discards. Seeded from the live popup each open.
  const [draftHtml, setDraftHtml] = useState(popup.html);

  const previewPopup: PopupProperties = { ...popup, html: draftHtml };

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="lg"
      fullWidth
      PaperProps={{ sx: { height: "82vh", borderRadius: 2 } }}>
      <DialogTitle
        sx={{
          px: 4,
          pt: 3,
          pb: 2,
          fontSize: 18,
          fontWeight: 700,
          borderBottom: `1px solid ${theme.palette.divider}`,
        }}>
        {t("popup_html_editor_title")}
      </DialogTitle>

      {/* overflow hidden so the dialog itself never scrolls — only the
          CodeMirror editor scrolls internally (preview + settings panes fit). */}
      <DialogContent sx={{ p: 0, overflow: "hidden", display: "flex" }}>
        <Stack direction="row" sx={{ height: "100%", width: "100%" }}>
          {/* Left — editor (the only scrollable region) */}
          <Box
            sx={{
              width: "38%",
              borderRight: `1px solid ${theme.palette.divider}`,
              p: 3,
              minHeight: 0,
              display: "flex",
              flexDirection: "column",
              overflow: "hidden",
            }}>
            <HtmlModeEditor
              value={draftHtml}
              onChange={setDraftHtml}
              fields={layerFields as LayerField[]}
            />
          </Box>

          {/* Center — preview canvas */}
          <Box
            sx={{
              flex: 1,
              minWidth: 0,
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              gap: 3,
              px: 4,
              py: 3,
              overflow: "hidden",
              // Subtle neutral canvas so the white popup card reads as a
              // floating element, the way it does over the map.
              bgcolor: (th) =>
                th.palette.mode === "light"
                  ? th.palette.grey[100]
                  : alpha(th.palette.common.white, 0.04),
            }}>
            {/* Desktop/Mobile preview toggle hidden until a real mobile popup
                render target exists (mobile bottom sheet is a deferred phase).
                Preview is pinned to the desktop width. */}
            <Box
              className="goat-feature-popup"
              sx={{
                width: popup.width ?? 360,
                // Cap to the preview pane so a tall popup scrolls inside its
                // own card (via PopupContent) instead of clipping.
                maxHeight: popup.max_height ? `${popup.max_height}px` : "100%",
                display: "flex",
                flexDirection: "column",
                minHeight: 0,
                bgcolor: "background.paper",
                borderRadius: 2.5,
                boxShadow: theme.shadows[6],
                overflow: "hidden",
              }}>
              <PopupHtmlStyles />
              {/* Render the same header chrome as the real popup so the
                  preview reflects the Header setting (standard/compact/none). */}
              {popup.header !== "none" && (
                <PopupHeader
                  layerName={layerName}
                  layerIcon={layerIcon}
                  onClose={() => {}}
                  compact={popup.header === "compact"}
                />
              )}
              {feature ? (
                <PopupContent
                  layerId={layerId}
                  popup={previewPopup}
                  properties={feature.properties}
                />
              ) : (
                <Typography
                  variant="caption"
                  sx={{ p: 2, display: "block" }}
                  color="text.secondary">
                  {t("loading")}
                </Typography>
              )}
            </Box>
          </Box>

          {/* Right — settings */}
          <Box
            sx={{
              width: "26%",
              borderLeft: `1px solid ${theme.palette.divider}`,
              px: 3,
              py: 3,
              overflow: "hidden",
            }}>
            <PopupAppearanceSettings popup={popup} onChange={onChange} />
          </Box>
        </Stack>
      </DialogContent>

      <DialogActions
        sx={{
          // Scope under the root class: MUI's default `.MuiDialogActions-root
          // { padding: 8px }` otherwise wins on specificity and our padding
          // never applies (same workaround as EditFields.tsx).
          "&.MuiDialogActions-root": {
            px: 4,
            py: 3,
            borderTop: `1px solid ${theme.palette.divider}`,
          },
          justifyContent: "flex-end",
          gap: 1.5,
        }}>
        <Button onClick={onClose} variant="text">
          <Typography variant="body2" fontWeight="bold">
            {t("cancel")}
          </Typography>
        </Button>
        <Button
          variant="contained"
          color="primary"
          onClick={() => {
            onChange({ html: draftHtml });
            onClose();
          }}>
          <Typography variant="body2" fontWeight="bold" color="inherit">
            {t("save")}
          </Typography>
        </Button>
      </DialogActions>
    </Dialog>
  );
}
