import { Box, Divider, IconButton, Link, Paper, Stack, Tooltip, Typography } from "@mui/material";
import { useState } from "react";
import { Popup } from "react-map-gl/maplibre";

import { ICON_NAME, Icon } from "@p4b/ui/components/Icon";

import { useTranslation } from "@/i18n/client";

import type { MapPopoverInfoProps } from "@/types/map/popover";

// Assuming this type remains relevant for the popover itself
import { OverflowTypograpy } from "@/components/common/OverflowTypography";

// --- Helper Components (Row, ViewTableRow) - Keep them here or move to a shared file ---

interface RowProps {
  name: string;
  value: string;
}

const Row: React.FC<RowProps> = ({ name, value }) => {
  let url = "";
  if (!url && value && typeof value === "string" && value.match(/^(http|www)/)) {
    url = value;
  }

  return (
    <tr>
      <td>
        <OverflowTypograpy
          variant="body2"
          tooltipProps={{
            placement: "top",
            arrow: true,
            enterDelay: 200,
          }}>
          {name}
        </OverflowTypograpy>
      </td>
      <td style={{ textAlign: "right" }}>
        <OverflowTypograpy
          variant="body2"
          fontWeight="bold"
          tooltipProps={{
            placement: "top",
            arrow: true,
            enterDelay: 200,
          }}>
          {url ? (
            <Link target="_blank" rel="noopener noreferrer" href={url}>
              {value}
            </Link>
          ) : (
            <>{value}</>
          )}
        </OverflowTypograpy>
      </td>
    </tr>
  );
};

interface ViewTableRowProps {
  name: string;
  onClick: () => void;
}

const ViewTableRow: React.FC<ViewTableRowProps> = ({ name, onClick }) => {
  const { t } = useTranslation("common");

  return (
    <tr>
      <td>
        <OverflowTypograpy
          variant="body2"
          tooltipProps={{
            placement: "top",
            arrow: true,
            enterDelay: 200,
          }}>
          {name}
        </OverflowTypograpy>
      </td>
      <td style={{ textAlign: "right" }}>
        <Tooltip
          placement="top"
          arrow
          title={t("view_property_data", {
            property: name,
          })}>
          <IconButton size="small" onClick={onClick}>
            <Icon iconName={ICON_NAME.TABLE} style={{ fontSize: 16 }} />
          </IconButton>
        </Tooltip>
      </td>
    </tr>
  );
};

// --- Define DetailsViewType ---
export interface DetailsViewType {
  property: string;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  data: Array<{ [key: string]: any }>; // Allow any value type in data
}

interface LayerInfoHeaderProps {
  title: string;
  onClose: () => void;
}

export const LayerInfoHeader: React.FC<LayerInfoHeaderProps> = ({ title, onClose }) => {
  return (
    <Stack sx={{ px: 2, pt: 2 }} direction="row" alignItems="center" justifyContent="space-between">
      <Stack direction="row" spacing={2} alignItems="center" sx={{ width: "90%" }}>
        <Icon iconName={ICON_NAME.LAYERS} style={{ fontSize: 16 }} />
        <Typography variant="body2" fontWeight="bold">
          {title}
        </Typography>
      </Stack>
      <IconButton onClick={onClose} sx={{ pointerEvents: "all" }}>
        <Icon iconName={ICON_NAME.XCLOSE} style={{ fontSize: 16 }} />
      </IconButton>
    </Stack>
  );
};

// --- New Reusable LayerInfo Component ---

interface LayerInfoProps {
  properties?: Record<string, string>;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  jsonProperties?: Record<string, Array<{ [key: string]: any }>>;
  detailsView: DetailsViewType | undefined;
  setDetailsView: (details: DetailsViewType | undefined) => void;
}

export const LayerInfo: React.FC<LayerInfoProps> = ({
  properties,
  jsonProperties,
  detailsView,
  setDetailsView,
}) => {
  return (
    <Box>
      <Paper elevation={0}>
        {/* Content Area */}
        <Box sx={{ overflowY: "auto" }}>
          {/* Default View: Properties and JSON Property Links */}
          {!detailsView && (
            <table
              style={{
                tableLayout: "fixed",
                width: "100%",
                padding: 5,
              }}>
              <tbody>
                {properties &&
                  Object.entries(properties).map(
                    ([key, value]) => <Row key={key} name={key} value={String(value)} /> // Ensure value is string
                  )}
                {jsonProperties &&
                  Object.entries(jsonProperties).map(([key, data]) => (
                    <ViewTableRow
                      key={key}
                      name={key}
                      onClick={() =>
                        setDetailsView({
                          property: key,
                          data: data, // data is already Array<{ [key: string]: any }>
                        })
                      }
                    />
                  ))}
              </tbody>
            </table>
          )}

          {/* Details View: Table for JSON Property */}
          {detailsView && (
            <Stack direction="column">
              {/* Details Header */}
              <Stack direction="row" spacing={1} alignItems="center" sx={{ px: 1, pt: 1 }}>
                <IconButton
                  size="small"
                  onClick={() => {
                    setDetailsView(undefined);
                  }}>
                  <Icon iconName={ICON_NAME.CHEVRON_LEFT} style={{ fontSize: 16 }} />
                </IconButton>
                <Typography variant="body2" fontWeight="bold">
                  {detailsView.property}
                </Typography>
              </Stack>
              <Divider sx={{ mb: 0, mt: 1 }} />

              {/* Details Table */}
              <table
                style={{ tableLayout: "auto", width: "100%", padding: "5px 10px", borderSpacing: "0 4px" }}>
                {" "}
                {/* Adjusted styles */}
                <thead>
                  <tr style={{ textAlign: "left" }}>
                    {" "}
                    {/* Align header text left */}
                    {detailsView.data.length > 0 &&
                      Object.keys(detailsView.data[0]).map((key) => (
                        <th key={key} style={{ padding: "4px 8px", borderBottom: "1px solid #eee" }}>
                          {" "}
                          {/* Added padding & border */}
                          <Typography variant="caption" color="textSecondary">
                            {key}
                          </Typography>{" "}
                          {/* Style header */}
                        </th>
                      ))}
                  </tr>
                </thead>
                <tbody>
                  {detailsView.data.length > 0 &&
                    detailsView.data.map((item, index) => (
                      <tr key={index} style={{ borderBottom: "1px solid #f5f5f5" }}>
                        {" "}
                        {/* Add subtle row separator */}
                        {Object.entries(item).map(([key, value]) => (
                          <td style={{ padding: "4px 8px" }} key={key}>
                            {" "}
                            {/* Added padding */}
                            <Typography variant="body2"> {String(value)} </Typography>{" "}
                            {/* Ensure value is string & style */}
                          </td>
                        ))}
                      </tr>
                    ))}
                  {detailsView.data.length === 0 && ( // Handle empty data case
                    <tr>
                      <td
                        colSpan={Object.keys(detailsView.data[0] || {}).length || 1}
                        style={{ padding: "10px", textAlign: "center" }}>
                        <Typography variant="body2" color="textSecondary">
                          No data available.
                        </Typography>
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </Stack>
          )}
        </Box>
      </Paper>
    </Box>
  );
};

export const MapPopoverInfo: React.FC<MapPopoverInfoProps> = ({
  title,
  properties,
  jsonProperties,
  lngLat,
  onClose,
}) => {
  const [detailsView, setDetailsView] = useState<DetailsViewType | undefined>(undefined);

  return (
    <Popup
      onClose={() => {
        setDetailsView(undefined); // Reset details view when popup closes externally
        onClose();
      }}
      longitude={lngLat[0]}
      latitude={lngLat[1]}
      closeButton={false} // The close button is now inside LayerInfo
      closeOnClick={false} // Keep popup open on map click
      maxWidth={detailsView ? "500px" : "300px"} // maxWidth still controlled here
    >
      <Box>
        <LayerInfoHeader title={title} onClose={onClose} />
        <Divider sx={{ mb: 0 }} />
        <Box sx={{ overflowY: "auto", maxHeight: "280px" }}>
          <LayerInfo
            properties={properties}
            jsonProperties={jsonProperties}
            detailsView={detailsView}
            setDetailsView={setDetailsView}
          />
        </Box>
      </Box>
    </Popup>
  );
};
