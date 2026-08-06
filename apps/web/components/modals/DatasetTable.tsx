import { IconButton } from "@mui/material";
import { Dialog, DialogActions, DialogContent, DialogTitle, Stack, TablePagination } from "@mui/material";
import { useMemo } from "react";

import { ICON_NAME, Icon } from "@p4b/ui/components/Icon";

import type { Layer } from "@/lib/validations/layer";
import type { ProjectLayer } from "@/lib/validations/project";

import { DEFAULT_ROWS_PER_PAGE_OPTIONS } from "@/lib/utils/pagination";

import { useFeaturePage } from "@/hooks/useFeaturePage";

import FeatureTable from "@/components/common/FeatureTable";

interface DatasetTableDialogProps {
  open: boolean;
  onClose?: () => void;
  disabled?: boolean;
  dataset: ProjectLayer | Layer;
}

const DatasetTableModal: React.FC<DatasetTableDialogProps> = ({ open, onClose, dataset }) => {
  const datasetId = dataset["layer_id"] || dataset["id"] || "";
  // A project layer's saved filter must narrow the preview too.
  const filter = useMemo(() => dataset["query"]?.["cql"] ?? undefined, [dataset]);

  const {
    fields,
    areFieldsLoading,
    data,
    rowsPerPage,
    page,
    totalCount,
    onPageChange,
    onRowsPerPageChange,
  } = useFeaturePage(datasetId, { limit: 50, filter });

  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="lg">
      <DialogTitle>
        <Stack direction="row" spacing={1} justifyContent="space-between">
          {`${dataset.name}`}
          <IconButton onClick={() => onClose && onClose()}>
            <Icon iconName={ICON_NAME.CLOSE} htmlColor="inherit" fontSize="small" />
          </IconButton>
        </Stack>
      </DialogTitle>
      <DialogContent sx={{ px: 0, mx: 0, pb: 0, minHeight: "250px" }}>
        <FeatureTable fields={fields} data={data} isLoading={areFieldsLoading} />
      </DialogContent>
      <DialogActions sx={{ pb: 0 }}>
        {data && (
          <TablePagination
            rowsPerPageOptions={DEFAULT_ROWS_PER_PAGE_OPTIONS}
            component="div"
            count={totalCount}
            rowsPerPage={rowsPerPage}
            page={page}
            onPageChange={onPageChange}
            onRowsPerPageChange={onRowsPerPageChange}
          />
        )}
      </DialogActions>
    </Dialog>
  );
};

export default DatasetTableModal;
