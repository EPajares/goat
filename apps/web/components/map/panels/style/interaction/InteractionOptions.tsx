// DEPRECATED — replaced by PopupSection at
// apps/web/components/map/panels/style/popup/PopupSection.tsx.
// Kept for reference / rollback only. Schedule for removal once v2
// lazy-on-read migration ships.
import type { DragEndEvent } from "@dnd-kit/core";
import { arrayMove } from "@dnd-kit/sortable";
import {
  Box,
  Button,
  ClickAwayListener,
  Collapse,
  Divider,
  Fade,
  IconButton,
  ListItemIcon,
  Menu,
  MenuItem,
  MenuList,
  Popper,
  Stack,
  TextField,
  Typography,
  useTheme,
} from "@mui/material";
import { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { v4 } from "uuid";

import { ICON_NAME, Icon } from "@p4b/ui/components/Icon";

import type { FormatNumberTypes } from "@/lib/validations/common";
import { formatNumber } from "@/lib/utils/format-number";
import type {
  LayerInteractionContent,
  LayerInteractionContentType,
  LayerInteractionFieldListContent,
} from "@/lib/validations/layer";
import {
  type FeatureLayerProperties,
  interactionFieldListContent,
  interactionImageContent,
  layerInteractionContentType,
  layerInteractionType,
} from "@/lib/validations/layer";
import type { ProjectLayer } from "@/lib/validations/project";

import type { SelectorItem } from "@/types/map/common";

import useLayerFields from "@/hooks/map/CommonHooks";
import { useInteractionOptions } from "@/hooks/map/LayerDesignHooks";

import { NumberFormatSelector } from "@/components/builder/widgets/common/WidgetCommonConfigs";
import { OverflowTypograpy } from "@/components/common/OverflowTypography";
import FieldKindIcon, { fieldIndicatorKind } from "@/components/common/FieldKindIcon";
import SectionHeader from "@/components/map/panels/common/SectionHeader";
import SectionOptions from "@/components/map/panels/common/SectionOptions";
import Selector from "@/components/map/panels/common/Selector";
import { SortableItem } from "@/components/map/panels/style/other/SortableItem";
import SortableWrapper from "@/components/map/panels/style/other/SortableWrapper";

const InteractionFieldListOptions: React.FC<{
  layer: ProjectLayer;
  item: LayerInteractionFieldListContent;
  onSave: (item: LayerInteractionFieldListContent) => void;
}> = ({ layer, item, onSave }) => {
  const { t, i18n } = useTranslation("common");
  const theme = useTheme();
  const [addContentAnchorEl, setAddContentAnchorEl] = useState<null | HTMLElement>(null);
  const [existingFields, setExistingFields] = useState(item.attributes || []);
  const [expandedField, setExpandedField] = useState<string | null>(null);
  const open = Boolean(addContentAnchorEl);
  const handleAddContentOnClose = () => {
    setAddContentAnchorEl(null);
  };
  const handleContentAddOnClick = (event: React.MouseEvent<HTMLButtonElement>) => {
    setAddContentAnchorEl(event.currentTarget);
  };

  const { layerFields } = useLayerFields(layer?.layer_id || "");

  // Auto-populate fields when layer fields are loaded and no attributes exist
  useEffect(() => {
    if (layerFields.length > 0 && existingFields.length === 0) {
      setExistingFields(
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        layerFields.map((field) => ({ name: field.name, type: field.type as any }))
      );
    }
  }, [layerFields]); // eslint-disable-line react-hooks/exhaustive-deps

  const unAddedFields = useMemo(() => {
    return layerFields.filter((field) => !existingFields.some((attr) => attr.name === field.name));
  }, [layerFields, existingFields]);

  const addField = (field: { name: string; type: string }) => {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    setExistingFields([...existingFields, { name: field.name, type: field.type as any }]);
  };

  const resetToAllFields = () => {
    setExistingFields(
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      layerFields.map((field) => ({ name: field.name, type: field.type as any }))
    );
  };

  const updateField = (fieldName: string, updates: Record<string, unknown>) => {
    setExistingFields(existingFields.map((f) => (f.name === fieldName ? { ...f, ...updates } : f)));
  };

  const removeField = (fieldName: string) => {
    setExistingFields(existingFields.filter((f) => f.name !== fieldName));
    if (expandedField === fieldName) setExpandedField(null);
  };

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;
    const oldIndex = existingFields.findIndex((value) => value.name === active.id);
    const newIndex = existingFields.findIndex((value) => value.name === over?.id);
    const newOrderArray = arrayMove(existingFields, oldIndex, newIndex);
    setExistingFields(newOrderArray);
  };

  const getFormatPreview = (field: { format?: FormatNumberTypes; prefix?: string; suffix?: string }) => {
    const sampleValue = 12345.678;
    const formatted = field.format
      ? formatNumber(sampleValue, field.format, i18n.language)
      : String(sampleValue);
    return `${field.prefix || ""}${formatted}${field.suffix || ""}`;
  };

  const hasFormatConfig = (field: { format?: unknown; prefix?: string; suffix?: string }) =>
    !!(field.format || field.prefix || field.suffix);

  return (
    <Box sx={{ minWidth: "400px", maxHeight: "500px", display: "flex", flexDirection: "column" }}>
      {/* Header */}
      <Stack direction="row" alignItems="center" justifyContent="space-between" sx={{ px: 2, pt: 2, pb: 1 }}>
        <Typography variant="body2" fontWeight="bold">
          {t("field_list")}
        </Typography>
        {unAddedFields.length > 0 && (
          <Typography
            variant="caption"
            color="primary"
            sx={{ cursor: "pointer", "&:hover": { textDecoration: "underline" } }}
            onClick={resetToAllFields}>
            {t("common:add_all_fields")}
          </Typography>
        )}
      </Stack>

      {/* Field list — no overflow clipping so Select dropdowns render correctly */}
      <Box sx={{ flex: 1, overflowY: "auto", maxHeight: "320px", px: 1 }}>
        <SortableWrapper
          handleDragEnd={handleDragEnd}
          items={existingFields.map((field) => ({ ...field, id: field.name }))}>
          {existingFields.map((field) => {
            const isExpanded = expandedField === field.name;
            const isNumber = field.type === "number";

            return (
              <SortableItem
                key={field.name}
                item={{ ...field, id: field.name }}
                label={field.name}
                active={false}>
                <Stack spacing={0.5} sx={{ py: 0.5 }}>
                  {/* Row 1: Type tag + field name + actions */}
                  <Stack direction="row" spacing={1} alignItems="center">
                    <FieldKindIcon kind={fieldIndicatorKind(field)} />
                    <OverflowTypograpy variant="body2" fontWeight="bold" sx={{ flex: 1 }}>
                      {field.name}
                    </OverflowTypograpy>
                    {isNumber && hasFormatConfig(field) && !isExpanded && (
                      <Typography
                        variant="caption"
                        sx={{
                          bgcolor: theme.palette.action.selected,
                          color: theme.palette.text.secondary,
                          px: 0.75,
                          py: 0.125,
                          borderRadius: 0.5,
                          fontSize: 10,
                          lineHeight: 1.4,
                          whiteSpace: "nowrap",
                        }}>
                        {field.suffix || field.prefix || field.format}
                      </Typography>
                    )}
                    {isNumber && (
                      <IconButton
                        size="small"
                        onClick={(e) => {
                          e.stopPropagation();
                          setExpandedField(isExpanded ? null : field.name);
                        }}
                        sx={{ p: 0.25 }}>
                        <Icon
                          iconName={ICON_NAME.SETTINGS}
                          style={{ fontSize: 12 }}
                          htmlColor={
                            hasFormatConfig(field)
                              ? theme.palette.primary.main
                              : theme.palette.text.secondary
                          }
                        />
                      </IconButton>
                    )}
                    <IconButton
                      size="small"
                      onClick={() => removeField(field.name)}
                      sx={{
                        p: 0.25,
                        "&:hover": { color: theme.palette.error.main },
                      }}>
                      <Icon
                        iconName={ICON_NAME.TRASH}
                        style={{ fontSize: 12 }}
                        htmlColor="inherit"
                      />
                    </IconButton>
                  </Stack>
                  {/* Row 2: Label input */}
                  <TextField
                    value={field.label || ""}
                    inputProps={{ style: { fontSize: 12, padding: "6px 10px" } }}
                    placeholder={field.name}
                    onChange={(e) => updateField(field.name, { label: e.target.value })}
                    fullWidth
                    variant="outlined"
                    size="small"
                  />
                  {/* Row 3: Expandable format options (number fields only) */}
                  {isNumber && (
                    <Collapse in={isExpanded}>
                      <Stack
                        spacing={1}
                        sx={{
                          pt: 1,
                          pb: 0.5,
                          mt: 0.5,
                          borderTop: `1px solid ${theme.palette.divider}`,
                        }}>
                        <Box sx={{
                          "& .MuiSelect-select": { fontSize: 12, py: "6px" },
                          "& .MuiInputLabel-root": { fontSize: 12 },
                        }}>
                          <NumberFormatSelector
                            numberFormat={field.format as FormatNumberTypes | undefined}
                            onNumberFormatChange={(format) => updateField(field.name, { format })}
                          />
                        </Box>
                        <Stack direction="row" spacing={1}>
                          <TextField
                            value={field.prefix || ""}
                            inputProps={{ style: { fontSize: 12, padding: "6px 10px" } }}
                            placeholder={t("prefix")}
                            onChange={(e) => updateField(field.name, { prefix: e.target.value })}
                            variant="outlined"
                            size="small"
                            sx={{ flex: 1 }}
                          />
                          <TextField
                            value={field.suffix || ""}
                            inputProps={{ style: { fontSize: 12, padding: "6px 10px" } }}
                            placeholder={t("suffix")}
                            onChange={(e) => updateField(field.name, { suffix: e.target.value })}
                            variant="outlined"
                            size="small"
                            sx={{ flex: 1 }}
                          />
                        </Stack>
                        {hasFormatConfig(field) && (
                          <Typography
                            variant="caption"
                            sx={{
                              bgcolor: theme.palette.action.hover,
                              color: theme.palette.text.secondary,
                              px: 1,
                              py: 0.5,
                              borderRadius: 1,
                              display: "inline-block",
                              width: "fit-content",
                              fontSize: 11,
                            }}>
                            {t("preview")}:{" "}
                            <strong>{getFormatPreview(field)}</strong>
                          </Typography>
                        )}
                      </Stack>
                    </Collapse>
                  )}
                </Stack>
              </SortableItem>
            );
          })}
        </SortableWrapper>
      </Box>

      {/* Add field button + menu */}
      <Stack sx={{ px: 2, pt: 1, pb: 0 }}>
        <Button
          variant="outlined"
          size="small"
          onClick={handleContentAddOnClick}
          disabled={unAddedFields.length === 0}
          startIcon={<Icon iconName={ICON_NAME.PLUS} style={{ fontSize: 12 }} />}>
          {t("add_field")}
        </Button>
        <Menu
          anchorEl={addContentAnchorEl}
          sx={{
            "& .MuiPaper-root": {
              boxShadow: "0px 0px 10px 0px rgba(58, 53, 65, 0.1)",
            },
            zIndex: 2001,
          }}
          anchorOrigin={{ vertical: "top", horizontal: "center" }}
          transformOrigin={{ vertical: "bottom", horizontal: "center" }}
          open={open}
          MenuListProps={{
            sx: {
              width: addContentAnchorEl && addContentAnchorEl.offsetWidth - 10,
              p: 0,
            },
          }}
          onClose={handleAddContentOnClose}>
          <Box sx={{ maxHeight: "300px", overflowY: "auto" }}>
            <ClickAwayListener onClickAway={handleAddContentOnClose}>
              <MenuList>
                <MenuItem
                  key="add-all-fields"
                  onClick={() => {
                    resetToAllFields();
                    handleAddContentOnClose();
                  }}>
                  <Typography variant="body2" fontWeight="bold">
                    {t("common:add_all_fields")}
                  </Typography>
                </MenuItem>
                <Divider />
                {unAddedFields.map((field) => (
                  <MenuItem
                    key={field.name}
                    onClick={() => {
                      addField(field);
                    }}>
                    <Stack direction="row" spacing={1} alignItems="center">
                      <FieldKindIcon kind={fieldIndicatorKind(field)} />
                      <Typography variant="body2">{field.name}</Typography>
                    </Stack>
                  </MenuItem>
                ))}
              </MenuList>
            </ClickAwayListener>
          </Box>
        </Menu>
      </Stack>

      {/* Save footer */}
      <Stack sx={{ px: 2, pt: 1, pb: 2 }}>
        <Divider />
        <Stack direction="row" alignItems="center" justifyContent="flex-end" sx={{ pt: 1 }}>
          <Button
            variant="text"
            size="small"
            color="primary"
            onClick={() => {
              onSave({
                ...item,
                attributes: existingFields,
              });
            }}>
            <Typography variant="body2" fontWeight="bold" color="inherit">
              {t("common:save")}
            </Typography>
          </Button>
        </Stack>
      </Stack>
    </Box>
  );
};

const InteractionContentPopper = ({
  layer,
  editingContentItem,
  anchorEl,
  onSave,
}: {
  layer: ProjectLayer;
  editingContentItem: LayerInteractionContent;
  anchorEl: HTMLElement | null;
  onSave: (item: LayerInteractionContent) => void;
}) => {
  return (
    <Popper
      open={editingContentItem !== null}
      anchorEl={anchorEl}
      transition
      sx={{ zIndex: 1250 }}
      placement="left"
      modifiers={[
        {
          name: "offset",
          options: {
            offset: [0, 75],
          },
        },
      ]}>
      {({ TransitionProps }) => (
        <Fade {...TransitionProps}>
          <Box sx={{ bgcolor: "background.paper", borderRadius: 1 }}>
            <>
              {editingContentItem.type === layerInteractionContentType.Enum.field_list && (
                <InteractionFieldListOptions
                  layer={layer}
                  item={editingContentItem}
                  onSave={(item) => {
                    onSave(item);
                  }}
                />
              )}
            </>
          </Box>
        </Fade>
      )}
    </Popper>
  );
};

const InteractionOptions = ({
  layer,
  onStyleChange,
}: {
  layer: ProjectLayer;
  onStyleChange?: (newStyle: FeatureLayerProperties) => void;
}) => {
  const { t } = useTranslation("common");
  const theme = useTheme();
  const { interactionOptions, contentTypes } = useInteractionOptions(layer);

  const selectedInteractionOption = useMemo(() => {
    if (!layer?.properties?.interaction?.type) {
      return interactionOptions.find((option) => option.value === layerInteractionType.Enum.click);
    }

    return interactionOptions.find((option) => option.value === layer?.properties?.interaction?.type);
  }, [interactionOptions, layer?.properties?.interaction?.type]);

  const interactionContents = useMemo(() => {
    return (
      layer?.properties?.interaction?.content?.map((content) => ({
        ...content,
        id: content.id || v4(),
      })) || []
    );
  }, [layer?.properties?.interaction]);

  const [addContentAnchorEl, setAddContentAnchorEl] = useState<null | HTMLElement>(null);
  const [contentPopoverAnchorEl, setContentPopoverAnchorEl] = useState<null | HTMLElement>(null);
  const handleContentAddOnClick = (event: React.MouseEvent<HTMLButtonElement>) => {
    setAddContentAnchorEl(event.currentTarget);
  };
  const handleAddContentOnClose = () => {
    setAddContentAnchorEl(null);
  };
  const open = Boolean(addContentAnchorEl);

  const addContent = (contentType: LayerInteractionContentType) => {
    const newStyle = JSON.parse(JSON.stringify(layer.properties)) || {};
    newStyle.interaction = {
      ...newStyle.interaction,
      content: newStyle.interaction?.content || [],
    };
    if (contentType === layerInteractionContentType.Enum.field_list) {
      // Add an empty field list to the interaction properties
      const fieldList = interactionFieldListContent.safeParse({});
      if (fieldList.success) {
        const newContent: LayerInteractionContent = {
          id: fieldList.data.id || v4(),
          type: contentType,
          attributes: [],
        };
        newStyle.interaction.content.push(newContent);
      }
    } else if (contentType === layerInteractionContentType.Enum.image) {
      const image = interactionImageContent.safeParse({});
      if (image.success) {
        const newContent: LayerInteractionContent = {
          id: image.data.id || v4(),
          type: contentType,
          url: "",
        };
        newStyle.interaction.content.push(newContent);
      }
    } else {
      console.error("Unsupported content type:", contentType);
      return;
    }

    onStyleChange?.(newStyle);
  };

  const [editingContentItem, setEditingContentItem] = useState<LayerInteractionContent | undefined>(
    undefined
  );

  function handleDragEnd(event: DragEndEvent) {
    const { active, over } = event;
    const oldIndex = interactionContents.findIndex((value) => value.id === active.id);
    const newIndex = interactionContents.findIndex((value) => value.id === over?.id);
    const newOrderArray = arrayMove(interactionContents, oldIndex, newIndex);
    if (onStyleChange) {
      const newStyle = JSON.parse(JSON.stringify(layer.properties)) || {};
      newStyle.interaction = {
        ...newStyle.interaction,
        content: newOrderArray,
      };
      onStyleChange(newStyle);
    }
  }

  function deleteContent(item: LayerInteractionContent) {
    const newContents = interactionContents.filter((content) => content.id !== item.id);
    if (onStyleChange) {
      const newStyle = JSON.parse(JSON.stringify(layer.properties)) || {};
      newStyle.interaction = {
        ...newStyle.interaction,
        content: newContents,
      };
      onStyleChange(newStyle);
    }
    if (editingContentItem?.id === item.id) {
      setEditingContentItem(undefined);
    }
  }

  return (
    <>
      {editingContentItem && (
        <InteractionContentPopper
          layer={layer}
          editingContentItem={editingContentItem}
          anchorEl={contentPopoverAnchorEl}
          onSave={(item: LayerInteractionContent) => {
            const newStyle = JSON.parse(JSON.stringify(layer.properties)) || {};
            newStyle.interaction = {
              ...newStyle.interaction,
              content: newStyle.interaction?.content?.map((content) =>
                content.id === item.id ? item : content
              ) || [item],
            };
            onStyleChange?.(newStyle);
            setEditingContentItem(undefined);
          }}
        />
      )}

      <SectionHeader active alwaysActive label={t("options")} disableAdvanceOptions />
      <SectionOptions
        active={true}
        baseOptions={
          <Selector
            selectedItems={selectedInteractionOption}
            setSelectedItems={(item: SelectorItem | undefined) => {
              if (item) {
                const newStyle = JSON.parse(JSON.stringify(layer.properties)) || {};
                newStyle.interaction = {
                  ...newStyle.interaction,
                  type: item.value as LayerInteractionContentType,
                };
                onStyleChange?.(newStyle);
              }
            }}
            items={interactionOptions}
            label={t("show")}
            placeholder={t("show_popup_on")}
          />
        }
        collapsed={false}
      />

      <SectionHeader active alwaysActive label={t("content")} disableAdvanceOptions />
      <SectionOptions
        active={true}
        baseOptions={
          <div>
            <Box sx={{ maxHeight: "340px", overflowY: "auto" }}>
              <SortableWrapper handleDragEnd={handleDragEnd} items={interactionContents}>
                {interactionContents?.map((item) => (
                  <SortableItem
                    active={item.id === editingContentItem?.id}
                    key={item.id}
                    item={item}
                    label={t(`${item.type}`)}
                    actions={
                      <>
                        <Icon
                          sx={{
                            transition: theme.transitions.create(["color", "transform"], {
                              duration: theme.transitions.duration.standard,
                            }),
                            "&:hover": {
                              cursor: "pointer",
                              color: theme.palette.error.main,
                            },
                          }}
                          onClick={() => deleteContent(item)}
                          iconName={ICON_NAME.TRASH}
                          style={{
                            fontSize: 12,
                          }}
                          htmlColor="inherit"
                        />
                      </>
                    }>
                    <Stack
                      direction="row"
                      spacing={2}
                      alignItems="center"
                      onClick={(e) => {
                        if (editingContentItem?.id === item.id) {
                          setEditingContentItem(undefined);
                        } else {
                          setEditingContentItem(item);
                          setContentPopoverAnchorEl(e.currentTarget);
                        }
                        e.stopPropagation();
                      }}
                      sx={{
                        py: 1,
                        pr: 0,
                        "&:hover": {
                          color: "primary.main",
                        },
                      }}>
                      <Icon
                        iconName={
                          contentTypes.find((type) => type.value === item.type)?.icon || ICON_NAME.CIRCLEINFO
                        }
                        color={item.id === editingContentItem?.id ? "primary" : "secondary"}
                        style={{
                          fontSize: 15,
                        }}
                        htmlColor="inherit"
                      />
                      <OverflowTypograpy variant="body2" fontWeight="bold">
                        {t(item.type)}
                      </OverflowTypograpy>
                    </Stack>
                  </SortableItem>
                ))}
              </SortableWrapper>
            </Box>

            <Stack spacing={2} sx={{ pt: 4 }}>
              <Button
                onClick={handleContentAddOnClick}
                fullWidth
                variant="text"
                size="small"
                startIcon={<Icon iconName={ICON_NAME.PLUS} style={{ fontSize: "15px" }} />}>
                <Typography variant="body2" fontWeight="bold" color="inherit">
                  {t("common:add_content")}
                </Typography>
              </Button>

              <Menu
                anchorEl={addContentAnchorEl}
                sx={{
                  "& .MuiPaper-root": {
                    boxShadow: "0px 0px 10px 0px rgba(58, 53, 65, 0.1)",
                  },
                }}
                anchorOrigin={{ vertical: "top", horizontal: "center" }}
                transformOrigin={{ vertical: "bottom", horizontal: "center" }}
                open={open}
                MenuListProps={{
                  "aria-labelledby": "basic-button",
                  sx: {
                    width: addContentAnchorEl && addContentAnchorEl.offsetWidth - 10,
                    p: 0,
                  },
                }}
                onClose={handleAddContentOnClose}>
                <Box>
                  <ClickAwayListener onClickAway={handleAddContentOnClose}>
                    <MenuList>
                      {contentTypes.map((item, index) => (
                        <MenuItem
                          key={index}
                          onClick={() => {
                            addContent(item.value as LayerInteractionContentType);
                            handleAddContentOnClose();
                          }}>
                          {item.icon && (
                            <ListItemIcon>
                              <Icon iconName={item.icon} style={{ fontSize: "15px" }} />
                            </ListItemIcon>
                          )}
                          <Typography variant="body2">{item.label}</Typography>
                        </MenuItem>
                      ))}
                    </MenuList>
                  </ClickAwayListener>
                </Box>
              </Menu>
            </Stack>
          </div>
        }
        collapsed={false}
      />
    </>
  );
};

export default InteractionOptions;
