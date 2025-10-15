import type { Meta, StoryObj } from "@storybook/react";

import ThemeProvider from "../../theme/ThemeProvider";
import { useDarkMode } from "storybook-dark-mode";
import { Alert } from "@mui/material";

const meta: Meta<typeof Alert> = {
  component: Alert,
  tags: ["autodocs"],
  argTypes: {
    severity: {
      options: ["error", "warning", "info", "success"],
      control: { type: "select" },
    }
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
type Story = StoryObj<typeof Alert>;

export const Default: Story = {
  args: {
    children: "This is an error alert — check it out!",
    severity: "error"
  },
  render: (args) => {
    const { severity, children, ...rest } = args;
    return <Alert severity={severity}>{children}</Alert>;
  },
  parameters: {
    design: {
      type: "figma",
      url: "https://www.figma.com/file/tu6pPILBRSUuy3Hbu8Lphk/Root_Goat-3.0?type=design&node-id=6583-46474&mode=design&t=9dTs5ps2RVfIB1th-0",
    },
  },
};
