import { useState } from "react";
import type { Meta, StoryObj } from "@storybook/react";

import ThemeProvider from "../../theme/ThemeProvider";
import { useDarkMode } from "storybook-dark-mode";
import { Select, FormControl, InputLabel, MenuItem } from "@mui/material";
import type { SelectChangeEvent } from "@mui/material";

const meta: Meta<typeof Select> = {
  component: Select,
  tags: ["autodocs"],
  argTypes: {
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
type Story = StoryObj<typeof Select>;

export const Default: Story = {
  args: {variant: "outlined", label: "Outlined", size: "medium"  },
  render: (args) => {
    // eslint-disable-next-line react-hooks/rules-of-hooks
    const [age, setAge] = useState("");

    const handleChange = (event: SelectChangeEvent) => {
      setAge(event.target.value as string);
    };
    const { label, size } = args;
    return (
      <FormControl fullWidth size={size}>
        <InputLabel id="demo-simple-select-label">{label}</InputLabel>
        <Select
          labelId="demo-simple-select-label"
          id="demo-simple-select"
          value={age}
          label="Age"
          onChange={handleChange}
        >
          <MenuItem value={10}>Ten</MenuItem>
          <MenuItem value={20}>Twenty</MenuItem>
          <MenuItem value={30}>Thirty</MenuItem>
        </Select>
      </FormControl>
    );
  },
  parameters: {
    design: {
      type: "figma",
      url: "https://www.figma.com/file/tu6pPILBRSUuy3Hbu8Lphk/Root_Goat-3.0?type=design&node-id=6583-46474&mode=design&t=9dTs5ps2RVfIB1th-0",
    },
  },
};
