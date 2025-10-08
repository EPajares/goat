import { LoadingButton } from "@mui/lab";
import {
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
  Typography,
} from "@mui/material";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { toast } from "react-toastify";

import {
  deleteInvitation as deleteOrganizationInvitation,
  deleteMember as deleteOrganizationMember,
} from "@/lib/api/organizations";
import { deleteMember as deleteTeamMember } from "@/lib/api/teams";
import { invitationStatusEnum } from "@/lib/validations/invitation";

import type { MemberDialogBaseProps } from "@/types/dashboard/settings";

interface DeleteMemberDialogProps extends MemberDialogBaseProps {
  disabled?: boolean;
  onDelete?: () => void;
  teamId?: string;
  organizationId?: string;
}

const DeleteMemberModal: React.FC<DeleteMemberDialogProps> = ({
  open,
  disabled,
  onClose,
  onDelete,
  member,
  organizationId,
  teamId,
}) => {
  const { t } = useTranslation("common");
  const [isBusy, setIsBusy] = useState(false);
  const handleDelete = async () => {
    try {
      setIsBusy(true);
      if (organizationId) {
        if (member.invitation_status === invitationStatusEnum.Enum.accepted) {
          await deleteOrganizationMember(organizationId, member.id);
        } else {
          await deleteOrganizationInvitation(organizationId, member.id);
        }
      } else if (teamId) {
        await deleteTeamMember(teamId, member.id);
      }
      toast.success(t("member_deleted_success"));
    } catch {
      toast.error(t("member_delete_error"));
    } finally {
      setIsBusy(false);
    }

    onDelete?.();
  };

  return (
    <Dialog open={open} onClose={onClose}>
      <DialogTitle>{t("delete_member")}</DialogTitle>
      <DialogContent>
        <DialogContentText>
          {t("delete_member_description")}
          <br />
          <b>{member?.email}</b>
        </DialogContentText>
      </DialogContent>
      <DialogActions
        disableSpacing
        sx={{
          pb: 2,
        }}>
        <Button onClick={onClose} variant="text" sx={{ borderRadius: 0 }}>
          <Typography variant="body2" fontWeight="bold">
            {t("cancel")}
          </Typography>
        </Button>
        <LoadingButton
          onClick={handleDelete}
          loading={isBusy}
          variant="text"
          color="error"
          disabled={disabled}
          sx={{ borderRadius: 0 }}>
          <Typography variant="body2" fontWeight="bold" color="inherit">
            {t("remove")}
          </Typography>
        </LoadingButton>
      </DialogActions>
    </Dialog>
  );
};

export default DeleteMemberModal;
