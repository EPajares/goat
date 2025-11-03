import KeyboardArrowDownIcon from "@mui/icons-material/KeyboardArrowDown";
import { LoadingButton } from "@mui/lab";
import {
  Avatar,
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Divider,
  List,
  ListItem,
  ListItemAvatar,
  ListItemSecondaryAction,
  ListItemText,
  Menu,
  MenuItem,
  MenuList,
  Stack,
  Tab,
  Tabs,
  Typography,
} from "@mui/material";
import { formatDistance } from "date-fns";
import { useMemo, useState } from "react";
import { Trans } from "react-i18next";
import { toast } from "react-toastify";
import { mutate } from "swr";

import { Loading } from "@p4b/ui/components/Loading";

import { useDateFnsLocale, useTranslation } from "@/i18n/client";

import { LAYERS_API_BASE_URL } from "@/lib/api/layers";
import {
  PROJECTS_API_BASE_URL,
  publishProject,
  unpublishProject,
  usePublicProject,
} from "@/lib/api/projects";
import { shareLayer, shareProject } from "@/lib/api/share";
import { useTeams } from "@/lib/api/teams";
import { useOrganization } from "@/lib/api/users";
import { type Layer, layerShareRoleEnum } from "@/lib/validations/layer";
import { type Project, projectShareRoleEnum } from "@/lib/validations/project";

import CopyField from "@/components/common/CopyField";
import { CustomTabPanel, a11yProps } from "@/components/common/CustomTabPanel";

interface ShareProps {
  open: boolean;
  onClose?: () => void;
  type: "layer" | "project";
  content: Layer | Project;
}

interface Item {
  id: string;
  name: string;
  avatar: string;
  role: string;
}

interface ShareWithItemsTabProps {
  items: Item[];
  roleOptions: string[];
  onRoleChange: (id: string, role: string) => void;
}

interface ShareWithPublicTabProps {
  project: Project;
}

const ShareWithItemsTab: React.FC<ShareWithItemsTabProps> = ({ items, roleOptions, onRoleChange }) => {
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [selectedItemId, setSelectedItemId] = useState<string | null>(null);
  const open = Boolean(anchorEl);
  const { t } = useTranslation("common");

  const handleClick = (event: React.MouseEvent<HTMLButtonElement>, itemId: string) => {
    setAnchorEl(event.currentTarget);
    setSelectedItemId(itemId);
  };

  const handleClose = () => {
    setAnchorEl(null);
    setSelectedItemId(null);
  };

  const handleRoleChange = (role: string) => {
    if (selectedItemId) {
      onRoleChange(selectedItemId, role);
      handleClose();
    }
  };

  const getRoleTranslation = (role: string) => {
    if (role.includes("editor")) {
      return t("editor");
    } else if (role.includes("viewer")) {
      return t("viewer");
    }
  };

  return (
    <>
      <List disablePadding sx={{ width: "100%", bgcolor: "background.paper" }}>
        {items.map((item) => (
          <Stack key={item.id} justifyContent="center">
            <ListItem>
              <ListItemAvatar>
                <Avatar alt={item.name} src={item.avatar} />
              </ListItemAvatar>
              <ListItemText primary={item.name} />
              <ListItemSecondaryAction
                sx={{
                  display: "flex",
                  alignItems: "center",
                }}>
                <Button
                  variant="text"
                  sx={{ borderRadius: "4px" }}
                  size="small"
                  color="secondary"
                  onClick={(event) => handleClick(event, item.id)}
                  endIcon={<KeyboardArrowDownIcon color="inherit" />}>
                  <Typography variant="body2" fontWeight="bold" color="inherit">
                    {item.role ? getRoleTranslation(item.role) : t("no_access")}
                  </Typography>
                </Button>
              </ListItemSecondaryAction>
            </ListItem>
            <Divider sx={{ mt: 0, pt: 0 }} />
          </Stack>
        ))}
      </List>
      <Menu
        id="role-select-menu"
        anchorEl={anchorEl}
        open={open}
        onClose={handleClose}
        MenuListProps={{
          "aria-labelledby": "role-select-button",
        }}>
        <MenuList dense>
          {roleOptions.map((role) => (
            <MenuItem
              sx={{ width: "110px" }}
              selected={
                selectedItemId ? items.find((item) => item.id === selectedItemId)?.role === role : false
              }
              key={role}
              onClick={() => handleRoleChange(role)}>
              {role ? getRoleTranslation(role) : t("no_access")}
            </MenuItem>
          ))}
        </MenuList>
      </Menu>
    </>
  );
};

const ShareWithPublicTab: React.FC<ShareWithPublicTabProps> = ({ project }) => {
  const { t } = useTranslation("common");
  const { sharedProject, isLoading, mutate } = usePublicProject(project.id);
  const [isPublishing, setIsPublishing] = useState(false);
  const [isUnpublishing, setIsUnpublishing] = useState(false);
  const dateLocale = useDateFnsLocale();
  const baseUrl = window.location.origin;
  const publicUrl = `${baseUrl}/map/public/${project.id}`;
  const embedCode = `<iframe src="${publicUrl}" width="100%" height="600" frameborder="0" style="max-width: 100%; border: 1px solid #EAEAEA; border-radius: 4px;"></iframe>`;

  const handlePublish = async () => {
    try {
      setIsPublishing(true);
      await publishProject(project.id);
      mutate();
    } catch {
      toast.error(t("error_publishing_project"));
    } finally {
      setIsPublishing(false);
    }
  };

  const handleUnpublish = async () => {
    try {
      setIsUnpublishing(true);
      await unpublishProject(project.id);
      mutate();
    } catch {
      toast.error(t("error_unpublishing_project"));
    } finally {
      setIsUnpublishing(false);
    }
  };

  return (
    <>
      {/* {sharedProject && (
        <Alert variant="outlined" severity="warning" sx={{ my: 2 }}>
          {t("map_has_unsaved")} <br />
          <b>{t("click_republish_to_make_live")}</b>
        </Alert>
      )} */}
      {isLoading && (
        <Box
          sx={{
            minHeight: "80px",
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
          }}>
          <Loading size={40} />
        </Box>
      )}

      {!isLoading && (
        <Stack spacing={4} sx={{ my: 4, mx: 0 }}>
          {/* <Divider /> */}
          <Stack direction="row" justifyContent="space-between" alignItems="center">
            {!sharedProject && (
              <>
                <Stack>
                  <Typography variant="body1">{t("publish_map")}</Typography>
                  <Typography variant="caption">{t("publish_map_description")}</Typography>
                </Stack>
                <LoadingButton
                  variant="contained"
                  color="primary"
                  disableElevation
                  onClick={handlePublish}
                  loading={isPublishing}>
                  {t("publish")}
                </LoadingButton>
              </>
            )}
            {sharedProject && (
              <>
                <Stack>
                  <Typography variant="body1">{t("publish_map")}</Typography>
                  <Typography variant="caption">
                    {t("last_published")}
                    {": "}
                    {formatDistance(new Date(sharedProject.updated_at), new Date(), {
                      addSuffix: true,
                      locale: dateLocale,
                    })}
                  </Typography>
                </Stack>
                <Stack direction="row" spacing={2}>
                  <LoadingButton
                    variant="text"
                    color="error"
                    disableElevation
                    onClick={handleUnpublish}
                    disabled={isLoading || isPublishing}
                    loading={isUnpublishing}>
                    {t("unpublish")}
                  </LoadingButton>
                  <LoadingButton
                    variant="contained"
                    color="primary"
                    disabled={isUnpublishing || isLoading}
                    disableElevation
                    onClick={handlePublish}
                    loading={isPublishing}>
                    {t("republish")}
                  </LoadingButton>
                </Stack>
              </>
            )}
          </Stack>
          <Divider />
          {/* Public URL  */}
          {sharedProject && (
            <>
              <Stack spacing={1}>
                <Typography variant="body1">{t("public_url")}</Typography>
                <CopyField value={publicUrl} copyText="Copy URL" copiedText="Copied URL" />
              </Stack>

              {/* Embed Code */}
              <Stack spacing={1}>
                <Typography variant="body1">{t("embed_code")}</Typography>
                <CopyField value={embedCode} copyText="Copy Code" copiedText="Copied Code" />
              </Stack>
            </>
          )}
        </Stack>
      )}
    </>
  );
};

const ShareModal: React.FC<ShareProps> = ({ open, onClose, type, content }) => {
  const { t } = useTranslation("common");
  const [isBusy, setIsBusy] = useState(false);
  const [value, setValue] = useState(0);
  const { organization: organization } = useOrganization();
  const { teams: teamsList } = useTeams();
  const [sharedWith, setSharedWith] = useState(() => {
    const { teams = [], organizations = [] } = content.shared_with || {};
    const mapToIdAndRole = (item) => ({
      id: item.id,
      role: item.role,
    });

    return {
      teams: teams.map(mapToIdAndRole),
      organizations: organizations.map(mapToIdAndRole),
    };
  });
  const handleChange = (_event: React.SyntheticEvent, newValue: number) => {
    setValue(newValue);
  };

  const tabItems = useMemo(() => {
    const items = [
      { label: t("organization"), value: "organization" },
      { label: t("teams"), value: "teams" },
      { label: t("public"), value: "public" },
    ];

    if (type === "layer") {
      return items.filter((item) => item.value !== "public");
    }

    return items;
  }, [t, type]);

  const handleOnClose = () => {
    setIsBusy(false);
    onClose && onClose();
  };

  const organizationsAccessLevel: Item[] = useMemo(() => {
    if (!organization) {
      return [];
    }
    const sharedWitthOrg = sharedWith?.organizations;
    const accessLevels = [
      {
        id: organization.id,
        name: organization.name,
        avatar: organization.avatar as string,
        role: sharedWitthOrg?.find((org) => org.id === organization.id)?.role || "",
      },
    ];
    return accessLevels;
  }, [organization, sharedWith]);

  const teamsAccessLevel: Item[] = useMemo(() => {
    if (!teamsList) {
      return [];
    }
    const sharedWithTeams = sharedWith?.teams;
    const accessLevels = teamsList.map((team) => ({
      id: team.id,
      name: team.name,
      avatar: team.avatar as string,
      role: sharedWithTeams?.find((t) => t.id === team.id)?.role || "",
    }));
    return accessLevels;
  }, [teamsList, sharedWith]);

  const roleOptions = useMemo(() => {
    if (type === "layer") {
      return [...layerShareRoleEnum.options, ""] as string[];
    } else if (type === "project") {
      return [...projectShareRoleEnum.options, ""] as string[];
    }
    return [];
  }, [type]);

  const handleSubmit = async () => {
    try {
      setIsBusy(true);
      if (type === "project") {
        await shareProject(content.id, sharedWith);
        mutate((key) => Array.isArray(key) && key[0] === PROJECTS_API_BASE_URL);
      } else if (type === "layer") {
        await shareLayer(content.id, sharedWith);
        mutate((key) => Array.isArray(key) && key[0] === LAYERS_API_BASE_URL);
      }
      toast.success(t("share_access_updated_successfully"));
    } catch {
      toast.error(t("error_updating_share_access"));
    } finally {
      handleOnClose();
    }
  };

  const handleRoleChange = (type: "organizations" | "teams", id: string, role: string) => {
    setSharedWith((prevSharedWith) => {
      const items = prevSharedWith?.[type] || [];
      const itemExists = items.some((item) => item.id === id);

      let updatedItems;
      if (role === "") {
        // Remove the item if the role is an empty string
        updatedItems = items.filter((item) => item.id !== id);
      } else if (itemExists) {
        // Update the role if the item exists
        updatedItems = items.map((item) => {
          if (item.id === id) {
            return { ...item, role };
          }
          return item;
        });
      } else {
        // Add the item if it doesn't exist
        updatedItems = [...items, { id, role }];
      }

      return { ...prevSharedWith, [type]: updatedItems };
    });
  };
  const handleOrganizationRoleChange = (id: string, role: string) => {
    handleRoleChange("organizations", id, role);
  };

  const handleTeamRoleChange = (id: string, role: string) => {
    handleRoleChange("teams", id, role);
  };

  // const isSharingUpdated = useMemo(() => {
  //   const { teams = [], organizations = [] } = content.shared_with || {};

  //   const sharedWithTeams = sharedWith.teams;
  //   const sharedWithOrgs = sharedWith.organizations;

  //   const isTeamsUpdated = sharedWithTeams
  //     ? sharedWithTeams.some((team) => {
  //         const existingTeam = teams.find((t) => t.id === team.id);
  //         return !existingTeam || existingTeam.role !== team.role;
  //       })
  //     : false;

  //   const isOrgsUpdated = sharedWithOrgs
  //     ? sharedWithOrgs.some((org) => {
  //         const existingOrg = organizations.find((o) => o.id === org.id);
  //         return !existingOrg || existingOrg.role !== org.role;
  //       })
  //     : false;

  //   return isTeamsUpdated || isOrgsUpdated;
  // }, [content.shared_with, sharedWith]);

  return (
    <>
      <Dialog open={open} onClose={handleOnClose} fullWidth maxWidth="sm">
        <DialogTitle>
          <Trans
            i18nKey="common:manage_share_access_for_content"
            values={{
              content_type: type === "layer" ? t("layer") : t("project"),
              content_name: content.name,
            }}
          />
        </DialogTitle>
        <DialogContent>
          <Box sx={{ mt: 1, maxHeight: "500px" }}>
            <Box sx={{ width: "100%", mt: 8 }}>
              <Box sx={{ borderBottom: 1, borderColor: "divider" }}>
                <Tabs value={value} scrollButtons onChange={handleChange}>
                  {tabItems.map((item) => (
                    <Tab key={item.value} label={item.label} {...a11yProps(item.value)} />
                  ))}
                </Tabs>
              </Box>
              {/* <Divider sx={{ mt: 2, mb: 0, pb: 0 }} /> */}
              {tabItems.map((item) => (
                <CustomTabPanel
                  disablePadding
                  key={item.value}
                  value={value}
                  index={tabItems.findIndex((tab) => tab.value === item.value)}>
                  {item.value === "organization" && (
                    <ShareWithItemsTab
                      items={organizationsAccessLevel}
                      roleOptions={roleOptions}
                      onRoleChange={handleOrganizationRoleChange}
                    />
                  )}
                  {item.value === "teams" && (
                    <ShareWithItemsTab
                      items={teamsAccessLevel}
                      roleOptions={roleOptions}
                      onRoleChange={handleTeamRoleChange}
                    />
                  )}
                  {item.value === "public" && type === "project" && (
                    <ShareWithPublicTab project={content as Project} />
                  )}
                </CustomTabPanel>
              ))}
            </Box>
          </Box>
        </DialogContent>
        {/* Disable for public sharing */}
        {value !== 2 && (
          <DialogActions
            disableSpacing
            sx={{
              pt: 6,
              pb: 2,
              justifyContent: "flex-end",
            }}>
            <Stack direction="row" spacing={2}>
              <Button onClick={handleOnClose} variant="text">
                <Typography variant="body2" fontWeight="bold">
                  {t("cancel")}
                </Typography>
              </Button>
              <LoadingButton
                // disabled={!isSharingUpdated}
                loading={isBusy}
                variant="contained"
                color="primary"
                onClick={handleSubmit}>
                {t("save")}
              </LoadingButton>
            </Stack>
          </DialogActions>
        )}
      </Dialog>
    </>
  );
};

export default ShareModal;
