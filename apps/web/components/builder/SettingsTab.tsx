import { Box, Button, Stack, Switch, Typography } from "@mui/material";

import { useTranslation } from "@/i18n/client";

import SettingsGroupHeader from "@/components/builder/widgets/common/SettingsGroupHeader";

interface SettingsTabProps {
  settings: { [key: string]: boolean };
  onChange: (name: string, value: boolean) => void;
  onReset: () => void;
}

interface SettingGroup {
  group: string;
  label: string;
  options: { name: string; label: string }[];
}

const SettingsTab: React.FC<SettingsTabProps> = ({ settings, onChange, onReset }) => {
  const { t } = useTranslation("common");

  const settingsGroups: SettingGroup[] = [
    {
      group: "map_tools",
      label: t("map_tools"),
      options: [
        { name: "location", label: t("location_search") },
        { name: "find_my_location", label: t("find_my_location") },
        { name: "scalebar", label: t("scalebar") },
      ],
    },
    {
      group: "map_controls",
      label: t("controls"),
      options: [
        { name: "zoom_controls", label: t("zoom_controls") },
        { name: "basemap", label: t("basemap") },
      ],
    },
    {
      group: "map_view",
      label: t("view"),
      options: [
        { name: "fullscreen", label: t("fullscreen") },
        { name: "toolbar", label: t("toolbar") },
        { name: "project_info", label: t("project_info") },
      ],
    },
  ];

  return (
    <Stack direction="column" spacing={2} justifyContent="space-between" sx={{ p: 3 }}>
      <Stack direction="column">
        {settingsGroups.map((group) => (
          <Box key={group.group} sx={{ mb: 6 }}>
            <SettingsGroupHeader label={t(group.label)} />
            <Stack spacing={1}>
              {group.options.map(
                (option) =>
                  settings?.hasOwnProperty(option.name) && (
                    <Stack direction="row" alignItems="center" key={option.name}>
                      <Switch
                        name={option.name}
                        checked={settings[option.name]}
                        onChange={(event: React.ChangeEvent<HTMLInputElement>) =>
                          onChange(option.name, event.target.checked)
                        }
                      />
                      <Typography variant="body2" fontWeight="bold" color="textSecondary">
                        {option.label}
                      </Typography>
                    </Stack>
                  )
              )}
            </Stack>
          </Box>
        ))}
      </Stack>
      <Stack>
        <Button onClick={onReset} fullWidth size="small" color="error">
          <Typography variant="body2" fontWeight="bold" color="inherit">
            {t("common:reset")}
          </Typography>
        </Button>
      </Stack>
    </Stack>
  );
};

export default SettingsTab;
