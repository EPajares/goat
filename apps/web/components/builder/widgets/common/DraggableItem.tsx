import { useDraggable } from "@dnd-kit/core";
import { Card, CardHeader, Stack, Typography, useTheme } from "@mui/material";
import React from "react";

import { Icon } from "@p4b/ui/components/Icon";

import { useTranslation } from "@/i18n/client";

import type { WidgetTypes } from "@/lib/validations/widget";

import { iconMap } from "@/components/builder/widgets/common/WidgetIconMap";

export interface DraggableItemProps {
  widgetType: WidgetTypes;
  isDragging?: boolean;
}

export function Draggable(props) {
  const Element = props.element || "div";
  const { attributes, listeners, setNodeRef } = useDraggable({
    id: props.id,
  });

  return (
    <Element ref={setNodeRef} {...listeners} {...attributes}>
      {props.children}
    </Element>
  );
}

export const DraggableItem = ({ widgetType, isDragging }: DraggableItemProps) => {
  const { t } = useTranslation("common");
  const theme = useTheme();
  return (
    <Card
      sx={{
        cursor: isDragging ? "grabbing" : "grab",
        maxWidth: "130px",
        borderRadius: "6px",
      }}>
      <CardHeader
        sx={{
          px: 2,
          py: 4,
          ".MuiCardHeader-content": {
            width: "100%",
            color: isDragging ? theme.palette.primary.main : theme.palette.text.secondary,
          },
        }}
        title={
          <Stack
            direction="row"
            alignItems="center"
            justifyContent="space-between"
            spacing={2}
            style={{
              color: theme.palette.text.secondary,
            }}>
            <Typography variant="body2" fontWeight="bold" noWrap color="inherit">
              {t(widgetType)}
            </Typography>
            <Icon
              iconName={iconMap[widgetType]}
              style={{
                fontSize: "1.2rem",
                color: isDragging ? theme.palette.primary.main : "inherit",
              }}
            />
          </Stack>
        }
      />
    </Card>
  );
};
