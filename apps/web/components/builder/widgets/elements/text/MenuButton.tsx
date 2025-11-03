import { ToggleButton, type ToggleButtonProps, styled, toggleButtonClasses } from "@mui/material";
import type { ReactNode, Ref } from "react";

// your centralized Icon
import type { ICON_NAME } from "@p4b/ui/components/Icon";
import { Icon } from "@p4b/ui/components/Icon";

// import MenuButtonTooltip, { type MenuButtonTooltipProps } from "./MenuButtonTooltip";

export interface MenuButtonProps extends Omit<ToggleButtonProps, "ref" | "children" | "value"> {
  // tooltipLabel: MenuButtonTooltipProps["label"];
  //   tooltipShortcutKeys?: MenuButtonTooltipProps["shortcutKeys"];
  iconName?: ICON_NAME;
  children?: ReactNode;
  value: ToggleButtonProps["value"];
  ref?: Ref<HTMLButtonElement>;
}

const Root = styled("span")(() => ({
  [`& .${toggleButtonClasses.root}`]: {
    border: "none",
    padding: 5,
  },
}));

export default function MenuButton({
  // tooltipLabel,
  //   tooltipShortcutKeys,
  iconName,
  children,
  value,
  ref,
  ...toggleButtonProps
}: MenuButtonProps) {
  const renderContent =
    children ??
    (iconName ? (
      <Icon iconName={iconName} fontSize="small" color={toggleButtonProps.selected ? "primary" : "inherit"} />
    ) : null);

  return (
    <Root>
      {/* <MenuButtonTooltip label={tooltipLabel} shortcutKeys={tooltipShortcutKeys}> */}
      <ToggleButton ref={ref} size="small" value={value} {...toggleButtonProps}>
        {renderContent}
      </ToggleButton>
      {/* </MenuButtonTooltip> */}
    </Root>
  );
}
