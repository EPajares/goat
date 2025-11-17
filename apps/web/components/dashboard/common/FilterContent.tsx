import {
  Badge,
  Checkbox,
  FormControlLabel,
  Grid,
  IconButton,
  Link,
  Paper,
  Stack,
  Tooltip,
  Typography,
  useTheme,
} from "@mui/material";
import { useState } from "react";
import { useTranslation } from "react-i18next";

import { ICON_NAME, Icon } from "@p4b/ui/components/Icon";

import { type LayerType, layerTypesArray } from "@/lib/validations/layer";

import { ArrowPopper } from "@/components/ArrowPoper";

export interface FilterContentMenuProps {
  type: "project" | "layer";
  onLayerTypeSelect?: (layerTypes: LayerType[]) => void;
  onTagSelect?: (tags: string[]) => void;
}

export default function FilterContentMenu(props: FilterContentMenuProps) {
  const theme = useTheme();
  const [layerTypes, setLayerTypes] = useState<LayerType[]>([]);
  const [filterContentMenuOpen, setFilterContentMenuOpen] = useState<boolean>(false);
  const { t } = useTranslation("common");

  //todo get tags from api
  const [tags, setTags] = useState<string[]>([]);

  return (
    <ArrowPopper
      open={filterContentMenuOpen}
      placement="bottom"
      onClose={() => setFilterContentMenuOpen(false)}
      arrow={false}
      content={
        <Paper
          elevation={8}
          sx={{
            minWidth: 220,
            maxWidth: 340,
            overflow: "auto",
            py: theme.spacing(2),
            px: theme.spacing(3),
          }}>
          <Stack direction="row" justifyContent="space-between">
            <Typography variant="body1" sx={{ pb: 4 }}>
              {t("filter")}
            </Typography>
            {/* Clear all */}
            {tags.length > 0 ||
              (layerTypes.length > 0 && (
                <Link
                  underline="none"
                  typography="body2"
                  onClick={() => {
                    setLayerTypes([]);
                    setTags([]);
                    props.onLayerTypeSelect?.([]);
                    props.onTagSelect?.([]);
                  }}
                  sx={{ cursor: "pointer", color: theme.palette.primary.main }}>
                  {t("clear_all")}
                </Link>
              ))}
          </Stack>
          <Grid container spacing={2}>
            {props.type === "layer" && (
              <Grid item xs={12}>
                <Stack direction="column">
                  <Typography variant="body2" fontWeight="bold" gutterBottom>
                    {t("dataset_types")}
                  </Typography>
                  {layerTypesArray.map((layerType, index) => (
                    <FormControlLabel
                      key={index}
                      control={
                        <Checkbox
                          size="small"
                          checked={layerTypes?.includes(layerType)}
                          onChange={() => {
                            let newLayerTypes = [...layerTypes];
                            if (layerTypes?.includes(layerType)) {
                              newLayerTypes = newLayerTypes.filter((type) => type !== layerType);
                            } else {
                              newLayerTypes.push(layerType);
                            }
                            props.onLayerTypeSelect?.(newLayerTypes);
                            setLayerTypes(newLayerTypes);
                          }}
                        />
                      }
                      label={<Typography variant="body2">{t(`${layerType}`)}</Typography>}
                    />
                  ))}
                </Stack>
              </Grid>
            )}
            {tags.length > 0 && (
              <Grid item xs={12}>
                <Stack direction="column">
                  <Typography variant="body2" gutterBottom>
                    Tags
                  </Typography>
                  {tags.map((tag, index) => (
                    <FormControlLabel
                      key={index}
                      control={
                        <Checkbox
                          size="small"
                          checked={tags?.includes(tag)}
                          onChange={() => {
                            if (tags?.includes(tag)) {
                              setTags(tags.filter((type) => type !== tag));
                            } else {
                              setTags([...tags, tag]);
                            }
                            props.onTagSelect?.(tags);
                          }}
                        />
                      }
                      label={tag}
                    />
                  ))}
                </Stack>
              </Grid>
            )}
          </Grid>
        </Paper>
      }>
      <Tooltip title={t("filter")}>
        <IconButton
          onClick={(event) => {
            event.stopPropagation();
            setFilterContentMenuOpen(!filterContentMenuOpen);
          }}
          disabled={tags.length === 0 && props.type === "project"}
          sx={{
            mx: 2,
            p: 2,
            borderRadius: 1,
            ...(layerTypes.length > 0 && {
              color: theme.palette.primary.main,
            }),
          }}>
          <Badge badgeContent={layerTypes.length} color="primary">
            <Icon iconName={ICON_NAME.FILTER} fontSize="small" htmlColor="inherit" />
          </Badge>
        </IconButton>
      </Tooltip>
    </ArrowPopper>
  );
}
