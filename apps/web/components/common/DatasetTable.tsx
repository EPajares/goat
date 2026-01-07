import KeyboardArrowDownIcon from "@mui/icons-material/KeyboardArrowDown";
import KeyboardArrowUpIcon from "@mui/icons-material/KeyboardArrowUp";
import { Box, Collapse, IconButton, Skeleton } from "@mui/material";
import { Stack, Table, TableBody, TableCell, TableHead, TableRow, Typography } from "@mui/material";
import { useMemo, useState } from "react";
import { v4 } from "uuid";

import type { DatasetCollectionItems } from "@/lib/validations/layer";

import { FieldTypeTag } from "@/components/map/common/LayerFieldSelector";
import NoValuesFound from "@/components/map/common/NoValuesFound";

const formatCellValue = (value: unknown): string => {
  if (value === null || value === undefined) {
    return "";
  }
  if (typeof value === "object") {
    return JSON.stringify(value);
  }
  return String(value);
};

const Row = ({ row, fields }) => {
  const [open, setOpen] = useState(false);

  const primitiveFields = useMemo(() => fields.filter((field) => field.type !== "object"), [fields]);

  const objectFields = useMemo(() => fields.filter((field) => field.type === "object"), [fields]);

  return (
    <>
      <TableRow key={row.id}>
        {objectFields.length > 0 && (
          <TableCell>
            <IconButton aria-label="expand row" size="small" onClick={() => setOpen(!open)}>
              {open ? <KeyboardArrowUpIcon /> : <KeyboardArrowDownIcon />}
            </IconButton>
          </TableCell>
        )}
        {primitiveFields.map((field, fieldIndex) => (
          <TableCell key={fieldIndex}>{formatCellValue(row.properties[field.name])}</TableCell>
        ))}
      </TableRow>

      {!!objectFields.length && (
        <TableRow>
          <TableCell style={{ paddingBottom: 0, paddingTop: 0 }} colSpan={primitiveFields.length + 1}>
            <Collapse in={open} timeout="auto" unmountOnExit>
              <Box sx={{ margin: 2 }}>
                {objectFields.map((field) => {
                  const rawValue = row.properties[field.name];
                  // Handle both string (JSON) and object values
                  const jsonData = typeof rawValue === "string" ? JSON.parse(rawValue) : rawValue;
                  const isJsonDataArrayOfObjects =
                    Array.isArray(jsonData) &&
                    jsonData.length > 0 &&
                    typeof jsonData[0] === "object" &&
                    !Array.isArray(jsonData[0]);

                  return (
                    <>
                      <Stack direction="column" spacing={1} sx={{ py: 1, pl: 4 }}>
                        <Typography variant="body2" fontWeight="bold">
                          {field.name}
                        </Typography>
                        <FieldTypeTag fieldType={field.type}>{field.type}</FieldTypeTag>
                      </Stack>
                      {isJsonDataArrayOfObjects ? (
                        <Table size="small" aria-label="purchases" key={field.name}>
                          <TableHead>
                            <TableRow>
                              {Object.keys(jsonData[0]).map((key) => (
                                <TableCell key={key}>{key}</TableCell>
                              ))}
                            </TableRow>
                          </TableHead>
                          <TableBody>
                            {jsonData.map((item, rowIndex) => (
                              <TableRow key={rowIndex}>
                                {Object.values(item).map((value: string, cellIndex) => (
                                  <TableCell key={cellIndex}>{formatCellValue(value)}</TableCell>
                                ))}
                              </TableRow>
                            ))}
                          </TableBody>
                        </Table>
                      ) : (
                        // Handle the case where jsonData is not an array of objects
                        // This could be rendering it as a string or handling other data structures in the future.
                        <Typography>{JSON.stringify(jsonData, null, 2)}</Typography>
                      )}
                    </>
                  );
                })}
              </Box>
            </Collapse>
          </TableCell>
        </TableRow>
      )}
    </>
  );
};

interface DatasetTableProps {
  areFieldsLoading: boolean;
  displayData?: DatasetCollectionItems;
  fields: Array<{ name: string; type: string }>; // Adjust the type based on your data structure
}

const DatasetTable: React.FC<DatasetTableProps> = ({ areFieldsLoading, displayData, fields }) => {
  return (
    <>
      {areFieldsLoading && !displayData && (
        <>
          <Skeleton variant="rectangular" height={60} sx={{ m: 4 }} />
          <Skeleton variant="rectangular" height={240} sx={{ m: 4 }} />
        </>
      )}

      {!areFieldsLoading && displayData && (
        <Table size="small" aria-label="simple table" stickyHeader>
          <TableHead>
            <TableRow>
              {fields.some((field) => field.type === "object") && <TableCell />}
              {fields
                .filter((field) => field.type !== "object")
                .map((field) => (
                  <TableCell key={field.name}>
                    <Stack direction="column" spacing={1} sx={{ py: 1 }}>
                      <Typography variant="body2" fontWeight="bold">
                        {field.name}
                      </Typography>
                      <FieldTypeTag fieldType={field.type}>{field.type}</FieldTypeTag>
                    </Stack>
                  </TableCell>
                ))}
            </TableRow>
          </TableHead>
          <TableBody>
            {displayData.features.length === 0 && (
              <TableRow>
                <TableCell align="center" colSpan={fields.length} sx={{ borderBottom: "none" }}>
                  <NoValuesFound />
                </TableCell>
              </TableRow>
            )}
            {displayData.features?.length &&
              displayData.features.map((row) => <Row key={row.id || v4()} row={row} fields={fields} />)}
          </TableBody>
        </Table>
      )}
    </>
  );
};

export default DatasetTable;
