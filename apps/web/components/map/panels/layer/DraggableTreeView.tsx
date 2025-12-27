import type { DragEndEvent, DragStartEvent } from "@dnd-kit/core";
import {
  DndContext,
  DragOverlay,
  KeyboardSensor,
  PointerSensor,
  closestCenter,
  useDraggable,
  useDroppable,
  useSensor,
  useSensors,
} from "@dnd-kit/core";
import { arrayMove, sortableKeyboardCoordinates } from "@dnd-kit/sortable";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import KeyboardArrowRightIcon from "@mui/icons-material/KeyboardArrowRight";
import { Divider, IconButton, Tooltip } from "@mui/material";
import Box from "@mui/material/Box";
import Collapse from "@mui/material/Collapse";
import Typography from "@mui/material/Typography";
import { alpha, styled } from "@mui/material/styles";
import React, { useEffect, useMemo, useRef, useState } from "react";

// ----------------------------------------------------------------------
// 1. INTERFACES
// ----------------------------------------------------------------------
export interface BaseTreeItem {
  id: string;
  parentId?: string | null;
  label: string;
  collapsed?: boolean;
  isGroup?: boolean;
  icon?: React.ReactNode;
  legendContent?: React.ReactNode;
  isSelectable?: boolean;
  isVisible?: boolean; // Add this property for visibility styling
  labelInfo?: string; // Add missing property
  canExpand?: boolean; // Add missing property
}

interface DraggableTreeViewProps<T extends BaseTreeItem> {
  items: T[];
  onItemsChange: (newItems: T[]) => void;
  renderActions?: (item: T) => React.ReactNode;
  enableSelection?: boolean;
  selectedIds?: string[];
  onSelect?: (ids: string[]) => void;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  sx?: any;
}

// ----------------------------------------------------------------------
// 2. STYLED COMPONENTS
// ----------------------------------------------------------------------
const CustomTreeItemRoot = styled("div")(({ theme }) => ({
  color: theme.palette.text.secondary,
  position: "relative",
  userSelect: "none",
}));

const CustomTreeItemContent = styled("div", {
  shouldForwardProp: (prop) =>
    prop !== "enableSelection" && prop !== "isDragging" && prop !== "itemVisible" && prop !== "isSelectable",
})<{
  enableSelection?: boolean;
  isDragging?: boolean;
  itemVisible?: boolean;
  isSelectable?: boolean;
}>(({ theme, enableSelection, isDragging, itemVisible, isSelectable }) => ({
  color: theme.palette.text.secondary,
  borderRadius: 0,
  paddingRight: theme.spacing(0.5),
  fontWeight: theme.typography.fontWeightMedium,
  display: "flex",
  alignItems: "center",
  minHeight: 40,
  paddingTop: theme.spacing(0.5),
  paddingBottom: theme.spacing(0.5),
  border: "1px solid transparent",
  transition: "background-color 0.1s, opacity 0.2s",
  cursor: !enableSelection || isSelectable === false ? "default" : "pointer", // Updated cursor logic

  // Apply visibility opacity only to the content part, not actions
  "& .tree-content-area": {
    opacity: itemVisible ? 1 : 0.5,
    transition: "opacity 0.2s",
  },

  ".dnd-drag-active &": {
    cursor: enableSelection ? "grabbing" : "default",
  },

  // 1. Show background on Mouse Hover (actions are always visible)
  "&:hover": {
    backgroundColor: theme.palette.action.hover,
  },

  ...(isDragging && {
    opacity: 0.5,
    backgroundColor: theme.palette.action.selected,
    cursor: "grabbing",
    "& .tree-row-actions": {
      opacity: 0.3, // Just dim them slightly when dragging
    },
  }),

  "&.selected": {
    backgroundColor: alpha(theme.palette.primary.main, 0.08),
    color: theme.palette.primary.main,
    "&:hover": {
      backgroundColor: alpha(theme.palette.primary.main, 0.12),
    },
  },
}));

const LeftIconContainer = styled("div")(({ theme }) => ({
  marginRight: theme.spacing(1),
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  width: 24,
  height: 24,
  flexShrink: 0,
  fontSize: "1.2rem",
  color: theme.palette.action.active,
}));

const ActionsContainer = styled("div")(({ theme }) => ({
  display: "flex",
  alignItems: "center",
  gap: theme.spacing(0.5),
  opacity: 1, // Always visible
  pointerEvents: "auto", // Always interactive
  paddingLeft: theme.spacing(1),
}));

const InsertionLine = styled("div")(({ theme }) => ({
  position: "absolute",
  bottom: 0,
  left: 0,
  right: 0,
  height: 2,
  backgroundColor: theme.palette.primary.main,
  zIndex: 10,
  pointerEvents: "none",
}));

const EmptyPlaceholderBox = styled("div")(({ theme }) => ({
  height: 32,
  display: "flex",
  alignItems: "center",
  color: theme.palette.text.disabled,
  fontSize: "0.8rem",
  fontStyle: "italic",
  border: `1px dashed ${theme.palette.action.disabled}`,
  borderRadius: 4,
  margin: "4px 8px 4px 0",
  "&.is-over": {
    borderColor: theme.palette.primary.main,
    color: theme.palette.primary.main,
    backgroundColor: alpha(theme.palette.primary.main, 0.05),
  },
}));

// ----------------------------------------------------------------------
// 3. HELPER COMPONENTS
// ----------------------------------------------------------------------

const TruncatedLabel = ({ label }: { label: string }) => {
  const textRef = useRef<HTMLSpanElement>(null);
  const [isTooltipEnabled, setIsTooltipEnabled] = useState(false);

  useEffect(() => {
    const compareSize = () => {
      if (textRef.current) {
        setIsTooltipEnabled(textRef.current.scrollWidth > textRef.current.clientWidth);
      }
    };
    compareSize();
    window.addEventListener("resize", compareSize);
    return () => window.removeEventListener("resize", compareSize);
  }, [label]);

  return (
    <Tooltip title={label} disableHoverListener={!isTooltipEnabled} arrow placement="top" enterDelay={1000}>
      <Typography
        ref={textRef}
        variant="body2"
        sx={{
          fontWeight: "inherit",
          flexGrow: 1,
          whiteSpace: "nowrap",
          overflow: "hidden",
          textOverflow: "ellipsis",
          display: "block",
          minWidth: 0,
        }}>
        {label}
      </Typography>
    </Tooltip>
  );
};

const EmptyGroupPlaceholder = ({
  parentId,
  level,
  enableSelection,
}: {
  parentId: string;
  level: number;
  enableSelection?: boolean;
}) => {
  const { setNodeRef, isOver } = useDroppable({
    id: `placeholder-${parentId}`,
    data: { parentId: parentId },
    disabled: !enableSelection,
  });
  const indentStyle = { marginLeft: (level + 1) * 24 };

  if (!enableSelection) {
    return (
      <Typography
        variant="caption"
        sx={{
          marginLeft: (level + 1) * 12,
          display: "block",
          py: 0.5,
          color: "text.disabled",
          fontStyle: "italic",
        }}>
        (No items)
      </Typography>
    );
  }
  return (
    <EmptyPlaceholderBox ref={setNodeRef} className={isOver ? "is-over" : ""} style={indentStyle}>
      <Typography variant="caption" sx={{ ml: 1 }}>
        Drag items here
      </Typography>
    </EmptyPlaceholderBox>
  );
};

// ----------------------------------------------------------------------
// 4. RECURSIVE ITEM COMPONENT
// ----------------------------------------------------------------------

const RecursiveTreeItem = <T extends BaseTreeItem>({
  item,
  allData,
  level,
  onCollapse,
  renderActions,
  isOverlay,
  enableSelection,
  selectedIds,
  onSelect,
}: {
  item: T;
  allData: T[];
  level: number;
  onCollapse: (id: string) => void;
  renderActions?: (item: T) => React.ReactNode;
  isOverlay?: boolean;
  enableSelection?: boolean;
  selectedIds: string[];
  onSelect?: (ids: string[]) => void;
}) => {
  const children = allData.filter((i) => i.parentId === item.id);
  const isSelected = selectedIds.includes(item.id);
  const isDragDisabled = !enableSelection || isOverlay;

  const hasLegend = !!item.legendContent;
  const isExpanded = !item.collapsed;

  const {
    attributes,
    listeners,
    setNodeRef: setDraggableRef,
    isDragging,
  } = useDraggable({
    id: item.id,
    disabled: isDragDisabled,
    data: item,
  });
  const { setNodeRef: setDroppableRef, isOver } = useDroppable({
    id: item.id,
    disabled: isDragDisabled,
    data: item,
  });

  const setNodeRef = (node: HTMLElement | null) => {
    setDraggableRef(node);
    setDroppableRef(node);
  };

  // Deselect item when it becomes non-selectable
  useEffect(() => {
    if (item.isSelectable === false && isSelected && onSelect) {
      onSelect(selectedIds.filter((id) => id !== item.id));
    }
  }, [item.isSelectable, isSelected, selectedIds, onSelect, item.id]);

  const handleRowClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    // Check if item is selectable
    if (!enableSelection || !onSelect || item.isSelectable === false) return;

    if (e.ctrlKey || e.metaKey) {
      isSelected ? onSelect(selectedIds.filter((id) => id !== item.id)) : onSelect([...selectedIds, item.id]);
    } else {
      onSelect([item.id]);
    }
  };

  const handleCollapseToggle = (e: React.MouseEvent) => {
    e.stopPropagation();
    onCollapse(item.id);
  };

  const baseIndent = level * 24;

  // Determine what icon to show on the left
  let LeftIconContent: React.ReactNode = item.icon;

  // For layers with legend content, show clickable arrow
  if (!item.isGroup && hasLegend) {
    LeftIconContent = (
      <KeyboardArrowRightIcon
        sx={{
          transform: isExpanded ? "rotate(90deg)" : "rotate(0deg)",
          transition: "transform 0.2s",
          cursor: "pointer",
        }}
        onClick={handleCollapseToggle}
      />
    );
  }

  const isVisible = item.isVisible ?? true; // Default to visible if not specified

  return (
    <Box sx={{ width: "100%" }}>
      <CustomTreeItemRoot
        ref={!isOverlay ? setNodeRef : null}
        {...(!isOverlay ? listeners : {})}
        {...(!isOverlay ? attributes : {})}
        style={{ touchAction: "none", paddingBottom: isOverlay ? 0 : undefined }}>
        <CustomTreeItemContent
          onClick={handleRowClick}
          ref={setNodeRef}
          enableSelection={enableSelection}
          isDragging={isDragging}
          isSelectable={item.isSelectable}
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          itemVisible={(item as any).data?.visibility ?? true} // Pass visibility from node data
          className={`tree-item ${isSelected ? "selected" : ""}`}
          sx={{
            opacity: isVisible ? 1 : 0.5, // Apply opacity based on visibility
            flexDirection: "column", // Stack main row and caption vertically
            alignItems: "stretch", // Stretch to full width
          }}>
          {/* Main content row */}
          <Box
            className="tree-content-area"
            sx={{ display: "flex", alignItems: "center", flex: 1, minWidth: 0 }}>
            <Box sx={{ ml: `${baseIndent}px` }} />
            <LeftIconContainer>{LeftIconContent}</LeftIconContainer>
            <Box sx={{ flex: 1, minWidth: 0 }}>
              <TruncatedLabel label={item.label} />
            </Box>

            {/* Actions container - always fully visible */}
            <ActionsContainer className="tree-row-actions">
              {/* Show collapse button for groups that can expand */}
              {item.isGroup && item.canExpand !== false && (
                <IconButton
                  size="small"
                  onClick={handleCollapseToggle}
                  sx={{
                    p: 0.5,
                    mr: 0.5,
                    transform: isExpanded ? "rotate(180deg)" : "rotate(0deg)",
                    transition: "transform 0.2s",
                  }}>
                  <ExpandMoreIcon fontSize="inherit" />
                </IconButton>
              )}

              {renderActions && <Box onClick={(e) => e.stopPropagation()}>{renderActions(item)}</Box>}
            </ActionsContainer>
          </Box>

          {/* Caption row - part of the same tree item */}
          {item.labelInfo && (
            <Box
              sx={{
                ml: `${baseIndent + 28}px`, // Align with label text (indent + icon container width + margin)
                mr: 2,
                pb: 0.5,
              }}>
              <Typography
                variant="caption"
                sx={{
                  color: "text.secondary",
                  wordBreak: "break-word",
                  lineHeight: 1.3,
                }}>
                {item.labelInfo}
              </Typography>
            </Box>
          )}
        </CustomTreeItemContent>
        {isOver && !isDragging && !isOverlay && <InsertionLine sx={{ ml: `${baseIndent}px` }} />}
      </CustomTreeItemRoot>

      {/* Add divider between rows */}
      {!isOverlay && (
        <Divider
          sx={{
            my: 0,
            opacity: 0.5,
          }}
        />
      )}

      {/* EXPANSION */}
      {isExpanded && !isOverlay && item.canExpand !== false && (
        <Collapse in={isExpanded} timeout="auto" unmountOnExit>
          <Box>
            {/* For groups: show children */}
            {item.isGroup && (
              <>
                {children.map((child) => (
                  <RecursiveTreeItem
                    key={child.id}
                    item={child}
                    allData={allData}
                    level={level + 1}
                    onCollapse={onCollapse}
                    renderActions={renderActions}
                    selectedIds={selectedIds}
                    onSelect={onSelect}
                    enableSelection={enableSelection}
                  />
                ))}
                {children.length === 0 && (
                  <EmptyGroupPlaceholder parentId={item.id} level={level} enableSelection={enableSelection} />
                )}
              </>
            )}

            {/* For layers: show legend content if available */}
            {!item.isGroup && hasLegend && (
              <Box
                sx={{
                  paddingLeft: `${baseIndent + 28}px`,
                  paddingRight: 1,
                  paddingBottom: 1,
                  paddingTop: 0.5,
                }}>
                {item.legendContent}
              </Box>
            )}
          </Box>
        </Collapse>
      )}
    </Box>
  );
};

export function DraggableTreeView<T extends BaseTreeItem>(props: DraggableTreeViewProps<T>) {
  const {
    items,
    onItemsChange,
    renderActions,
    selectedIds = [],
    onSelect,
    enableSelection = false,
    sx,
  } = props;
  const [activeId, setActiveId] = React.useState<string | null>(null);
  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 10 } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates })
  );
  const rootItems = useMemo(() => items.filter((i) => i.parentId === null), [items]);

  const handleDragStart = (event: DragStartEvent) => setActiveId(String(event.active.id));

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;
    setActiveId(null);
    if (!enableSelection || !over) return;
    const activeIdStr = String(active.id);
    const overIdStr = String(over.id);
    if (overIdStr.startsWith("placeholder-")) {
      const targetParentId = overIdStr.replace("placeholder-", "");
      const oldIndex = items.findIndex((i) => i.id === activeIdStr);
      if (oldIndex > -1) {
        const newItems = [...items];
        newItems[oldIndex] = { ...newItems[oldIndex], parentId: targetParentId };
        onItemsChange(newItems);
      }
      return;
    }
    if (activeIdStr !== overIdStr) {
      const activeItem = items.find((i) => i.id === activeIdStr);
      const overItem = items.find((i) => i.id === overIdStr);
      if (activeItem && overItem) {
        const oldIndex = items.findIndex((i) => i.id === activeIdStr);
        const targetIndex = items.findIndex((i) => i.id === overIdStr);
        const newItems = [...items];
        newItems[oldIndex] = { ...newItems[oldIndex], parentId: overItem.parentId };
        onItemsChange(arrayMove(newItems, oldIndex, targetIndex));
      }
    }
  };

  const handleCollapse = (id: string) => {
    // Allow collapse for both groups and layers with legends
    onItemsChange(items.map((i) => (i.id === id ? { ...i, collapsed: !i.collapsed } : i)));
  };

  const activeItem = activeId ? items.find((i) => i.id === activeId) : null;

  return (
    <DndContext
      sensors={sensors}
      collisionDetection={closestCenter}
      onDragStart={handleDragStart}
      onDragEnd={handleDragEnd}>
      <Box sx={{ flexGrow: 1, ...sx }} className={activeId ? "dnd-drag-active" : ""}>
        {rootItems.map((item) => (
          <RecursiveTreeItem
            key={item.id}
            item={item}
            allData={items}
            level={0}
            onCollapse={handleCollapse}
            renderActions={renderActions}
            selectedIds={selectedIds}
            onSelect={onSelect}
            enableSelection={enableSelection}
          />
        ))}
      </Box>
      <DragOverlay dropAnimation={null}>
        {activeItem ? (
          <RecursiveTreeItem
            item={{ ...activeItem, collapsed: true }}
            allData={[]}
            level={0}
            onCollapse={() => {}}
            renderActions={renderActions}
            isOverlay
            selectedIds={selectedIds}
            enableSelection={true}
          />
        ) : null}
      </DragOverlay>
    </DndContext>
  );
}
