import type { DragEndEvent } from "@dnd-kit/core";
import { DndContext, closestCenter } from "@dnd-kit/core";
import { restrictToVerticalAxis } from "@dnd-kit/modifiers";
import { SortableContext, useSortable, verticalListSortingStrategy } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  DragIndicator as DragIndicatorIcon,
  ExpandLess,
  ExpandMore,
  MoreVert as MoreVertIcon,
} from "@mui/icons-material";
import {
  Box,
  Collapse,
  IconButton,
  ListItemIcon,
  ListItemText,
  Menu,
  MenuItem,
  Stack,
  TextField,
  Typography,
  useTheme,
} from "@mui/material";
import { useCallback, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { v4 } from "uuid";

import { ICON_NAME } from "@p4b/ui/components/Icon";

import type { BuilderWidgetSchema } from "@/lib/validations/project";
import type { TabItemSchema, TabsContainerSchema, WidgetConfigSchema } from "@/lib/validations/widget";

import SectionHeader from "@/components/map/panels/common/SectionHeader";
import SectionOptions from "@/components/map/panels/common/SectionOptions";
import Selector from "@/components/map/panels/common/Selector";
import TextFieldInput from "@/components/map/panels/common/TextFieldInput";

interface TabsWidgetConfigProps {
  widget: BuilderWidgetSchema;
  config: TabsContainerSchema;
  onChange: (widget: BuilderWidgetSchema) => void;
  samePanelWidgets: BuilderWidgetSchema[]; // Widgets from the same panel only
}

// Get widget display name
const getWidgetDisplayName = (widget: BuilderWidgetSchema, t: (key: string) => string): string => {
  const config = widget.config as WidgetConfigSchema;
  if (!config) return widget.id;

  // Try to get title from setup
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const title = (config as any)?.setup?.title;
  if (title) return title;

  // Fall back to translated type name
  return t(config.type);
};

// Sortable widget item component
const SortableWidgetItem: React.FC<{
  widget: BuilderWidgetSchema;
  onRemove: () => void;
  t: (key: string) => string;
}> = ({ widget, onRemove, t }) => {
  const theme = useTheme();
  const { attributes, listeners, setNodeRef, transform, transition } = useSortable({ id: widget.id });
  const [menuAnchorEl, setMenuAnchorEl] = useState<null | HTMLElement>(null);

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  };

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    event.stopPropagation();
    setMenuAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setMenuAnchorEl(null);
  };

  const handleRemove = () => {
    handleMenuClose();
    onRemove();
  };

  return (
    <Stack
      ref={setNodeRef}
      style={style}
      direction="row"
      alignItems="center"
      spacing={1}
      sx={{
        p: 1,
        backgroundColor: theme.palette.background.paper,
        borderRadius: 1,
        border: `1px solid ${theme.palette.divider}`,
      }}>
      <Box {...attributes} {...listeners} sx={{ cursor: "grab", display: "flex", alignItems: "center" }}>
        <DragIndicatorIcon fontSize="small" sx={{ color: theme.palette.text.secondary }} />
      </Box>
      <Typography variant="body2" sx={{ flex: 1 }}>
        {getWidgetDisplayName(widget, t)}
      </Typography>
      <IconButton size="small" onClick={handleMenuOpen}>
        <MoreVertIcon fontSize="small" />
      </IconButton>
      <Menu anchorEl={menuAnchorEl} open={Boolean(menuAnchorEl)} onClose={handleMenuClose}>
        <MenuItem onClick={handleRemove}>
          <ListItemIcon>
            <DeleteIcon fontSize="small" color="error" />
          </ListItemIcon>
          <ListItemText>{t("remove")}</ListItemText>
        </MenuItem>
      </Menu>
    </Stack>
  );
};

// Single tab item component
const TabItemConfig: React.FC<{
  tab: TabItemSchema;
  isExpanded: boolean;
  onToggleExpand: () => void;
  onNameChange: (name: string) => void;
  onDelete: () => void;
  assignedWidgets: BuilderWidgetSchema[];
  availableWidgets: BuilderWidgetSchema[];
  onAddWidget: (widgetId: string) => void;
  onRemoveWidget: (widgetId: string) => void;
  onReorderWidgets: (widgetIds: string[]) => void;
  canDelete: boolean;
}> = ({
  tab,
  isExpanded,
  onToggleExpand,
  onNameChange,
  onDelete,
  assignedWidgets,
  availableWidgets,
  onAddWidget,
  onRemoveWidget,
  onReorderWidgets,
  canDelete,
}) => {
  const { t } = useTranslation("common");
  const theme = useTheme();

  // Widget options for dropdown (availableWidgets is already filtered by parent)
  const widgetOptions = useMemo(() => {
    return availableWidgets.map((widget) => ({
      value: widget.id,
      label: getWidgetDisplayName(widget, t),
    }));
  }, [availableWidgets, t]);

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;
    if (over && active.id !== over.id) {
      const oldIndex = assignedWidgets.findIndex((w) => w.id === active.id);
      const newIndex = assignedWidgets.findIndex((w) => w.id === over.id);
      const newOrder = [...assignedWidgets];
      const [removed] = newOrder.splice(oldIndex, 1);
      newOrder.splice(newIndex, 0, removed);
      onReorderWidgets(newOrder.map((w) => w.id));
    }
  };

  return (
    <Box
      sx={{
        border: `1px solid ${theme.palette.divider}`,
        borderRadius: 1,
        mb: 1,
      }}>
      {/* Tab header */}
      <Stack
        direction="row"
        alignItems="center"
        spacing={1}
        sx={{
          px: 2,
          py: 1,
          cursor: "pointer",
          "&:hover": {
            backgroundColor: theme.palette.action.hover,
          },
        }}
        onClick={onToggleExpand}>
        <TextField
          size="small"
          value={tab.name}
          onChange={(e) => {
            e.stopPropagation();
            onNameChange(e.target.value);
          }}
          onClick={(e) => e.stopPropagation()}
          variant="standard"
          InputProps={{
            disableUnderline: false,
            sx: { fontWeight: 500, fontSize: "0.8rem" },
          }}
          sx={{
            flex: 1,
            "& .MuiInput-underline:before": {
              borderBottomStyle: "dashed",
              borderBottomColor: theme.palette.divider,
            },
            "& .MuiInput-underline:hover:before": {
              borderBottomColor: theme.palette.primary.main,
            },
          }}
        />
        <Typography variant="caption" color="text.secondary">
          {assignedWidgets.length} {assignedWidgets.length === 1 ? t("widget") : t("widgets")}
        </Typography>
        <IconButton size="small" onClick={onToggleExpand}>
          {isExpanded ? <ExpandLess /> : <ExpandMore />}
        </IconButton>
        {canDelete && (
          <IconButton
            size="small"
            onClick={(e) => {
              e.stopPropagation();
              onDelete();
            }}
            sx={{
              "&:hover": {
                color: theme.palette.error.main,
              },
            }}>
            <DeleteIcon fontSize="small" />
          </IconButton>
        )}
      </Stack>

      {/* Expanded content */}
      <Collapse in={isExpanded}>
        <Box sx={{ px: 2, pb: 2 }}>
          {/* Add widget dropdown - always show but disable when no options */}
          <Box sx={{ mb: 2 }}>
            {widgetOptions.length > 0 ? (
              <Selector
                selectedItems={undefined}
                setSelectedItems={(item) => {
                  if (item && !Array.isArray(item) && item.value) {
                    onAddWidget(item.value as string);
                  }
                }}
                items={widgetOptions}
                label={t("add_widget_to_tab")}
                placeholder={t("select_widget")}
              />
            ) : assignedWidgets.length === 0 ? (
              <Typography variant="caption" color="text.secondary" sx={{ fontStyle: "italic" }}>
                {t("no_widgets_available_for_tabs")}
              </Typography>
            ) : null}
          </Box>

          {/* Assigned widgets list with drag & drop */}
          {assignedWidgets.length > 0 && (
            <DndContext
              collisionDetection={closestCenter}
              modifiers={[restrictToVerticalAxis]}
              onDragEnd={handleDragEnd}>
              <SortableContext
                items={assignedWidgets.map((w) => w.id)}
                strategy={verticalListSortingStrategy}>
                <Stack spacing={1}>
                  {assignedWidgets.map((widget) => (
                    <SortableWidgetItem
                      key={widget.id}
                      widget={widget}
                      onRemove={() => onRemoveWidget(widget.id)}
                      t={t}
                    />
                  ))}
                </Stack>
              </SortableContext>
            </DndContext>
          )}
        </Box>
      </Collapse>
    </Box>
  );
};

const TabsWidgetConfig: React.FC<TabsWidgetConfigProps> = ({
  widget,
  config,
  onChange,
  samePanelWidgets,
}) => {
  const { t } = useTranslation("common");
  const [expandedTabId, setExpandedTabId] = useState<string | null>(config.tabs[0]?.id || null);

  // Filter out tabs widgets and the current widget from same panel widgets
  const allNonTabWidgets = useMemo(() => {
    return samePanelWidgets.filter((w) => {
      const widgetType = w.config?.type;
      return widgetType !== "tabs" && w.id !== widget.id;
    });
  }, [samePanelWidgets, widget.id]);

  // Get all widget IDs that are assigned to ANY tab
  const allAssignedWidgetIds = useMemo(() => {
    const ids = new Set<string>();
    config.tabs.forEach((tab) => {
      tab.widgetIds?.forEach((id) => ids.add(id));
    });
    return ids;
  }, [config.tabs]);

  // Widgets that are NOT assigned to any tab (truly available for assignment)
  const availableWidgets = useMemo(() => {
    return allNonTabWidgets.filter((w) => !allAssignedWidgetIds.has(w.id));
  }, [allNonTabWidgets, allAssignedWidgetIds]);

  // Get widgets assigned to a specific tab (in order from tab.widgetIds)
  const getAssignedWidgets = useCallback(
    (tab: TabItemSchema): BuilderWidgetSchema[] => {
      const widgetIds = tab.widgetIds || [];
      return widgetIds
        .map((id) => allNonTabWidgets.find((w) => w.id === id))
        .filter((w): w is BuilderWidgetSchema => w !== undefined);
    },
    [allNonTabWidgets]
  );

  // Update config
  const handleConfigChange = useCallback(
    (updates: Partial<TabsContainerSchema>) => {
      onChange({
        ...widget,
        config: {
          ...config,
          ...updates,
        },
      });
    },
    [widget, config, onChange]
  );

  // Update a specific tab
  const handleTabChange = useCallback(
    (tabId: string, updates: Partial<TabItemSchema>) => {
      const newTabs = config.tabs.map((tab) => (tab.id === tabId ? { ...tab, ...updates } : tab));
      handleConfigChange({ tabs: newTabs });
    },
    [config.tabs, handleConfigChange]
  );

  // Add a new tab
  const handleAddTab = useCallback(() => {
    const newTab: TabItemSchema = {
      id: `tab-${v4().slice(0, 8)}`,
      name: `Tab ${config.tabs.length + 1}`,
      widgetIds: [],
    };
    handleConfigChange({
      tabs: [...config.tabs, newTab],
    });
    setExpandedTabId(newTab.id);
  }, [config.tabs, handleConfigChange]);

  // Delete a tab
  const handleDeleteTab = useCallback(
    (tabId: string) => {
      const newTabs = config.tabs.filter((tab) => tab.id !== tabId);
      handleConfigChange({ tabs: newTabs });

      // Update expanded tab
      if (expandedTabId === tabId && newTabs.length > 0) {
        setExpandedTabId(newTabs[0].id);
      }
    },
    [config.tabs, expandedTabId, handleConfigChange]
  );

  // Rename a tab
  const handleRenameTab = useCallback(
    (tabId: string, newName: string) => {
      handleTabChange(tabId, { name: newName });
    },
    [handleTabChange]
  );

  // Add widget to tab
  const handleAddWidgetToTab = useCallback(
    (tabId: string, widgetId: string) => {
      const tab = config.tabs.find((t) => t.id === tabId);
      if (tab) {
        handleTabChange(tabId, { widgetIds: [...(tab.widgetIds || []), widgetId] });
      }
    },
    [config.tabs, handleTabChange]
  );

  // Remove widget from tab
  const handleRemoveWidgetFromTab = useCallback(
    (tabId: string, widgetId: string) => {
      const tab = config.tabs.find((t) => t.id === tabId);
      if (tab) {
        handleTabChange(tabId, { widgetIds: (tab.widgetIds || []).filter((id) => id !== widgetId) });
      }
    },
    [config.tabs, handleTabChange]
  );

  // Reorder widgets within a tab
  const handleReorderWidgets = useCallback(
    (tabId: string, widgetIds: string[]) => {
      handleTabChange(tabId, { widgetIds });
    },
    [handleTabChange]
  );

  return (
    <Stack spacing={2}>
      {/* Info Section - Title */}
      <SectionHeader
        active
        alwaysActive
        label={t("info")}
        icon={ICON_NAME.CIRCLEINFO}
        disableAdvanceOptions
      />
      <SectionOptions
        active
        baseOptions={
          <TextFieldInput
            type="text"
            label={t("title")}
            placeholder={t("add_widget_title")}
            clearable={false}
            value={config.setup?.title || ""}
            onChange={(value: string) => {
              handleConfigChange({
                setup: {
                  ...config.setup,
                  title: value,
                },
              });
            }}
          />
        }
      />

      {/* Tabs & Widgets Section */}
      <SectionHeader
        active
        alwaysActive
        label={t("tabs_and_widgets")}
        icon={ICON_NAME.LIST}
        disableAdvanceOptions
      />
      <SectionOptions
        active
        baseOptions={
          <>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              {t("tabs_widget_description")}
            </Typography>

            {/* Tab list */}
            {config.tabs.map((tab) => (
              <TabItemConfig
                key={tab.id}
                tab={tab}
                isExpanded={expandedTabId === tab.id}
                onToggleExpand={() => setExpandedTabId(expandedTabId === tab.id ? null : tab.id)}
                onNameChange={(name) => handleRenameTab(tab.id, name)}
                onDelete={() => handleDeleteTab(tab.id)}
                assignedWidgets={getAssignedWidgets(tab)}
                availableWidgets={availableWidgets}
                onAddWidget={(widgetId) => handleAddWidgetToTab(tab.id, widgetId)}
                onRemoveWidget={(widgetId) => handleRemoveWidgetFromTab(tab.id, widgetId)}
                onReorderWidgets={(widgetIds) => handleReorderWidgets(tab.id, widgetIds)}
                canDelete={config.tabs.length > 1}
              />
            ))}

            {/* Add tab button */}
            <Box
              sx={{
                display: "flex",
                justifyContent: "center",
                mt: 2,
              }}>
              <IconButton onClick={handleAddTab} color="primary">
                <AddIcon />
              </IconButton>
            </Box>
          </>
        }
      />
    </Stack>
  );
};

export default TabsWidgetConfig;
