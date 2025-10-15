import type { TooltipProps } from "@mui/material";
import { Button, Menu, MenuItem, Tooltip, Typography } from "@mui/material";
import React from "react";

import { ICON_NAME, Icon } from "./Icon";

export type LanguageSelectProps<Language extends string = string> = {
  /** Example { "en": "English", "de": "Deutsch" } */
  languages: Record<Language, string>;
  /** Example "en" or "de" */
  selected: Language;
  onLanguageChange(language: Language): void;
  toolTipProps?: Omit<TooltipProps, "children">;
  size?: "small" | "medium" | "large";
};

export default function LanguageSelect<Language extends string = string>(
  props: LanguageSelectProps<Language>
) {
  const { languages, selected, onLanguageChange, toolTipProps } = props;
  const [anchorEl, setAnchorEl] = React.useState<HTMLButtonElement | undefined>(undefined);
  const open = Boolean(anchorEl);
  const handleClose = () => {
    setAnchorEl(undefined);
  };
  return (
    <>
      <Tooltip title={toolTipProps?.title ? toolTipProps.title : null} {...toolTipProps}>
        <Button
          color="secondary"
          variant="text"
          size={props.size || "small"}
          startIcon={<Icon iconName={ICON_NAME.LANGUAGE} fontSize="inherit" />}
          onClick={(event: React.MouseEvent<HTMLButtonElement>) => {
            setAnchorEl(event.currentTarget);
          }}
          data-ga-event-category="header"
          data-ga-event-action="language"
          aria-haspopup="true"
          aria-owns={open ? "language-menu" : undefined}
          aria-expanded={open ? "true" : undefined}>
          {languages[selected]}
        </Button>
      </Tooltip>
      <Menu id="language-menu" anchorEl={anchorEl} open={open} onClose={handleClose} onClick={handleClose}>
        {Object.entries(languages).map(([language, languageName]) => (
          <MenuItem
            component="a"
            data-no-link="true"
            key={language}
            selected={language === selected}
            onClick={() => {
              onLanguageChange(language as Language);
            }}
            lang={language}>
            <Typography fontFamily="'Mulish', sans-serif">{languageName as string}</Typography>
          </MenuItem>
        ))}
      </Menu>
    </>
  );
}
