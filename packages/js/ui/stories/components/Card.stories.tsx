import type { Meta, StoryObj } from "@storybook/react";

import ThemeProvider from "../../theme/ThemeProvider";
import { Card, CardMedia, CardContent, Typography } from "@mui/material";
import { useDarkMode } from "storybook-dark-mode";

const meta: Meta<typeof Card> = {
  component: Card,
  tags: ["autodocs"],
  argTypes: {},
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
type Story = StoryObj<typeof Card>;

export const Default: Story = {
  args: {
    children: "Card",
  },
  render: () => {
    return (
      <Card sx={{ width: "280px" }}>
        <CardMedia
          sx={{ height: 100 }}
          image="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSQy9x3wyV5OWYWA8XxBJKMlH2QvuSSOIdOItRK1jgXSQ&s"
          title="green iguana"
        />
        <CardContent>
          <Typography variant="body2" color="secondary">
            Test Body
          </Typography>
        </CardContent>
      </Card>
    );
  },
  parameters: {
    design: {
      type: "figma",
      url: "https://www.figma.com/file/tu6pPILBRSUuy3Hbu8Lphk/Root_Goat-3.0?type=design&node-id=6583-46474&mode=design&t=9dTs5ps2RVfIB1th-0",
    },
  },
};
