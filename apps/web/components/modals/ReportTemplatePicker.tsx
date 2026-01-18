"use client";

import {
  Box,
  Button,
  Collapse,
  Dialog,
  DialogContent,
  Divider,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Paper,
  Stack,
  Typography,
} from "@mui/material";
import { useTheme } from "@mui/material/styles";
import React, { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";

import { ICON_NAME, Icon } from "@p4b/ui/components/Icon";

import type { ReportLayoutConfig } from "@/lib/validations/reportLayout";
import type { ProjectViewState } from "@/lib/validations/project";

// Default viewState (Munich) - used as fallback when project viewState is not available
const DEFAULT_VIEW_STATE = {
  latitude: 48.13,
  longitude: 11.57,
  zoom: 10,
  bearing: 0,
  pitch: 0,
};

export type ReportTemplateType =
  | "single_map_portrait"
  | "single_map_landscape"
  | "poster_portrait"
  | "poster_landscape"
  | "blank";

export type ReportTemplateCategory = "single_map" | "poster" | "blank";

export interface ReportTemplate {
  id: ReportTemplateType;
  categoryId: ReportTemplateCategory;
  name: string;
  displayName: string;
  description: string;
  config: ReportLayoutConfig;
}

// Type for translation function
type TranslationFn = (key: string) => string;

// Type for viewState parameter in template config functions
type ViewStateParam = {
  latitude: number;
  longitude: number;
  zoom: number;
  bearing: number;
  pitch: number;
};

// Default config for blank template
const getBlankConfig = (): ReportLayoutConfig => ({
  page: {
    size: "A4",
    orientation: "portrait",
    margins: { top: 10, right: 10, bottom: 10, left: 10 },
    snapToGuides: true,
    showRulers: false,
  },
  layout: {
    type: "grid",
    columns: 12,
    rows: 12,
    gap: 5,
  },
  elements: [],
});

// Single map template - portrait orientation (A4)
// A4: 210x297mm, with 10mm margins = usable area 190x277mm (from x:10 to x:200, y:10 to y:287)
const getSingleMapPortraitConfig = (t: TranslationFn, viewState: ViewStateParam): ReportLayoutConfig => ({
  page: {
    size: "A4",
    orientation: "portrait",
    margins: { top: 10, right: 10, bottom: 10, left: 10 },
    snapToGuides: true,
    showRulers: false,
  },
  layout: {
    type: "grid",
    columns: 12,
    rows: 12,
    gap: 5,
  },
  elements: [
    // Title - top full width
    {
      id: "text-title",
      type: "text",
      position: { x: 10, y: 10, width: 190, height: 15, z_index: 2 },
      config: {
        type: "text",
        setup: { text: `<h1 style="text-align: center">${t("title_placeholder")}</h1>` },
      },
      style: { padding: 0, opacity: 1 },
    },
    // Map - large area below title
    {
      id: "map-1",
      type: "map",
      position: { x: 10, y: 28, width: 190, height: 210, z_index: 1 },
      config: {
        viewState,
      },
      style: {
        padding: 0,
        opacity: 1,
        border: { enabled: true, color: "#cccccc", width: 0.5 },
      },
    },
    // Description - bottom left
    {
      id: "text-desc",
      type: "text",
      position: { x: 10, y: 242, width: 50, height: 45, z_index: 3 },
      config: {
        type: "text",
        setup: { text: `<p>${t("description_placeholder")}</p>` },
      },
      style: { padding: 0, opacity: 1 },
    },
    // Legend - bottom center
    {
      id: "legend-1",
      type: "legend",
      position: { x: 65, y: 242, width: 80, height: 45, z_index: 4 },
      config: {
        mapElementId: "map-1",
      },
      style: { padding: 0, opacity: 1, background: { enabled: true, color: "#ffffff", opacity: 0.9 } },
    },
    // Logo - bottom right
    {
      id: "image-logo",
      type: "image",
      position: { x: 150, y: 242, width: 50, height: 45, z_index: 5 },
      config: {
        url: "https://assets.plan4better.de/img/logo/plan4better_standard.svg",
      },
      style: { padding: 0, opacity: 1 },
    },
  ],
});

// Single map template - landscape orientation (A4)
// A4 landscape: 297x210mm, with 10mm margins = usable area 277x190mm (from x:10 to x:287, y:10 to y:200)
const getSingleMapLandscapeConfig = (t: TranslationFn, viewState: ViewStateParam): ReportLayoutConfig => ({
  page: {
    size: "A4",
    orientation: "landscape",
    margins: { top: 10, right: 10, bottom: 10, left: 10 },
    snapToGuides: true,
    showRulers: false,
  },
  layout: {
    type: "grid",
    columns: 12,
    rows: 12,
    gap: 5,
  },
  elements: [
    // Title - top full width
    {
      id: "text-title",
      type: "text",
      position: { x: 10, y: 10, width: 277, height: 15, z_index: 2 },
      config: {
        type: "text",
        setup: { text: `<h1 style="text-align: center">${t("title_placeholder")}</h1>` },
      },
      style: { padding: 0, opacity: 1 },
    },
    // Map - large area on left
    {
      id: "map-1",
      type: "map",
      position: { x: 10, y: 28, width: 220, height: 162, z_index: 1 },
      config: {
        viewState,
      },
      style: {
        padding: 0,
        opacity: 1,
        border: { enabled: true, color: "#cccccc", width: 0.5 },
      },
    },
    // Description - right column top
    {
      id: "text-desc",
      type: "text",
      position: { x: 235, y: 28, width: 52, height: 40, z_index: 3 },
      config: {
        type: "text",
        setup: { text: `<p>${t("description_placeholder")}</p>` },
      },
      style: { padding: 0, opacity: 1 },
    },
    // Legend - right column middle
    {
      id: "legend-1",
      type: "legend",
      position: { x: 235, y: 73, width: 52, height: 80, z_index: 4 },
      config: {
        mapElementId: "map-1",
      },
      style: { padding: 0, opacity: 1, background: { enabled: true, color: "#ffffff", opacity: 0.9 } },
    },
    // Logo - right column bottom
    {
      id: "image-logo",
      type: "image",
      position: { x: 235, y: 158, width: 52, height: 32, z_index: 5 },
      config: {
        url: "https://assets.plan4better.de/img/logo/plan4better_standard.svg",
      },
      style: { padding: 0, opacity: 1 },
    },
  ],
});

// Poster template - portrait orientation (A3)
// A3 portrait: 297x420mm, with 10mm margins = usable area 277x400mm (from x:10 to x:287, y:10 to y:410)
const getPosterPortraitConfig = (t: TranslationFn, viewState: ViewStateParam): ReportLayoutConfig => ({
  page: {
    size: "A3",
    orientation: "portrait",
    margins: { top: 10, right: 10, bottom: 10, left: 10 },
    snapToGuides: true,
    showRulers: false,
  },
  layout: {
    type: "grid",
    columns: 12,
    rows: 12,
    gap: 5,
  },
  elements: [
    // Title - top left
    {
      id: "text-title",
      type: "text",
      position: { x: 10, y: 10, width: 200, height: 20, z_index: 2 },
      config: {
        type: "text",
        setup: { text: `<h1 style="text-align: left">${t("poster_title_placeholder")}</h1>` },
      },
      style: { padding: 0, opacity: 1 },
    },
    // Subtitle - below title
    {
      id: "text-subtitle",
      type: "text",
      position: { x: 10, y: 33, width: 200, height: 25, z_index: 3 },
      config: {
        type: "text",
        setup: { text: `<p>${t("subtitle_placeholder")}</p>` },
      },
      style: { padding: 0, opacity: 1 },
    },
    // Image/Logo - top right
    {
      id: "image-logo",
      type: "image",
      position: { x: 227, y: 10, width: 60, height: 48, z_index: 7 },
      config: {
        url: "https://assets.plan4better.de/img/logo/plan4better_standard.svg",
      },
      style: { padding: 0, opacity: 1 },
    },
    // Map - large center area
    {
      id: "map-1",
      type: "map",
      position: { x: 10, y: 63, width: 277, height: 337, z_index: 1 },
      config: {
        viewState,
      },
      style: {
        padding: 0,
        opacity: 1,
        border: { enabled: true, color: "#cccccc", width: 0.5 },
      },
    },
    // North arrow - bottom left on map
    {
      id: "north-1",
      type: "north_arrow",
      position: { x: 15, y: 375, width: 20, height: 20, z_index: 5 },
      config: {
        style: "circle",
        mapElementId: "map-1",
      },
      style: { padding: 0, opacity: 1 },
    },
    // Legend - bottom right on map
    {
      id: "legend-1",
      type: "legend",
      position: { x: 242, y: 315, width: 40, height: 80, z_index: 8 },
      config: {
        mapElementId: "map-1",
      },
      style: { padding: 0, opacity: 1, background: { enabled: true, color: "#ffffff", opacity: 0.9 } },
    },
  ],
});

// Poster template - landscape orientation (A3)
// A3 landscape: 420x297mm, with 10mm margins = usable area 400x277mm (from x:10 to x:410, y:10 to y:287)
const getPosterLandscapeConfig = (t: TranslationFn, viewState: ViewStateParam): ReportLayoutConfig => ({
  page: {
    size: "A3",
    orientation: "landscape",
    margins: { top: 10, right: 10, bottom: 10, left: 10 },
    snapToGuides: true,
    showRulers: false,
  },
  layout: {
    type: "grid",
    columns: 12,
    rows: 12,
    gap: 5,
  },
  elements: [
    // Title - top left
    {
      id: "text-title",
      type: "text",
      position: { x: 10, y: 10, width: 90, height: 20, z_index: 2 },
      config: {
        type: "text",
        setup: { text: `<h1 style="text-align: left">${t("poster_title_placeholder")}</h1>` },
      },
      style: { padding: 0, opacity: 1 },
    },
    // Subtitle - below title on left
    {
      id: "text-subtitle",
      type: "text",
      position: { x: 10, y: 33, width: 90, height: 90, z_index: 3 },
      config: {
        type: "text",
        setup: { text: `<p>${t("subtitle_placeholder")}</p>` },
      },
      style: { padding: 0, opacity: 1 },
    },
    // Image/Logo - left side middle
    {
      id: "image-logo",
      type: "image",
      position: { x: 10, y: 128, width: 90, height: 60, z_index: 7 },
      config: {
        url: "https://assets.plan4better.de/img/logo/plan4better_standard.svg",
      },
      style: { padding: 0, opacity: 1 },
    },
    // Text description - left side bottom
    {
      id: "text-desc",
      type: "text",
      position: { x: 10, y: 193, width: 90, height: 84, z_index: 6 },
      config: {
        type: "text",
        setup: { text: `<p>${t("graph_description_placeholder")}</p>` },
      },
      style: { padding: 0, opacity: 1 },
    },
    // Map - large right area
    {
      id: "map-1",
      type: "map",
      position: { x: 105, y: 10, width: 305, height: 267, z_index: 1 },
      config: {
        viewState,
      },
      style: {
        padding: 0,
        opacity: 1,
        border: { enabled: true, color: "#cccccc", width: 0.5 },
      },
    },
    // North arrow - bottom left of map
    {
      id: "north-1",
      type: "north_arrow",
      position: { x: 110, y: 252, width: 20, height: 20, z_index: 5 },
      config: {
        style: "circle",
        mapElementId: "map-1",
      },
      style: { padding: 0, opacity: 1 },
    },
    // Legend - bottom right on map
    {
      id: "legend-1",
      type: "legend",
      position: { x: 365, y: 192, width: 40, height: 80, z_index: 8 },
      config: {
        mapElementId: "map-1",
      },
      style: { padding: 0, opacity: 1, background: { enabled: true, color: "#ffffff", opacity: 0.9 } },
    },
  ],
});

interface TemplateCategory {
  id: ReportTemplateCategory;
  name: string;
  description: string;
  templates: ReportTemplate[];
}

interface ReportTemplatePickerModalProps {
  open: boolean;
  onClose: () => void;
  onSelectTemplate: (template: ReportTemplate) => void;
  initialViewState?: ProjectViewState;
}

const ReportTemplatePickerModal: React.FC<ReportTemplatePickerModalProps> = ({
  open,
  onClose,
  onSelectTemplate,
  initialViewState,
}) => {
  const { t, i18n } = useTranslation("common");
  const theme = useTheme();
  const [selectedTemplate, setSelectedTemplate] = useState<ReportTemplateType>("single_map_portrait");
  const [expandedCategories, setExpandedCategories] = useState<Record<ReportTemplateCategory, boolean>>({
    single_map: true,
    poster: false,
    blank: false,
  });

  // Memoize categories with i18n.language dependency to ensure translations are updated
  // Build viewState from project's initial_view_state or fall back to default
  const viewState: ViewStateParam = useMemo(
    () => ({
      latitude: initialViewState?.latitude ?? DEFAULT_VIEW_STATE.latitude,
      longitude: initialViewState?.longitude ?? DEFAULT_VIEW_STATE.longitude,
      zoom: initialViewState?.zoom ?? DEFAULT_VIEW_STATE.zoom,
      bearing: initialViewState?.bearing ?? DEFAULT_VIEW_STATE.bearing,
      pitch: initialViewState?.pitch ?? DEFAULT_VIEW_STATE.pitch,
    }),
    [initialViewState]
  );

  const categories: TemplateCategory[] = useMemo(
    () => [
      {
        id: "single_map",
        name: t("single_map"),
        description: t("single_map_category_description"),
        templates: [
          {
            id: "single_map_portrait",
            categoryId: "single_map",
            name: `${t("single_map")} - ${t("portrait")}`,
            displayName: t("portrait"),
            description: t("portrait_layout"),
            config: getSingleMapPortraitConfig(t, viewState),
          },
          {
            id: "single_map_landscape",
            categoryId: "single_map",
            name: `${t("single_map")} - ${t("landscape")}`,
            displayName: t("landscape"),
            description: t("landscape_layout"),
            config: getSingleMapLandscapeConfig(t, viewState),
          },
        ],
      },
      {
        id: "poster",
        name: t("poster"),
        description: t("poster_category_description"),
        templates: [
          {
            id: "poster_portrait",
            categoryId: "poster",
            name: `${t("poster")} - ${t("portrait")}`,
            displayName: t("portrait"),
            description: t("portrait_layout"),
            config: getPosterPortraitConfig(t, viewState),
          },
          {
            id: "poster_landscape",
            categoryId: "poster",
            name: `${t("poster")} - ${t("landscape")}`,
            displayName: t("landscape"),
            description: t("landscape_layout"),
            config: getPosterLandscapeConfig(t, viewState),
          },
        ],
      },
      {
        id: "blank",
        name: t("blank"),
        description: t("blank_description"),
        templates: [
          {
            id: "blank",
            categoryId: "blank",
            name: t("blank"),
            displayName: t("blank"),
            description: t("blank_description"),
            config: getBlankConfig(),
          },
        ],
      },
    ],
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [t, i18n.language, viewState]
  );

  const allTemplates = categories.flatMap((cat) => cat.templates);
  const selectedTemplateData = allTemplates.find((t) => t.id === selectedTemplate);

  const toggleCategory = (categoryId: ReportTemplateCategory) => {
    setExpandedCategories((prev) => ({
      ...prev,
      [categoryId]: !prev[categoryId],
    }));
  };

  const handleSelectTemplate = (templateId: ReportTemplateType, categoryId: ReportTemplateCategory) => {
    setSelectedTemplate(templateId);
    // Ensure the category is expanded when selecting a template
    if (!expandedCategories[categoryId]) {
      setExpandedCategories((prev) => ({
        ...prev,
        [categoryId]: true,
      }));
    }
  };

  const handleUseTemplate = () => {
    if (selectedTemplateData) {
      onSelectTemplate(selectedTemplateData);
      onClose();
    }
  };

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="md"
      fullWidth
      PaperProps={{
        sx: {
          borderRadius: 2,
          maxHeight: "80vh",
        },
      }}>
      <DialogContent sx={{ p: 4 }}>
        <Typography variant="h5" fontWeight="bold" gutterBottom>
          {t("templates")}
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
          {t("templates_description")}
        </Typography>

        <Stack direction="row" spacing={3}>
          {/* Template List with Categories */}
          <Box sx={{ width: 280, flexShrink: 0 }}>
            <List disablePadding>
              {categories.map((category, index) => {
                const hasSubTemplates = category.templates.length > 1;
                const isCategorySelected = category.templates.some((t) => t.id === selectedTemplate);
                const isLastCategory = index === categories.length - 1;

                return (
                  <Box key={category.id}>
                    {/* Category Header */}
                    <ListItemButton
                      onClick={() => {
                        if (hasSubTemplates) {
                          toggleCategory(category.id);
                        } else {
                          // For single template categories like "blank", select directly
                          handleSelectTemplate(category.templates[0].id, category.id);
                        }
                      }}
                      sx={{
                        borderRadius: 1,
                        py: 1,
                        "&:hover": {
                          backgroundColor: theme.palette.action.hover,
                        },
                      }}>
                      {hasSubTemplates && (
                        <ListItemIcon sx={{ minWidth: 28 }}>
                          <Icon
                            iconName={
                              expandedCategories[category.id]
                                ? ICON_NAME.CHEVRON_DOWN
                                : ICON_NAME.CHEVRON_RIGHT
                            }
                            fontSize="small"
                            htmlColor={theme.palette.text.secondary}
                          />
                        </ListItemIcon>
                      )}
                      {!hasSubTemplates && (
                        <ListItemIcon sx={{ minWidth: 28 }}>
                          <Icon
                            iconName={ICON_NAME.FILE}
                            fontSize="small"
                            htmlColor={
                              isCategorySelected ? theme.palette.primary.main : theme.palette.text.secondary
                            }
                          />
                        </ListItemIcon>
                      )}
                      <ListItemText
                        primary={
                          <Typography
                            variant="body1"
                            fontWeight={isCategorySelected ? 600 : 500}
                            color={isCategorySelected ? "primary" : "text.primary"}>
                            {category.name}
                          </Typography>
                        }
                        secondary={
                          <Typography variant="caption" color="text.secondary">
                            {category.description}
                          </Typography>
                        }
                      />
                    </ListItemButton>

                    {/* Sub-templates (only for categories with multiple templates) */}
                    {hasSubTemplates && (
                      <Collapse in={expandedCategories[category.id]} timeout="auto" unmountOnExit>
                        <List disablePadding sx={{ pl: 7 }}>
                          {category.templates.map((template) => (
                            <ListItemButton
                              key={template.id}
                              selected={selectedTemplate === template.id}
                              onClick={() => handleSelectTemplate(template.id, category.id)}
                              sx={{
                                borderRadius: 1,
                                mb: 0.5,
                                py: 0.75,
                                "&.Mui-selected": {
                                  backgroundColor: "transparent",
                                },
                                "&.Mui-selected:hover": {
                                  backgroundColor: theme.palette.action.hover,
                                },
                              }}>
                              <ListItemText
                                primary={
                                  <Typography
                                    variant="body2"
                                    fontWeight={selectedTemplate === template.id ? 600 : 400}
                                    color={selectedTemplate === template.id ? "primary" : "text.primary"}>
                                    {template.displayName}
                                  </Typography>
                                }
                              />
                            </ListItemButton>
                          ))}
                        </List>
                      </Collapse>
                    )}

                    {/* Divider between categories */}
                    {!isLastCategory && <Divider sx={{ my: 1.5 }} />}
                  </Box>
                );
              })}
            </List>
          </Box>

          {/* Preview Area */}
          <Box sx={{ flex: 1, display: "flex", flexDirection: "column" }}>
            <Paper
              variant="outlined"
              sx={{
                flex: 1,
                minHeight: 350,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                backgroundColor: theme.palette.grey[100],
                position: "relative",
                overflow: "hidden",
                p: 3,
              }}>
              {/* Preview representation */}
              <TemplatePreview templateId={selectedTemplate} />
            </Paper>

            <Box sx={{ mt: 3, display: "flex", justifyContent: "flex-end" }}>
              <Button
                variant="contained"
                color="primary"
                onClick={handleUseTemplate}
                sx={{ textTransform: "none", px: 3, py: 1 }}>
                {t("use_this_template")}
              </Button>
            </Box>
          </Box>
        </Stack>
      </DialogContent>
    </Dialog>
  );
};

// Visual preview of template layout - matching the actual template configs
const TemplatePreview: React.FC<{ templateId: ReportTemplateType }> = ({ templateId }) => {
  const theme = useTheme();

  const elementStyle = {
    backgroundColor: theme.palette.grey[200],
    border: `1px solid ${theme.palette.grey[300]}`,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    fontSize: 10,
    color: theme.palette.grey[500],
    fontWeight: 500,
  };

  // Single Map Portrait Preview - Title at top, large map below, bottom row with desc/legend/logo
  if (templateId === "single_map_portrait") {
    return (
      <Box
        sx={{
          width: 200,
          height: 280,
          display: "flex",
          flexDirection: "column",
          gap: 1,
        }}>
        {/* Title - top full width */}
        <Box sx={{ ...elementStyle, height: 22 }}>TITLE</Box>
        {/* Map - large center area */}
        <Box sx={{ ...elementStyle, flex: 1 }}>MAP</Box>
        {/* Bottom row: Description | Legend | Logo */}
        <Box sx={{ display: "flex", gap: 1, height: 45 }}>
          <Box sx={{ ...elementStyle, width: 50 }}>Desc</Box>
          <Box sx={{ ...elementStyle, flex: 1 }}>LEGEND</Box>
          <Box sx={{ ...elementStyle, width: 50 }}>LOGO</Box>
        </Box>
      </Box>
    );
  }

  // Single Map Landscape Preview - Title at top, map left, sidebar right (desc/legend/logo)
  if (templateId === "single_map_landscape") {
    return (
      <Box
        sx={{
          width: 310,
          height: 220,
          display: "flex",
          flexDirection: "column",
          gap: 1,
        }}>
        {/* Title - top full width */}
        <Box sx={{ ...elementStyle, height: 22 }}>TITLE</Box>
        {/* Content: Map left, sidebar right */}
        <Box sx={{ display: "flex", flex: 1, gap: 1 }}>
          {/* Map - large left area */}
          <Box sx={{ ...elementStyle, flex: 1 }}>MAP</Box>
          {/* Right sidebar: Description, Legend, Logo */}
          <Box
            sx={{
              width: 55,
              display: "flex",
              flexDirection: "column",
              gap: 1,
            }}>
            <Box sx={{ ...elementStyle, height: 35 }}>Desc</Box>
            <Box sx={{ ...elementStyle, flex: 1 }}>LEGEND</Box>
            <Box sx={{ ...elementStyle, height: 30 }}>LOGO</Box>
          </Box>
        </Box>
      </Box>
    );
  }

  // Poster Portrait Preview - Title/subtitle top-left, logo top-right, large map center, north arrow bottom-left, legend bottom-right
  if (templateId === "poster_portrait") {
    return (
      <Box
        sx={{
          width: 200,
          height: 280,
          display: "flex",
          flexDirection: "column",
          gap: 1,
        }}>
        {/* Top row: Title/Subtitle left, Image right */}
        <Box sx={{ display: "flex", gap: 1, height: 50 }}>
          <Box
            sx={{
              flex: 1,
              display: "flex",
              flexDirection: "column",
              gap: 0.5,
            }}>
            <Box sx={{ ...elementStyle, height: 20 }}>Title</Box>
            <Box sx={{ ...elementStyle, flex: 1 }}>Subtitle</Box>
          </Box>
          <Box sx={{ ...elementStyle, width: 55 }}>IMAGE</Box>
        </Box>
        {/* Map - large center area */}
        <Box
          sx={{
            ...elementStyle,
            flex: 1,
            position: "relative",
          }}>
          MAP
          {/* North arrow indicator - bottom left */}
          <Box
            sx={{
              position: "absolute",
              bottom: 4,
              left: 4,
              width: 16,
              height: 16,
              backgroundColor: theme.palette.grey[300],
              border: `1px solid ${theme.palette.grey[400]}`,
              borderRadius: "50%",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: 8,
            }}>
            N
          </Box>
          {/* Legend indicator - bottom right */}
          <Box
            sx={{
              position: "absolute",
              bottom: 4,
              right: 4,
              width: 30,
              height: 50,
              backgroundColor: theme.palette.grey[300],
              border: `1px solid ${theme.palette.grey[400]}`,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: 7,
            }}>
            Legend
          </Box>
        </Box>
      </Box>
    );
  }

  // Poster Landscape Preview - Left sidebar (title/subtitle/image/desc), large map right, north arrow on map, legend on map
  if (templateId === "poster_landscape") {
    return (
      <Box
        sx={{
          width: 310,
          height: 220,
          display: "flex",
          flexDirection: "row",
          gap: 1,
        }}>
        {/* Left sidebar: Title, Subtitle, Image, Description */}
        <Box
          sx={{
            width: 70,
            display: "flex",
            flexDirection: "column",
            gap: 1,
          }}>
          <Box sx={{ ...elementStyle, height: 20 }}>Title</Box>
          <Box sx={{ ...elementStyle, flex: 1 }}>Subtitle</Box>
          <Box sx={{ ...elementStyle, height: 45 }}>IMAGE</Box>
          <Box sx={{ ...elementStyle, height: 45 }}>Desc</Box>
        </Box>
        {/* Map - large right area with overlays */}
        <Box
          sx={{
            ...elementStyle,
            flex: 1,
            position: "relative",
          }}>
          MAP
          {/* North arrow indicator - bottom left */}
          <Box
            sx={{
              position: "absolute",
              bottom: 4,
              left: 4,
              width: 16,
              height: 16,
              backgroundColor: theme.palette.grey[300],
              border: `1px solid ${theme.palette.grey[400]}`,
              borderRadius: "50%",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: 8,
            }}>
            N
          </Box>
          {/* Legend indicator - bottom right */}
          <Box
            sx={{
              position: "absolute",
              bottom: 4,
              right: 4,
              width: 30,
              height: 55,
              backgroundColor: theme.palette.grey[300],
              border: `1px solid ${theme.palette.grey[400]}`,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: 7,
            }}>
            Legend
          </Box>
        </Box>
      </Box>
    );
  }

  // Blank template
  return (
    <Box
      sx={{
        width: 200,
        height: 280,
        backgroundColor: theme.palette.grey[200],
        border: `1px solid ${theme.palette.grey[300]}`,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
      }}>
      <Typography variant="caption" color="text.disabled">
        Empty canvas
      </Typography>
    </Box>
  );
};

export default ReportTemplatePickerModal;
