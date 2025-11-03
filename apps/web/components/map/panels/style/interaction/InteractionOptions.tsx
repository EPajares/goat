import type { DragEndEvent } from "@dnd-kit/core";
import { arrayMove } from "@dnd-kit/sortable";
import {
  Box,
  Button,
  ClickAwayListener,
  Divider,
  Fade,
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
import { useMemo, useState } from "react";
import { v4 } from "uuid";

import { ICON_NAME, Icon } from "@p4b/ui/components/Icon";

import { useTranslation } from "@/i18n/client";

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

import { OverflowTypograpy } from "@/components/common/OverflowTypography";
import { FieldTypeTag } from "@/components/map/common/LayerFieldSelector";
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
  const { t } = useTranslation("common");
  const theme = useTheme();
  const [addContentAnchorEl, setAddContentAnchorEl] = useState<null | HTMLElement>(null);
  const [existingFields, setExistingFields] = useState(item.attributes || []);
  const open = Boolean(addContentAnchorEl);
  const handleAddContentOnClose = () => {
    setAddContentAnchorEl(null);
  };
  const handleContentAddOnClick = (event: React.MouseEvent<HTMLButtonElement>) => {
    setAddContentAnchorEl(event.currentTarget);
  };

  const { layerFields } = useLayerFields(layer?.layer_id || "");

  const unAddedFields = useMemo(() => {
    return layerFields.filter((field) => !existingFields.some((attr) => attr.name === field.name));
  }, [layerFields, existingFields]);

  const addField = (field: { name: string; type: string }) => {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    setExistingFields([...existingFields, { name: field.name, type: field.type as any }]);
  };

  const handleDragEnd = (event: DragEndEvent) => {
    console.log("Drag End Event:", event);
    const { active, over } = event;
    const oldIndex = existingFields.findIndex((value) => value.name === active.id);
    const newIndex = existingFields.findIndex((value) => value.name === over?.id);
    const newOrderArray = arrayMove(existingFields, oldIndex, newIndex);
    setExistingFields(newOrderArray);
  };

  return (
    <Box sx={{ minWidth: "400px", maxHeight: "400px", overflowY: "auto" }}>
      <Typography variant="body2" fontWeight="bold" gutterBottom sx={{ p: 2 }}>
        {t("field_list")}
      </Typography>
      <Box sx={{ mb: 2, maxHeight: "210px", overflowY: "auto" }}>
        <SortableWrapper
          handleDragEnd={handleDragEnd}
          items={existingFields.map((field) => ({ ...field, id: field.name }))}>
          {existingFields.map((field) => (
            <SortableItem
              key={field.name}
              item={{ ...field, id: field.name }}
              label={field.name}
              active={false}
              actions={
                <Icon
                  sx={{
                    transition: (theme) =>
                      theme.transitions.create(["color", "transform"], {
                        duration: theme.transitions.duration.standard,
                      }),
                    "&:hover": {
                      cursor: "pointer",
                      color: theme.palette.error.main,
                    },
                  }}
                  onClick={() => {
                    setExistingFields(existingFields.filter((f) => f.name !== field.name));
                  }}
                  iconName={ICON_NAME.TRASH}
                  style={{ fontSize: 12 }}
                  htmlColor="inherit"
                />
              }>
              <Stack
                direction="row"
                spacing={2}
                alignItems="center"
                sx={{
                  py: 1,
                  pr: 0,
                  "&:hover": {
                    color: "primary.main",
                  },
                }}>
                <FieldTypeTag fieldType={field.type}>{field.type}</FieldTypeTag>
                <OverflowTypograpy variant="body2" fontWeight="bold" sx={{ minWidth: "100px" }}>
                  {field.name}
                </OverflowTypograpy>
                <Box sx={{ flexGrow: 1, width: "100%" }}>
                  <TextField
                    value={field.label || ""}
                    inputProps={{ style: { fontSize: 13 } }}
                    onChange={(e) => {
                      const newFields = existingFields.map((f) =>
                        f.name === field.name ? { ...f, label: e.target.value } : f
                      );
                      setExistingFields(newFields);
                    }}
                    fullWidth
                    variant="outlined"
                    size="small"
                  />
                </Box>
              </Stack>
            </SortableItem>
          ))}
        </SortableWrapper>
      </Box>

      <Stack spacing={2} height="100%" sx={{ overflowY: "auto", maxHeight: "300px", px: 2, pt: 2, pb: 0 }}>
        {/* Add any specific options for field list content here */}
        <Button
          variant="outlined"
          size="small"
          onClick={handleContentAddOnClick}
          disabled={unAddedFields.length === 0}>
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
            "aria-labelledby": "basic-button",
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
                    setExistingFields(
                      // eslint-disable-next-line @typescript-eslint/no-explicit-any
                      layerFields.map((field) => ({ name: field.name, type: field.type as any }))
                    );
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
                    <FieldTypeTag fieldType={field.type}>{field.type}</FieldTypeTag>
                    <Typography variant="body2">{field.name}</Typography>
                  </MenuItem>
                ))}
              </MenuList>
            </ClickAwayListener>
          </Box>
        </Menu>
      </Stack>
      <Stack sx={{ p: 2 }}>
        <Divider />
        <Stack direction="row" alignItems="center" justifyContent="flex-end" sx={{ px: 2 }}>
          <Button
            variant="text"
            size="small"
            color="primary"
            sx={{ borderRadius: 0 }}
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
      sx={{ zIndex: 2000 }}
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
        <ClickAwayListener onClickAway={() => setEditingContentItem(undefined)}>
          <Box>
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
          </Box>
        </ClickAwayListener>
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
        advancedOptions={<></>}
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
                        setEditingContentItem(item);
                        setContentPopoverAnchorEl(e.currentTarget);
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
        advancedOptions={<></>}
        collapsed={false}
      />
    </>
  );
};

export default InteractionOptions;
