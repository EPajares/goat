/* eslint-disable @typescript-eslint/no-explicit-any */
import { useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { Box, IconButton, Tooltip, alpha, useTheme } from "@mui/material";
import { useMemo } from "react";

import { ICON_NAME, Icon } from "@p4b/ui/components/Icon";

import { useTranslation } from "@/i18n/client";

import { setSelectedBuilderItem } from "@/lib/store/map/slice";
import type { BuilderWidgetSchema, ProjectLayer } from "@/lib/validations/project";
import type {
  WidgetChartConfig,
  WidgetDataConfig,
  WidgetElementConfig,
  WidgetInformationConfig,
} from "@/lib/validations/widget";
import { chartTypes, dataTypes, elementTypes, informationTypes } from "@/lib/validations/widget";

import { useAppDispatch, useAppSelector } from "@/hooks/store/ContextHooks";

import WidgetChart from "@/components/builder/widgets/chart/WidgetChart";
import WidgetData from "@/components/builder/widgets/data/WidgetData";
import WidgetElement from "@/components/builder/widgets/elements/WidgetElement";
import WidgetInformation from "@/components/builder/widgets/information/WidgetInformation";

interface WidgetWrapper {
  widget: BuilderWidgetSchema;
  projectLayers: ProjectLayer[];
  viewOnly?: boolean;
  onWidgetDelete?: (widgetId: string) => void;
  onWidgetUpdate?: (updatedWidget: BuilderWidgetSchema) => void;
}

interface DraggableWidgetContainerProps {
  children: React.ReactNode;
  widget: BuilderWidgetSchema;
  onWidgetDelete?: (widgetId: string) => void;
}

const DraggableWidgetContainer: React.FC<DraggableWidgetContainerProps> = ({
  children,
  widget,
  onWidgetDelete,
}) => {
  const { t } = useTranslation("common");
  const dispatch = useAppDispatch();
  const selectedWidget = useAppSelector((state) => state.map.selectedBuilderItem);
  const theme = useTheme();

  const { attributes, listeners, setNodeRef, transform, transition } = useSortable({
    id: widget.id,
    data: widget,
  });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition: `${transition}, border-color 0.2s ease-in-out`,
  };

  const isSelected = useMemo(() => {
    if (!selectedWidget || selectedWidget.type !== "widget") return false;
    if (selectedWidget.id === widget.id) return true;
    return false;
  }, [selectedWidget, widget.id]);

  return (
    <Box
      style={style}
      ref={setNodeRef}
      onClick={(e) => {
        e.stopPropagation();
        dispatch(setSelectedBuilderItem(widget));
      }}
      sx={{
        width: "100%",
        p: 2,
        pointerEvents: "all",
        position: "relative",
        "&:hover": {
          "& > .content-box": {
            borderColor: isSelected ? theme.palette.primary.main : alpha(theme.palette.primary.main, 0.4),
          },
        },
      }}>
      {/* Control Panel */}
      {isSelected && (
        <Box
          sx={{
            position: "absolute",
            top: 8,
            right: 8,
            zIndex: 1,
            borderTopRightRadius: "1rem",
            borderTopLeftRadius: "0rem",
            borderBottomRightRadius: "0rem",
            borderBottomLeftRadius: "0.5rem",
            display: "flex",
            gap: 0.5,
            backgroundColor: theme.palette.primary.main,
            boxShadow: 0,
          }}>
          <Tooltip title={t("drag_to_move")} placement="top" arrow>
            <IconButton
              sx={{ borderRadius: 0, color: "white", cursor: "move" }}
              {...attributes}
              {...listeners}>
              <Icon iconName={ICON_NAME.GRIP_VERTICAL} style={{ fontSize: "12px" }} />
            </IconButton>
          </Tooltip>
          <Tooltip title={t("delete")} placement="top" arrow>
            <IconButton
              sx={{ borderRadius: 0, color: "white" }}
              onClick={(e) => {
                e.stopPropagation();
                onWidgetDelete?.(widget.id);
              }}>
              <Icon iconName={ICON_NAME.TRASH} style={{ fontSize: "12px" }} />
            </IconButton>
          </Tooltip>
        </Box>
      )}

      <Box
        className="content-box"
        sx={{
          borderRadius: 2,
          border: "2px solid",
          borderColor: isSelected ? theme.palette.primary.main : "transparent",
          transition: "border-color 0.2s ease",
          pointerEvents: isSelected ? "all" : "none",
        }}>
        {children}
      </Box>
    </Box>
  );
};

const WidgetWrapper: React.FC<WidgetWrapper> = ({
  widget,
  projectLayers,
  viewOnly,
  onWidgetDelete,
  onWidgetUpdate,
}) => {
  const widgetContent = (
    <Box sx={{ p: 1 }}>
      {widget.config?.type && informationTypes.options.includes(widget.config?.type as any) && (
        <WidgetInformation
          config={widget.config as WidgetInformationConfig}
          projectLayers={projectLayers}
          viewOnly={viewOnly}
        />
      )}
      {widget.config?.type && dataTypes.options.includes(widget.config?.type as any) && (
        <WidgetData
          id={widget.id}
          config={widget.config as WidgetDataConfig}
          projectLayers={projectLayers}
          viewOnly={viewOnly}
        />
      )}
      {widget.config?.type && chartTypes.options.includes(widget.config?.type as any) && (
        <WidgetChart config={widget.config as WidgetChartConfig} viewOnly={viewOnly} />
      )}
      {widget.config?.type && elementTypes.options.includes(widget.config?.type as any) && (
        <WidgetElement
          config={widget.config as WidgetElementConfig}
          viewOnly={viewOnly}
          onWidgetUpdate={(newConfig) => {
            onWidgetUpdate?.({ ...widget, config: newConfig });
          }}
        />
      )}
    </Box>
  );

  return viewOnly ? (
    <Box sx={{ width: "100%", p: 2, pointerEvents: "all" }}>{widgetContent}</Box>
  ) : (
    <DraggableWidgetContainer widget={widget} onWidgetDelete={onWidgetDelete}>
      {widgetContent}
    </DraggableWidgetContainer>
  );
};

export default WidgetWrapper;
