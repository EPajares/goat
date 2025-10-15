import type { Meta, StoryObj } from "@storybook/react";

import ThemeProvider from "../../theme/ThemeProvider";
import { useDarkMode } from "storybook-dark-mode";
import { Icon, ICON_NAME } from "../../components/Icon";
import { Chip, Typography } from "@mui/material";

const meta: Meta<typeof Chip> = {
  component: Chip,
  tags: ["autodocs"],
  argTypes: {
    label: {
      control: { type: "text" },
    },
    variant: {
      options: ["filled", "outlined"],
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
type Story = StoryObj<typeof Chip>;

export const Default: Story = {
  args: {
    label: "Chip",
    variant: "filled"
  },
  render: (args) => {
    const { label, variant } = args;
    return <Chip label={label} variant={variant}/>;
  },
  parameters: {
    design: {
      type: "figma",
      url: "https://www.figma.com/file/tu6pPILBRSUuy3Hbu8Lphk/Root_Goat-3.0?type=design&node-id=6583-46474&mode=design&t=9dTs5ps2RVfIB1th-0",
    },
  },
};

export const WithIcon: Story = {
  args: {
    label: (
      <Typography sx={{ display: "flex", alignItems: "center", gap: "4px" }}>
        <Icon iconName={ICON_NAME.BUS} />
        Bus
      </Typography>
    ),
    variant: "outlined"
  },
  render: (args) => {
    const { label, variant } = args;
    return <Chip label={label} variant={variant}/>;
  },
  parameters: {
    design: {
      type: "figma",
      url: "https://www.figma.com/file/tu6pPILBRSUuy3Hbu8Lphk/Root_Goat-3.0?type=design&node-id=6583-46474&mode=design&t=9dTs5ps2RVfIB1th-0",
    },
  },
};
