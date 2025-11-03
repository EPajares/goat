import { useState } from "react";

import { ICON_NAME } from "@p4b/ui/components/Icon";

import { useTranslation } from "@/i18n/client";

import type { OrganizationMember } from "@/lib/validations/organization";

import { OrgMemberActions } from "@/types/common";

import type { PopperMenuItem } from "@/components/common/PopperMenu";
import type { TeamMember } from "@/lib/validations/team";

export const useMemberSettingsMoreMenu = (type: "organization" | "team") => {
  const { t } = useTranslation("common");
  const activeMemberMoreMenuOptions: PopperMenuItem[] = [
    // only for organization at the moment. todo: enable it also for team
    ...(type === "organization" ? [
    ] : []),
    {
      id: OrgMemberActions.DELETE,
      label: t("delete"),
      icon: ICON_NAME.TRASH,
      color: "error.main",
    },
  ];

  const pendingInvitationMoreMenuOptions: PopperMenuItem[] = [
    {
      id: OrgMemberActions.CANCEL_INVITATION,
      label: t("cancel_invitation"),
      icon: ICON_NAME.TRASH,
      color: "error.main",
    },
  ];

  const [activeMember, setActiveMember] = useState<OrganizationMember | TeamMember>();
  const [moreMenuState, setMoreMenuState] = useState<PopperMenuItem>();

  const closeMoreMenu = () => {
    setActiveMember(undefined);
    setMoreMenuState(undefined);
  };

  const openMoreMenu = (menuItem: PopperMenuItem, memberItem: OrganizationMember | TeamMember) => {
    setActiveMember(memberItem);
    setMoreMenuState(menuItem);
  };

  return {
    activeMemberMoreMenuOptions,
    pendingInvitationMoreMenuOptions,
    activeMember,
    moreMenuState,
    closeMoreMenu,
    openMoreMenu,
  };
};
