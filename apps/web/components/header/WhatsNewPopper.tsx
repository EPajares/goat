"use client";

import {
  Box,
  Button,
  Card,
  CardContent,
  CardMedia,
  IconButton,
  Paper,
  Stack,
  Tooltip,
  Typography,
  useTheme,
} from "@mui/material";
import { useState } from "react";
import { useTranslation } from "react-i18next";

import { ICON_NAME, Icon } from "@p4b/ui/components/Icon";

import { ArrowPopper } from "@/components/ArrowPoper";

type ReleaseNote = {
  title: string;
  date: string;
  thumbnail: string;
  url: string;
};

const releaseNotesEnglish: ReleaseNote = {
  title: 'GOAT 2.3.0 "Tarn" is here',
  date: "January 13, 2026",
  thumbnail:
    "https://cdn.prod.website-files.com/6554ce5f672475c1f40445af/6964f6ab66d9b7fec644a6b5_blogpost_cover-p-1600.webp",
  url: "https://www.plan4better.de/en/post/goat-2-3-0-tarn-is-here",
};

const releaseNotesGerman: ReleaseNote = {
  title: 'GOAT 2.3.0 „Tarn" ist da',
  date: "13. Januar 2026",
  thumbnail:
    "https://cdn.prod.website-files.com/6554ce5f672475c1f40445af/6964f6ab66d9b7fec644a6b5_blogpost_cover-p-1600.webp",
  url: "https://www.plan4better.de/de/post/goat-2-3-0-tarn-ist-da",
};

export default function WhatsNewPopper() {
  const { t, i18n } = useTranslation("common");
  const theme = useTheme();
  const [open, setOpen] = useState(false);

  const releaseNote = i18n.language === "de" ? releaseNotesGerman : releaseNotesEnglish;

  return (
    <ArrowPopper
      open={open}
      onClose={() => setOpen(false)}
      placement="bottom-end"
      arrow
      content={
        <Paper
          sx={{
            width: 320,
            maxHeight: 400,
            overflow: "hidden",
          }}>
          <Box sx={{ p: 3 }}>
            <Stack direction="row" alignItems="center" spacing={2} sx={{ mb: 2 }}>
              <Icon iconName={ICON_NAME.ROCKET} style={{ fontSize: 18, color: theme.palette.primary.main }} />
              <Typography variant="body1" fontWeight="bold">
                {t("whats_new")}
              </Typography>
            </Stack>
            <Card
              sx={{
                cursor: "pointer",
                transition: "box-shadow 0.2s ease-in-out",
                "&:hover": {
                  boxShadow: theme.shadows[4],
                },
              }}
              onClick={() => window.open(releaseNote.url, "_blank")}>
              <CardMedia
                component="img"
                height="140"
                image={releaseNote.thumbnail}
                alt={releaseNote.title}
                sx={{
                  objectFit: "cover",
                }}
              />
              <CardContent sx={{ p: 2 }}>
                <Typography variant="body2" fontWeight="bold" gutterBottom>
                  {releaseNote.title}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  {releaseNote.date}
                </Typography>
              </CardContent>
            </Card>
            <Button
              fullWidth
              variant="text"
              size="small"
              sx={{ mt: 2 }}
              endIcon={<Icon iconName={ICON_NAME.EXTERNAL_LINK} style={{ fontSize: 12 }} />}
              onClick={() => window.open(releaseNote.url, "_blank")}>
              {t("view_all_updates")}
            </Button>
          </Box>
        </Paper>
      }>
      <Tooltip title={t("whats_new")}>
        <IconButton size="small" onClick={() => setOpen(!open)}>
          <Icon iconName={ICON_NAME.ROCKET} fontSize="inherit" />
        </IconButton>
      </Tooltip>
    </ArrowPopper>
  );
}
