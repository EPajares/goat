"use client";

import { LoadingButton } from "@mui/lab";
import {
  Avatar,
  Box,
  Chip,
  Divider,
  List,
  ListItemAvatar,
  ListItemButton,
  ListItemSecondaryAction,
  ListItemText,
  Skeleton,
  Stack,
  Typography,
  useTheme,
} from "@mui/material";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useTranslation } from "react-i18next";

import { ICON_NAME, Icon } from "@p4b/ui/components/Icon";

import { useTeams } from "@/lib/api/teams";

import { useAuthZ } from "@/hooks/auth/AuthZ";

import TeamCreateModal from "@/components/modals/settings/TeamCreateModal";

export default function Teams() {
  const { t } = useTranslation("common");
  const theme = useTheme();
  const [openTeamCreateModal, setOpenTeamCreateModal] = useState(false);
  const { teams, mutate: mutateTeams, isLoading } = useTeams();
  const { isOrgEditor, isLoading: isUserProfileLoading } = useAuthZ();
  const router = useRouter();
  return (
    <>
      <Box sx={{ p: 4 }}>
        <Stack spacing={theme.spacing(6)}>
          <Divider />
          <Box>
            <Typography variant="body1" fontWeight="bold">
              {t("teams")}
            </Typography>
            <Typography variant="caption">{t("teams_header_information")}</Typography>
          </Box>
          <Divider />
          <TeamCreateModal
            open={openTeamCreateModal}
            onClose={() => {
              setOpenTeamCreateModal(false);
              mutateTeams();
            }}
          />
          {isOrgEditor && (
            <Stack alignItems="flex-end">
              <LoadingButton
                variant="contained"
                sx={{ whiteSpace: "nowrap" }}
                onClick={() => setOpenTeamCreateModal(true)}
                startIcon={<Icon fontSize="small" iconName={ICON_NAME.PLUS} />}
                aria-label="new-team-member"
                name="new-team-member">
                {t("new_team")}
              </LoadingButton>
            </Stack>
          )}
          <Stack>
            <Divider sx={{ py: 0, my: 0 }} />
            <List disablePadding sx={{ width: "100%", mt: 0, bgcolor: "background.paper" }}>
              {teams &&
                teams.map((team) => (
                  <Stack key={team.id}>
                    <ListItemButton
                      onClick={(item) => {
                        if (item && team.id) {
                          router.push(`/settings/teams/${team.id}`);
                        }
                      }}>
                      <ListItemAvatar>
                        <Avatar alt={team.name} src={team.avatar as string} />
                      </ListItemAvatar>
                      <ListItemText primary={team.name} secondary={team.description} />
                      <ListItemSecondaryAction>
                        <Chip
                          label={t(team.role)}
                          icon={
                            team.role.includes("owner") ? (
                              <Icon iconName={ICON_NAME.CROWN} style={{ fontSize: "12px" }} color="inherit" />
                            ) : undefined
                          }
                          size="small"
                          sx={{
                            "& .MuiChip-label": {
                              fontStyle: "normal",
                            },
                          }}
                        />
                      </ListItemSecondaryAction>
                    </ListItemButton>
                    <Divider variant="inset" component="li" sx={{ py: 0, my: 0 }} />
                  </Stack>
                ))}
              {(!teams || teams.length === 0) && !isLoading && (
                <Stack spacing={4} sx={{ mt: 10, mb: 5 }} alignItems="center">
                  <Typography variant="body1" fontWeight="bold">
                    {t("no_teams_found")}
                  </Typography>
                  <Typography variant="body2">{t("no_teams_found_subtitle")}</Typography>
                </Stack>
              )}
              {isLoading ||
                (isUserProfileLoading && <Skeleton variant="rectangular" width="100%" height={400} />)}
            </List>
          </Stack>
        </Stack>
      </Box>
    </>
  );
}
