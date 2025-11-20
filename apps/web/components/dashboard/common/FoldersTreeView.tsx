import {
  Collapse,
  IconButton,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Tooltip,
  Typography,
  useTheme,
} from "@mui/material";
import { useCallback, useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";

import { ICON_NAME, Icon } from "@p4b/ui/components/Icon";

import { useFolders } from "@/lib/api/folders";
import { useTeams } from "@/lib/api/teams";
import { useOrganization } from "@/lib/api/users";
import type { GetDatasetSchema } from "@/lib/validations/layer";
import type { GetProjectsQueryParams } from "@/lib/validations/project";

import type { PopperMenuItem } from "@/components/common/PopperMenu";
import MoreMenu from "@/components/common/PopperMenu";
import type { SelectedFolderForEdit } from "@/components/modals/Folder";
import FolderModal from "@/components/modals/Folder";

type EditModal = {
  type: "create" | "update" | "delete";
  selectedFolder?: SelectedFolderForEdit;
  open: boolean;
};

export type SelectedFolder = {
  type: "folder" | "team" | "organization";
  id: string;
  name: string;
};

function getIconName(type: string, id: string): ICON_NAME {
  if (type === "team") {
    return ICON_NAME.USERS;
  } else if (type === "organization") {
    return ICON_NAME.ORGANIZATION;
  } else if (type === "folder" && id === "0") {
    return ICON_NAME.HOUSE;
  } else {
    return ICON_NAME.FOLDER;
  }
}

interface FoldersTreeViewProps {
  setQueryParams: (
    params: GetDatasetSchema | GetProjectsQueryParams,
    teamId: string | undefined,
    organizationId: string | undefined
  ) => void;
  queryParams: GetDatasetSchema | GetProjectsQueryParams;
  enableActions?: boolean;
  hideMyContent?: boolean;
}

export default function FoldersTreeView(props: FoldersTreeViewProps) {
  const { setQueryParams, queryParams, hideMyContent, enableActions = true } = props;
  const [open, setOpen] = useState<boolean[]>([true, true, true]);
  const { organization } = useOrganization();
  const { teams: teamsData } = useTeams();
  const { t } = useTranslation("common");

  const [editModal, setEditModal] = useState<EditModal>();
  const { folders } = useFolders({});
  const homeFolder = useMemo(() => {
    const homeFolder = folders?.find((folder) => folder.name === "home");
    if (homeFolder) {
      return {
        type: "folder",
        id: homeFolder.id,
        name: homeFolder.name,
      } as SelectedFolder;
    } else {
      return undefined;
    }
  }, [folders]);

  const organizationFolder = useMemo(() => {
    if (organization) {
      return {
        type: "organization",
        id: organization.id,
        name: organization.name,
      } as SelectedFolder;
    } else {
      return undefined;
    }
  }, [organization]);

  const organizations = useMemo(() => {
    if (organization) {
      return [
        {
          id: organization.id,
          avatar: organization.avatar,
          name: organization.name,
        },
      ];
    } else {
      return [];
    }
  }, [organization]);

  const teams = useMemo(() => {
    return teamsData?.map((team) => ({
      id: team.id,
      avatar: team.avatar,
      name: team.name,
    }));
  }, [teamsData]);

  const theme = useTheme();
  const hideTeamsAndOrgs = !process.env.NEXT_PUBLIC_ACCOUNTS_API_URL;
  const folderTypes = hideTeamsAndOrgs ? ["folder"] : ["folder", "team", "organization"];

  const folderTypeTitles = hideTeamsAndOrgs
    ? [t("my_content")]
    : [t("my_content"), t("teams"), t("organizations")];

  const moreMenuItems: PopperMenuItem[] = [
    {
      id: "rename",
      label: t("rename"),
      icon: ICON_NAME.EDIT,
    },
    {
      id: "delete",
      label: t("delete"),
      icon: ICON_NAME.TRASH,
      color: theme.palette.error.main,
    },
  ];
  const [selectedFolder, setSelectedFolder] = useState<SelectedFolder | undefined>(undefined);

  const handleListItemClick = useCallback(
    (_event: React.MouseEvent<HTMLDivElement, MouseEvent>, item: SelectedFolder) => {
      setSelectedFolder(item);
      if (item.id !== "0" && item.type === "folder") {
        setQueryParams(
          {
            ...queryParams,
            folder_id: item.id,
          },
          undefined,
          undefined
        );
      } else if (item.type === "team") {
        const { folder_id: _, ...rest } = queryParams;
        setQueryParams(rest, item.id, undefined);
      } else if (item.type === "organization") {
        const { folder_id: _, ...rest } = queryParams;
        setQueryParams(rest, undefined, item.id);
      }
    },
    [queryParams, setQueryParams]
  );

  useEffect(() => {
    if (!selectedFolder && folders && homeFolder && !hideMyContent) {
      handleListItemClick({} as React.MouseEvent<HTMLDivElement, MouseEvent>, homeFolder);
    }
  }, [folders, handleListItemClick, homeFolder, selectedFolder, hideMyContent]);

  useEffect(() => {
    if (!selectedFolder && organizationFolder && hideMyContent) {
      handleListItemClick({} as React.MouseEvent<HTMLDivElement, MouseEvent>, organizationFolder);
    }
  }, [organizationFolder, selectedFolder, handleListItemClick, hideMyContent]);

  return (
    <>
      {enableActions && (
        <FolderModal
          type={editModal?.type || "create"}
          open={editModal?.open || false}
          onClose={() => {
            setEditModal(undefined);
          }}
          onEdit={() => {
            if (editModal?.type === "delete") {
              if (homeFolder) {
                setSelectedFolder(homeFolder);
              }
            }

            setEditModal(undefined);
          }}
          existingFolderNames={folders?.map((folder) => folder.name)}
          selectedFolder={editModal?.selectedFolder}
        />
      )}

      <List sx={{ width: "100%", maxWidth: 360 }} component="nav" aria-labelledby="content-tree-view">
        {(hideTeamsAndOrgs ? [folders ?? []] : [folders ?? [], teams ?? [], organizations ?? []])
          .map((folder, typeIndex) => {
            // Filter out "My Content" section if hideMyContent is true
            if (hideMyContent && folderTypes[typeIndex] === "folder") {
              return null;
            }

            return (
              <div key={typeIndex}>
                <ListItemButton
                  disableRipple
                  selected={selectedFolder?.type === folderTypes[typeIndex] && !open[typeIndex]}
                  onClick={() => {
                    setOpen((prevOpen) => {
                      const newOpen = [...prevOpen];
                      newOpen[typeIndex] = !prevOpen[typeIndex];
                      return newOpen;
                    });
                  }}>
                  {open[typeIndex] ? (
                    <Icon iconName={ICON_NAME.CHEVRON_DOWN} style={{ fontSize: "15px" }} />
                  ) : (
                    <Icon iconName={ICON_NAME.CHEVRON_RIGHT} style={{ fontSize: "15px" }} />
                  )}

                  <ListItemIcon sx={{ ml: 3, minWidth: "40px" }}>
                    <Icon
                      iconName={getIconName(folderTypes[typeIndex], selectedFolder?.id ?? "")}
                      fontSize="small"
                      htmlColor={
                        selectedFolder?.type === folderTypes[typeIndex] && !open[typeIndex]
                          ? theme.palette.primary.main
                          : "inherit"
                      }
                    />
                  </ListItemIcon>
                  <ListItemText
                    sx={{
                      "& .MuiTypography-root": {
                        ...(selectedFolder?.type === folderTypes[typeIndex] &&
                          !open[typeIndex] && {
                            color: theme.palette.primary.main,
                            fontWeight: 700,
                          }),
                      },
                    }}
                    primary={
                      <Typography variant="body1">
                        {selectedFolder?.type === folderTypes[typeIndex] && !open[typeIndex]
                          ? `${folderTypeTitles[typeIndex]} / ${selectedFolder?.name}`
                          : `${folderTypeTitles[typeIndex]}`}
                      </Typography>
                    }
                  />
                  {typeIndex === 0 && enableActions && (
                    <Tooltip title={t("new_folder")} placement="top">
                      <IconButton
                        size="small"
                        onClick={(event) => {
                          setEditModal({
                            type: "create",
                            open: true,
                          });
                          event.stopPropagation();
                        }}>
                        <Icon iconName={ICON_NAME.FOLDER_NEW} fontSize="small" htmlColor="inherit" />
                      </IconButton>
                    </Tooltip>
                  )}
                </ListItemButton>
                <Collapse in={open[typeIndex]} timeout="auto" unmountOnExit>
                  <List component="div" disablePadding>
                    {folder.map((item) => (
                      <ListItemButton
                        disableRipple
                        selected={selectedFolder?.id === item.id}
                        onClick={(event) =>
                          handleListItemClick(event, {
                            type: folderTypes[typeIndex] as "folder" | "team" | "organization",
                            id: item.id,
                            name: item.name,
                          })
                        }
                        sx={{
                          pl: 10,
                          ...(selectedFolder?.id === item.id && {
                            color: theme.palette.primary.main,
                          }),
                        }}
                        key={item.id}>
                        <ListItemIcon sx={{ ml: 4, minWidth: "40px" }}>
                          <Icon
                            iconName={getIconName(folderTypes[typeIndex], item.id)}
                            fontSize="small"
                            htmlColor={
                              selectedFolder?.id === item.id ? theme.palette.primary.main : "inherit"
                            }
                          />
                        </ListItemIcon>
                        <ListItemText
                          primary={item.name}
                          sx={{
                            "& .MuiTypography-root": {
                              ...(selectedFolder?.id === item.id && {
                                color: theme.palette.primary.main,
                                fontWeight: 700,
                              }),
                            },
                          }}
                        />
                        {folderTypes[typeIndex] === "folder" && item?.name !== "home" && enableActions && (
                          <MoreMenu
                            menuItems={moreMenuItems}
                            menuButton={
                              <IconButton size="medium">
                                <Icon iconName={ICON_NAME.MORE_VERT} fontSize="small" />
                              </IconButton>
                            }
                            onSelect={(menuItem: PopperMenuItem) => {
                              setEditModal({
                                type: menuItem.id === "rename" ? "update" : "delete",
                                selectedFolder: {
                                  id: item.id,
                                  name: item.name,
                                },
                                open: true,
                              });
                            }}
                          />
                        )}
                      </ListItemButton>
                    ))}
                  </List>
                </Collapse>
              </div>
            );
          })
          .filter(Boolean)}
      </List>
    </>
  );
}
