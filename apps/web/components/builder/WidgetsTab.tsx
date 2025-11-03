import { useDraggable } from "@dnd-kit/core";
import { Search as SearchIcon } from "@mui/icons-material";
import { Box, Grid, InputAdornment, Stack, TextField } from "@mui/material";
import React, { useMemo, useState } from "react";

import { useTranslation } from "@/i18n/client";

import type { WidgetTypes } from "@/lib/validations/widget";
import { chartTypes, dataTypes, elementTypes, informationTypes } from "@/lib/validations/widget";

import { DraggableItem } from "@/components/builder/widgets/common/DraggableItem";
import SettingsGroupHeader from "@/components/builder/widgets/common/SettingsGroupHeader";

function Draggable(props) {
  const Element = props.element || "div";
  const { attributes, listeners, setNodeRef } = useDraggable({
    id: props.id,
    data: {
      config: {
        type: props.id,
      },
    },
  });

  return (
    <Element ref={setNodeRef} {...listeners} {...attributes}>
      {props.children}
    </Element>
  );
}

const WidgetTab = () => {
  const { t } = useTranslation("common");
  const [searchTerm, setSearchTerm] = useState("");
  const sections = useMemo(
    () => [
      {
        group: "information",
        widgets: [
          informationTypes.enum.layers,
          // informationTypes.enum.bookmarks, //Todo
          // informationTypes.enum.comments, //Todo
        ] as WidgetTypes[],
      },
      {
        group: "data",
        widgets: [
          dataTypes.enum.filter,
          // dataTypes.enum.table, //Todo
          dataTypes.enum.numbers,
          // dataTypes.enum.feature_list, //Todo
        ] as WidgetTypes[],
      },
      {
        group: "charts",
        widgets: [
          chartTypes.enum.categories_chart,
          chartTypes.enum.histogram_chart,
          chartTypes.enum.pie_chart,
        ] as WidgetTypes[],
      },
      {
        group: "project_elements",
        widgets: [
          elementTypes.enum.text,
          elementTypes.enum.divider,
          elementTypes.enum.image,
        ] as WidgetTypes[],
      },
    ],
    []
  );

  const filteredSections = useMemo(() => {
    if (!searchTerm) {
      return sections;
    }
    const lowerSearchTerm = searchTerm.toLowerCase();
    return sections
      .map((section) => ({
        ...section,
        widgets: section.widgets.filter((widget) => {
          const translatedWidgetName = t(widget).toLowerCase();
          const originalWidgetKey = widget.toLowerCase();
          return (
            translatedWidgetName.includes(lowerSearchTerm) || originalWidgetKey.includes(lowerSearchTerm)
          );
        }),
      }))
      .filter((section) => section.widgets.length > 0);
  }, [sections, searchTerm, t]);
  return (
    <>
      <Stack direction="column" height="100%" width="100%">
        <TextField
          fullWidth
          placeholder={t("search")}
          sx={{ p: 3 }}
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon fontSize="small" />
              </InputAdornment>
            ),
          }}
          size="small"
        />
        {/* Scrollable Content */}
        <Box
          sx={{
            flex: 1,
            overflowY: "auto", // Enable vertical scrolling
            height: "100%",
          }}>
          <Stack spacing={4} sx={{ p: 3 }}>
            <Box>
              {filteredSections.map((section) => (
                <Box key={section.group} sx={{ mb: 8 }}>
                  <SettingsGroupHeader label={t(section.group)} />
                  <Grid container spacing={4}>
                    {section.widgets.map((widget) => (
                      <Grid item xs={6} key={widget}>
                        <Draggable id={widget}>
                          <DraggableItem widgetType={widget} />
                        </Draggable>
                      </Grid>
                    ))}
                  </Grid>
                </Box>
              ))}
            </Box>
          </Stack>
        </Box>
      </Stack>
    </>
  );
};

export default WidgetTab;
