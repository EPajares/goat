import {
  Avatar,
  Divider,
  IconButton,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Paper,
  Stack,
  Typography,
  useTheme,
} from "@mui/material";
import { signOut } from "next-auth/react";
import { useState } from "react";
import { useTranslation } from "react-i18next";

import { ICON_NAME, Icon } from "@p4b/ui/components/Icon";

import { useOrganization, useUserProfile } from "@/lib/api/users";

import { ArrowPopper } from "@/components/ArrowPoper";

export default function UserInfoMenu() {
  const theme = useTheme();
  const { t } = useTranslation("common");
  const [open, setOpen] = useState(false);
  const { organization } = useOrganization();
  const { userProfile } = useUserProfile();
  return (
    <>
      <ArrowPopper
        content={
          <Paper
            sx={{
              width: 240,
              overflow: "auto",
              py: theme.spacing(2),
            }}>
            <Stack
              spacing={2}
              sx={{
                pt: theme.spacing(2),
              }}>
              <Stack sx={{ px: theme.spacing(4), pb: theme.spacing(2) }} spacing={3}>
                <Stack direction="row" justifyContent="flex-start" alignItems="center" spacing={2}>
                  {organization?.avatar ? (
                    <>
                      <Avatar alt={organization.name || "Organization"} src={organization?.avatar} />
                    </>
                  ) : (
                    <Avatar sx={{ bgcolor: "rgba(71, 219, 153, 0.12)" }}>
                      <Icon
                        iconName={ICON_NAME.ORGANIZATION}
                        htmlColor={theme.palette.primary.main}
                        fontSize="medium"
                      />
                    </Avatar>
                  )}

                  <Typography variant="body1" fontWeight="bold">
                    {organization?.name ?? "Organization"}
                  </Typography>
                </Stack>

                {userProfile && (
                  <>
                    <Typography variant="body1" gutterBottom>
                      {userProfile?.firstname} {userProfile?.lastname}
                    </Typography>
                    <Typography variant="caption">
                      {userProfile?.roles?.length > 0
                        ? userProfile?.roles?.map((role) => t(role)).join(", ")
                        : t("user")}
                    </Typography>
                  </>
                )}
              </Stack>
              <Divider />
              <ListItemButton
                onClick={() => signOut({ callbackUrl: process.env.NEXT_PUBLIC_APP_URL })}
                sx={{
                  color: theme.palette.error.main,
                }}>
                <ListItemIcon
                  sx={{
                    minWidth: 35,
                    color: "inherit",
                  }}>
                  <Icon
                    iconName={ICON_NAME.SIGNOUT}
                    fontSize="small"
                    fontWeight="light"
                    htmlColor="inherit"
                  />
                </ListItemIcon>
                <ListItemText
                  primary={
                    <Typography variant="body2" color="inherit" fontWeight="bold">
                      {t("logout")}
                    </Typography>
                  }
                />
              </ListItemButton>
            </Stack>
          </Paper>
        }
        open={open}
        placement="bottom"
        onClose={() => setOpen(false)}>
        <IconButton
          onClick={() => {
            setOpen(!open);
          }}
          size="small">
          {userProfile?.avatar ? (
            <Avatar
              sx={{ width: 36, height: 36 }}
              alt={userProfile.email || "User"}
              src={userProfile?.avatar}
            />
          ) : (
            <Avatar sx={{ width: 36, height: 36 }} alt={userProfile?.email || "User"}>
              <Icon fontSize="inherit" iconName={ICON_NAME.USER} htmlColor="inherit" />
            </Avatar>
          )}
        </IconButton>
      </ArrowPopper>
    </>
  );
}
