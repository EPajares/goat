"use client";

import {
  Box,
  Button,
  Dialog,
  DialogContent,
  List,
  ListItemButton,
  ListItemText,
  Paper,
  Stack,
  Typography,
} from "@mui/material";
import { useTheme } from "@mui/material/styles";
import React, { useState } from "react";
import { useTranslation } from "react-i18next";

import type { ReportLayoutConfig } from "@/lib/validations/reportLayout";

export type ReportTemplateType = "single_map" | "poster" | "blank";

export interface ReportTemplate {
  id: ReportTemplateType;
  name: string;
  description: string;
  config: ReportLayoutConfig;
}

// Default config for blank template
const getBlankConfig = (): ReportLayoutConfig => ({
  page: {
    size: "A4",
    orientation: "portrait",
    margins: { top: 10, right: 10, bottom: 10, left: 10 },
    snapToGuides: false,
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

// Single map template - simple layout with map, title, description, legend and logo
const getSingleMapConfig = (): ReportLayoutConfig => ({
  page: {
    size: "A4",
    orientation: "portrait",
    margins: { top: 10, right: 10, bottom: 10, left: 10 },
    snapToGuides: false,
    showRulers: false,
  },
  layout: {
    type: "grid",
    columns: 12,
    rows: 12,
    gap: 5,
  },
  elements: [
    // Map - large area on the left
    {
      id: "map-1",
      type: "map",
      position: { x: 10, y: 30, width: 140, height: 200, z_index: 1 },
      config: {
        viewState: { latitude: 48.13, longitude: 11.57, zoom: 10, bearing: 0, pitch: 0 },
      },
      style: { padding: 0, opacity: 1 },
    },
    // Title - top right
    {
      id: "text-title",
      type: "text",
      position: { x: 155, y: 30, width: 45, height: 15, z_index: 2 },
      config: {
        content: "TITLE",
        fontSize: 14,
        fontWeight: "bold",
        textAlign: "left",
      },
      style: { padding: 2, opacity: 1 },
    },
    // Description - below title
    {
      id: "text-desc",
      type: "text",
      position: { x: 155, y: 50, width: 45, height: 40, z_index: 3 },
      config: {
        content: "Description",
        fontSize: 10,
        textAlign: "left",
      },
      style: { padding: 2, opacity: 1 },
    },
    // Legend - middle right
    {
      id: "legend-1",
      type: "legend",
      position: { x: 155, y: 100, width: 45, height: 80, z_index: 4 },
      config: {
        mapElementId: "map-1",
      },
      style: { padding: 2, opacity: 1 },
    },
    // Logo placeholder - bottom right
    {
      id: "image-logo",
      type: "image",
      position: { x: 155, y: 200, width: 45, height: 30, z_index: 5 },
      config: {
        placeholder: "LOGO",
      },
      style: { padding: 2, opacity: 1 },
    },
  ],
});

// Poster template - more detailed layout with charts and metrics
const getPosterConfig = (): ReportLayoutConfig => ({
  page: {
    size: "A4",
    orientation: "portrait",
    margins: { top: 10, right: 10, bottom: 10, left: 10 },
    snapToGuides: false,
    showRulers: false,
  },
  layout: {
    type: "grid",
    columns: 12,
    rows: 12,
    gap: 5,
  },
  elements: [
    // Map - center area
    {
      id: "map-1",
      type: "map",
      position: { x: 10, y: 50, width: 180, height: 150, z_index: 1 },
      config: {
        viewState: { latitude: 48.13, longitude: 11.57, zoom: 10, bearing: 0, pitch: 0 },
      },
      style: { padding: 0, opacity: 1 },
    },
    // Title - top
    {
      id: "text-title",
      type: "text",
      position: { x: 10, y: 10, width: 180, height: 15, z_index: 2 },
      config: {
        content: "Report Title",
        fontSize: 18,
        fontWeight: "bold",
        textAlign: "center",
      },
      style: { padding: 2, opacity: 1 },
    },
    // Subtitle
    {
      id: "text-subtitle",
      type: "text",
      position: { x: 10, y: 28, width: 180, height: 12, z_index: 3 },
      config: {
        content: "Subtitle or description",
        fontSize: 11,
        textAlign: "center",
      },
      style: { padding: 2, opacity: 1 },
    },
    // Legend - bottom left
    {
      id: "legend-1",
      type: "legend",
      position: { x: 10, y: 210, width: 60, height: 60, z_index: 4 },
      config: {
        mapElementId: "map-1",
      },
      style: { padding: 2, opacity: 1 },
    },
    // North arrow - bottom right
    {
      id: "north-1",
      type: "north_arrow",
      position: { x: 170, y: 210, width: 20, height: 20, z_index: 5 },
      config: {
        mapElementId: "map-1",
      },
      style: { padding: 0, opacity: 1 },
    },
  ],
});

interface ReportTemplatePickerModalProps {
  open: boolean;
  onClose: () => void;
  onSelectTemplate: (template: ReportTemplate) => void;
}

const ReportTemplatePickerModal: React.FC<ReportTemplatePickerModalProps> = ({
  open,
  onClose,
  onSelectTemplate,
}) => {
  const { t } = useTranslation("common");
  const theme = useTheme();
  const [selectedTemplate, setSelectedTemplate] = useState<ReportTemplateType>("single_map");

  const templates: ReportTemplate[] = [
    {
      id: "single_map",
      name: t("single_map"),
      description: t("single_map_description"),
      config: getSingleMapConfig(),
    },
    {
      id: "poster",
      name: t("poster"),
      description: t("poster_description"),
      config: getPosterConfig(),
    },
    {
      id: "blank",
      name: t("blank"),
      description: t("blank_description"),
      config: getBlankConfig(),
    },
  ];

  const selectedTemplateData = templates.find((t) => t.id === selectedTemplate);

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
          {/* Template List */}
          <List sx={{ width: 220, flexShrink: 0 }}>
            {templates.map((template) => (
              <ListItemButton
                key={template.id}
                selected={selectedTemplate === template.id}
                onClick={() => setSelectedTemplate(template.id)}
                sx={{
                  borderRadius: 1,
                  mb: 1,
                  border:
                    selectedTemplate === template.id
                      ? `2px solid ${theme.palette.primary.main}`
                      : "2px solid transparent",
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
                      variant="body1"
                      fontWeight={selectedTemplate === template.id ? "bold" : "normal"}
                      color={selectedTemplate === template.id ? "primary" : "text.primary"}>
                      {template.name}
                    </Typography>
                  }
                  secondary={
                    <Typography variant="caption" color="text.secondary">
                      {template.description}
                    </Typography>
                  }
                />
              </ListItemButton>
            ))}
          </List>

          {/* Preview Area */}
          <Box sx={{ flex: 1, display: "flex", flexDirection: "column" }}>
            <Paper
              variant="outlined"
              sx={{
                flex: 1,
                minHeight: 300,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                backgroundColor: theme.palette.grey[100],
                position: "relative",
                overflow: "hidden",
              }}>
              {/* Simple preview representation */}
              <TemplatePreview templateId={selectedTemplate} />
            </Paper>

            <Box sx={{ mt: 3, display: "flex", justifyContent: "flex-end" }}>
              <Button
                variant="contained"
                color="primary"
                onClick={handleUseTemplate}
                sx={{ textTransform: "none" }}>
                {t("use_this_template")}
              </Button>
            </Box>
          </Box>
        </Stack>
      </DialogContent>
    </Dialog>
  );
};

// Simple visual preview of template layout
const TemplatePreview: React.FC<{ templateId: ReportTemplateType }> = ({ templateId }) => {
  const theme = useTheme();

  const previewStyles = {
    paper: {
      width: 150,
      height: 212, // A4 ratio
      backgroundColor: "white",
      border: `1px solid ${theme.palette.grey[300]}`,
      position: "relative" as const,
      padding: 8,
    },
    element: {
      position: "absolute" as const,
      backgroundColor: theme.palette.grey[200],
      border: `1px solid ${theme.palette.grey[300]}`,
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      fontSize: 8,
      color: theme.palette.grey[600],
    },
  };

  if (templateId === "single_map") {
    return (
      <Box sx={previewStyles.paper}>
        {/* Map */}
        <Box
          sx={{
            ...previewStyles.element,
            left: 8,
            top: 20,
            width: 95,
            height: 140,
          }}>
          MAP
        </Box>
        {/* Title */}
        <Box
          sx={{
            ...previewStyles.element,
            right: 8,
            top: 20,
            width: 35,
            height: 12,
            fontSize: 7,
          }}>
          TITLE
        </Box>
        {/* Description */}
        <Box
          sx={{
            ...previewStyles.element,
            right: 8,
            top: 36,
            width: 35,
            height: 25,
            fontSize: 6,
          }}>
          Description
        </Box>
        {/* Legend */}
        <Box
          sx={{
            ...previewStyles.element,
            right: 8,
            top: 68,
            width: 35,
            height: 50,
          }}>
          LEGEND
        </Box>
        {/* Logo */}
        <Box
          sx={{
            ...previewStyles.element,
            right: 8,
            bottom: 8,
            width: 35,
            height: 20,
          }}>
          LOGO
        </Box>
      </Box>
    );
  }

  if (templateId === "poster") {
    return (
      <Box sx={previewStyles.paper}>
        {/* Title */}
        <Box
          sx={{
            ...previewStyles.element,
            left: 8,
            top: 8,
            right: 8,
            width: "auto",
            height: 12,
          }}>
          Report Title
        </Box>
        {/* Subtitle */}
        <Box
          sx={{
            ...previewStyles.element,
            left: 8,
            top: 24,
            right: 8,
            width: "auto",
            height: 8,
            fontSize: 6,
          }}>
          Subtitle
        </Box>
        {/* Map */}
        <Box
          sx={{
            ...previewStyles.element,
            left: 8,
            top: 38,
            right: 8,
            width: "auto",
            height: 110,
          }}>
          MAP
        </Box>
        {/* Legend */}
        <Box
          sx={{
            ...previewStyles.element,
            left: 8,
            bottom: 8,
            width: 45,
            height: 40,
          }}>
          LEGEND
        </Box>
        {/* North arrow */}
        <Box
          sx={{
            ...previewStyles.element,
            right: 8,
            bottom: 8,
            width: 15,
            height: 15,
            fontSize: 6,
          }}>
          N
        </Box>
      </Box>
    );
  }

  // Blank template
  return (
    <Box sx={previewStyles.paper}>
      <Box
        sx={{
          width: "100%",
          height: "100%",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          color: theme.palette.grey[400],
          fontSize: 10,
        }}>
        Empty canvas
      </Box>
    </Box>
  );
};

export default ReportTemplatePickerModal;
