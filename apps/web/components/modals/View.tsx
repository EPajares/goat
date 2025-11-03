import { Button, Dialog, DialogActions, DialogContent, DialogTitle, Typography } from "@mui/material";

interface ViewModalProps {
  title: string;
  children?: React.ReactNode;
  open: boolean;
  closeText?: string;
  onClose?: () => void;
}

const ViewModal: React.FC<ViewModalProps> = ({ open, title, children, closeText, onClose }) => {
  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="md">
      <DialogTitle>{title}</DialogTitle>
      <DialogContent>{children}</DialogContent>
      <DialogActions
        disableSpacing
        sx={{
          pb: 2,
        }}>
        <Button onClick={onClose} variant="text">
          <Typography variant="body2" fontWeight="bold">
            {closeText || "Close"}
          </Typography>
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default ViewModal;
