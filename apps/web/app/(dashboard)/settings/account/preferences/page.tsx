"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import DarkModeIcon from "@mui/icons-material/Brightness4";
import LightModeIcon from "@mui/icons-material/Brightness7";
import type { PaletteMode } from "@mui/material";
import {
  Box,
  Divider,
  InputAdornment,
  MenuItem,
  Stack,
  TextField,
  Typography,
  useTheme,
} from "@mui/material";
import { useSession } from "next-auth/react";
import React, { useCallback, useContext, useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { useTranslation } from "react-i18next";
import { toast } from "react-toastify";

import { ICON_NAME, Icon } from "@p4b/ui/components/Icon";

import { languages } from "@/i18n/settings";

import { updateSystemSettings } from "@/lib/api/system/client";
import { type SystemSettingsUpdate, systemSettingsSchemaUpdate } from "@/lib/validations/system";

import { ColorModeContext } from "@/components/@mui/ThemeRegistry";

const AccountPreferences = () => {
  const { i18n, t } = useTranslation("common");
  const { data: session } = useSession();
  const [isBusy, setIsBusy] = useState(false);
  const muiTheme = useTheme();
  const { changeColorMode } = useContext(ColorModeContext);
  const themeModes = ["dark", "light"] as const;

  const { register, handleSubmit, watch } = useForm<SystemSettingsUpdate>({
    mode: "onChange",
    resolver: zodResolver(systemSettingsSchemaUpdate),
  });

  const onSubmit = useCallback(
    async (settings: SystemSettingsUpdate) => {
      if (!session?.access_token) return;
      try {
        setIsBusy(true);

        const payload: SystemSettingsUpdate = {
          preferred_language: settings.preferred_language ?? (i18n.language as "en" | "de"),
          client_theme: settings.client_theme ?? muiTheme.palette.mode,
          unit: "metric",
        };
        // Tell FastAPI to update and receive validated settings back
        const validated = await updateSystemSettings(payload, session.access_token);
        if (!validated) throw new Error("No validated settings returned");
        await fetch("/api/preferences/update", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            lang: validated?.preferred_language,
            theme: validated?.client_theme,
          }),
        });

        // Apply instantly in UI
        await i18n.changeLanguage(validated.preferred_language);
        changeColorMode(validated.client_theme as PaletteMode);
      } catch (err) {
        console.error(err);
        toast.error(t("failed_to_update_preferences"));
      } finally {
        setIsBusy(false);
      }
    },
    [i18n, muiTheme.palette.mode, changeColorMode, session, t]
  );

  // Auto‑submit whenever fields change
  useEffect(() => {
    const sub = watch(() => handleSubmit(onSubmit)());
    return () => sub.unsubscribe();
  }, [watch, handleSubmit, onSubmit]);

  return (
    <Box sx={{ p: 4 }}>
      <Box component="form">
        <Stack spacing={muiTheme.spacing(6)}>
          <Divider />
          <Box>
            <Typography variant="body1" fontWeight="bold">
              {t("preferences")}
            </Typography>
            <Typography variant="caption">{t("manage_preferences")}</Typography>
          </Box>
          <Divider />

          {/* Language selector */}
          <TextField
            select
            label={t("language")}
            size="medium"
            disabled={isBusy}
            defaultValue={i18n.language ?? languages[0]}
            {...register("preferred_language")}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <Icon iconName={ICON_NAME.LANGUAGE} fontSize="small" />
                </InputAdornment>
              ),
            }}>
            {languages.map((lng) => (
              <MenuItem key={lng} value={lng}>
                {t(lng)}
              </MenuItem>
            ))}
          </TextField>

          {/* Theme selector */}
          <TextField
            select
            label={t("theme")}
            size="medium"
            disabled={isBusy}
            defaultValue={muiTheme.palette.mode}
            {...register("client_theme")}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  {muiTheme.palette.mode === "dark" ? (
                    <DarkModeIcon fontSize="small" />
                  ) : (
                    <LightModeIcon fontSize="small" />
                  )}
                </InputAdornment>
              ),
            }}>
            {themeModes.map((mode) => (
              <MenuItem key={mode} value={mode}>
                {t(mode)}
              </MenuItem>
            ))}
          </TextField>
        </Stack>
      </Box>
    </Box>
  );
};

export default AccountPreferences;
