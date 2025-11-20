import { useCallback, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";

import { ICON_NAME } from "@p4b/ui/components/Icon";

import type { Layer } from "@/lib/validations/layer";
import type { Project } from "@/lib/validations/project";

import { ContentActions } from "@/types/common";

import type { PopperMenuItem } from "@/components/common/PopperMenu";

export const useContentMoreMenu = () => {
  const { t } = useTranslation("common");
  const getMoreMenuOptions = function (contentType: "project" | "layer", item: Project | Layer) {
    if (contentType === "layer") {
      const layerItem = item as Layer;
      const layerMoreMenuOptions: PopperMenuItem[] = [
        {
          id: ContentActions.EDIT_METADATA,
          label: t("edit_metadata"),
          icon: ICON_NAME.EDIT,
        },
        {
          id: ContentActions.MOVE_TO_FOLDER,
          label: t("move_to_folder"),
          icon: ICON_NAME.FOLDER,
        },
        ...(layerItem?.type === "feature" || layerItem?.type === "table"
          ? [
              {
                id: ContentActions.DOWNLOAD,
                label: t("download"),
                icon: ICON_NAME.DOWNLOAD,
              },
              {
                id: ContentActions.UPDATE,
                label: t("update"),
                icon: ICON_NAME.REFRESH,
              },
            ]
          : []),
        // Include SHARE only if NEXT_PUBLIC_ACCOUNTS_API_URL is set
        ...(process.env.NEXT_PUBLIC_ACCOUNTS_API_URL
          ? [
              {
                id: ContentActions.SHARE,
                label: t("share"),
                icon: ICON_NAME.SHARE,
              },
            ]
          : []),
        {
          id: ContentActions.DELETE,
          label: t("delete"),
          icon: ICON_NAME.TRASH,
          color: "error.main",
        },
      ];
      return layerMoreMenuOptions;
    }

    if (contentType === "project") {
      const projectMoreMenuOptions: PopperMenuItem[] = [
        {
          id: ContentActions.EDIT_METADATA,
          label: t("edit_metadata"),
          icon: ICON_NAME.EDIT,
        },
        {
          id: ContentActions.MOVE_TO_FOLDER,
          label: t("move_to_folder"),
          icon: ICON_NAME.FOLDER,
        },
        {
          id: ContentActions.SHARE,
          label: t("share"),
          icon: ICON_NAME.SHARE,
        },
        {
          id: ContentActions.DELETE,
          label: t("delete"),
          icon: ICON_NAME.TRASH,
          color: "error.main",
        },
      ];
      return projectMoreMenuOptions;
    }
    return [];
  };

  const [activeContent, setActiveContent] = useState<Project | Layer>();
  const [moreMenuState, setMoreMenuState] = useState<PopperMenuItem>();

  const closeMoreMenu = () => {
    setActiveContent(undefined);
    setMoreMenuState(undefined);
  };

  const openMoreMenu = (menuItem: PopperMenuItem, contentItem: Project | Layer) => {
    setActiveContent(contentItem);
    setMoreMenuState(menuItem);
  };

  return {
    getMoreMenuOptions,
    activeContent,
    moreMenuState,
    closeMoreMenu,
    openMoreMenu,
  };
};

export const useFileUpload = () => {
  const [fileUploadError, setFileUploadError] = useState<string | undefined>(undefined);
  const [fileValue, setFileValue] = useState<File | undefined>(undefined);
  const [datasetType, setDatasetType] = useState<string | undefined>(undefined);

  const acceptedFileTypes = useMemo(() => {
    return [".gpkg", ".geojson", ".zip", ".kml", ".csv", ".xlsx"];
  }, []);

  const handleChange = useCallback(
    (file: File) => {
      setFileUploadError(undefined);
      setFileValue(undefined);
      if (file && file.name) {
        const isAcceptedType = acceptedFileTypes.some((type) => file.name.endsWith(type));
        if (!isAcceptedType) {
          setFileUploadError("Invalid file type. Please select a file of type");
          return;
        }

        // Autodetect dataset type
        const isFeatureLayer =
          file.name.endsWith(".gpkg") ||
          file.name.endsWith(".geojson") ||
          file.name.endsWith(".shp") ||
          file.name.endsWith(".kml");
        const isTable = file.name.endsWith(".csv") || file.name.endsWith(".xlsx");
        if (isFeatureLayer) {
          setDatasetType("feature_layer");
        } else if (isTable) {
          setDatasetType("table");
        }
        setFileValue(file);
      }
    },
    [acceptedFileTypes]
  );

  return {
    acceptedFileTypes,
    fileUploadError,
    setFileUploadError,
    fileValue,
    setFileValue,
    datasetType,
    setDatasetType,
    handleChange,
  };
};
