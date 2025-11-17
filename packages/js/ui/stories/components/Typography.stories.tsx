import type { Meta, StoryObj } from "@storybook/react";

import ThemeProvider from "../../theme/ThemeProvider";
import { useDarkMode } from "storybook-dark-mode";
import { Typography } from "@mui/material";

const meta: Meta<typeof Typography> = {
  component: Typography,
  tags: ["autodocs"],
  argTypes: {
    variant: {
      options: [
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "subtitle1",
        "subtitle2",
        "body1",
        "body2",
        "button",
        "caption",
        "overline",
      ],
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
type Story = StoryObj<typeof Typography>;

export const Default: Story = {
  args: {
    children: "This is an error alert — check it out!",
    variant: "h1",
  },
  render: (args) => {
    const { children, variant } = args;
    return <Typography variant={variant}>{children}</Typography>;
  },
  parameters: {
    design: {
      type: "figma",
      url: "https://www.figma.com/file/tu6pPILBRSUuy3Hbu8Lphk/Root_Goat-3.0?type=design&node-id=6583-46474&mode=design&t=9dTs5ps2RVfIB1th-0",
    },
  },
};
