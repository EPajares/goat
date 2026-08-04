/**
 * Shared look for a data-table column menu.
 *
 * The map data table and the dashboard table widget both open one of these, from
 * different components — these constants are what keep them from drifting apart.
 * Items are expected to be `<MenuItem><ListItemIcon>…</ListItemIcon><ListItemText>…`,
 * which is what these selectors target.
 */
export const COLUMN_MENU_PAPER_SX = {
  minWidth: 180,
  "& .MuiMenuItem-root": {
    py: 0.5,
    minHeight: 32,
    fontSize: "0.8rem",
  },
  "& .MuiListItemIcon-root": {
    minWidth: 28,
  },
  "& .MuiListItemText-root .MuiTypography-root": {
    fontSize: "0.8rem",
  },
  "& .MuiSvgIcon-root": {
    fontSize: "1rem",
  },
} as const;

export const COLUMN_MENU_DIVIDER_SX = { my: 0.5 } as const;
