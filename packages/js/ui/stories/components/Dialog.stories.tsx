import type { Meta, StoryObj } from "@storybook/react";
import { useState } from "react";

import ThemeProvider from "../../theme/ThemeProvider";
import { useDarkMode } from "storybook-dark-mode";
import {
  Dialog,
  Button,
  DialogTitle,
  DialogActions,
  DialogContent,
  DialogContentText,
} from "@mui/material";

const meta: Meta<typeof Dialog> = {
  component: Dialog,
  tags: ["autodocs"],
  argTypes: {},
  decorators: [
    (Story) => (
      <ThemeProvider
        settings={{
          mode: useDarkMode() ? "dark" : "light",
        }}
      >
        <Story />
      </ThemeProvider>
    ),
  ],
};

export default meta;
type Story = StoryObj<typeof Dialog>;

export const Default: Story = {
  args: {},
  render: () => {
    // eslint-disable-next-line react-hooks/rules-of-hooks
    const [open, setOpen] = useState(false);

    const handleClickOpen = () => {
      setOpen(true);
    };

    const handleClose = () => {
      setOpen(false);
    };

    return (
      <div>
        <Button variant="outlined" onClick={handleClickOpen}>
          Remove User
        </Button>
        <Dialog
          open={open}
          onClose={handleClose}
          aria-labelledby="alert-dialog-title"
          aria-describedby="alert-dialog-description"
        >
          <DialogTitle id="alert-dialog-title">Attention</DialogTitle>
          <DialogContent>
            <DialogContentText id="alert-dialog-description">
              Are you sure you want to remove the user.
            </DialogContentText>
          </DialogContent>
          <DialogActions>
            <Button onClick={handleClose} autoFocus>
              Remove
            </Button>
          </DialogActions>
        </Dialog>
      </div>
    );
  },
  parameters: {
    design: {
      type: "figma",
      url: "https://www.figma.com/file/tu6pPILBRSUuy3Hbu8Lphk/Root_Goat-3.0?type=design&node-id=6583-46474&mode=design&t=9dTs5ps2RVfIB1th-0",
    },
  },
};
