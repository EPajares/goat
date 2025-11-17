import type { Meta, StoryObj } from "@storybook/react";

import ThemeProvider from "../../theme/ThemeProvider";
import { useDarkMode } from "storybook-dark-mode";
import { TextField } from "@mui/material";

const meta: Meta<typeof TextField> = {
  component: TextField,
  tags: ["autodocs"],
  argTypes: {
    variant: {
      options: ["outlined", "filled", "standard"],
      control: { type: "select" },
    },
    size: {
      options: ["small", "medium"],
      control: { type: "select" },
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
type Story = StoryObj<typeof TextField>;

export const Default: Story = {
  args: { variant: "outlined", label: "Outlined", size: "medium" },
  render: (args) => {
    const { variant, label, size } = args;
    return <TextField variant={variant} size={size} label={label}/>;
  },
  parameters: {
    design: {
      type: "figma",
      url: "https://www.figma.com/file/tu6pPILBRSUuy3Hbu8Lphk/Root_Goat-3.0?type=design&node-id=6583-46474&mode=design&t=9dTs5ps2RVfIB1th-0",
    },
  },
};
