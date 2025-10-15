import type { Meta, StoryObj } from "@storybook/react";

import ThemeProvider from "../../theme/ThemeProvider";
import Button from "@mui/material/Button";
import { useDarkMode } from "storybook-dark-mode";
import { Icon, ICON_NAME } from "../../components/Icon";

const meta: Meta<typeof Button> = {
  component: Button,
  tags: ["autodocs"],
  argTypes: {
    variant: {
      options: ["text", "contained", "outlined"],
      control: { type: "select" },
    },
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
    startIcon: {
      options: ICON_NAME,
      control: { type: "select" },
    },
    endIcon: {
      options: ICON_NAME,
      control: { type: "select" },
    },
    disabled: {
      control: { type: "boolean" },
    },
    size: {
      options: ["small", "medium", "large"],
      control: { type: "select" },
    },
    fullWidth: {
      control: { type: "boolean" },
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
type Story = StoryObj<typeof Button>;

export const Default: Story = {
  args: {
    children: "Button",
    color: "primary",
    variant: "contained",
    size: "medium",
  },
  render: (args) => {
    const { startIcon, endIcon, ...rest } = args;
    return (
      <Button
        startIcon={
          startIcon ? (
            <Icon iconName={startIcon as ICON_NAME} fontSize="inherit" />
          ) : undefined
        }
        endIcon={
          endIcon ? (
            <Icon iconName={endIcon as ICON_NAME} fontSize="inherit" />
          ) : undefined
        }
        {...rest}
      />
    );
  },
  parameters: {
    design: {
      type: "figma",
      url: "https://www.figma.com/file/tu6pPILBRSUuy3Hbu8Lphk/Goat-3.0?type=design&node-id=6543-36744&t=m1TtlHDKRmJk5wCK-0",
    },
  },
};
