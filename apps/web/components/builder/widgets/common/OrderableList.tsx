import type { DragEndEvent } from "@dnd-kit/core";
import { DndContext, closestCenter } from "@dnd-kit/core";
import { restrictToVerticalAxis } from "@dnd-kit/modifiers";
import { SortableContext, useSortable, verticalListSortingStrategy } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import {
  Delete as DeleteIcon,
  DragIndicator as DragIndicatorIcon,
  MoreVert as MoreVertIcon,
  SwapVert as SortIcon,
} from "@mui/icons-material";
import {
  Box,
  Chip,
  IconButton,
  ListItemIcon,
  ListItemText,
  Menu,
  MenuItem,
  Skeleton,
  Stack,
  Tooltip,
  Typography,
  useTheme,
} from "@mui/material";
import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";

import type { SelectorItem } from "@/types/map/common";

import Selector from "@/components/map/panels/common/Selector";

interface SortableItemProps {
  value: string;
  onRemove: (value: string) => void;
}

const SortableItem = ({ value, onRemove }: SortableItemProps) => {
  const theme = useTheme();
  const { t } = useTranslation("common");
  const { attributes, listeners, setNodeRef, transform, transition } = useSortable({ id: value });
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
    onRemove(value);
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
      <Typography
        variant="body2"
        sx={{
          flex: 1,
          overflow: "hidden",
          textOverflow: "ellipsis",
          whiteSpace: "nowrap",
        }}>
        {value}
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

export interface OrderableListProps {
  /** All available items that can be added */
  allItems: string[];
  /** Currently visible/ordered items. If undefined, shows all items */
  visibleItems: string[] | undefined;
  /** Callback when the order or visible items change */
  onOrderChange: (items: string[]) => void;
  /** Whether data is loading */
  isLoading?: boolean;
  /** Warning message to show (e.g., when items are truncated) */
  warningMessage?: string;
  /** Label for the add item dropdown */
  addLabel?: string;
  /** Placeholder for the add item dropdown */
  addPlaceholder?: string;
  /** Empty state message when no items are available */
  emptyMessage?: string;
}

/**
 * A generic orderable list component with drag-and-drop, add/remove functionality.
 * Can be used for ordering categories, tabs, or any string-based items.
 */
const OrderableList = ({
  allItems,
  visibleItems,
  onOrderChange,
  isLoading = false,
  warningMessage,
  addLabel,
  addPlaceholder,
  emptyMessage,
}: OrderableListProps) => {
  const { t } = useTranslation("common");

  // Currently visible/selected values (respecting custom order)
  // If visibleItems is undefined, show all. If it's an empty array, show none.
  const currentItems = useMemo(() => {
    if (visibleItems === undefined) {
      return allItems;
    }
    // Only show items that are in visibleItems AND still exist in allItems
    return visibleItems.filter((v) => allItems.includes(v));
  }, [visibleItems, allItems]);

  // Items that can be added (not currently visible)
  const availableToAdd = useMemo(() => {
    return allItems.filter((v) => !currentItems.includes(v));
  }, [allItems, currentItems]);

  // Options for the selector dropdown
  const itemOptions = useMemo(() => {
    return availableToAdd.map((value) => ({
      value,
      label: value,
    }));
  }, [availableToAdd]);

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;
    if (over && active.id !== over.id) {
      const oldIndex = currentItems.findIndex((v) => v === active.id);
      const newIndex = currentItems.findIndex((v) => v === over.id);
      const newOrder = [...currentItems];
      const [removed] = newOrder.splice(oldIndex, 1);
      newOrder.splice(newIndex, 0, removed);
      onOrderChange(newOrder);
    }
  };

  const handleRemoveItem = (value: string) => {
    const newOrder = currentItems.filter((v) => v !== value);
    onOrderChange(newOrder);
  };

  const handleAddItem = (item: SelectorItem | SelectorItem[] | undefined) => {
    if (item && !Array.isArray(item) && item.value) {
      const value = item.value as string;
      if (!currentItems.includes(value)) {
        const newOrder = [...currentItems, value];
        onOrderChange(newOrder);
      }
    }
  };

  const handleAddAll = () => {
    onOrderChange([...allItems]);
  };

  const handleRemoveAll = () => {
    onOrderChange([]);
  };

  // Smart sort: handles numbers numerically and strings alphabetically
  const handleSort = () => {
    const sorted = [...currentItems].sort((a, b) => {
      const numA = parseFloat(a);
      const numB = parseFloat(b);
      // If both are valid numbers, sort numerically
      if (!isNaN(numA) && !isNaN(numB)) {
        return numA - numB;
      }
      // Otherwise, sort alphabetically
      return a.localeCompare(b);
    });
    onOrderChange(sorted);
  };

  if (isLoading) {
    return (
      <Stack spacing={1}>
        {Array.from({ length: 3 }).map((_, index) => (
          <Skeleton key={index} variant="rounded" height={40} />
        ))}
      </Stack>
    );
  }

  if (allItems.length === 0) {
    return (
      <Typography variant="caption" color="text.secondary" sx={{ fontStyle: "italic" }}>
        {emptyMessage || t("no_items_found")}
      </Typography>
    );
  }

  return (
    <Box>
      {/* Header with title and actions */}
      <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 1 }}>
        <Typography variant="body2" fontWeight="medium">
          {t("order")} ({currentItems.length}/{allItems.length})
        </Typography>
        <Stack direction="row" spacing={0.5}>
          <Tooltip title={t("sort_ascending")}>
            <span>
              <IconButton size="small" onClick={handleSort} disabled={currentItems.length < 2}>
                <SortIcon fontSize="small" />
              </IconButton>
            </span>
          </Tooltip>
        </Stack>
      </Stack>

      {warningMessage && (
        <Typography variant="caption" color="warning.main" sx={{ mb: 1, display: "block" }}>
          {warningMessage}
        </Typography>
      )}

      {/* Add item dropdown */}
      {itemOptions.length > 0 ? (
        <Box sx={{ mb: 1 }}>
          <Selector
            selectedItems={undefined}
            setSelectedItems={handleAddItem}
            items={itemOptions}
            label={addLabel || t("add_item")}
            placeholder={addPlaceholder || t("select_item")}
          />
        </Box>
      ) : null}

      {/* Quick actions */}
      <Stack direction="row" spacing={1} sx={{ mb: 1 }}>
        <Chip
          label={t("add_all")}
          size="small"
          variant="outlined"
          onClick={handleAddAll}
          disabled={availableToAdd.length === 0}
          sx={{ fontSize: "0.75rem" }}
        />
        <Chip
          label={t("remove_all")}
          size="small"
          variant="outlined"
          onClick={handleRemoveAll}
          disabled={currentItems.length === 0}
          sx={{ fontSize: "0.75rem" }}
        />
      </Stack>

      {/* Visible items list */}
      {currentItems.length > 0 && (
        <DndContext
          collisionDetection={closestCenter}
          modifiers={[restrictToVerticalAxis]}
          onDragEnd={handleDragEnd}>
          <SortableContext items={currentItems} strategy={verticalListSortingStrategy}>
            <Stack spacing={1}>
              {currentItems.map((value) => (
                <SortableItem key={value} value={value} onRemove={handleRemoveItem} />
              ))}
            </Stack>
          </SortableContext>
        </DndContext>
      )}
    </Box>
  );
};

export default OrderableList;
