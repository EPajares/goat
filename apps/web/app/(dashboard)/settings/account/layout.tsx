"use client";

import { Box, Tab, Tabs } from "@mui/material";
import NextLink from "next/link";
import { usePathname } from "next/navigation";
import { useTranslation } from "react-i18next";

import { ICON_NAME, Icon } from "@p4b/ui/components/Icon";

import type { NavItem } from "@/types/common/navigation";

interface AccountLayoutProps {
  children: React.ReactNode;
}

const AccountLayout = (props: AccountLayoutProps) => {
  const pathname = usePathname();
  const { t } = useTranslation("common");

  const navigation: NavItem[] = [
    {
      link: "/profile",
      icon: ICON_NAME.USER,
      label: t("profile"),
      current: pathname?.includes("/profile"),
    },
    {
      link: "/preferences",
      icon: ICON_NAME.SETTINGS,
      label: t("preferences"),
      current: pathname?.includes("/preferences"),
    },
  ];
  return (
    <>
      <Tabs value={navigation.find((item) => item.current)?.link || false} variant="fullWidth" scrollButtons>
        {navigation.map((item) => (
          <Tab
            LinkComponent={NextLink}
            key={item.link}
            href={`/settings/account${item.link}`}
            icon={
              <Box sx={{ pr: 2 }}>
                <Icon iconName={item.icon} htmlColor="inherit" style={{ fontSize: 15 }} />
              </Box>
            }
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
        ))}
      </Tabs>
      {props.children}
    </>
  );
};

export default AccountLayout;
