"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { LoadingButton } from "@mui/lab";
import { Box, Divider, Skeleton, Stack, TextField, Typography } from "@mui/material";
import { useTheme } from "@mui/material";
import { signOut } from "next-auth/react";
import React, { useEffect, useMemo, useState } from "react";
import { useForm } from "react-hook-form";
import { useTranslation } from "react-i18next";
import { Trans } from "react-i18next";
import { toast } from "react-toastify";

import { ICON_NAME, Icon } from "@p4b/ui/components/Icon";

import { deleteAccount, updateUserProfile, useUserProfile } from "@/lib/api/users";
import type { UserUpdate } from "@/lib/validations/user";
import { userSchemaUpdate } from "@/lib/validations/user";

import { RhfAvatar } from "@/components/common/form-inputs/AvatarUpload";
import ConfirmModal from "@/components/modals/Confirm";

const Profile = () => {
  const theme = useTheme();
  const { t } = useTranslation("common");
  const { userProfile, isLoading } = useUserProfile();
  const [isProfileUpdateBusy, setIsProfileUpdateBusy] = useState<boolean>(false);
  const [isDeleteAccountBusy, setIsDeleteAccountBusy] = useState<boolean>(false);
  const [confirmLogoutDialogOpen, setConfirmLogoutDialogOpen] = useState(false);
  const [confirmDeleteAccountDialogOpen, setConfirmDeleteAccountDialogOpen] = useState(false);
  const {
    register: registerUserProfile,
    handleSubmit: handleUserProfileSubmit,
    formState: { errors, isDirty, isValid },
    getValues,
    control,
    reset,
  } = useForm<UserUpdate>({
    mode: "onChange",
    resolver: zodResolver(userSchemaUpdate),
    defaultValues: useMemo(() => {
      if (userProfile) {
        const parsed = userSchemaUpdate.safeParse(userProfile);
        if (!parsed.success) {
          return {};
        }
        return parsed.data;
      }
      return {};
    }, [userProfile]),
  });

  useEffect(() => {
    if (userProfile) {
      const parsed = userSchemaUpdate.safeParse(userProfile);
      if (!parsed.success) {
        return;
      }
      reset(parsed.data);
    }
  }, [userProfile, reset]);

  async function _updateUserProfile(data: UserUpdate) {
    setIsProfileUpdateBusy(true);
    try {
      await updateUserProfile(data);
      toast.success(t("profile_updated_success"));
      reset({}, { keepValues: true });
    } catch (_error) {
      toast.error(t("profile_update_error"));
    } finally {
      setIsProfileUpdateBusy(false);
    }
  }

  async function _deleteAccount() {
    setIsDeleteAccountBusy(true);
    try {
      await deleteAccount();
      toast.success(t("account_deleted_success"));
      reset({}, { keepValues: true });
    } catch (_error) {
      toast.error(t("account_delete_error"));
    } finally {
      setIsDeleteAccountBusy(false);
    }
  }

  async function onUserProfileSubmit(data: UserUpdate) {
    if (data.email !== userProfile?.email) {
      setConfirmLogoutDialogOpen(true);
      return;
    }
    await _updateUserProfile(data);
  }
  return (
    <Box sx={{ p: 4 }}>
      <Box component="form" onSubmit={handleUserProfileSubmit(onUserProfileSubmit)}>
        <Stack spacing={theme.spacing(6)}>
          <Divider />
          <Box>
            <Typography variant="body1" fontWeight="bold">
              {t("personal_information")}
            </Typography>
            <Typography variant="caption">{t("update_personal_information")}</Typography>
          </Box>
          <Divider />

          {/* Email Change Confirmation */}
          <ConfirmModal
            open={confirmLogoutDialogOpen}
            title={t("email_change_confirmation")}
            body={t("email_change_confirmation_body")}
            onClose={() => {
              setConfirmLogoutDialogOpen(false);
            }}
            onConfirm={async () => {
              setConfirmLogoutDialogOpen(false);
              const data = getValues();
              await _updateUserProfile(data);
              signOut({ callbackUrl: process.env.NEXT_PUBLIC_APP_URL });
            }}
          />

          {isLoading ? (
            <>
              <Skeleton variant="circular" width={64} height={64} />
              <Skeleton variant="rectangular" height={300} />
            </>
          ) : (
            <>
              <RhfAvatar
                name="avatar"
                control={control}
                title={t("user_avatar")}
                avatar={userProfile?.avatar ?? ""}
              />

              <TextField
                required
                helperText={errors.firstname ? errors.firstname?.message : ""}
                label={t("first_name")}
                id="name"
                {...registerUserProfile("firstname")}
                error={errors.firstname ? true : false}
              />

              <TextField
                required
                helperText={errors.lastname ? errors.lastname?.message : ""}
                label={t("last_name")}
                id="name"
                {...registerUserProfile("lastname")}
                error={errors.lastname ? true : false}
              />

              <TextField
                required
                helperText={errors.email ? errors.email?.message : t("email_change_warning")}
                label={t("email")}
                id="name"
                {...registerUserProfile("email")}
                error={errors.email ? true : false}
              />
              <Stack direction="row" alignItems="center" justifyContent="flex-end">
                <LoadingButton
                  loading={isProfileUpdateBusy}
                  variant="contained"
                  startIcon={<Icon fontSize="small" iconName={ICON_NAME.SAVE} />}
                  aria-label="update-profile"
                  name="update-profile"
                  disabled={isProfileUpdateBusy || !isDirty || !isValid}
                  type="submit">
                  {t("update")}
                </LoadingButton>
              </Stack>
            </>
          )}
        </Stack>
      </Box>

      <Box sx={{ mt: 16 }}>
        <Stack spacing={theme.spacing(6)}>
          <Divider />

          {/* Delete Account Confirmation */}
          <ConfirmModal
            open={confirmDeleteAccountDialogOpen}
            title={t("delete_account")}
            body={
              <Trans
                i18nKey="common:delete_account_confirmation_body"
                values={{ email: userProfile?.email }}
                components={{ b: <b />, ul: <ul />, li: <li /> }}
              />
            }
            onClose={() => {
              setConfirmDeleteAccountDialogOpen(false);
            }}
            onConfirm={async () => {
              setConfirmDeleteAccountDialogOpen(false);
              await _deleteAccount();
              signOut({ callbackUrl: process.env.NEXT_PUBLIC_APP_URL });
            }}
            closeText={t("close")}
            confirmText={t("delete")}
            matchText={userProfile?.email}
          />

          <Box>
            <Typography variant="body1" fontWeight="bold" color={theme.palette.error.main}>
              {t("danger_zone")}
            </Typography>
            <Typography variant="caption">{t("danger_zone_account_description")}</Typography>
          </Box>
          <Divider />
          <Stack>
            <Typography variant="body1">
              <Trans i18nKey="common:danger_zone_account_body" components={{ b: <b /> }} />
            </Typography>
          </Stack>
          <Stack direction="row" alignItems="center" justifyContent="flex-end">
            <LoadingButton
              size="large"
              startIcon={<Icon fontSize="small" iconName={ICON_NAME.TRASH} />}
              variant="outlined"
              color="error"
              aria-label="delete-account"
              name="delete-account"
              loading={isDeleteAccountBusy}
              onClick={() => {
                setConfirmDeleteAccountDialogOpen(true);
              }}
              disabled={isProfileUpdateBusy}>
              <Typography variant="body1" fontWeight="bold" color="inherit">
                {t("delete_account")}
              </Typography>
            </LoadingButton>
          </Stack>
        </Stack>
      </Box>
    </Box>
  );
};

export default Profile;
