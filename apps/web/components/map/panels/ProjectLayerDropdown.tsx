import { FormControl, InputLabel, MenuItem, Select, Typography } from "@mui/material";
import { useMemo } from "react";
import { useTranslation } from "react-i18next";

import { setActiveLayer } from "@/lib/store/layer/slice";
import type { LayerType } from "@/lib/validations/common";

import { useActiveLayer, useFilteredProjectLayers } from "@/hooks/map/LayerPanelHooks";
import { useAppDispatch } from "@/hooks/store/ContextHooks";

interface ProjectLayerDropdownProps {
  projectId: string;
  layerTypes?: LayerType[];
  onChange?: (id: number) => void;
}

const ProjectLayerDropdown = ({ projectId, layerTypes, onChange }: ProjectLayerDropdownProps) => {
  const { t } = useTranslation("common");
  const { layers: projectLayers } = useFilteredProjectLayers(projectId);
  const filteredLayers = useMemo(() => {
    if (!layerTypes) return projectLayers;
    return projectLayers?.filter((layer) => layerTypes.includes(layer.type));
  }, [layerTypes, projectLayers]);
  const { activeLayer } = useActiveLayer(projectId);
  const dispatch = useAppDispatch();

  return (
    <>
      {filteredLayers && filteredLayers.length > 0 && activeLayer && (
        <FormControl fullWidth sx={{ mb: 4 }}>
          <InputLabel id="select-active-layer-title">{t("active_layer")}</InputLabel>
          <Select
            sx={{ width: "100%" }}
            labelId="select-active-layer"
            id="select-active-layer"
            value={activeLayer.id}
            label={t("active_layer")}
            onChange={(event) => {
              const id = event.target.value as number;
              dispatch(setActiveLayer(id));
              if (onChange) {
                onChange(id);
              }
            }}
            MenuProps={{
              MenuListProps: {
                sx: {
                  maxWidth: "290px",
                },
              },
            }}>
            {filteredLayers.map((layer) => {
              return (
                <MenuItem key={layer.id} value={layer.id}>
                  <Typography noWrap>{layer.name}</Typography>
                </MenuItem>
              );
            })}
          </Select>
        </FormControl>
      )}
    </>
  );
};

export default ProjectLayerDropdown;
