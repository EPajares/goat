import { TabContext, TabPanel } from "@mui/lab";
import { Divider, Fab, Tab, TextField, Tooltip, useTheme } from "@mui/material";
import Tabs from "@mui/material/Tabs";
import React, { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import ReactMarkdown from "react-markdown";

import { ICON_NAME, Icon } from "@p4b/ui/components/Icon";

import type { Project } from "@/lib/validations/project";

import { ProjectMetadataEdit, ProjectMetadataView } from "@/components/dashboard/project/Metadata";
import ViewModal from "@/components/modals/View";

interface ProjectInfoProps {
  project: Project;
  viewOnly?: boolean;
  onProjectUpdate?: (key: string, value: unknown, refresh?: boolean) => void;
}

export function ProjectInfo({ project, viewOnly, onProjectUpdate }: ProjectInfoProps) {
  const { t } = useTranslation("common");
  const builderConfig = project?.builder_config;
  const theme = useTheme();
  const [value, setValue] = useState("info");
  const [open, setOpen] = useState(false);

  const infoContent = project?.builder_config?.settings?.project_info_content || "";
  const hasInfo = infoContent.trim().length > 0;
  const shouldSkipTabs = viewOnly && !hasInfo;

  const handleChange = (_event: React.SyntheticEvent, newValue: string) => {
    setValue(newValue);
  };

  const onClose = () => {
    setOpen(false);
  };

  // Open modal only on first visit
  useEffect(() => {
    if (!project?.id) return;
    const key = `project_info_seen_${project.id}`;
    const seen = localStorage.getItem(key);

    if (!seen && viewOnly) {
      setOpen(true);
      localStorage.setItem(key, "true");
    }
  }, [project?.id, viewOnly]);

  return (
    <>
      <ViewModal title={project.name} open={!!open} onClose={onClose} closeText={t("close")}>
        {shouldSkipTabs ? (
          // --- VIEW ONLY + NO INFO → Only Metadata ---
          <ProjectMetadataView project={project} />
        ) : (
          // --- NORMAL CASE → Show Tabs ---
          <TabContext value={value}>
            <Tabs variant="fullWidth" value={value} onChange={handleChange}>
              <Tab value="info" label={t("info")} />
              <Tab value="metadata" label={t("metadata.title")} />
            </Tabs>

            <Divider sx={{ mt: 0 }} />

            <TabPanel value="info">
              {viewOnly ? (
                <ReactMarkdown
                  components={{
                    img: ({ node: _, ...props }) => {
                      const hasSize =
                        props.width !== undefined ||
                        props.height !== undefined ||
                        (props.style && (props.style.width || props.style.height));
                      const style = hasSize ? props.style : { width: "100%" };
                      // eslint-disable-next-line jsx-a11y/alt-text
                      return <img {...props} style={style} />;
                    },
                    a: ({ node: _, href, children, ...props }) => (
                      <a href={href} target="_blank" rel="noopener noreferrer" {...props}>
                        {children}
                      </a>
                    ),
                  }}>
                  {infoContent}
                </ReactMarkdown>
              ) : (
                <TextField
                  fullWidth
                  placeholder={t("info_placeholder")}
                  multiline
                  rows={10}
                  value={infoContent}
                  onChange={(e) => {
                    builderConfig.settings.project_info_content = e.target.value;
                    onProjectUpdate && onProjectUpdate("builder_config", builderConfig);
                  }}
                />
              )}
            </TabPanel>

            <TabPanel value="metadata">
              {viewOnly ? (
                <ProjectMetadataView project={project} />
              ) : (
                <ProjectMetadataEdit project={project} onChange={onProjectUpdate} />
              )}
            </TabPanel>
          </TabContext>
        )}
      </ViewModal>

      {/* Floating FAB */}
      <Tooltip title={t("info")} arrow placement="left">
        <Fab
          onClick={() => setOpen(true)}
          size="small"
          sx={{
            backgroundColor: theme.palette.background.paper,
            marginBottom: theme.spacing(1),
            pointerEvents: "all",
            color: theme.palette.text.secondary,
            "&:hover": {
              backgroundColor: theme.palette.background.default,
            },
          }}>
          <Icon iconName={ICON_NAME.INFO} htmlColor="inherit" fontSize="small" />
        </Fab>
      </Tooltip>
    </>
  );
}
