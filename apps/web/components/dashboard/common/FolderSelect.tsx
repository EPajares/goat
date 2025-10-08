import Autocomplete from "@mui/material/Autocomplete";
import InputAdornment from "@mui/material/InputAdornment";
import ListItem from "@mui/material/ListItem";
import ListItemIcon from "@mui/material/ListItemIcon";
import ListItemText from "@mui/material/ListItemText";
import TextField from "@mui/material/TextField";
import React from "react";
import { useTranslation } from "react-i18next";

import { ICON_NAME, Icon } from "@p4b/ui/components/Icon";

const FolderSelect = ({ folders, selectedFolder, setSelectedFolder }) => {
  const { t } = useTranslation("common");

  return (
    <Autocomplete
      fullWidth
      value={selectedFolder}
      onChange={(_event, newValue) => {
        setSelectedFolder(newValue);
      }}
      disableClearable
      autoHighlight
      id="folder-select"
      options={folders ? [...folders] : []}
      getOptionLabel={(option) => {
        if (typeof option === "string") {
          return option;
        }
        return option.name;
      }}
      renderOption={(props, option) => (
        <ListItem key={option.id} {...props}>
          <ListItemIcon>
            <Icon
              iconName={option?.id === "0" ? ICON_NAME.HOUSE : ICON_NAME.FOLDER}
              style={{ marginLeft: 2 }}
              fontSize="small"
            />
          </ListItemIcon>
          <ListItemText primary={option.name} />
        </ListItem>
      )}
      renderInput={(params) => (
        <TextField
          {...params}
          fullWidth
          sx={{
            mt: 4,
          }}
          InputProps={{
            ...params.InputProps,
            startAdornment: (
              <InputAdornment position="start">
                <Icon
                  iconName={selectedFolder?.id === "0" ? ICON_NAME.HOUSE : ICON_NAME.FOLDER}
                  style={{ marginLeft: 2 }}
                  fontSize="small"
                />
              </InputAdornment>
            ),
          }}
          label={t("select_folder_destination")}
        />
      )}
    />
  );
};

export default FolderSelect;
