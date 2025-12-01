import {
  Box,
  Button,
  ClickAwayListener,
  Divider,
  ListItemIcon,
  Menu,
  MenuItem,
  MenuList,
  Stack,
  Typography,
  useTheme,
} from "@mui/material";
import React, { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { v4 } from "uuid";

import { ICON_NAME, Icon } from "@p4b/ui/components/Icon";

import { updateProjectLayer } from "@/lib/api/projects";
import { createTheCQLBasedOnExpression, parseCQLQueryToObject } from "@/lib/transformers/filter";
import { layerType } from "@/lib/validations/common";
import { type Expression as ExpressionType, FilterType } from "@/lib/validations/filter";
import type { ProjectLayer } from "@/lib/validations/project";

import type { SelectorItem } from "@/types/map/common";

import useLayerFields from "@/hooks/map/CommonHooks";
import { useFilteredProjectLayers } from "@/hooks/map/LayerPanelHooks";

import Selector from "@/components/map/panels/common/Selector";
import Expression from "@/components/map/panels/filter/Expression";

const FilterPanel = ({ activeLayer, projectId }: { activeLayer: ProjectLayer; projectId: string }) => {
  const { t } = useTranslation("common");
  const theme = useTheme();
  const [previousLayerId, setPreviousLayerId] = useState<string | null>(null);
  const { layerFields } = useLayerFields(activeLayer?.layer_id || "");
  const { layers: projectLayers, mutate: mutateProjectLayers } = useFilteredProjectLayers(projectId);

  // Add filter expression
  const [addExpressionAnchorEl, setAddExpressionAnchorEl] = React.useState<null | HTMLElement>(null);
  const handleAddExpressionClick = (event: React.MouseEvent<HTMLButtonElement>) => {
    if (activeLayer?.type === layerType.Values.feature) {
      setAddExpressionAnchorEl(event.currentTarget);
    } else {
      createExpression(FilterType.Logical);
    }
  };
  const handleAddExpressionClose = () => {
    setAddExpressionAnchorEl(null);
  };
  const open = Boolean(addExpressionAnchorEl);
  const addExpressionItems = [
    {
      sourceType: FilterType.Logical,
      iconName: ICON_NAME.TABLE,
      label: t("logical_expression"),
    },
    {
      sourceType: FilterType.Spatial,
      iconName: ICON_NAME.MAP,
      label: t("spatial_expression"),
    },
  ];

  const [expressions, setExpressions] = useState<ExpressionType[]>([]);

  const defaultLogicalOperator: SelectorItem = {
    value: "and",
    label: t("and"),
  };
  const logicalOperators = useMemo(() => {
    return [
      {
        value: "and",
        label: t("match_all_filters"),
      },
      {
        value: "or",
        label: t("match_at_least_one_filter"),
      },
    ];
  }, [t]);

  const [logicalOperator, setLogicalOperator] = useState<SelectorItem | undefined>(defaultLogicalOperator);

  const createExpression = (type: FilterType) => {
    if (expressions) {
      setExpressions([
        ...expressions,
        {
          id: v4(),
          attribute: "",
          expression: "",
          value: "",
          type,
        },
      ]);
    }
  };

  // Load existing expressions
  useEffect(() => {
    if (activeLayer?.layer_id !== previousLayerId && activeLayer?.layer_id) {
      setPreviousLayerId(activeLayer?.layer_id);
      setExpressions([]);
    }
    if (expressions.length) return;
    const existingExpressions = parseCQLQueryToObject(
      activeLayer?.query?.cql as { op: string; args: unknown[] }
    );
    if (activeLayer?.query?.cql?.["op"] && activeLayer.query.cql !== null) {
      const operator = activeLayer.query.cql["op"];
      if (operator) {
        setLogicalOperator(logicalOperators.find((item) => item.value === operator));
      }
    }
    setExpressions(existingExpressions);
  }, [activeLayer, expressions.length, logicalOperators, previousLayerId]);

  const validateExpressions = (expressions) => {
    return expressions.every((expression) => {
      let hasValue = !!expression.value.toString();
      if (
        expression.expression === "is_empty_string" ||
        expression.expression === "is_not_empty_string" ||
        expression.expression === "is_blank" ||
        expression.expression === "is_not_blank"
      ) {
        hasValue = true;
      }
      return expression.attribute && expression.expression && hasValue;
    });
  };

  const areAllExpressionsValid = useMemo(() => {
    return validateExpressions(expressions);
  }, [expressions]);

  const updateLayer = async (query) => {
    if (!activeLayer) return;
    const layers = JSON.parse(JSON.stringify(projectLayers));
    const index = layers.findIndex((l) => l.id === activeLayer.id);
    const layerToUpdate = layers[index];
    if (query === null) {
      layerToUpdate.query = null;
    } else {
      layerToUpdate.query = {
        cql: query,
      };
    }
    await mutateProjectLayers(layers, false);
    await updateProjectLayer(projectId, activeLayer.id, layerToUpdate);
  };

  const updateLayerQuery = async (expressions, logicalOperator) => {
    if (expressions.length === 0) {
      await updateLayer(null);
      return;
    }
    if (!activeLayer || !logicalOperator || !validateExpressions(expressions)) return;
    const query = createTheCQLBasedOnExpression(
      expressions,
      layerFields,
      logicalOperator.value as "and" | "or"
    );
    await updateLayer(query);
  };

  const clearFilter = async () => {
    setExpressions([]);
    await updateLayer(null);
  };

  return (
    <Box sx={{ p: 3 }}>
      {/* DESCRIPTION */}
      {!expressions?.length && (
        <Typography variant="body2" sx={{ fontStyle: "italic", marginBottom: theme.spacing(4) }}>
          {t("filter_layer_message")}
        </Typography>
      )}
      {expressions && expressions?.length > 1 && (
        <>
          <Divider />
          <Selector
            selectedItems={logicalOperator}
            setSelectedItems={(item: SelectorItem[] | SelectorItem | undefined) => {
              setLogicalOperator(item as SelectorItem);
              updateLayerQuery(expressions, item);
            }}
            items={logicalOperators}
            label={t("filter_results")}
          />
        </>
      )}

      {expressions && !!expressions?.length && (
        <Stack spacing={4} sx={{ pt: 4 }}>
          <Divider />
          {expressions.map((expression: ExpressionType) => (
            <Expression
              key={expression.id}
              expression={expression}
              onDelete={async (expression) => {
                const updatedExpressions = expressions.filter((e) => e.id !== expression.id);
                setExpressions(updatedExpressions);
                await updateLayerQuery(updatedExpressions, logicalOperator);
              }}
              onDuplicate={async (expression: ExpressionType) => {
                const updatedExpressions = [...expressions, { ...expression, id: v4() }];
                setExpressions(updatedExpressions);
                await updateLayerQuery(updatedExpressions, logicalOperator);
              }}
              onUpdate={async (expression: ExpressionType) => {
                const updatedExpressions = expressions.map((e) => (e.id === expression.id ? expression : e));
                setExpressions(updatedExpressions);
                await updateLayerQuery(updatedExpressions, logicalOperator);
              }}
            />
          ))}
        </Stack>
      )}

      {activeLayer && (
        <Stack spacing={2} sx={{ pt: 4 }}>
          {/* ADD EXPRESSION */}
          <Button
            onClick={handleAddExpressionClick}
            fullWidth
            size="small"
            disabled={!areAllExpressionsValid}
            startIcon={<Icon iconName={ICON_NAME.PLUS} style={{ fontSize: "15px" }} />}>
            <Typography variant="body2" fontWeight="bold" color="inherit">
              {t("common:add_expression")}
            </Typography>
          </Button>
          {activeLayer.type === layerType.Values.feature && (
            <Menu
              anchorEl={addExpressionAnchorEl}
              sx={{
                "& .MuiPaper-root": {
                  boxShadow: "0px 0px 10px 0px rgba(58, 53, 65, 0.1)",
                },
              }}
              anchorOrigin={{ vertical: "top", horizontal: "center" }}
              transformOrigin={{ vertical: "bottom", horizontal: "center" }}
              open={open}
              MenuListProps={{
                "aria-labelledby": "basic-button",
                sx: {
                  width: addExpressionAnchorEl && addExpressionAnchorEl.offsetWidth - 10,
                  p: 0,
                },
              }}
              onClose={handleAddExpressionClose}>
              <Box>
                <ClickAwayListener onClickAway={handleAddExpressionClose}>
                  <MenuList>
                    {addExpressionItems.map((item, index) => (
                      <MenuItem
                        key={index}
                        onClick={() => {
                          createExpression(item.sourceType);
                          handleAddExpressionClose();
                        }}>
                        <ListItemIcon>
                          <Icon iconName={item.iconName} style={{ fontSize: "15px" }} />
                        </ListItemIcon>
                        <Typography variant="body2">{item.label}</Typography>
                      </MenuItem>
                    ))}
                  </MenuList>
                </ClickAwayListener>
              </Box>
            </Menu>
          )}
          {/* CLEAR FILTER */}
          <Button
            variant="outlined"
            fullWidth
            size="small"
            color="error"
            disabled={!expressions?.length}
            onClick={clearFilter}>
            <Typography variant="body2" color="inherit">
              {t("common:clear_filter")}
            </Typography>
          </Button>
        </Stack>
      )}
    </Box>
  );
};

export default FilterPanel;
