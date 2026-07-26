import { Box, Dialog, IconButton, InputBase, LinearProgress, Slide, Stack } from "@mui/material";
import type { TransitionProps } from "@mui/material/transitions";
import { forwardRef, useRef } from "react";
import { useTranslation } from "react-i18next";

import { ICON_NAME, Icon } from "@p4b/ui/components/Icon";

import type { LayerSearchGroup, LayerSearchResultItem } from "@/lib/api/processes";

import type { Feature } from "@/types/map/controllers";

import SearchResultsList, {
  type SearchLayersById,
  type SearchRow,
  searchOptionId,
} from "@/components/map/controls/search/SearchResultsList";

const SlideUpTransition = forwardRef(function SlideUpTransition(
  props: TransitionProps & { children: React.ReactElement },
  ref: React.Ref<unknown>
) {
  return <Slide direction="up" ref={ref} {...props} />;
});

export type MobileSearchOverlayProps = {
  open: boolean;
  onClose: () => void;
  query: string;
  setQuery: (query: string) => void;
  /** Clears the query and the selected-place pin (desktop parity). */
  onClear: () => void;
  rows: SearchRow[];
  layerGroups: LayerSearchGroup[];
  layersById: SearchLayersById;
  activeIndex: number;
  loading: boolean;
  listboxId: string;
  placeholder: string;
  onKeyDown: (event: React.KeyboardEvent) => void;
  onSelectPlace: (feature: Feature) => void;
  onSelectFeature: (group: LayerSearchGroup, item: LayerSearchResultItem) => void;
};

const MobileSearchOverlay = ({
  open,
  onClose,
  query,
  setQuery,
  onClear,
  rows,
  layerGroups,
  layersById,
  activeIndex,
  loading,
  listboxId,
  placeholder,
  onKeyDown,
  onSelectPlace,
  onSelectFeature,
}: MobileSearchOverlayProps) => {
  const { t } = useTranslation("common");
  const inputRef = useRef<HTMLInputElement>(null);
  const hasVisibleResults =
    rows.length > 0 ||
    layerGroups.some((group) => (group.timed_out || !!group.error) && group.results.length === 0);

  return (
    <Dialog
      fullScreen
      open={open}
      onClose={onClose}
      // MUI puts `role="dialog"` on the Paper, not on the Modal root that
      // top-level props land on — so the label has to go on the Paper to be
      // picked up as the dialog's accessible name.
      PaperProps={{ "aria-label": t("search") }}
      TransitionComponent={SlideUpTransition}
      TransitionProps={{
        onEnter: () => inputRef.current?.focus(),
        onEntered: () => inputRef.current?.focus(),
      }}>
      <Stack
        direction="row"
        alignItems="center"
        spacing={1}
        sx={{
          px: 1,
          // Symmetric vertical padding; the notch/status-bar inset is added on
          // top of it so the bar only grows where a device actually needs it.
          py: 1.25,
          pt: "calc(env(safe-area-inset-top, 0px) + 10px)",
          borderBottom: 1,
          borderColor: "divider",
        }}>
        <IconButton onClick={onClose} aria-label={t("back")}>
          <Icon iconName={ICON_NAME.CHEVRON_LEFT} fontSize="small" />
        </IconButton>
        <InputBase
          inputRef={inputRef}
          autoFocus
          fullWidth
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          onKeyDown={onKeyDown}
          placeholder={placeholder}
          inputProps={{
            role: "combobox",
            "aria-label": t("search"),
            "aria-expanded": hasVisibleResults,
            "aria-controls": listboxId,
            "aria-autocomplete": "list",
            ...(activeIndex >= 0 && activeIndex < rows.length
              ? { "aria-activedescendant": searchOptionId(listboxId, activeIndex) }
              : {}),
          }}
        />
        {query && (
          <IconButton onClick={onClear} aria-label={t("clear")}>
            <Icon iconName={ICON_NAME.CLOSE} fontSize="small" />
          </IconButton>
        )}
      </Stack>
      <Box sx={{ height: 2, flex: "none" }}>{loading && <LinearProgress sx={{ height: 2 }} />}</Box>
      <Box sx={{ flex: 1, overflowY: "auto" }}>
        <SearchResultsList
          query={query}
          rows={rows}
          layerGroups={layerGroups}
          layersById={layersById}
          activeIndex={activeIndex}
          loading={loading}
          listboxId={listboxId}
          onSelectPlace={onSelectPlace}
          onSelectFeature={onSelectFeature}
        />
      </Box>
    </Dialog>
  );
};

export default MobileSearchOverlay;
