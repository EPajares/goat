import React, { useState } from "react";
import type { Meta, StoryObj } from "@storybook/react";

import ThemeProvider from "../../theme/ThemeProvider";
import { useDarkMode } from "storybook-dark-mode";
import { Snackbar, Button } from "@mui/material";

const meta: Meta<typeof Snackbar> = {
  component: Snackbar,
  tags: ["autodocs"],
  argTypes: {
    anchorOrigin: {
      control: "object"
    },
  },
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
type Story = StoryObj<typeof Snackbar>;

export const Default: Story = {
  args: {
    anchorOrigin: {
      vertical: "top",
      horizontal: "center",
    },
  },
  render: (args) => {
    const { anchorOrigin } = args;
    // eslint-disable-next-line react-hooks/rules-of-hooks
    const [open, setOpen] = useState(false);

    const handleClick = () => {
      setOpen(true);
    };

    const handleClose = (_?: React.SyntheticEvent | Event, reason?: string) => {
      if (reason === "clickaway") {
        return;
      }

      setOpen(false);
    };

    return (
      <div>
        <Button variant="outlined" onClick={handleClick}>
          Open success snackbar
        </Button>
        <Snackbar
          open={open}
          anchorOrigin={anchorOrigin}
          autoHideDuration={6000}
          onClose={handleClose}
          message={`This is snackbar message on the ${anchorOrigin?.vertical}-${anchorOrigin?.horizontal}`}
        />
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
