import type { Meta, StoryObj } from "@storybook/react";

import ThemeProvider from "../../theme/ThemeProvider";
import { useDarkMode } from "storybook-dark-mode";
import { Divider } from "@mui/material";

const meta: Meta<typeof Divider> = {
  component: Divider,
  tags: ["autodocs"],
  argTypes: {
    variant: {
      options: ["fullWidth", "inset", "middle"],
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
type Story = StoryObj<typeof Divider>;

export const Default: Story = {
  args: { variant: "fullWidth" },
  render: (args) => {
    const { variant } = args;
    return <Divider variant={variant} />;
  },
  parameters: {
    design: {
      type: "figma",
      url: "https://www.figma.com/file/tu6pPILBRSUuy3Hbu8Lphk/Root_Goat-3.0?type=design&node-id=6583-46474&mode=design&t=9dTs5ps2RVfIB1th-0",
    },
  },
};
