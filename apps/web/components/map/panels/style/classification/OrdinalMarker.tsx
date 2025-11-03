import type { DragEndEvent } from "@dnd-kit/core";
import { arrayMove } from "@dnd-kit/sortable";
import { Box, Button, Chip, IconButton, Stack, Tooltip, Typography, useTheme } from "@mui/material";
import React from "react";
import { v4 } from "uuid";

import { ICON_NAME, Icon } from "@p4b/ui/components/Icon";

import { useTranslation } from "@/i18n/client";

import type { MarkerMap } from "@/lib/validations/layer";

import type { MarkerItem, MarkerMapItem, OrdinalMarkerSelectorProps, ValueItem } from "@/types/map/marker";

import { OverflowTypograpy } from "@/components/common/OverflowTypography";
import MarkerPopper from "@/components/map/panels/style/marker/MarkerPopper";
import DropdownFooter from "@/components/map/panels/style/other/DropdownFooter";
import { LayerValueSelectorPopper } from "@/components/map/panels/style/other/LayerValueSelectorPopper";
import { MaskedImageIcon } from "@/components/map/panels/style/other/MaskedImageIcon";
import { SortableItem } from "@/components/map/panels/style/other/SortableItem";
import SortableWrapper from "@/components/map/panels/style/other/SortableWrapper";

const OrdinalMarker = (props: OrdinalMarkerSelectorProps) => {
  const theme = useTheme();
  const { markerMaps, activeLayerField, activeLayerId } = props;
  const { t } = useTranslation("common");
  const [valueMaps, setValueMaps] = React.useState<MarkerMapItem[]>(
    markerMaps.map((markerMap) => {
      return {
        id: v4(),
        value: markerMap[0],
        marker: markerMap[1],
      };
    }) || []
  );

  const [editingMarkerItem, setEditingMarkerItem] = React.useState<MarkerItem | null>(null);
  const [editingValues, setEditingValues] = React.useState<ValueItem | null>(null);
  const [anchorEl, setAnchorEl] = React.useState<HTMLElement | null>(null);

  function onMarkerChange(item: MarkerItem) {
    const index = valueMaps.findIndex((marker: MarkerMapItem) => marker.id === item.id);
    if (index !== -1) {
      const newMarkerMaps = [...valueMaps];
      newMarkerMaps[index] = {
        ...newMarkerMaps[index],
        marker: item.marker,
      };
      setValueMaps(newMarkerMaps);
    }
    setEditingMarkerItem(null);
  }

  function handleDragEnd(event: DragEndEvent) {
    const { active, over } = event;
    const oldIndex = valueMaps.findIndex((marker) => marker.id === active.id);
    const newIndex = valueMaps.findIndex((marker) => marker.id === over?.id);
    const newOrderArray = arrayMove(valueMaps, oldIndex, newIndex);
    setValueMaps(newOrderArray);
  }

  function deleteStep(item: MarkerItem) {
    if (valueMaps.length === 1) {
      return;
    }
    const index = valueMaps.findIndex((marker) => marker.id === item.id);
    if (index !== -1) {
      const newMarkerMaps = [...valueMaps];
      newMarkerMaps.splice(index, 1);
      setValueMaps(newMarkerMaps);
    }
  }

  const handleMarkerPicker = (event: React.MouseEvent<HTMLElement, MouseEvent>, item: MarkerItem) => {
    setEditingMarkerItem(item);
    setAnchorEl(event.currentTarget);
  };

  const handleValueSelector = (event: React.MouseEvent<HTMLElement, MouseEvent>, item: MarkerMapItem) => {
    const valueItem = {
      id: item.id,
      values: item.value,
    };
    setEditingValues(valueItem);
    setAnchorEl(event.currentTarget);
  };

  const handleAddStep = () => {
    const newMarkerMaps = [...valueMaps];
    newMarkerMaps.push({
      id: v4(),
      value: null,
      marker: {
        name: "",
        url: "",
        category: "",
        source: "library",
        id: "",
      },
    });
    setValueMaps(newMarkerMaps);
  };

  const handleValueSelectorChange = (values: string[] | null) => {
    const updatedValues = [] as MarkerMapItem[];
    valueMaps.forEach((value) => {
      if (value.id === editingValues?.id) {
        const updatedSelectedValue = {
          ...value,
          value: values,
        };
        updatedValues.push(updatedSelectedValue);
      } else {
        // check if the values are already in other valueMaps (not selected). If yes, remove it
        if (Array.isArray(value.value) && values?.length) {
          const updatedOtherValues = value.value.filter((item) => !values.includes(item));
          updatedValues.push({
            ...value,
            value: updatedOtherValues?.length ? updatedOtherValues : null,
          });
        } else {
          // already null
          updatedValues.push(value);
        }
      }
    });

    setValueMaps(updatedValues);
    editingValues && setEditingValues({ ...editingValues, values });
  };

  function onCancel() {
    props.onCancel && props.onCancel();
  }

  function onApply() {
    const markerMaps = [] as MarkerMap;
    valueMaps.forEach((item) => {
      markerMaps.push([item.value, item.marker]);
    });
    props.onCustomApply && props.onCustomApply(markerMaps);
  }

  return (
    <>
      <MarkerPopper
        anchorEl={anchorEl}
        selectedMarker={editingMarkerItem?.marker}
        onClose={() => {
          setEditingMarkerItem(null);
          setEditingValues(null);
        }}
        open={!!editingMarkerItem}
        onSelectMarker={(marker) => onMarkerChange({ id: editingMarkerItem?.id || "", marker })}
        popperProps={{
          modifiers: [
            {
              name: "offset",
              options: { offset: [0, 80] },
            },
          ],
        }}
      />
      {editingValues && (
        <LayerValueSelectorPopper
          open={!!editingValues?.id}
          layerId={activeLayerId}
          selectedValues={editingValues.values}
          fieldName={activeLayerField?.name || ""}
          anchorEl={anchorEl}
          onSelectedValuesChange={handleValueSelectorChange}
          onDone={() => setEditingValues(null)}
        />
      )}
      <Box
        sx={{ py: 3 }}
        onClick={() => {
          setEditingValues(null);
          setEditingMarkerItem(null);
        }}>
        <Box sx={{ maxHeight: "340px", overflowY: "auto" }}>
          <SortableWrapper handleDragEnd={handleDragEnd} items={valueMaps}>
            {valueMaps?.map((item: MarkerMapItem) => (
              <SortableItem
                active={item.id === editingMarkerItem?.id || item.id === editingValues?.id}
                key={item.id}
                item={item}
                label={item.marker?.name || t("select_marker")}
                picker={
                  <>
                    <IconButton
                      size="small"
                      color="secondary"
                      onClick={(e) => {
                        setEditingValues(null);
                        e.stopPropagation();
                        const markerItem = {
                          id: item.id,
                          marker: item.marker,
                        } as MarkerItem;
                        handleMarkerPicker(e, markerItem);
                      }}>
                      {!item.marker.name && (
                        <Icon
                          iconName={ICON_NAME.ADD_IMAGE}
                          style={{
                            fontSize: 19,
                          }}
                          htmlColor="inherit"
                        />
                      )}
                      {item.marker.url && (
                        <MaskedImageIcon
                          imageUrl={`${item.marker.url}`}
                          dimension="19px"
                          applyMask={item.marker?.source === "custom" ? false : true}
                        />
                      )}
                    </IconButton>
                  </>
                }
                actions={
                  <>
                    <IconButton onClick={() => deleteStep(item)}>
                      <Icon
                        iconName={ICON_NAME.TRASH}
                        style={{
                          fontSize: 12,
                        }}
                        htmlColor="inherit"
                      />
                    </IconButton>
                  </>
                }>
                <Stack
                  direction="row"
                  sx={{
                    py: 1,
                    pr: 0,
                    "&:hover": {
                      color: "primary.main",
                    },
                  }}>
                  <OverflowTypograpy
                    variant="body2"
                    fontWeight="bold"
                    onClick={(e) => {
                      setEditingMarkerItem(null);
                      e.stopPropagation();
                      handleValueSelector(e, item);
                    }}
                    sx={{
                      ...(item.id === editingValues?.id && {
                        color: theme.palette.primary.main,
                      }),
                      transition: theme.transitions.create(["color", "transform"], {
                        duration: theme.transitions.duration.standard,
                      }),
                      "&:hover": {
                        cursor: "pointer",
                        color: theme.palette.primary.main,
                      },
                    }}
                    tooltipProps={{
                      placement: "top",
                      arrow: true,
                      enterDelay: 200,
                    }}>
                    <>{item.value?.length ? item.value[0] : t("assign_values")}</>
                  </OverflowTypograpy>
                  {item?.value?.length && item.value.length > 1 && (
                    <Tooltip
                      placement="top"
                      arrow
                      title={
                        <div style={{ whiteSpace: "pre-line" }}>
                          {item.value.slice(0, 4).join("\n")}
                          {item.value.length > 4 && "\n ..."}
                        </div>
                      }>
                      <Chip size="small" sx={{ ml: 2 }} label={`+${item.value.length - 1}`} />
                    </Tooltip>
                  )}
                </Stack>
              </SortableItem>
            ))}
          </SortableWrapper>
          <Button
            onClick={handleAddStep}
            variant="text"
            sx={{ borderRadius: 0, ml: 4, my: 2 }}
            size="small"
            startIcon={<Icon iconName={ICON_NAME.PLUS} style={{ fontSize: "15px" }} />}>
            <Typography variant="body2" fontWeight="bold" color="inherit">
              {t("common:add_step")}
            </Typography>
          </Button>
        </Box>
        <DropdownFooter isValid={true} onCancel={onCancel} onApply={onApply} />
      </Box>
    </>
  );
};

export default OrdinalMarker;
