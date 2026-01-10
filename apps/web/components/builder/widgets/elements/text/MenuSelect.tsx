import ArrowDropDownIcon from "@mui/icons-material/ArrowDropDown";
import { ToggleButton } from "@mui/material";
import ListItemIcon from "@mui/material/ListItemIcon";
import ListItemText from "@mui/material/ListItemText";
import Menu from "@mui/material/Menu";
import MenuItem from "@mui/material/MenuItem";
import { useEffect, useState } from "react";

import { ICON_NAME, Icon } from "@p4b/ui/components/Icon";

export type MenuItemOption = {
  label: string;
  value: string;
  icon: ICON_NAME;
};

type MenuSelectProps = {
  items: MenuItemOption[];
  value: string;
  onChange: (value: string) => void;
  buttonValue: string; // e.g. "blockType" or "textAlign"
  buttonIcon?: ICON_NAME; // optional: always show this icon on button
  highlightWhenSelected?: boolean; // optional: make icon primary when value is selected
  onOpen?: () => void; // callback when dropdown opens (to close others)
  onClose?: () => void; // callback when dropdown closes
  forceClose?: boolean; // when true, forces the dropdown to close
};

export const MenuSelect = ({
  items,
  value,
  onChange,
  buttonValue,
  buttonIcon,
  highlightWhenSelected = false,
  onOpen,
  onClose,
  forceClose,
}: MenuSelectProps) => {
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const open = Boolean(anchorEl);

  // Close when forceClose becomes true
  useEffect(() => {
    if (forceClose && anchorEl) {
      setAnchorEl(null);
    }
  }, [forceClose, anchorEl]);

  const selectedItem = items.find((item) => item.value === value);

  const handleOpen = (event: React.MouseEvent<HTMLElement>) => {
    event.stopPropagation();
    if (anchorEl) {
      setAnchorEl(null); // Close if already open
    } else {
      onOpen?.(); // Notify parent to close other dropdowns
      setAnchorEl(event.currentTarget); // Open if closed
    }
  };

  // Allow parent to close this dropdown
  const handleClose = () => {
    setAnchorEl(null);
    onClose?.();
  };

  const handleSelect = (val: string) => {
    onChange(val);
    handleClose();
  };

  // Decide icon color
  const iconColor = highlightWhenSelected && value ? "primary" : open ? "primary" : "inherit";

  return (
    <>
      <ToggleButton
        value={buttonValue}
        size="small"
        selected={open}
        onClick={handleOpen}
        sx={{ display: "flex", alignItems: "center" }}>
        <Icon
          iconName={buttonIcon ?? selectedItem?.icon ?? ICON_NAME.TEXT}
          fontSize="small"
          color={iconColor}
        />
        <ArrowDropDownIcon fontSize="small" />
      </ToggleButton>

      <Menu
        anchorEl={anchorEl}
        open={open}
        onClose={handleClose}
        anchorOrigin={{ vertical: "bottom", horizontal: "left" }}
        transformOrigin={{ vertical: "top", horizontal: "left" }}
        sx={{ zIndex: 1500 }}
        slotProps={{
          paper: {
            onMouseDown: (e: React.MouseEvent) => e.stopPropagation(),
            onPointerDown: (e: React.PointerEvent) => e.stopPropagation(),
          },
        }}>
        {items.map((item) => (
          <MenuItem
            dense
            key={item.value}
            selected={item.value === value}
            onClick={() => handleSelect(item.value)}>
            <ListItemIcon>
              <Icon iconName={item.icon} fontSize="small" />
            </ListItemIcon>
            <ListItemText>{item.label}</ListItemText>
          </MenuItem>
        ))}
      </Menu>
    </>
  );
};
