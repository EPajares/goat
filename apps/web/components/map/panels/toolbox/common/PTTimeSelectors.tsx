import { Stack } from "@mui/material";
import React from "react";
import { useTranslation } from "react-i18next";

import TimePicker from "@p4b/ui/components/TimePicker";

import type { SelectorItem } from "@/types/map/common";

import FormLabelHelper from "@/components/common/FormLabelHelper";
import Selector from "@/components/map/panels/common/Selector";

interface PTTimeSelectorsProps {
  setPTDay: (item: SelectorItem) => void;
  ptDays: SelectorItem[];
  ptDay: SelectorItem | undefined;
  ptStartTime: number | undefined;
  setPTStartTime: (time: number) => void;
  ptEndTime: number | undefined;
  setPTEndTime: (time: number) => void;
  isPTValid: boolean;
}

const PTTimeSelectors: React.FC<PTTimeSelectorsProps> = ({
  ptDay,
  setPTDay,
  ptDays,
  ptStartTime,
  setPTStartTime,
  ptEndTime,
  setPTEndTime,
  isPTValid,
}) => {
  const { t } = useTranslation("common");

  return (
    <Stack spacing={2}>
      <Selector
        selectedItems={ptDay}
        setSelectedItems={(item: SelectorItem[] | SelectorItem | undefined) => {
          setPTDay(item as SelectorItem);
        }}
        items={ptDays}
        label={t("pt_day")}
        tooltip={t("pt_day_tooltip")}
      />
      <Stack>
        <FormLabelHelper label={t("pt_start_time")} color="inherit" tooltip={t("pt_start_time_tooltip")} />
        <TimePicker
          time={ptStartTime || 25200}
          onChange={(time) => {
            setPTStartTime(time);
          }}
          error={!isPTValid}
        />
      </Stack>
      <Stack>
        <FormLabelHelper label={t("pt_end_time")} color="inherit" tooltip={t("pt_end_time_tooltip")} />
        <TimePicker
          time={ptEndTime || 32400}
          onChange={(time) => {
            setPTEndTime(time);
          }}
          errorMessage={!isPTValid ? t("pt_end_time_error") : ""}
        />
      </Stack>
    </Stack>
  );
};

export default PTTimeSelectors;
