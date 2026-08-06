import { Box, Tab, Tabs, TextField, Typography } from "@mui/material";
import { useState } from "react";
import ReactMarkdown from "react-markdown";
import { useTranslation } from "react-i18next";

import { popupMarkdownComponents } from "@/components/builder/widgets/common/markdownComponents";

interface MarkdownContentEditorProps {
  value: string;
  onChange: (value: string) => void;
  /** When true, shows a plain textarea with no markdown tabs/preview/hint. */
  plainText?: boolean;
  minRows?: number;
  maxRows?: number;
  placeholder?: string;
  /** Override hint text (defaults to the markdown syntax hint). */
  hint?: string;
}

const previewStyles = {
  "& p": { mb: 1, lineHeight: 1.7 },
  "& p:last-child": { mb: 0 },
  "& h1, & h2, & h3": { mt: 1.5, mb: 0.5, fontWeight: 700 },
  "& h1:first-of-type, & h2:first-of-type, & h3:first-of-type": { mt: 0 },
  "& strong": { fontWeight: 700 },
  "& a": { color: "primary.main" },
  "& ul, & ol": { pl: 2.5, mb: 1 },
} as const;

/**
 * Reusable markdown content editor with Write/Preview tabs.
 * Used by InfoChipEditDialog and the Links widget popup-content editor.
 *
 * In plainText mode, drops the tabs and preview pane and shows a plain textarea
 * — used for tooltip-type popups where markdown is stripped on render.
 */
const MarkdownContentEditor = ({
  value,
  onChange,
  plainText = false,
  minRows = 5,
  maxRows = 14,
  placeholder,
  hint,
}: MarkdownContentEditorProps) => {
  const { t } = useTranslation("common");
  const [tab, setTab] = useState<"write" | "preview">("write");
  const resolvedPlaceholder = placeholder ?? t("popup_content_placeholder");
  const resolvedHint = hint ?? (plainText ? t("tooltip_text_only_hint") : t("markdown_syntax_hint"));

  if (plainText) {
    return (
      <>
        <TextField
          multiline
          minRows={Math.min(minRows, 3)}
          maxRows={Math.max(maxRows - 6, 8)}
          fullWidth
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={resolvedPlaceholder}
          InputProps={{ sx: { fontSize: 13, lineHeight: 1.7 } }}
        />
        <Typography variant="caption" color="text.disabled" sx={{ mt: 0.5, display: "block" }}>
          {resolvedHint}
        </Typography>
      </>
    );
  }

  return (
    <>
      <Tabs
        value={tab}
        onChange={(_, v) => setTab(v as "write" | "preview")}
        sx={{ borderBottom: 1, borderColor: "divider", minHeight: 32, mb: 1 }}>
        <Tab value="write" label={t("write")} sx={{ textTransform: "none", fontWeight: 600, minHeight: 32, py: 0.5 }} />
        <Tab value="preview" label={t("preview")} sx={{ textTransform: "none", fontWeight: 600, minHeight: 32, py: 0.5 }} />
      </Tabs>
      {tab === "write" ? (
        <TextField
          multiline
          minRows={minRows}
          maxRows={maxRows}
          fullWidth
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={resolvedPlaceholder}
          InputProps={{
            sx: { fontFamily: "monospace", fontSize: 13, lineHeight: 1.7 },
          }}
        />
      ) : (
        <Box
          sx={{
            minHeight: 120,
            bgcolor: "background.default",
            borderRadius: 1,
            p: 1.5,
            fontSize: 13,
            lineHeight: 1.7,
            ...previewStyles,
          }}>
          {value.trim() ? (
            <ReactMarkdown components={popupMarkdownComponents}>{value}</ReactMarkdown>
          ) : (
            <Typography variant="body2" color="text.disabled">
              {resolvedPlaceholder}
            </Typography>
          )}
        </Box>
      )}
      {tab === "write" && (
        <>
          <Typography variant="caption" color="text.disabled" sx={{ mt: 0.5, display: "block" }}>
            {resolvedHint}
          </Typography>
          {/* Own line: the poster syntax is too easy to miss inside the list above. */}
          <Typography variant="caption" color="text.disabled" sx={{ display: "block" }}>
            {t("markdown_video_hint")}
          </Typography>
        </>
      )}
    </>
  );
};

export default MarkdownContentEditor;
