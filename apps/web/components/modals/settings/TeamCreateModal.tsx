import { zodResolver } from "@hookform/resolvers/zod";
import { LoadingButton } from "@mui/lab";
import {
  Box,
  Button,
  Dialog,
  DialogContent,
  DialogContentText,
  DialogTitle,
  Stack,
  TextField,
  Typography,
  useTheme,
} from "@mui/material";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { useTranslation } from "react-i18next";
import { toast } from "react-toastify";

import { createTeam } from "@/lib/api/teams";
import type { TeamBase } from "@/lib/validations/team";
import { teamBaseSchema } from "@/lib/validations/team";

interface TeamCreateDialogProps {
  onClose: () => void;
  open: boolean;
  onCreate?: () => void;
}

const TeamCreateModal: React.FC<TeamCreateDialogProps> = ({ open, onClose, onCreate }) => {
  const theme = useTheme();
  const { t } = useTranslation(["common"]);

  const [isBusy, setIsBusy] = useState(false);

  const { register, handleSubmit, reset, formState, getValues } = useForm<TeamBase>({
    mode: "onChange",
    resolver: zodResolver(teamBaseSchema),
  });

  const onTeamCreate = async () => {
    try {
      onCreate?.();
      setIsBusy(true);
      const payload = getValues();
      await createTeam(payload);
      toast.success(t("common:team_created_success"));
    } catch {
      toast.error(t("common:error_creating_team"));
    } finally {
      setIsBusy(false);
      reset();
      onClose();
    }
  };

  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="sm">
      <DialogTitle>{t("common:create_team")}</DialogTitle>
      <DialogContent sx={{ pb: 2 }}>
        <DialogContentText>{t("common:team_create_description")}</DialogContentText>
        <Box component="form" onSubmit={handleSubmit(onTeamCreate)}>
          <Stack
            spacing={theme.spacing(6)}
            sx={{
              mt: 4,
            }}>
            <TextField fullWidth required label={t("common:team_name")} {...register("name")} id="name" />
            <TextField
              fullWidth
              label={t("common:team_description")}
              {...register("description")}
              id="description"
            />
          </Stack>
          <Stack direction="row" justifyContent="flex-end" alignItems="center" sx={{ mt: 8, mb: 0 }}>
            <Button onClick={onClose} variant="text" sx={{ borderRadius: 0 }}>
              <Typography variant="body2" fontWeight="bold">
                {t("common:cancel")}
              </Typography>
            </Button>
            <LoadingButton type="submit" variant="text" disabled={!formState.isValid} loading={isBusy}>
              <Typography variant="body2" fontWeight="bold" color="inherit">
                {t("common:create")}
              </Typography>
            </LoadingButton>
          </Stack>
        </Box>
      </DialogContent>
    </Dialog>
  );
};

export default TeamCreateModal;
