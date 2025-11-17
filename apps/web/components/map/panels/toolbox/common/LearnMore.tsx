import { Tooltip, styled, useTheme } from "@mui/material";
import React from "react";
import { useTranslation } from "react-i18next";

import { ICON_NAME, Icon } from "@p4b/ui/components/Icon";

import { DOCS_URL, DOCS_VERSION } from "@/lib/constants";

const HoverSpan = styled("span")<{ hoverColor: string }>`
  cursor: pointer;
  margin-left: 5px;
  color: inherit;
  transition: color 0.3s ease;

  &:hover {
    color: ${(props) => props.hoverColor};
  }
`;
interface LearnMoreProps {
  docsPath: string;
}

const LearnMore: React.FC<LearnMoreProps> = ({ docsPath }) => {
  const theme = useTheme();
  const { t, i18n } = useTranslation("common");

  const lng = i18n.language === "de" ? "/de" : "";

  //TODO: Get this dynamically
  const docsVersion = `/${DOCS_VERSION}`;

  return (
    <Tooltip title={t("learn_more")} placement="top">
      <HoverSpan
        hoverColor={theme.palette.primary.main}
        onClick={() => window.open(`${DOCS_URL}${lng}${docsVersion}${docsPath}`, "_blank")}>
        <Icon
          iconName={ICON_NAME.BOOK}
          style={{
            fontSize: "12px",
          }}
        />
      </HoverSpan>
    </Tooltip>
  );
};

export default LearnMore;
