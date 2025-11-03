import { Collapse, Divider, Stack } from "@mui/material";

const SectionOptions = ({
  active,
  baseOptions,
  advancedOptions,
  collapsed,
}: {
  active: boolean;
  baseOptions: React.ReactNode;
  advancedOptions?: React.ReactNode;
  collapsed?: boolean;
}) => {
  return (
    <Collapse in={!!active}>
      <Stack direction="row" alignItems="center" sx={{ pl: 2, height: "100%" }}>
        <Divider orientation="vertical" sx={{ borderRightWidth: "2px", my: -4 }} />
        <Stack sx={{ pl: 4, pr: 2, py: 4, width: "100%", pt: 2 }} spacing={4} justifyContent="center">
          {baseOptions}
          {/* { Options } */}
          {advancedOptions && (
            <Collapse in={!collapsed}>
              <Stack spacing={4}>{advancedOptions}</Stack>
            </Collapse>
          )}
        </Stack>
      </Stack>
    </Collapse>
  );
};

export default SectionOptions;
