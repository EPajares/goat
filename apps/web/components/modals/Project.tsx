import { zodResolver } from "@hookform/resolvers/zod";
import LoadingButton from "@mui/lab/LoadingButton";
import { Box, Button, Dialog, DialogTitle, Stack, TextField, Typography } from "@mui/material";
import { useRouter } from "next/navigation";
import { useMemo, useState } from "react";
import { useForm } from "react-hook-form";
import { toast } from "react-toastify";

import { ICON_NAME, Icon } from "@p4b/ui/components/Icon";

import { useTranslation } from "@/i18n/client";

import { useFolders } from "@/lib/api/folders";
import { createProject } from "@/lib/api/projects";
import type { GetContentQueryParams } from "@/lib/validations/common";
import type { PostProject } from "@/lib/validations/project";
import { postProjectSchema } from "@/lib/validations/project";

import { RhfAutocompleteField } from "@/components/common/form-inputs/AutocompleteField";

interface ProjectDialogProps {
  type: "upload" | "create";
  open: boolean;
  onClose?: () => void;
}

const ProjectModal: React.FC<ProjectDialogProps> = ({ open, onClose }) => {
  const { t } = useTranslation("common");
  const queryParams: GetContentQueryParams = {
    order: "descendent",
    order_by: "updated_at",
  };
  const router = useRouter();

  const { folders } = useFolders(queryParams);
  const [isBusy, setIsBusy] = useState(false);
  const {
    handleSubmit,
    register,
    getValues,
    watch,
    reset,
    control,
    formState: { errors },
  } = useForm<PostProject>({
    mode: "onChange",
    resolver: zodResolver(postProjectSchema),
    defaultValues: {
      description: "",
      //todo: get this from user preferences settings.
      thumbnail_url: "https://assets.plan4better.de/img/goat_new_project_artwork.png",
      initial_view_state: {
        latitude: 48.1502132,
        longitude: 11.5696284,
        zoom: 12,
        min_zoom: 0,
        max_zoom: 20,
        bearing: 0,
        pitch: 0,
      },
    },
  });
  const watchFormValues = watch();

  const handleOnClose = () => {
    reset();
    onClose?.();
  };

  const allowSubmit = useMemo(() => {
    return watchFormValues.folder_id;
  }, [watchFormValues]);
  const onSubmit = async () => {
    const values = getValues();
    try {
      setIsBusy(true);
      const project = await createProject(values);
      const { id } = project;
      if (id) {
        router.push(`/map/${id}`);
      }
      onClose?.();
    } catch (_error) {
      toast.error(t("error_creating_project"));
    } finally {
      setIsBusy(false);
    }
  };

  const folderOptions = useMemo(() => {
    return folders?.map((folder) => {
      return {
        value: folder.id,
        label: folder.name,
        icon: (
          <Icon fontSize="small" iconName={folder.name === "home" ? ICON_NAME.HOUSE : ICON_NAME.FOLDER} />
        ),
      };
    });
  }, [folders]);

  return (
    <Dialog open={open} onClose={handleOnClose} fullWidth maxWidth="sm">
      <DialogTitle>{t("create_project")}</DialogTitle>
      <Box sx={{ px: 4, pb: 2 }}>
        <Box sx={{ width: "100%" }} component="form" onSubmit={handleSubmit(onSubmit)}>
          <Stack direction="column" spacing={4} sx={{ my: 1 }}>
            <RhfAutocompleteField
              disabled={isBusy}
              options={folderOptions ?? []}
              control={control}
              name="folder_id"
              label={t("folder_location")}
            />
            <TextField
              fullWidth
              required
              {...register("name")}
              error={errors.name ? true : false}
              label={t("name")}
              helperText={errors.name?.message}
            />
            <TextField
              fullWidth
              multiline
              rows={4}
              label={t("description")}
              {...register("description")}
              error={!!errors.description}
              helperText={errors.description?.message}
            />
          </Stack>
          <Stack direction="row" justifyContent="flex-end" spacing={1} sx={{ mt: 4 }}>
            <Button onClick={handleOnClose} variant="text" sx={{ borderRadius: 0 }}>
              <Typography variant="body2" fontWeight="bold">
                {t("cancel")}
              </Typography>
            </Button>
            <LoadingButton
              type="submit"
              disabled={isBusy || !allowSubmit}
              loading={isBusy}
              variant="contained"
              color="primary">
              <Typography variant="body2" fontWeight="bold" color="inherit">
                {t("create")}
              </Typography>
            </LoadingButton>
          </Stack>
        </Box>
      </Box>
    </Dialog>
  );
};

export default ProjectModal;
