"use client";

import { Info } from "@mui/icons-material";
import { Box, Button, Chip, IconButton, Link, Stack, Tooltip, Typography, useTheme } from "@mui/material";
import Divider from "@mui/material/Divider";
import { format, formatDistance, parseISO } from "date-fns";
import { useMemo, useState } from "react";
import { Trans } from "react-i18next";
import { useMap } from "react-map-gl";

import { GOATLogoIconOnlyGreen } from "@p4b/ui/assets/svg/GOATLogoIconOnlyGreen";
import { ICON_NAME, Icon } from "@p4b/ui/components/Icon";

import { useDateFnsLocale, useTranslation } from "@/i18n/client";

import { useOrganization } from "@/lib/api/users";
import { CONTACT_US_URL, DOCS_URL, DOCS_VERSION, WEBSITE_URL } from "@/lib/constants";
import { setMapMode } from "@/lib/store/map/slice";
import type { Project } from "@/lib/validations/project";

import { useAuthZ } from "@/hooks/auth/AuthZ";
import { useAppDispatch, useAppSelector } from "@/hooks/store/ContextHooks";

import UserInfoMenu from "@/components/UserInfoMenu";
import EditableTypography from "@/components/common/EditableTypography";
import type { PopperMenuItem } from "@/components/common/PopperMenu";
import MoreMenu from "@/components/common/PopperMenu";
import SlidingToggle from "@/components/common/SlidingToggle";
import { ProjectMetadataView } from "@/components/dashboard/project/Metadata";
import JobsPopper from "@/components/jobs/JobsPopper";
import ContentDeleteModal from "@/components/modals/ContentDelete";
import Metadata from "@/components/modals/Metadata";
import ShareModal from "@/components/modals/Share";
import ViewModal from "@/components/modals/View";

import { Toolbar } from "./Toolbar";

export type HeaderProps = {
  title?: string;
  showHambugerMenu?: boolean;
  onMenuIconClick?: () => void;
  height?: number;
  mapHeader?: boolean;
  project?: Project;
  viewOnly?: boolean;
  showInfo?: boolean; // Only when viewOnly is true
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  onProjectUpdate?: (key: string, value: any, refresh?: boolean) => void;
};

export default function Header(props: HeaderProps) {
  const theme = useTheme();
  const { map } = useMap();
  const { t, i18n } = useTranslation(["common"]);
  const { onMenuIconClick, showHambugerMenu, height = 52, title, project, onProjectUpdate, viewOnly } = props;
  const { organization } = useOrganization();
  const { isOrgAdmin } = useAuthZ();
  const dateLocale = useDateFnsLocale();
  const lng = i18n.language === "de" ? "/de" : "";
  const docsVersion = `/${DOCS_VERSION}`;
  const dispatch = useAppDispatch();

  const [isEditingProjectName, setIsEditingProjectName] = useState(false);
  const [isEditingProjectMetadata, setIsEditingProjectMetadata] = useState(false);
  const [showProjectMetadataView, setShowProjectMetadataView] = useState(false);
  const [showDeleteProjectDialog, setShowDeleteProjectDialog] = useState(false);
  const [showShareDialog, setShowShareDialog] = useState(false);
  const mapMode = useAppSelector((state) => state.map.mapMode);

  const mapMenuItems: PopperMenuItem[] = useMemo(() => {
    const editorMenuItems: PopperMenuItem[] = [
      {
        id: "home",
        icon: ICON_NAME.HOUSE,
        label: t("common:home"),
        group: "basic",
        onClick: () => {
          window.location.href = "/home";
        },
      },
      {
        id: "edit_metadata",
        icon: ICON_NAME.EDIT,
        label: t("common:edit_metadata"),
        group: "project",
        onClick: () => {
          setIsEditingProjectMetadata(true);
        },
      },
      {
        id: "delete_project",
        icon: ICON_NAME.TRASH,
        label: t("common:delete_project"),
        group: "project",
        color: theme.palette.error.main,
        onClick: () => {
          setShowDeleteProjectDialog(true);
        },
      },
      {
        id: "lock_map_view",
        icon: project?.max_extent ? ICON_NAME.UNLOCK : ICON_NAME.LOCK,
        label: project?.max_extent ? t("common:unlock_map_view") : t("common:lock_map_view"),
        group: "map",
        onClick: async () => {
          if (map) {
            if (project?.max_extent) {
              await onProjectUpdate?.("max_extent", null);
            } else {
              const bounds = map.getBounds()?.toArray().flat();
              await onProjectUpdate?.("max_extent", bounds);
            }
          }
        },
      },
    ];

    const publicMenuItems: PopperMenuItem[] = [
      {
        id: "login",
        icon: ICON_NAME.USER,
        label: t("common:login"),
        group: "login",
        onClick: () => {
          window.location.href = "/auth/login";
        },
      },
    ];
    const commonMenuItems = [
      {
        id: "report_issue",
        icon: ICON_NAME.BUG,
        label: t("common:report_an_issue"),
        group: "help",
        onClick: () => {
          window.open("mailto:info@plan4better.de?subject=GOAT%20Support%20Request");
        },
      },
      {
        id: "privacy_policy",
        icon: ICON_NAME.COOKIES,
        label: t("common:privacy_policy"),
        group: "privacy",
        onClick: () => {
          window.open(`${WEBSITE_URL}${lng}/about-us/privacy`, "_blank");
        },
      },
    ];

    if (!viewOnly) {
      return [...editorMenuItems, ...commonMenuItems];
    } else {
      return [...publicMenuItems, ...commonMenuItems];
    }
  }, [t, theme.palette.error.main, project?.max_extent, viewOnly, map, onProjectUpdate, lng]);

  return (
    <>
      {showDeleteProjectDialog && project && (
        <ContentDeleteModal
          onDelete={() => {
            setShowDeleteProjectDialog(false);
            window.location.href = "/home";
          }}
          content={project}
          open={showDeleteProjectDialog}
          onClose={() => setShowDeleteProjectDialog(false)}
          type="project"
        />
      )}

      {project && props.mapHeader && (
        <ShareModal
          open={showShareDialog}
          onClose={() => setShowShareDialog(false)}
          type="project"
          content={project}
        />
      )}

      {project && isEditingProjectMetadata && (
        <Metadata
          open={isEditingProjectMetadata}
          onClose={() => setIsEditingProjectMetadata(false)}
          type="project"
          content={project}
        />
      )}

      {project && showProjectMetadataView && (
        <ViewModal
          title={t("project_info")}
          open={true}
          onClose={() => setShowProjectMetadataView(false)}
          closeText={t("close")}>
          <ProjectMetadataView project={project} />
        </ViewModal>
      )}

      <Toolbar
        showHambugerMenu={showHambugerMenu}
        onMenuIconClick={onMenuIconClick}
        height={height}
        LeftToolbarChild={
          <>
            {!props.mapHeader && (
              <Link
                href="/home"
                style={{
                  width: "32px",
                  height: "32px",
                  cursor: "pointer",
                }}>
                <Box
                  sx={{
                    transition: "transform 0.2s ease-in-out",
                    "&:hover": {
                      transform: "scale(1.1)",
                    },
                  }}>
                  <GOATLogoIconOnlyGreen style={{ width: "32px", height: "32px", cursor: "pointer" }} />
                </Box>
              </Link>
            )}
            {props.mapHeader && (
              <>
                <MoreMenu
                  menuItems={mapMenuItems}
                  disablePortal={false}
                  menuButton={
                    <Button
                      color="secondary"
                      endIcon={
                        <Icon
                          iconName={ICON_NAME.CHEVRON_DOWN}
                          style={{ fontSize: "14px", color: "inherit" }}
                        />
                      }
                      sx={{
                        textTransform: "none",
                        borderRadius: 1,
                        ml: -2,
                        my: 4,
                        "&:hover": {
                          color: theme.palette.primary.main,
                        },
                      }}
                      size="small"
                      variant="text">
                      <GOATLogoIconOnlyGreen style={{ width: "32px", height: "32px", cursor: "pointer" }} />
                    </Button>
                  }
                />

                <Divider orientation="vertical" flexItem />
              </>
            )}
            <EditableTypography
              variant="body1"
              fontWeight="bold"
              value={title || project?.name}
              readOnly={!props.mapHeader || !!title || viewOnly}
              isEditing={isEditingProjectName}
              onBlur={async (value) => {
                setIsEditingProjectName(false);
                if (value === project?.name || !project) return;
                await onProjectUpdate?.("name", value);
              }}
            />
            {props.mapHeader && <Divider orientation="vertical" flexItem />}
            {project?.updated_at && (
              <Typography variant="caption">
                {`${t("common:last_saved")}: ${format(parseISO(project.updated_at), "hh:mma dd/MM/yyyy")
                  .replace("PM", " PM")
                  .replace("AM", " AM")}`}
              </Typography>
            )}
            {project?.tags &&
              project?.tags.map((tag) => (
                <Chip
                  variant="outlined"
                  label={tag}
                  key={tag}
                  sx={{
                    mx: theme.spacing(1),
                  }}
                />
              ))}
          </>
        }
        RightToolbarChild={
          <>
            {!props.viewOnly && (
              <Stack direction="row" spacing={2} justifyContent="center" alignItems="center">
                {organization && organization.on_trial && isOrgAdmin && (
                  <Chip
                    icon={<Info />}
                    variant="outlined"
                    color="warning"
                    size="small"
                    label={
                      <Trans
                        i18nKey="common:your_trial_will_end_in"
                        values={{
                          expire_date: formatDistance(new Date(organization.plan_renewal_date), new Date(), {
                            locale: dateLocale,
                          }),
                        }}
                      />
                    }
                    sx={{
                      "& .MuiChip-label": {
                        fontWeight: "bold",
                        fontStyle: "normal",
                      },
                    }}
                    onClick={() => {
                      window.open(CONTACT_US_URL, "_blank");
                    }}
                  />
                )}
                {props.mapHeader && (
                  <>
                    <Stack sx={{ px: 4 }}>
                      <SlidingToggle
                        options={[
                          { label: t("common:data"), value: "data" },
                          { label: t("common:builder"), value: "builder" },
                        ]}
                        activeOption={mapMode}
                        onToggle={(value: "data" | "builder") => {
                          dispatch(setMapMode(value));
                        }}
                      />
                    </Stack>
                    <Divider orientation="vertical" flexItem />
                    <Stack sx={{ px: 4 }} spacing={2} direction="row">
                      <Button
                        startIcon={
                          <Icon iconName={ICON_NAME.GLOBE} style={{ fontSize: 16, color: "inherit" }} />
                        }
                        onClick={() => setShowShareDialog(true)}
                        variant="contained"
                        size="small">
                        <Typography variant="body2" color="inherit" fontWeight="bold">
                          {t("common:share")}
                        </Typography>
                      </Button>
                      {/* <Button
                        startIcon={
                          <Icon iconName={ICON_NAME.PLAY} style={{ fontSize: 16, color: "inherit" }} />
                        }
                        onClick={() => setShowShareDialog(true)}
                        variant="outlined"
                        size="small">
                        <Typography variant="body2" color="inherit" fontWeight="bold">
                          {t("common:preview")}
                        </Typography>
                      </Button> */}
                    </Stack>
                    <Divider orientation="vertical" flexItem />
                  </>
                )}

                <Tooltip title={t("common:open_documentation")}>
                  <IconButton
                    size="small"
                    onClick={() => {
                      window.open(`${DOCS_URL}${lng}${docsVersion}`, "_blank");
                    }}>
                    <Icon iconName={ICON_NAME.BOOK} fontSize="inherit" />
                  </IconButton>
                </Tooltip>
                <JobsPopper />
                <Divider orientation="vertical" flexItem />
                <UserInfoMenu />
              </Stack>
            )}
            {props.showInfo && (
              <Stack spacing={2} direction="row">
                <Tooltip title={t("common:project_info")}>
                  <IconButton
                    size="small"
                    onClick={() => {
                      setShowProjectMetadataView(!showProjectMetadataView);
                    }}>
                    <Icon iconName={ICON_NAME.CIRCLEINFO} fontSize="inherit" />
                  </IconButton>
                </Tooltip>
              </Stack>
            )}
          </>
        }
      />
    </>
  );
}
