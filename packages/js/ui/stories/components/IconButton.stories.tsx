import type { Meta, StoryObj } from "@storybook/react";

import ThemeProvider from "../../theme/ThemeProvider";
import { useDarkMode } from "storybook-dark-mode";
import { Icon, ICON_NAME } from "../../components/Icon";
import { IconButton } from "@mui/material";

const meta: Meta<typeof IconButton> = {
  component: IconButton,
  tags: ["autodocs"],
  argTypes: {
    color: {
      options: [
        "primary",
        "secondary",
        "error",
        "info",
        "success",
        "warning",
        "default",
      ],
      control: { type: "select" },
    },
    disabled: {
      control: { type: "boolean" },
    },
    size: {
      options: ["small", "medium", "large"],
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
type Story = StoryObj<typeof IconButton>;

export const Default: Story = {
  args: {
    color: "primary",
    size: "medium",
  },
  render: (args) => {
    const { ...rest } = args;
    return (
      <IconButton {...rest}>
        <Icon iconName={ICON_NAME.LAYERS} fontSize="inherit" />
      </IconButton>
    );
  },
  parameters: {
    design: {
      type: "figma",
      url: "https://www.figma.com/file/tu6pPILBRSUuy3Hbu8Lphk/Goat-3.0?type=design&node-id=6543-36744&t=m1TtlHDKRmJk5wCK-0",
    },
  },
};
