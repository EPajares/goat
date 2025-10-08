import { zodResolver } from "@hookform/resolvers/zod";
import { LoadingButton } from "@mui/lab";
import {
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { useTranslation } from "react-i18next";
import { toast } from "react-toastify";

import { createProjectScenario, updateProjectScenario } from "@/lib/api/projects";
import { type PostScenario, type Scenario, postScenarioSchema } from "@/lib/validations/scenario";

interface ScenarioProps {
  open: boolean;
  onClose?: () => void;
  projectId: string;
  scenario: Scenario | undefined;
  editType?: "edit" | "create";
}

const ScenarioModal: React.FC<ScenarioProps> = ({ open, onClose, projectId, editType, scenario }) => {
  const { t } = useTranslation("common");
  const [isBusy, setIsBusy] = useState(false);
  const {
    handleSubmit,
    register,
    reset,
    formState: { errors, isValid },
  } = useForm<PostScenario>({
    mode: "onChange",
    resolver: zodResolver(postScenarioSchema),
    defaultValues: {
      name: scenario?.name,
    },
  });

  const handleOnClose = () => {
    setIsBusy(false);
    reset();
    onClose && onClose();
  };

  const onSubmit = async (data: PostScenario) => {
    try {
      setIsBusy(true);
      if (editType === "edit" && scenario?.id) {
        await updateProjectScenario(projectId, scenario?.id, data);
        toast.success(t("scenario_updated_successfully"));
      } else {
        await createProjectScenario(projectId, data);
        toast.success(t("scenario_created_successfully"));
      }
      handleOnClose();
    } catch (error) {
      if (editType === "edit") {
        toast.error(t("error_updating_scenario"));
      } else {
        toast.error(t("error_creating_scenario"));
      }
    } finally {
      handleOnClose();
    }
  };

  return (
    <>
      <Dialog open={open} onClose={handleOnClose} fullWidth maxWidth="sm">
        <DialogTitle>{editType === "edit" ? t("edit_scenario") : t("create_scenario")}</DialogTitle>
        <DialogContent>
          <Box sx={{ mt: 1, maxHeight: "500px" }} component="form" onSubmit={handleSubmit(onSubmit)}>
            <Stack spacing={4}>
              <TextField
                fullWidth
                label={t("name")}
                {...register("name")}
                error={!!errors.name}
                helperText={errors.name?.message}
              />
            </Stack>
          </Box>
        </DialogContent>
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
              loading={isBusy}
              disabled={!isValid}
              variant="contained"
              color="primary"
              onClick={handleSubmit(onSubmit)}>
              {editType === "edit" ? t("update") : t("create")}
            </LoadingButton>
          </Stack>
        </DialogActions>
      </Dialog>
    </>
  );
};

export default ScenarioModal;
