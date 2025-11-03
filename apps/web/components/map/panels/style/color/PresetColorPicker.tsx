import { styled } from "@mui/material/styles";

import { ColorsByTheme, Themes } from "@/lib/constants/color";
import range, { hexToRgb } from "@/lib/utils/helpers";

import type { SingleColorSelectorProps } from "@/types/map/color";

const PALETTE_HEIGHT = "8px";
const ROWS = 22;

const StyledColorPalette = styled("div")({
  display: "flex",
  flexDirection: "row",
  justifyContent: "space-between",
  "&:hover": {
    cursor: "pointer",
  },
});

const StyledColorColumn = styled("div")({
  display: "flex",
  flexGrow: 1,
  flexDirection: "column",
  justifyContent: "space-between",
});

const StyledColorBlock = styled("div")<{ selected: boolean }>(({ theme, selected }) => ({
  flexGrow: 1,
  height: `${PALETTE_HEIGHT}`,
  borderWidth: "1px",
  borderStyle: "solid",
  borderColor: selected ? theme.palette.primary.main : "transparent",
}));

const PresetColorPicker: React.FC<SingleColorSelectorProps> = ({ selectedColor, onSelectColor }) => (
  <StyledColorPalette className="single-color-palette">
    {Themes.map((theme) => (
      <StyledColorColumn key={theme} className="single-color-palette__column">
        {range(1, ROWS + 1, 1).map((key) => (
          <StyledColorBlock
            className="single-color-palette__block"
            style={{
              backgroundColor: ColorsByTheme[theme][key],
              borderColor:
                selectedColor.toUpperCase() === ColorsByTheme[theme][key].toUpperCase()
                  ? "white"
                  : ColorsByTheme[theme][key],
            }}
            key={`${theme}_${key}`}
            selected={selectedColor === ColorsByTheme[theme][key].toUpperCase()}
            onClick={(e) => onSelectColor(hexToRgb(ColorsByTheme[theme][key]), e)}
          />
        ))}
      </StyledColorColumn>
    ))}
  </StyledColorPalette>
);

export default PresetColorPicker;
