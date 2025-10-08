import { LoadingButton } from "@mui/lab";
import type { SelectChangeEvent } from "@mui/material";
import {
  Avatar,
  Box,
  Button,
  Dialog,
  DialogContent,
  DialogContentText,
  DialogTitle,
  FormControl,
  InputLabel,
  ListItemAvatar,
  ListItemText,
  MenuItem,
  Select,
  Stack,
  Typography,
  useTheme,
} from "@mui/material";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { toast } from "react-toastify";

import { createTeamMember } from "@/lib/api/teams";

interface TeamMemberInviteDialogProps {
  onClose: () => void;
  open: boolean;
  onInvite?: () => void;
  teamId: string;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  members: any[];
}

const TeamMemberInviteModal: React.FC<TeamMemberInviteDialogProps> = ({ open, onClose, members, teamId }) => {
  const theme = useTheme();
  const { t } = useTranslation(["common"]);

  const [isBusy, setIsBusy] = useState(false);
  const [selectedMember, setSelectedMember] = useState("");
  const onSelectedMemberChange = (event: SelectChangeEvent) => {
    setSelectedMember(event.target.value as string);
  };

  const onTeamMemberInvite = async () => {
    try {
      setIsBusy(true);
      await createTeamMember(teamId, selectedMember);
      toast.success(t("common:member_added"));
    } catch {
      toast.error(t("common:error_adding_member"));
    } finally {
      setIsBusy(false);
      setSelectedMember("");
      onClose();
    }
  };

  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="sm">
      <DialogTitle>{t("common:add_member")}</DialogTitle>
      <DialogContent sx={{ pb: 2 }}>
        <DialogContentText>{t("common:select_an_organization_member")}</DialogContentText>
        <Box>
          <Stack
            spacing={theme.spacing(6)}
            sx={{
              mt: 4,
            }}
          />
          <FormControl fullWidth>
            <InputLabel id="demo-simple-select-disabled-label">{t("member")}</InputLabel>
            <Select
              value={selectedMember}
              label={t("common:member")}
              size="medium"
              fullWidth
              sx={{
                "& .MuiSelect-select": {
                  ...(selectedMember ? { py: 1 } : {}),
                },
              }}
              onChange={onSelectedMemberChange}>
              {members.map((member) => (
                <MenuItem key={member.id} value={member.id}>
                  <Stack direction="row" alignItems="center">
                    <ListItemAvatar>
                      <Avatar alt={`${member.firstname} ${member.lastname}`} src={member.avatar} />
                    </ListItemAvatar>
                    <ListItemText
                      primary={`${member.firstname} ${member.lastname}`}
                      secondary={member.email}
                    />
                  </Stack>
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          <Stack direction="row" justifyContent="flex-end" alignItems="center" sx={{ mt: 8, mb: 0 }}>
            <Button onClick={onClose} variant="text" sx={{ borderRadius: 0 }}>
              <Typography variant="body2" fontWeight="bold">
                {t("common:cancel")}
              </Typography>
            </Button>
            <LoadingButton type="submit" variant="text" loading={isBusy} disabled={isBusy || !selectedMember}>
              <Typography variant="body2" fontWeight="bold" color="inherit" onClick={onTeamMemberInvite}>
                {t("common:add")}
              </Typography>
            </LoadingButton>
          </Stack>
        </Box>
      </DialogContent>
    </Dialog>
  );
};

export default TeamMemberInviteModal;
