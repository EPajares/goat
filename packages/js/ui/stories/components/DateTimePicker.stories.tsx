import type { Meta, StoryObj } from "@storybook/react";

import ThemeProvider from "../../theme/ThemeProvider";
import { useDarkMode } from "storybook-dark-mode";
import { DatePicker } from "@mui/x-date-pickers/DatePicker";
import dayjs from "dayjs";
import { DemoContainer } from "@mui/x-date-pickers/internals/demo";
import { AdapterDayjs } from "@mui/x-date-pickers/AdapterDayjs";
import { LocalizationProvider } from "@mui/x-date-pickers/LocalizationProvider";

const meta: Meta<typeof DatePicker> = {
  component: DatePicker,
  tags: ["autodocs"],
  argTypes: {
    defaultValue: {
      control: { type: "object" },
    },
    disabled: {
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
type Story = StoryObj<typeof DatePicker>;

export const Default: Story = {
  args: {
    defaultValue: dayjs("2022-04-17"),
    disabled: false,
  },
  render: (args) => {
    const { defaultValue, disabled } = args;
    return (
      <LocalizationProvider dateAdapter={AdapterDayjs}>
        <DemoContainer components={["DatePicker"]}>
          <DatePicker defaultValue={defaultValue} disabled={disabled} />
        </DemoContainer>
      </LocalizationProvider>
    );
  },
  parameters: {
    design: {
      type: "figma",
      url: "https://www.figma.com/file/tu6pPILBRSUuy3Hbu8Lphk/Root_Goat-3.0?type=design&node-id=6583-46474&mode=design&t=9dTs5ps2RVfIB1th-0",
    },
  },
};
