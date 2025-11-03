import { useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { DragIndicator } from "@mui/icons-material";
import { Grid, MenuItem, Stack, useTheme } from "@mui/material";

import { DragHandle } from "@/components/common/DragHandle";

type SortableItemProps = {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  item: any;
  active?: boolean;
  label: string;
  picker?: React.ReactNode;
  children?: React.ReactNode;
  actions?: React.ReactNode;
};

export function SortableItem(props: SortableItemProps) {
  const { attributes, listeners, setNodeRef, transform, transition } = useSortable({ id: props.item.id });
  const theme = useTheme();
  const style = {
    transform: CSS.Transform.toString(transform),
    transition: `${transition}, border-color 0.2s ease-in-out`,
  };
  return (
    <MenuItem
      key={props.item.id}
      ref={setNodeRef}
      selected={props.active}
      style={style}
      disableGutters
      disableRipple
      sx={{
        pr: 0,
        transition: theme.transitions.create(["opacity"], {
          duration: theme.transitions.duration.standard,
        }),
        py: 1,
        ":hover": {
          "& div, & button": {
            opacity: 1,
          },
        },
      }}>
      <Grid container alignItems="center" justifyContent="start" spacing={2}>
        <Grid item xs={1} sx={{ mx: 1 }}>
          <DragHandle {...attributes} listeners={listeners}>
            <DragIndicator fontSize="small" />
          </DragHandle>
        </Grid>
        {props.picker && (
          <Grid item xs={2} zeroMinWidth>
            {props.picker}
          </Grid>
        )}
        <Grid item xs zeroMinWidth>
          {props.children}
        </Grid>
        <Grid item xs={2} zeroMinWidth>
          <Stack direction="row" justifyContent="flex-end" sx={{ pr: 3 }}>
            {props.actions && props.actions}
          </Stack>
        </Grid>
      </Grid>
    </MenuItem>
  );
}
