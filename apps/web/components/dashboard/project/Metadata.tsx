import { Divider, Stack, TextField, Typography } from "@mui/material";
import { formatDistance } from "date-fns";
import { useTranslation } from "react-i18next";
import ReactMarkdown from "react-markdown";

import { useDateFnsLocale } from "@/i18n/utils";

import type { Project } from "@/lib/validations/project";

interface ProjectMetadataProps {
  project: Project;
  onChange?: (key: string, value: unknown, refresh?: boolean) => void;
}

export const ProjectMetadataView: React.FC<ProjectMetadataProps> = ({ project }) => {
  const { t } = useTranslation("common");
  const dateLocale = useDateFnsLocale();

  return (
    <Stack spacing={4}>
      <Stack>
        <Typography variant="caption">{t("name")}</Typography>
        <Divider />
        <Typography variant="body2" fontWeight="bold">
          {project.name}
        </Typography>
      </Stack>

      {project.updated_at && (
        <Stack>
          <Typography variant="caption">{t("last_updated")}</Typography>
          <Divider />
          <Typography variant="body2" noWrap fontWeight="bold">
            {formatDistance(new Date(project.updated_at), new Date(), {
              addSuffix: true,
              locale: dateLocale,
            })}
          </Typography>
        </Stack>
      )}
      <Stack>
        <Typography variant="caption">{t("description")}</Typography>
        <Divider />
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
          {project.description}
        </ReactMarkdown>
      </Stack>
    </Stack>
  );
};

export const ProjectMetadataEdit: React.FC<ProjectMetadataProps> = ({ project, onChange }) => {
  const { t } = useTranslation("common");
  return (
    <Stack spacing={4}>
      <TextField
        fullWidth
        label={t("name")}
        defaultValue={project.name}
        onChange={(e) => onChange && onChange("name", e.target.value)}
      />
      <TextField
        fullWidth
        multiline
        rows={6}
        label={t("description")}
        defaultValue={project.description}
        onChange={(e) => onChange && onChange("description", e.target.value)}
      />
    </Stack>
  );
};
