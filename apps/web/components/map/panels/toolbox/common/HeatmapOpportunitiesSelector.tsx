import { Box, Button, Divider, IconButton, Stack, Typography, useTheme } from "@mui/material";
import { useParams } from "next/navigation";
import { type Dispatch, type SetStateAction, useMemo, useState } from "react";
import { v4 } from "uuid";

import { ICON_NAME, Icon } from "@p4b/ui/components/Icon";

import { useTranslation } from "@/i18n/client";

import { generateSeries } from "@/lib/utils/helpers";
import type { LayerFieldType } from "@/lib/validations/layer";
import { maxSensitivityValue } from "@/lib/validations/tools";

import type { SelectorItem } from "@/types/map/common";

import useLayerFields from "@/hooks/map/CommonHooks";
import { useLayerByGeomType, useLayerDatasetId } from "@/hooks/map/ToolsHooks";

import LayerFieldSelector from "@/components/map/common/LayerFieldSelector";
import Selector from "@/components/map/panels/common/Selector";
import SelectorFreeSolo from "@/components/map/panels/common/SelectorFreeSolo";
import { getTravelCostConfigValues } from "@/components/map/panels/toolbox/tools/catchment-area/utils";

export type Opportunity = {
  layer: SelectorItem | undefined;
  maxTravelTime: SelectorItem | undefined;
  sensitivity?: number | undefined;
  destinationPotentialColumn?: LayerFieldType | undefined;
  numberOfDestinations?: SelectorItem | undefined;
};

const HeatmapOpportunitiesSelector = ({
  opportunities,
  setOpportunities,
  heatmapType,
}: {
  opportunities: Opportunity[];
  setOpportunities: Dispatch<SetStateAction<Opportunity[]>>;
  heatmapType: "gravity" | "closest_average";
}) => {
  const { t } = useTranslation("common");
  const theme = useTheme();
  const { projectId } = useParams();
  const { filteredLayers } = useLayerByGeomType(["feature"], ["point", "polygon"], projectId as string);

  const createDefaultOpportunity = (options = {}) => ({
    layer: undefined,
    maxTravelTime: {
      value: 20,
      label: "20 (Min)",
    },
    ...options,
  });

  const defaultGravityOpportunities: Opportunity[] = [
    createDefaultOpportunity({
      sensitivity: 300000,
      destinationPotentialColumn: undefined,
    }),
  ];

  const defaultClosestAverageOpportunities: Opportunity[] = [
    createDefaultOpportunity({
      numberOfDestinations: {
        value: 1,
        label: "1",
      },
    }),
  ];

  const areOpportunitiesValid = useMemo(() => {
    return opportunities.every((opportunity) => {
      if (heatmapType === "gravity") {
        return (
          opportunity.layer !== undefined &&
          opportunity.maxTravelTime !== undefined &&
          opportunity.sensitivity !== undefined
        );
      } else if (heatmapType === "closest_average") {
        return (
          opportunity.layer !== undefined &&
          opportunity.maxTravelTime !== undefined &&
          opportunity.numberOfDestinations !== undefined
        );
      } else {
        return false;
      }
    });
  }, [heatmapType, opportunities]);

  const opportunityFilteredLayers = useMemo(() => {
    return filteredLayers.filter((layer) => {
      return !opportunities.some((opportunity) => opportunity.layer?.value === layer.value);
    });
  }, [filteredLayers, opportunities]);

  const [activeLayer, setActiveLayer] = useState<SelectorItem | undefined>(undefined);
  const activeLayerDatasetId = useLayerDatasetId(
    activeLayer?.value as number | undefined,
    projectId as string
  );

  const { layerFields: activeLayerFields } = useLayerFields(
    activeLayerDatasetId || "",
    "number",
    undefined,
    true
  );

  const sensitivityOptions = useMemo(() => {
    const series = generateSeries(50000, maxSensitivityValue);
    const options = series.map((s) => ({
      value: s,
      label: s.toString(),
    }));
    return options;
  }, []);

  const isValid = useMemo(() => {
    return !areOpportunitiesValid || !opportunityFilteredLayers.length || opportunities.length >= 5;
  }, [areOpportunitiesValid, opportunityFilteredLayers, opportunities.length]);

  return (
    <>
      {opportunities.map((opportunity, index) => {
        return (
          <Stack spacing={2} key={opportunity.layer?.value || v4()}>
            {/* LAYER */}
            <Box>
              {index > 0 && (
                <Stack direction="row" alignItems="end" justifyContent="end">
                  <IconButton
                    sx={{
                      pa: 0,
                      ma: 0,
                      "&:hover": {
                        color: theme.palette.error.main,
                      },
                    }}
                    onClick={() => {
                      setOpportunities((prev) => prev.filter((op) => op.layer !== opportunity.layer));
                    }}>
                    <Icon htmlColor="inherit" iconName={ICON_NAME.TRASH} style={{ fontSize: "12px" }} />
                  </IconButton>
                </Stack>
              )}
              <Selector
                selectedItems={opportunity.layer}
                setSelectedItems={(item: SelectorItem[] | SelectorItem | undefined) => {
                  const layer = item as SelectorItem;
                  setOpportunities((prev) =>
                    prev.map((op) => (op.layer === opportunity.layer ? { ...op, layer } : op))
                  );
                }}
                items={opportunityFilteredLayers || []}
                emptyMessage={t("no_layers_found")}
                emptyMessageIcon={ICON_NAME.LAYERS}
                label={t("opportunity_layer")}
                placeholder={t("select_opportunity_layer_placeholder")}
                tooltip={t("select_opportunity_layer_tooltip")}
              />
            </Box>

            {/* MAX TRAVEL TIME */}
            <Selector
              selectedItems={opportunity.maxTravelTime}
              setSelectedItems={(item: SelectorItem[] | SelectorItem | undefined) => {
                const maxTravelTime = item as SelectorItem;
                setOpportunities((prev) =>
                  prev.map((op) => (op.layer === opportunity.layer ? { ...op, maxTravelTime } : op))
                );
              }}
              items={getTravelCostConfigValues(3, 30, "min")}
              label={t("travel_time_limit") + " (Min)"}
              tooltip={t("travel_time_limit_tooltip")}
            />

            {/* DESTINATION POTENTIAL COLUMN */}
            {heatmapType === "gravity" && (
              <LayerFieldSelector
                fields={activeLayerFields}
                onFocus={() => setActiveLayer(opportunity.layer)}
                onClose={() => setActiveLayer(undefined)}
                selectedField={opportunity.destinationPotentialColumn}
                disabled={!opportunity.layer}
                setSelectedField={(field) => {
                  setOpportunities((prev) =>
                    prev.map((op) =>
                      op.layer === opportunity.layer ? { ...op, destinationPotentialColumn: field } : op
                    )
                  );
                }}
                label={t("destination_potential_column")}
                tooltip={t("destination_potential_column_tooltip")}
              />
            )}
            {/* SENSITIVITY */}
            {heatmapType === "gravity" && (
              <SelectorFreeSolo
                options={sensitivityOptions}
                selectedItem={
                  opportunity.sensitivity
                    ? {
                        value: opportunity.sensitivity,
                        label: opportunity.sensitivity.toString(),
                      }
                    : undefined
                }
                label={t("sensitivity")}
                placeholder={t("sensitivity_placeholder")}
                inputType="number"
                onSelect={(item: SelectorItem) => {
                  // eslint-disable-next-line @typescript-eslint/no-explicit-any
                  let newValue = undefined as any;
                  if (item) newValue = Number(item.value);
                  setOpportunities((prev) =>
                    prev.map((op) => (op.layer === opportunity.layer ? { ...op, sensitivity: newValue } : op))
                  );
                }}
              />
            )}

            {/* NUMBER OF DESTINATIONS */}
            {heatmapType === "closest_average" && (
              <Selector
                selectedItems={opportunity.numberOfDestinations}
                setSelectedItems={(item: SelectorItem[] | SelectorItem | undefined) => {
                  const numberOfDestinations = item as SelectorItem;
                  setOpportunities((prev) =>
                    prev.map((op) => (op.layer === opportunity.layer ? { ...op, numberOfDestinations } : op))
                  );
                }}
                items={getTravelCostConfigValues(1, 10, "")}
                label={t("number_of_destinations")}
                tooltip={t("number_of_destinations_tooltip")}
              />
            )}

            {index === 0 && opportunities.length > 1 && <Divider />}
          </Stack>
        );
      })}
      <Divider />
      <Button
        fullWidth
        disabled={isValid}
        onClick={() => {
          if (heatmapType === "gravity") {
            setOpportunities((prev) => [...prev, ...defaultGravityOpportunities]);
          }
          if (heatmapType === "closest_average") {
            setOpportunities((prev) => [...prev, ...defaultClosestAverageOpportunities]);
          }
        }}
        variant="text"
        size="small"
        startIcon={<Icon iconName={ICON_NAME.PLUS} style={{ fontSize: "15px" }} />}>
        <Typography variant="body2" color="inherit">
          {t("common:add_opportunity")}
        </Typography>
      </Button>
    </>
  );
};

export default HeatmapOpportunitiesSelector;
