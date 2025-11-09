import { useDroppable } from "@dnd-kit/core";
import {
  SortableContext,
  horizontalListSortingStrategy,
  verticalListSortingStrategy,
} from "@dnd-kit/sortable";
import { Box, IconButton, Stack, Typography, useTheme } from "@mui/material";
import { alpha } from "@mui/material";
import { useState } from "react";
import { useTranslation } from "react-i18next";

import { ICON_NAME, Icon } from "@p4b/ui/components/Icon";

import { setCollapsedPanels } from "@/lib/store/map/slice";
import type { BuilderPanelSchema, BuilderWidgetSchema, ProjectLayer } from "@/lib/validations/project";

import { useAppDispatch, useAppSelector } from "@/hooks/store/ContextHooks";

import ExpandCollapseButton from "@/components/builder/ExpandCollapsePanelButton";
import WidgetWrapper from "@/components/builder/widgets/WidgetWrapper";

export interface BuilderPanelSchemaWithPosition extends BuilderPanelSchema {
  orientation?: "horizontal" | "vertical";
  element: {
    top?: number;
    bottom?: number;
    left?: number;
    right?: number;
  };
}

interface ContainerProps {
  panel: BuilderPanelSchemaWithPosition; // A single panel
  projectLayers: ProjectLayer[];
  selected?: boolean; // Whether the panel is selected
  onClick?: () => void;
  onChangeOrder?: (panelId: string, position: "top" | "bottom" | "left" | "right") => void;
  onWidgetDelete?: (widgetId: string) => void;
  onWidgetUpdate?: (updatedWidget: BuilderWidgetSchema) => void;
  viewOnly?: boolean;
}

const ChangeOrderButton: React.FC<{
  onClick?: () => void;
  position: "left" | "top" | "bottom" | "right";
  iconName: ICON_NAME;
  isVisible: boolean;
}> = ({ onClick, position, iconName, isVisible }) => {
  const styles = {
    left: { position: "absolute", left: 0, top: "50%", transform: "translateY(-50%)" },
    top: { position: "absolute", top: 0, left: "50%", transform: "translateX(-50%)" },
    bottom: { position: "absolute", bottom: 0, left: "50%", transform: "translateX(-50%)" },
    right: { position: "absolute", right: 0, top: "50%", transform: "translateY(-50%)" },
  };

  return (
    <IconButton
      onClick={(e) => {
        e.stopPropagation();
        onClick?.();
      }}
      sx={{
        ...styles[position],
        pointerEvents: isVisible ? "all" : "none",
        opacity: isVisible ? 1 : 0,
        backgroundColor: "background.default",
        transform: isVisible ? styles[position].transform : `${styles[position].transform} scale(0.9)`,
        transition: "opacity 0.3s, transform 0.3s",
        cursor: "pointer",
        "&:hover": {
          backgroundColor: "background.default",
          color: "primary.main",
        },
        zIndex: 2,
      }}>
      <Icon iconName={iconName} htmlColor="inherit" fontSize="small" />
    </IconButton>
  );
};

export const Container: React.FC<ContainerProps> = ({
  panel,
  projectLayers,
  selected,
  onClick,
  onChangeOrder,
  onWidgetDelete,
  onWidgetUpdate,
  viewOnly,
}) => {
  const theme = useTheme();
  const { t } = useTranslation("common");
  const [isHovered, setIsHovered] = useState(false);
  const handleMouseEnter = () => setIsHovered(true);
  const handleMouseLeave = () => setIsHovered(false);
  const dispatch = useAppDispatch();
  const widgetIds = panel.widgets?.map((widget) => widget.id) || [];
  const sortingStrategy =
    panel.orientation === "horizontal" ? horizontalListSortingStrategy : verticalListSortingStrategy;

  const { setNodeRef } = useDroppable({
    id: panel.id,
    data: panel,
  });

  const collapsedPanels = useAppSelector((state) => state.map.collapsedPanels);
  const isCollapsed = !!collapsedPanels?.[panel.id];

  const handleToggleCollapse = () => {
    dispatch(setCollapsedPanels({ [panel.id]: !isCollapsed }));
  };

  const collapsedSize = 40; // width/height of mini sidebar

  return (
    // OUTER SECTION
    <Box
      ref={setNodeRef}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      onClick={onClick}
      sx={{
        ...panel.element,
        position: "absolute",
        ...(isHovered && !viewOnly && { outline: `1px solid ${theme.palette.primary.main}`, zIndex: 10 }),
        ...(selected && !viewOnly && { outline: `2px solid ${theme.palette.primary.main}`, zIndex: 11 }),
        cursor: "pointer",
        overflow: "hidden",
        transition: "all 0.3s",
        pointerEvents: "all",
        ...(viewOnly && {
          pointerEvents: "none",
          cursor: "default",
        }),
        ...(panel.config?.options?.style === "default" && {
          boxShadow: `rgba(0, 0, 0, 0.2) 0px 0px ${panel.config.appearance.shadow}px`,
        }),
        ...(isCollapsed && {
          ...(panel.orientation === "horizontal" && {
            height: collapsedSize,
          }),
          ...(panel.orientation === "vertical" && {
            width: collapsedSize,
          }),
        }),
      }}>
      {/* Conditional Buttons */}
      {!!panel.element?.left && !viewOnly && (
        <ChangeOrderButton
          onClick={() => onChangeOrder?.(panel.id, "left")}
          position="left"
          iconName={ICON_NAME.CHEVRON_LEFT}
          isVisible={isHovered}
        />
      )}
      {!!panel.element?.top && !viewOnly && (
        <ChangeOrderButton
          onClick={() => onChangeOrder?.(panel.id, "top")}
          position="top"
          iconName={ICON_NAME.CHEVRON_UP}
          isVisible={isHovered}
        />
      )}
      {!!panel.element?.bottom && !viewOnly && (
        <ChangeOrderButton
          onClick={() => onChangeOrder?.(panel.id, "bottom")}
          position="bottom"
          iconName={ICON_NAME.CHEVRON_DOWN}
          isVisible={isHovered}
        />
      )}
      {!!panel.element?.right && !viewOnly && (
        <ChangeOrderButton
          onClick={() => onChangeOrder?.(panel.id, "right")}
          position="right"
          iconName={ICON_NAME.CHEVRON_RIGHT}
          isVisible={isHovered}
        />
      )}
      <Box
        sx={{
          width: "100%",
          height: "100%",
          display: "flex",
          position: "relative",
          ...(panel.orientation === "horizontal" && {
            flexDirection: "row",
          }),
          ...(panel.orientation === "vertical" && {
            flexDirection: "column",
          }),
          transition: "all 0.3s",
          ...(panel.config?.options?.style !== "default" && {
            justifyContent: panel.config?.position?.alignItems,
          }),
        }}>
        {/* INNER SECTION  */}
        <Stack
          direction="column"
          sx={{
            display: "flex",
            transition: "all 0.3s",
            // Apply default styles when collapsed, regardless of the original style
            ...(isCollapsed && {
              width: "100%",
              height: "100%",
              backgroundColor: alpha(theme.palette.background.paper, 0.7),
              boxShadow: `rgba(0,0,0,0.2) 0px 0px 4px`,
              borderRadius: 0,
              margin: 0,
              backdropFilter: "none",
            }),
            // Only apply special styles when NOT collapsed
            ...(!isCollapsed && {
              ...(panel.config?.options?.style === "default" && {
                width: "100%",
                height: "100%",
                backgroundColor: alpha(theme.palette.background.paper, panel.config?.appearance?.opacity),
                backdropFilter: `blur(${panel.config.appearance.backgroundBlur}px)`,
              }),
              ...(panel.config?.options?.style === "rounded" && {
                ...(panel.orientation === "horizontal" && {
                  height: "calc(100% - 1rem)",
                  width: "fit-content",
                  minWidth: "220px",
                }),
                ...(panel.orientation === "vertical" && {
                  height: "fit-content",
                  width: "calc(100% - 1rem)",
                  maxWidth: "calc(100% - 1rem)",
                  maxHeight: "calc(100% - 1rem)",
                }),
                borderRadius: "1rem",
                margin: "0.5rem",
                backgroundColor: alpha(theme.palette.background.paper, panel.config?.appearance?.opacity),
                backdropFilter: `blur(${panel.config.appearance.backgroundBlur}px)`,
                boxShadow: `rgba(0, 0, 0, 0.2) 0px 0px ${panel.config.appearance.shadow}px`,
              }),
              ...(panel.config?.options?.style === "floated" && {
                ...(panel.orientation === "horizontal" && {
                  width: "fit-content",
                  maxWidth: "100%",
                }),
                ...(panel.orientation === "vertical" && {
                  height: "fit-content",
                  maxHeight: "100%",
                }),
                borderRadius: "1rem",
                backgroundColor: "transparent",
              }),
              ...(panel.widgets?.length === 0 && {
                backgroundColor: alpha(theme.palette.background.paper, panel.config?.appearance?.opacity),
                ...(panel.config?.options?.style !== "default" && {
                  height: "calc(100% - 1rem)",
                  width: "calc(100% - 1rem)",
                }),
                ...(panel.config?.options?.style === "floated" && {
                  backdropFilter: `blur(${panel.config.appearance.backgroundBlur}px)`,
                  boxShadow: `rgba(0, 0, 0, 0.2) 0px 0px ${panel.config.appearance.shadow}px`,
                  margin: "0.5rem",
                }),
              }),
            }),
          }}>
          <Box
            sx={{
              width: "100%",
              height: "100%",
              display: "flex",
              alignSelf: "stretch",
              ...(panel.orientation === "horizontal" && {
                flexDirection: "row",
                overflow: isCollapsed ? "hidden" : "auto hidden",
              }),
              ...(panel.orientation === "vertical" && {
                flexDirection: "column",
                overflow: isCollapsed ? "hidden" : "hidden auto",
              }),
              gap: isCollapsed ? 0 : `${panel?.config?.position?.spacing}rem`,
              transition: "all 0.3s",
              ...(panel.config?.options?.style === "default" && {
                justifyContent: panel.config?.position?.alignItems,
              }),
            }}>
            {/* Show empty message if widgets array is empty */}
            {panel.widgets?.length === 0 ? (
              <Stack
                width="100%"
                height="100%"
                alignItems="center"
                direction="column"
                display="flex"
                justifyContent="center">
                {!viewOnly && !isCollapsed && (
                  <>
                    <Icon
                      iconName={ICON_NAME.CUBE}
                      htmlColor={theme.palette.text.secondary}
                      fontSize="small"
                    />
                    <Typography variant="body2" fontWeight="bold" color="textSecondary">
                      {t("drag_and_drop_widgets_here")}
                    </Typography>
                  </>
                )}
              </Stack>
            ) : !viewOnly ? (
              <SortableContext items={widgetIds} strategy={sortingStrategy}>
                {panel.widgets?.map((widget) => (
                  <Box
                    key={widget.id}
                    sx={{
                      transition: "all 0.3s",
                      // Hide widgets when collapsed but maintain their size for smooth transition
                      ...(isCollapsed && {
                        opacity: 0,
                        visibility: "hidden",
                        position: "absolute",
                      }),
                      ...(!isCollapsed && {
                        ...(panel.config?.options?.style === "floated" && {
                          justifyContent: "center",
                          alignItems: "center",
                          backgroundColor: alpha(
                            theme.palette.background.paper,
                            panel.config?.appearance?.opacity
                          ),
                          backdropFilter: `blur(${panel.config.appearance.backgroundBlur}px)`,
                          boxShadow: `rgba(0, 0, 0, 0.2) 0px 0px ${panel.config.appearance.shadow}px`,
                          margin: "0.5rem",
                          borderRadius: "1rem",
                          height: "fit-content",
                          width: "calc(100% - 1rem)",
                        }),
                      }),
                    }}>
                    <WidgetWrapper
                      widget={widget}
                      projectLayers={projectLayers}
                      viewOnly={viewOnly}
                      onWidgetDelete={onWidgetDelete}
                      onWidgetUpdate={onWidgetUpdate}
                    />
                  </Box>
                ))}
              </SortableContext>
            ) : (
              // Render normally if viewOnly
              panel.widgets?.map((widget) => (
                <Box
                  key={widget.id}
                  sx={{
                    transition: "all 0.3s",
                    // Hide widgets when collapsed but maintain their size for smooth transition
                    ...(isCollapsed && {
                      opacity: 0,
                      visibility: "hidden",
                      position: "absolute",
                    }),
                    ...(!isCollapsed && {
                      ...(panel.config?.options?.style === "floated" && {
                        justifyContent: "center",
                        alignItems: "center",
                        backgroundColor: alpha(
                          theme.palette.background.paper,
                          panel.config?.appearance?.opacity
                        ),
                        backdropFilter: `blur(${panel.config.appearance.backgroundBlur}px)`,
                        boxShadow: `rgba(0, 0, 0, 0.2) 0px 0px ${panel.config.appearance.shadow}px`,
                        margin: "0.5rem",
                        borderRadius: "1rem",
                        height: "fit-content",
                        width: "calc(100% - 1rem)",
                      }),
                    }),
                  }}>
                  <WidgetWrapper widget={widget} projectLayers={projectLayers} viewOnly={viewOnly} />
                </Box>
              ))
            )}
            {viewOnly &&
              panel.config?.options?.collapsible &&
              (panel.config?.options?.style === "default" || panel.config?.options?.style === "rounded") && (
                <ExpandCollapseButton
                  position={panel.position}
                  expanded={!isCollapsed}
                  onClick={handleToggleCollapse}
                  isVisible={true}
                />
              )}
          </Box>
        </Stack>
      </Box>
    </Box>
  );
};
