import { Box, CircularProgress, Fab, Stack, Tooltip } from "@mui/material";
import { useRef, useState } from "react";
import { toast } from "react-toastify";

import { ICON_NAME, Icon } from "@p4b/ui/components/Icon";

import { useTranslation } from "@/i18n/client";

import { uploadAsset } from "@/lib/api/assets";
import { ASSETS_MAX_FILE_SIZE_MB, assetTypeEnum } from "@/lib/validations/assets";
import type { ImageElementSchema } from "@/lib/validations/widget";

const PLACEHOLDER_URL = "https://assets.plan4better.de/img/image-placeholder.webp";
const IMAGE_NOT_FOUND_PLACEHOLDER = "https://assets.plan4better.de/img/image-not-found-placeholder.webp";

// Base image component
const ImageElementBase = ({ config }: { config: ImageElementSchema }) => (
  <img
    style={{ width: "100%", height: "auto", display: "block" }}
    src={config.setup.url || PLACEHOLDER_URL}
    alt={config.setup.alt}
    onError={(e) => {
      const target = e.target as HTMLImageElement;
      target.src = IMAGE_NOT_FOUND_PLACEHOLDER;
    }}
  />
);

// Action buttons (UI only)
const ImageElementActionButtons = ({
  onUpload,
  onDelete,
  showDelete = true,
}: {
  onUpload: (file: File) => void;
  onDelete?: () => void;
  showDelete?: boolean;
}) => {
  const { t } = useTranslation("common");
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleUploadClick = () => fileInputRef.current?.click();

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      if (file.size > ASSETS_MAX_FILE_SIZE_MB * 1024 * 1024) {
        toast.error(`${t(" maximum_image_size_is")} ${ASSETS_MAX_FILE_SIZE_MB}MB`);
        e.target.value = ""; // reset input
        return;
      }
      onUpload(file);
      e.target.value = ""; // reset input for next upload
    }
  };

  return (
    <>
      <input
        type="file"
        accept="image/*"
        style={{ display: "none" }}
        ref={fileInputRef}
        onChange={handleFileChange}
      />
      <Stack direction="row" spacing={1}>
        <Tooltip title={t("upload_image")} arrow placement="top">
          <span>
            <Fab size="small" color="primary" onClick={handleUploadClick}>
              <Icon iconName={ICON_NAME.UPLOAD} htmlColor="inherit" style={{ fontSize: 15 }} />
            </Fab>
          </span>
        </Tooltip>
        {showDelete && onDelete && (
          <Tooltip title={t("remove_image")} arrow placement="top">
            <span>
              <Fab size="small" color="error" onClick={onDelete}>
                <Icon iconName={ICON_NAME.TRASH} htmlColor="inherit" style={{ fontSize: 15 }} />
              </Fab>
            </span>
          </Tooltip>
        )}
      </Stack>
    </>
  );
};

// Main widget
const ImageElementWidget = ({
  config,
  viewOnly,
  onWidgetUpdate,
}: {
  config: ImageElementSchema;
  viewOnly?: boolean;
  onWidgetUpdate?: (newConfig: ImageElementSchema) => void;
}) => {
  const [loading, setLoading] = useState(false);
  const { t } = useTranslation("common");

  if (viewOnly) {
    return (
      <Box
        sx={{
          height: "fit-content",
          maxHeight: "fit-content",
          width: "100%",
          ...(config.options?.has_padding && { p: 2 }),
        }}>
        <ImageElementBase config={config} />
      </Box>
    );
  }

  const showDelete = !!config.setup.url;

  const onUploadImage = async (file: File) => {
    setLoading(true);
    try {
      const uploaded = await uploadAsset(file, assetTypeEnum.Enum.image);
      onWidgetUpdate?.({ ...config, setup: { ...config.setup, url: uploaded.url } });
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
    } catch (err: any) {
      toast.error(t("image_upload_failed"));
      console.error("Upload failed:", err.message || err);
    } finally {
      setLoading(false);
    }
  };

  const onDeleteImage = () => {
    onWidgetUpdate?.({ ...config, setup: { ...config.setup, url: "" } });
  };

  return (
    <Box
      sx={{
        position: "relative",
        width: "100%",
        overflow: "hidden",
        borderRadius: 0,
        cursor: "pointer",
        "&:hover .overlay": { opacity: 1 },
        "&:hover .action-buttons": {
          opacity: 1,
          transform: "translateY(0)",
        },
        ...(config.options?.has_padding && { p: 2 }),
      }}>
      {/* Overlay */}
      <Box
        className="overlay"
        sx={{
          position: "absolute",
          inset: 0,
          backgroundColor: "rgba(0, 0, 0, 0.25)",
          opacity: loading ? 1 : 0,
          transition: "opacity 0.3s ease",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}>
        {loading && <CircularProgress size={40} sx={{ color: "white" }} />}
      </Box>

      {/* Action buttons (hidden when loading) */}
      {!loading && (
        <Box
          className="action-buttons"
          sx={{
            position: "absolute",
            top: 8,
            left: 8,
            opacity: 0,
            transform: "translateY(-10px)",
            transition: "all 0.3s ease",
          }}>
          <ImageElementActionButtons
            onUpload={onUploadImage}
            onDelete={onDeleteImage}
            showDelete={showDelete}
          />
        </Box>
      )}

      {/* Image */}
      <ImageElementBase config={config} />
    </Box>
  );
};

export default ImageElementWidget;
