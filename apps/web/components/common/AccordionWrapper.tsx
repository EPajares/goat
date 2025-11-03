import { Accordion, AccordionDetails, AccordionSummary } from "@mui/material";
import React from "react";
import type { ReactNode } from "react";

import { ICON_NAME, Icon } from "@p4b/ui/components/Icon";

const AccordionWrapper = ({
  header,
  body,
  expanded,
  disableGutters = false,
  boxShadow = "0px 2px 10px 0px rgba(58, 53, 65, 0.1)",
  backgroundColor,
  accordionSxProps,
  onChange,
}: {
  header: ReactNode;
  body: ReactNode;
  expanded?: boolean;
  disableGutters?: boolean;
  boxShadow?: string | undefined;
  backgroundColor?: string | undefined;
  accordionSxProps?: object;
  onChange?: (event: React.SyntheticEvent, newExpanded: boolean) => void;
}) => {
  return (
    <Accordion
      square={true}
      expanded={expanded}
      sx={{
        boxShadow,
        backgroundColor,
        ...accordionSxProps,
      }}
      onChange={onChange}
      disableGutters={disableGutters}>
      <AccordionSummary
        sx={{
          my: 0,
          py: 0,
        }}
        expandIcon={<Icon iconName={ICON_NAME.CHEVRON_DOWN} style={{ fontSize: "15px" }} />}
        aria-controls="panel1a-content">
        {header}
      </AccordionSummary>
      <AccordionDetails sx={{ mt: 0, p: 0 }}>{body}</AccordionDetails>
    </Accordion>
  );
};

export default AccordionWrapper;
