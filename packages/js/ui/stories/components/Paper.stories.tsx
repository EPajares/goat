import type { Meta, StoryObj } from "@storybook/react";

import ThemeProvider from "../../theme/ThemeProvider";
import { useDarkMode } from "storybook-dark-mode";
import { Paper, Box } from "@mui/material";

const meta: Meta<typeof Paper> = {
  component: Paper,
  tags: ["autodocs"],
  argTypes: {
    variant: {
      options: ['elevation', 'outlined'],
      control: { type: "select" }
    },
    elevation: {
      control: { type: "number" },
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
type Story = StoryObj<typeof Paper>;

export const Default: Story = {
  args: { elevation: 2, variant: "elevation" },
  render: (args) => {
    const { elevation, variant } = args;
    return (
      <Box
        sx={{
          display: "flex",
          flexWrap: "wrap",
          "& > :not(style)": {
            m: 1,
            width: 128,
            height: 128,
          },
        }}
      >
        <Paper elevation={elevation} variant={variant}/>
      </Box>
    );
  },
  parameters: {
    design: {
      type: "figma",
      url: "https://www.figma.com/file/tu6pPILBRSUuy3Hbu8Lphk/Root_Goat-3.0?type=design&node-id=6583-46474&mode=design&t=9dTs5ps2RVfIB1th-0",
    },
  },
};
