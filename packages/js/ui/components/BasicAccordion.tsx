import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import Accordion from "@mui/material/Accordion";
import AccordionDetails from "@mui/material/AccordionDetails";
import AccordionSummary from "@mui/material/AccordionSummary";
import Typography from "@mui/material/Typography";
import type { ReactNode } from "react";

export type BasicAccordionTypes = {
  title: string;
  children: NonNullable<ReactNode>;
  variant?: "primary" | "secondary";
};

export default function BasicAccordion(props: BasicAccordionTypes) {
  const { children, title, variant = "primary" } = props;

  const expandIconColor = variant === "secondary" ? "secondary" : "inherit";
  return (
    <div>
      <Accordion>
        <AccordionSummary
          expandIcon={<ExpandMoreIcon color={expandIconColor} />}
          aria-controls="panel1a-content"
          id="panel1a-header"
        >
          <Typography>{title}</Typography>
        </AccordionSummary>
        <AccordionDetails>{children}</AccordionDetails>
      </Accordion>
    </div>
  );
}
