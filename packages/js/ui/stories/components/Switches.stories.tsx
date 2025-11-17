import type { Meta, StoryObj } from "@storybook/react";

import ThemeProvider from "../../theme/ThemeProvider";
import { useDarkMode } from "storybook-dark-mode";
import { Switch } from "@mui/material";

const meta: Meta<typeof Switch> = {
  component: Switch,
  tags: ["autodocs"],
  argTypes: {
    defaultChecked: {
      control: { type: "boolean" },
    },
    disabled: {
      control: { type: "boolean" },
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
type Story = StoryObj<typeof Switch>;

export const Default: Story = {
  args: {
    defaultChecked: true,
    disabled: false
  },
  render: (args) => {
    const { defaultChecked, disabled } = args;
    return <Switch  defaultChecked={defaultChecked} disabled={disabled}/>;
  },
  parameters: {
    design: {
      type: "figma",
      url: "https://www.figma.com/file/tu6pPILBRSUuy3Hbu8Lphk/Root_Goat-3.0?type=design&node-id=6583-46474&mode=design&t=9dTs5ps2RVfIB1th-0",
    },
  },
};
