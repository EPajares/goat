import { Avatar, Button, Stack, Typography } from "@mui/material";
import React, { useRef } from "react";
import type { Control, FieldValues, Path } from "react-hook-form";
import { Controller } from "react-hook-form";
import { useTranslation } from "react-i18next";
import { toast } from "react-toastify";

interface RhfAvatarUploadProps<TField extends FieldValues> {
  title: string;
  control: Control<TField>;
  name: Path<TField>;
  avatar: string;
  readOnly?: boolean;
}

export const RhfAvatar = <TField extends FieldValues>(props: RhfAvatarUploadProps<TField>) => {
  const { control, name, avatar, title, readOnly } = props;
  const hiddenInputRef = useRef<HTMLInputElement | null>(null);
  const { t } = useTranslation("common");

  return (
    <Controller
      name={name}
      control={control}
      rules={{
        required: "this field is required",
      }}
      render={({ field }) => {
        const { onChange, value, ref } = field;
        return (
          <Stack direction="row" alignItems="center" spacing={4}>
            <Avatar src={value ?? avatar} sx={{ width: 64, height: 64 }} />
            <input
              type="file"
              accept="image/png, image/gif, image/jpeg"
              ref={(e) => {
                ref(e);
                hiddenInputRef.current = e;
              }}
              style={{ display: "none" }}
              name="avatarPicture"
              onChange={(event) => {
                const file = event.target.files?.[0];
                if (!file) {
                  return;
                }
                if (file.size > 1048576) {
                  toast.error(t("avatar_size_error"));
                  hiddenInputRef.current!.value = "";
                  return;
                }
                const reader = new FileReader();
                reader.readAsDataURL(file);
                reader.onload = (e: ProgressEvent<FileReader>) => {
                  onChange(e.target?.result ?? null);
                };
              }}
            />
            <Stack direction="column" spacing={2}>
              <Typography variant="body1">{title}</Typography>
              {!readOnly && (
                <Stack direction="row" spacing={2}>
                  <Button
                    variant="text"
                    color="primary"
                    onClick={() => {
                      hiddenInputRef?.current?.click();
                    }}>
                    {t("upload")}
                  </Button>
                  {value && avatar !== value && (
                    <Button
                      variant="text"
                      color="error"
                      onClick={() => {
                        onChange(avatar);
                      }}>
                      {t("cancel")}
                    </Button>
                  )}
                </Stack>
              )}
            </Stack>
          </Stack>
        );
      }}
    />
  );
};
