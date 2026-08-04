import { Box, TablePagination } from "@mui/material";

import type { Layer } from "@/lib/validations/layer";
import type { ProjectLayer } from "@/lib/validations/project";

import { DEFAULT_ROWS_PER_PAGE_OPTIONS } from "@/lib/utils/pagination";

import { useFeaturePage } from "@/hooks/useFeaturePage";

import FeatureTable from "@/components/common/FeatureTable";

interface DatasetTableTabProps {
  dataset: ProjectLayer | Layer;
}

const DatasetTableTab: React.FC<DatasetTableTabProps> = ({ dataset }) => {
  const {
    fields,
    areFieldsLoading,
    data,
    rowsPerPage,
    page,
    totalCount,
    onPageChange,
    onRowsPerPageChange,
  } = useFeaturePage((dataset["id"] as string) || "", { limit: 25 });

  return (
    <Box>
      <Box
        sx={{
          height: `calc(100vh - 440px)`,
          overflowX: "hidden",
        }}>
        <FeatureTable fields={fields} data={data} isLoading={areFieldsLoading} />
      </Box>
      {data && (
        <TablePagination
          sx={{ mt: 2 }}
          rowsPerPageOptions={DEFAULT_ROWS_PER_PAGE_OPTIONS}
          component="div"
          count={totalCount}
          rowsPerPage={rowsPerPage}
          page={page}
          onPageChange={onPageChange}
          onRowsPerPageChange={onRowsPerPageChange}
        />
      )}
    </Box>
  );
};

export default DatasetTableTab;
