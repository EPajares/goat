"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { LoadingButton } from "@mui/lab";
import { Box, Divider, IconButton, Stack, Tab, Tabs, TextField, Typography, useTheme } from "@mui/material";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { useForm } from "react-hook-form";
import { Trans, useTranslation } from "react-i18next";
import { toast } from "react-toastify";

import { ICON_NAME, Icon } from "@p4b/ui/components/Icon";

import { useOrganizationMembers } from "@/lib/api/organizations";
import { deleteTeam, updateTeam, useTeam, useTeamMembers } from "@/lib/api/teams";
import { useOrganization } from "@/lib/api/users";
import type { Team, TeamMember, TeamUpdate } from "@/lib/validations/team";
import { teamRoleEnum, teamUpdateSchema } from "@/lib/validations/team";

import type { TeamMemberActions } from "@/types/common";

import { useAuthZ } from "@/hooks/auth/AuthZ";
import { useMemberSettingsMoreMenu } from "@/hooks/dashboard/SettingsHooks";

import { CustomTabPanel, a11yProps } from "@/components/common/CustomTabPanel";
import { RhfAvatar } from "@/components/common/form-inputs/AvatarUpload";
import MembersTable from "@/components/dashboard/settings/MembersTable";
import ConfirmModal from "@/components/modals/Confirm";
import TeamMemberInviteModal from "@/components/modals/settings/InviteTeamMember";
import TeamMemberDialogWrapper from "@/components/modals/settings/TeamMembersDialogWrapper";

function TeamProfile({ team }: { team: Team }) {
  const theme = useTheme();
  const { t } = useTranslation("common");
  const [isDeleteOrLeaveTeamBusy, setIsDeleteOrLeaveTeamBusy] = useState<boolean>(false);
  const [isTeamUpdateBusy, setIsTeamUpdateBusy] = useState<boolean>(false);
  const [confirmDeleteOrLeaveTeamDialogOpen, setConfirmDeleteOrLeaveTeamDialogOpen] = useState(false);
  const router = useRouter();
  const { isTeamOwner } = useAuthZ({
    team,
  });

  const {
    register: registerTeamUpdate,
    handleSubmit: handleTeamUpdateSubmit,
    formState: { errors, isDirty, isValid },
    control,
    reset,
  } = useForm<TeamUpdate>({
    mode: "onChange",
    resolver: zodResolver(teamUpdateSchema),
    defaultValues: useMemo(() => {
      if (team) {
        return teamUpdateSchema.parse(team);
      }
      return {};
    }, [team]),
  });

  useEffect(() => {
    if (team) {
      reset(teamUpdateSchema.parse(team));
    }
  }, [team, reset]);

  async function _updateTeam(data: TeamUpdate) {
    setIsTeamUpdateBusy(true);
    try {
      if (team) {
        await updateTeam(team.id, data);
        toast.success(t("team_update_success"));
        reset({}, { keepValues: true });
      }
    } catch (_error) {
      toast.error(t("team_update_error"));
    } finally {
      setIsTeamUpdateBusy(false);
    }
  }

  async function onTeamUpdateSubmit(data: TeamUpdate) {
    await _updateTeam(data);
  }

  async function _deleteOrLeaveTeam() {
    setIsDeleteOrLeaveTeamBusy(true);
    try {
      if (team) {
        await deleteTeam(team.id);
        toast.success(t("team_delete_success"));
        router.push(`/settings/teams`);
      }
    } catch (_error) {
      toast.error(t("team_delete_error"));
    } finally {
      setIsDeleteOrLeaveTeamBusy(false);
    }
  }
  return (
    <>
      <Box component="form" onSubmit={handleTeamUpdateSubmit(onTeamUpdateSubmit)}>
        <Stack spacing={theme.spacing(6)}>
          <Divider />
          <Box>
            <Typography variant="body1" fontWeight="bold">
              {t("team_information")}
            </Typography>
            <Typography variant="caption">
              {isTeamOwner
                ? t("update_team_information_description")
                : t("overview_team_information_description")}
            </Typography>
          </Box>
          <Divider />
          <>
            <RhfAvatar
              name="avatar"
              control={control}
              title={t("team_avatar")}
              avatar={team?.avatar ?? ""}
              readOnly={!isTeamOwner}
            />

            <TextField
              required
              InputProps={{ readOnly: !isTeamOwner }}
              helperText={errors.name ? errors.name?.message : ""}
              label={t("team_name")}
              id="name"
              {...registerTeamUpdate("name")}
              error={errors.name ? true : false}
            />

            <TextField
              InputProps={{ readOnly: !isTeamOwner }}
              helperText={errors.description ? errors.description?.message : ""}
              label={t("team_description")}
              id="description"
              {...registerTeamUpdate("description")}
              error={errors.description ? true : false}
            />

            {isTeamOwner && (
              <Stack direction="row" alignItems="center" justifyContent="flex-end">
                <LoadingButton
                  loading={isTeamUpdateBusy}
                  variant="contained"
                  startIcon={<Icon fontSize="small" iconName={ICON_NAME.SAVE} />}
                  aria-label="update-profile"
                  name="update-profile"
                  disabled={isTeamUpdateBusy || !isDirty || !isValid}
                  type="submit">
                  {t("update")}
                </LoadingButton>
              </Stack>
            )}
          </>
        </Stack>
      </Box>
      <Box sx={{ mt: 16 }}>
        <Stack spacing={theme.spacing(6)}>
          <Divider />
          <ConfirmModal
            open={confirmDeleteOrLeaveTeamDialogOpen}
            title={isTeamOwner ? t("delete_team") : t("leave_team")}
            body={
              <Trans
                i18nKey={
                  isTeamOwner ? "common:delete_team_confirmation_body" : "common:leave_team_confirmation_body"
                }
                components={{ b: <b />, ul: <ul />, li: <li /> }}
              />
            }
            onClose={() => {
              setConfirmDeleteOrLeaveTeamDialogOpen(false);
            }}
            onConfirm={async () => {
              setConfirmDeleteOrLeaveTeamDialogOpen(false);
              await _deleteOrLeaveTeam();
            }}
            closeText={t("close")}
            confirmText={isTeamOwner ? t("delete_team") : t("leave_team")}
          />
          <Box>
            <Typography variant="body1" fontWeight="bold" color={theme.palette.error.main}>
              {t("danger_zone")}
            </Typography>
            <Typography variant="caption">
              {isTeamOwner ? t("danger_zone_delete_team_description") : t("leave_team")}
            </Typography>
          </Box>
          <Divider />
          <Stack>
            <Typography variant="body1">
              <Trans
                i18nKey={
                  isTeamOwner ? "common:danger_zone_delete_team_body" : "common:danger_zone_leave_team_body"
                }
                components={{ b: <b />, a: <b /> }}
              />
            </Typography>
          </Stack>
          <Stack direction="row" alignItems="center" justifyContent="flex-end">
            <LoadingButton
              size="large"
              startIcon={
                <Icon fontSize="small" iconName={isTeamOwner ? ICON_NAME.TRASH : ICON_NAME.SIGNOUT} />
              }
              variant="outlined"
              color="error"
              aria-label="delete-team"
              name="delete-team"
              disabled={confirmDeleteOrLeaveTeamDialogOpen}
              loading={isDeleteOrLeaveTeamBusy}
              onClick={() => {
                setConfirmDeleteOrLeaveTeamDialogOpen(true);
              }}>
              <Typography variant="body1" fontWeight="bold" color="inherit">
                {isTeamOwner ? t("delete_team") : t("leave_team")}
              </Typography>
            </LoadingButton>
          </Stack>
        </Stack>
      </Box>
    </>
  );
}

function TeamMembers({ team }: { team: Team }) {
  const { t } = useTranslation("common");
  const { id: teamId } = team;
  const { teamMembers, mutate: mutateMembers } = useTeamMembers(teamId);
  const theme = useTheme();
  const [openInviteModal, setOpenInviteModal] = useState(false);
  const { organization } = useOrganization();
  const { members: organizationMembers } = useOrganizationMembers(organization?.id || "");

  const membersNotInTeam = useMemo(() => {
    const teamMemberIds = new Set((teamMembers || []).map((member) => member.id));
    return (organizationMembers || []).filter((member) => !teamMemberIds.has(member.id));
  }, [teamMembers, organizationMembers]);
  const { isTeamOwner } = useAuthZ({
    team,
  });
  const {
    activeMemberMoreMenuOptions,
    pendingInvitationMoreMenuOptions,
    openMoreMenu,
    activeMember,
    moreMenuState,
    closeMoreMenu,
  } = useMemberSettingsMoreMenu("team");

  return (
    <>
      <Stack spacing={theme.spacing(6)}>
        {activeMember && moreMenuState && (
          <TeamMemberDialogWrapper
            member={activeMember as TeamMember}
            action={moreMenuState.id as TeamMemberActions}
            onClose={closeMoreMenu}
            teamId={teamId}
            onMemberDelete={() => {
              mutateMembers();
              closeMoreMenu();
            }}
          />
        )}
        {organizationMembers && teamMembers && isTeamOwner && (
          <TeamMemberInviteModal
            open={openInviteModal}
            onClose={() => {
              setOpenInviteModal(false);
              mutateMembers();
            }}
            members={membersNotInTeam || []}
            teamId={teamId}
            onInvite={() => {}}
          />
        )}

        <Divider />
        <Box>
          <Typography variant="body1" fontWeight="bold">
            {isTeamOwner ? t("team_manage_members") : t("members")}
          </Typography>
          <Typography variant="caption">
            {isTeamOwner ? t("team_manage_members_description") : t("team_members_description")}
          </Typography>
        </Box>
        <Divider />

        {isTeamOwner && (
          <Stack alignItems="flex-end">
            <LoadingButton
              variant="contained"
              disabled={!organizationMembers || !teamMembers}
              sx={{ whiteSpace: "nowrap" }}
              onClick={() => {
                setOpenInviteModal(true);
              }}
              startIcon={<Icon fontSize="small" iconName={ICON_NAME.PLUS} />}
              aria-label="send-invite"
              name="send-invite">
              {t("new_org_member")}
            </LoadingButton>
          </Stack>
        )}
        <MembersTable
          members={teamMembers || []}
          memberRoles={teamRoleEnum.options}
          activeMemberMoreMenuOptions={activeMemberMoreMenuOptions}
          pendingInvitationMoreMenuOptions={pendingInvitationMoreMenuOptions}
          onMoreMenuItemClick={openMoreMenu}
          type="team"
          viewOnly={!isTeamOwner}
        />
      </Stack>
    </>
  );
}

export default function TeamPage({ params: { teamId } }) {
  const { t } = useTranslation("common");

  const { team } = useTeam(teamId);

  const router = useRouter();

  const [value, setValue] = useState(0);
  const handleChange = (_event: React.SyntheticEvent, newValue: number) => {
    setValue(newValue);
  };

  const tabItems = useMemo(() => {
    return [
      { label: t("profile"), value: "profile", icon: ICON_NAME.USERS },
      { label: t("members"), value: "members", icon: ICON_NAME.ADD_USER },
    ];
  }, [t]);

  return (
    <>
      {team && (
        <Box sx={{ p: 4 }}>
          <Stack direction="row" alignItems="center" spacing={2}>
            <IconButton
              onClick={() => {
                router.push(`/settings/teams`);
              }}>
              <Icon iconName={ICON_NAME.CHEVRON_LEFT} style={{ fontSize: "15px" }} />
            </IconButton>
            <Typography
              variant="body1"
              fontWeight="bold"
              sx={{
                display: "flex",
              }}>
              {team.name}
            </Typography>
          </Stack>
          <Box sx={{ width: "100%", mt: 8 }}>
            <Box sx={{ borderBottom: 1, borderColor: "divider" }}>
              <Tabs variant="fullWidth" value={value} scrollButtons onChange={handleChange}>
                {tabItems.map((item) => (
                  <Tab
                    iconPosition="start"
                    icon={
                      <Box sx={{ pr: 2 }}>
                        <Icon iconName={item.icon} htmlColor="inherit" style={{ fontSize: 15 }} />
                      </Box>
                    }
                    key={item.value}
                    label={item.label}
                    {...a11yProps(item.value)}
                  />
                ))}
              </Tabs>
            </Box>

            {tabItems.map((item) => (
              <CustomTabPanel
                disablePadding
                key={item.value}
                value={value}
                index={tabItems.findIndex((tab) => tab.value === item.value)}>
                {item.value === "profile" && <TeamProfile team={team} />}
                {item.value === "members" && <TeamMembers team={team} />}
              </CustomTabPanel>
            ))}
          </Box>
        </Box>
      )}
    </>
  );
}
