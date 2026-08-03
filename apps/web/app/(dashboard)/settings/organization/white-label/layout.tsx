"use client";

import { Box, Tab, Tabs, Tooltip } from "@mui/material";
import NextLink from "next/link";
import { usePathname } from "next/navigation";
import { forwardRef, type ReactNode } from "react";
import { useTranslation } from "react-i18next";

import { ICON_NAME, Icon } from "@p4b/ui/components/Icon";

interface WhiteLabelTab {
  link: string;
  icon: ICON_NAME;
  label: string;
  current: boolean;
  disabled?: boolean;
  tooltip?: string;
}

interface WhiteLabelLayoutProps {
  children: React.ReactNode;
}

/**
 * Tooltip wrapper for a disabled <Tab>.
 *
 * MUI's <Tabs> clones its children and injects Tab-specific props
 * (textColor, indicator, fullWidth, selectionFollowsFocus, etc.). When the
 * direct child is a <span> instead of a <Tab>, those props leak onto the
 * DOM element and React warns. We swallow the known Tabs-injected props
 * here and forward only valid HTML attributes to the span.
 *
 * The forwardRef is required because <Tooltip> attaches a ref to its child
 * to anchor the popper.
 */
const DisabledTabSlot = forwardRef<
  HTMLSpanElement,
  { children: ReactNode } & Record<string, unknown>
>(function DisabledTabSlot({ children, ...rest }, ref) {
  const {
    // MUI Tabs internals — strip these so they don't leak onto the DOM:
    textColor: _textColor,
    indicator: _indicator,
    fullWidth: _fullWidth,
    selectionFollowsFocus: _selectionFollowsFocus,
    onChange: _onChange,
    // Forward everything else (e.g. aria-* and tooltip event handlers).
    ...domProps
  } = rest;
  return (
    <span ref={ref} {...domProps} style={{ flex: 1, display: "flex" }}>
      {children as ReactNode}
    </span>
  );
});

const WhiteLabelLayout = (props: WhiteLabelLayoutProps) => {
  const children = props.children;
  const pathname = usePathname();
  const { t } = useTranslation("common");

  const navigation: WhiteLabelTab[] = [
    {
      link: "/domains",
      icon: ICON_NAME.GLOBE,
      label: t("white_label_custom_domains_title"),
      current: pathname?.includes("/domains"),
    },
    {
      link: "/analytics",
      icon: ICON_NAME.CHART,
      label: t("analytics"),
      current: pathname?.includes("/analytics"),
    },
  ];

  return (
    <>
      <Tabs
        value={navigation.find((item) => item.current)?.link || false}
        variant="fullWidth"
        scrollButtons
      >
        {navigation.map((item) => {
          const icon = (
            <Box sx={{ pr: 2 }}>
              <Icon iconName={item.icon} htmlColor="inherit" style={{ fontSize: 15 }} />
            </Box>
          );

          // Disabled-with-tooltip branch: build a Tab that doesn't take
          // LinkComponent/href (it shouldn't navigate), wrap it in a slot
          // that strips MUI's Tabs-injected props from the host span, then
          // wrap that in a Tooltip.
          if (item.disabled) {
            const disabledTab = (
              <Tab
                icon={icon}
                iconPosition="start"
                label={item.label}
                value={item.link}
                disabled
                sx={{ width: "100%", justifyContent: "center" }}
              />
            );
            const slot = <DisabledTabSlot>{disabledTab}</DisabledTabSlot>;
            return item.tooltip ? (
              <Tooltip key={item.link} title={item.tooltip} placement="top" arrow>
                {slot}
              </Tooltip>
            ) : (
              <DisabledTabSlot key={item.link}>{disabledTab}</DisabledTabSlot>
            );
          }

          // Normal navigable tab.
          return (
            <Tab
              LinkComponent={NextLink}
              key={item.link}
              href={`/settings/organization/white-label${item.link}`}
              icon={icon}
              iconPosition="start"
              label={item.label}
              value={item.link}
              sx={{
                ...(item.current && {
                  color: "primary.main",
                  fontWeight: "bold",
                }),
              }}
            />
          );
        })}
      </Tabs>
      {children}
    </>
  );
};

export default WhiteLabelLayout;
