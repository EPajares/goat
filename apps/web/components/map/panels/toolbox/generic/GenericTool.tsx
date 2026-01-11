/**
 * Generic Tool Component
 *
 * Renders a tool form dynamically from OGC process description.
 * Handles input state, validation, and execution.
 * Supports section-based layout from x-ui metadata.
 */
import { Box, CircularProgress, Stack, Typography, useTheme } from "@mui/material";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { toast } from "react-toastify";

import { ICON_NAME } from "@p4b/ui/components/Icon";

import { useJobs } from "@/lib/api/processes";
import { useProject } from "@/lib/api/projects";
import { useUserProfile } from "@/lib/api/users";
import { setRunningJobIds } from "@/lib/store/jobs/slice";
import { setToolboxStartingPoints } from "@/lib/store/map/slice";
import {
  getDefaultValues,
  getVisibleInputs,
  isSectionEnabled,
  processInputsWithSections,
  validateInputs,
} from "@/lib/utils/ogc-utils";

import type { ProcessedSection } from "@/types/map/ogc-processes";
import type { IndicatorBaseProps } from "@/types/map/toolbox";

import { useFilteredProjectLayers } from "@/hooks/map/LayerPanelHooks";
import { useProcessDescription, useProcessExecution } from "@/hooks/map/useOgcProcesses";
import { useAppDispatch, useAppSelector } from "@/hooks/store/ContextHooks";

import Container from "@/components/map/panels/Container";
import SectionHeader from "@/components/map/panels/common/SectionHeader";
import SectionOptions from "@/components/map/panels/common/SectionOptions";
import ToolboxActionButtons from "@/components/map/panels/common/ToolboxActionButtons";
import ToolsHeader from "@/components/map/panels/common/ToolsHeader";
import LearnMore from "@/components/map/panels/toolbox/common/LearnMore";
import { GenericInput } from "@/components/map/panels/toolbox/generic/inputs";

// Map section icons from backend to ICON_NAME
const SECTION_ICON_MAP: Record<string, ICON_NAME> = {
  layers: ICON_NAME.LAYERS,
  route: ICON_NAME.ROUTE,
  settings: ICON_NAME.SETTINGS,
  hexagon: ICON_NAME.HEXAGON,
  table: ICON_NAME.TABLE,
  tag: ICON_NAME.BOOKMARK,
  grid: ICON_NAME.TABLE,
  list: ICON_NAME.LIST,
  globe: ICON_NAME.GLOBE,
  upload: ICON_NAME.UPLOAD,
  download: ICON_NAME.DOWNLOAD,
  location: ICON_NAME.LOCATION,
  "location-marker": ICON_NAME.LOCATION_MARKER,
  aggregate: ICON_NAME.AGGREGATE,
  chart: ICON_NAME.CHART,
  scenario: ICON_NAME.SCENARIO,
  clock: ICON_NAME.CLOCK,
};

interface GenericToolProps extends IndicatorBaseProps {
  processId: string;
}

export default function GenericTool({ processId, onBack, onClose }: GenericToolProps) {
  const { t } = useTranslation("common");
  const theme = useTheme();
  const { projectId } = useParams();
  const dispatch = useAppDispatch();
  const runningJobIds = useAppSelector((state) => state.jobs.runningJobIds);

  // Fetch process description
  const { process, isLoading: isLoadingProcess, error: processError } = useProcessDescription(processId);

  // Process execution
  const { execute, isExecuting } = useProcessExecution();

  // Jobs mutation for refreshing job list
  const { mutate: mutateJobs } = useJobs({ read: false });

  // User profile for user_id
  const { userProfile } = useUserProfile();

  // Project for active scenario
  const { project } = useProject(projectId as string);

  // Project layers for geometry type detection
  const { layers: projectLayers } = useFilteredProjectLayers(projectId as string);

  // Compute default values synchronously when process changes
  // This ensures visibility conditions work correctly on the first render
  const defaultValues = useMemo(() => {
    if (!process) return {};
    return getDefaultValues(process);
  }, [process]);

  // Form state - initialize with defaults
  const [values, setValues] = useState<Record<string, unknown>>({});

  // Layer filters state - maps layer input names to their CQL filters
  // e.g., { "input_layer_id": { "op": "=", ... }, "overlay_layer_id": { ... } }
  const [layerFilters, setLayerFilters] = useState<Record<string, Record<string, unknown> | undefined>>({});

  // Section collapse state
  const [collapsedSections, setCollapsedSections] = useState<Record<string, boolean>>({});

  // Advanced options collapse state (for the settings icon)
  const [advancedCollapsed, setAdvancedCollapsed] = useState<Record<string, boolean>>({});

  // Process inputs into sections
  const sections = useMemo(() => {
    if (!process) {
      return [];
    }
    return processInputsWithSections(process);
  }, [process]);

  // Initialize default values and collapsed states when process loads
  useEffect(() => {
    if (process) {
      const defaults = getDefaultValues(process);
      setValues(defaults);

      // Initialize collapsed states from section definitions
      const collapsed: Record<string, boolean> = {};
      const advCollapsed: Record<string, boolean> = {};
      for (const section of sections) {
        collapsed[section.id] = section.collapsed;
        // Advanced options start collapsed by default
        advCollapsed[section.id] = true;
      }
      setCollapsedSections(collapsed);
      setAdvancedCollapsed(advCollapsed);
    }
  }, [process, sections]);

  // Get all inputs from all sections (flattened)
  const allInputs = useMemo(() => {
    return sections.flatMap((section) => section.inputs);
  }, [sections]);

  // Compute layer geometry types for visibility conditions
  // Creates computed values like _target_layer_id_has_geometry, _join_layer_id_has_geometry
  const layerGeometryValues = useMemo(() => {
    if (!projectLayers) return {};

    const computed: Record<string, boolean> = {};
    const effectiveValues = { ...defaultValues, ...values };

    // Find all layer inputs and compute their geometry status
    for (const input of allInputs) {
      if (input.inputType === "layer") {
        const projectLayerId = effectiveValues[input.name] as string | undefined;
        if (projectLayerId) {
          // LayerInput stores project layer ID (integer as string), so find by id
          const numericId = parseInt(projectLayerId, 10);
          const layer = projectLayers.find((l) => l.id === numericId);
          // A layer has geometry if it has a feature_layer_geometry_type
          computed[`_${input.name}_has_geometry`] = !!layer?.feature_layer_geometry_type;
        } else {
          computed[`_${input.name}_has_geometry`] = false;
        }
      }
    }

    // Compute combined values for common patterns
    // _any_layer_has_geometry: true if ANY selected layer has geometry
    // _all_layers_have_geometry: true if ALL selected layers have geometry (and at least one is selected)
    const geometryFlags = Object.values(computed);
    computed["_any_layer_has_geometry"] = geometryFlags.some((v) => v === true);
    computed["_all_layers_have_geometry"] =
      geometryFlags.length > 0 && geometryFlags.every((v) => v === true);

    return computed;
  }, [projectLayers, allInputs, values, defaultValues]);

  // Update a single input value, applying dynamic defaults to dependent fields
  const handleInputChange = useCallback(
    (name: string, value: unknown) => {
      setValues((prev) => {
        const newValues = { ...prev, [name]: value };

        // Check if any other input has default_by_field referencing this field
        for (const input of allInputs) {
          const defaultByField = input.uiMeta?.widget_options?.default_by_field as
            | { field: string; values: Record<string, unknown> }
            | undefined;

          if (defaultByField && defaultByField.field === name) {
            // Apply dynamic default if the value matches
            const dynamicDefault = defaultByField.values[String(value)];
            if (dynamicDefault !== undefined) {
              newValues[input.name] = dynamicDefault;
            }
          }
        }

        return newValues;
      });
    },
    [allInputs]
  );

  // Update filter for a layer input
  const handleFilterChange = useCallback((inputName: string, filter: Record<string, unknown> | undefined) => {
    setLayerFilters((prev) => ({
      ...prev,
      [inputName]: filter,
    }));
  }, []);

  // Toggle section collapse
  const toggleSection = useCallback((sectionId: string) => {
    setCollapsedSections((prev) => ({
      ...prev,
      [sectionId]: !prev[sectionId],
    }));
  }, []);

  // Toggle advanced options collapse
  const toggleAdvanced = useCallback((sectionId: string) => {
    setAdvancedCollapsed((prev) => ({
      ...prev,
      [sectionId]: !prev[sectionId],
    }));
  }, []);

  // Reset form to defaults
  const handleReset = useCallback(() => {
    if (process) {
      const defaults = getDefaultValues(process);
      setValues(defaults);
      setLayerFilters({});
      // Clear starting points from Redux
      dispatch(setToolboxStartingPoints(undefined));
    }
  }, [process, dispatch]);

  // Validate and check if form is ready
  const isValid = useMemo(() => {
    if (!process) return false;

    // Merge defaults with user values and computed layer geometry for validation checks
    const effectiveValues = { ...defaultValues, ...values, ...layerGeometryValues };

    // Check required fields across all sections
    for (const section of sections) {
      const visibleInputs = getVisibleInputs(section.inputs, effectiveValues);
      for (const input of visibleInputs) {
        if (input.required) {
          const value = effectiveValues[input.name];
          if (value === undefined || value === null || value === "") {
            return false;
          }
        }
      }
    }

    return true;
  }, [process, sections, values, defaultValues, layerGeometryValues]);

  // Execute the process
  const handleRun = async () => {
    if (!process || !userProfile) {
      toast.error(t("error_running_tool"));
      return;
    }

    // Merge defaults with user values and computed layer geometry
    const effectiveValues = { ...defaultValues, ...values, ...layerGeometryValues };

    // Build filter fields from layer filters
    // Convention: layer field "input_layer_id" -> filter field "input_layer_filter"
    const filterFields: Record<string, unknown> = {};
    for (const [layerFieldName, filter] of Object.entries(layerFilters)) {
      if (filter) {
        // Convert layer_id suffix to _filter suffix
        const filterFieldName = layerFieldName.replace(/_id$/, "_filter");
        filterFields[filterFieldName] = filter;
      }
    }

    // Get all visible input names to filter out invisible fields
    const visibleInputNames = new Set<string>();
    for (const section of sections) {
      const sectionEnabled = isSectionEnabled(section, effectiveValues);
      if (sectionEnabled) {
        const visibleInputs = getVisibleInputs(section.inputs, effectiveValues);
        for (const input of visibleInputs) {
          visibleInputNames.add(input.name);
        }
      }
    }

    // Build payload with only visible inputs (to avoid sending conditional fields that shouldn't be set)
    const visibleValues: Record<string, unknown> = {};
    for (const [key, value] of Object.entries(effectiveValues)) {
      if (visibleInputNames.has(key)) {
        visibleValues[key] = value;
      }
    }

    // Convert project layer IDs to layer_ids (UUIDs) for layer inputs
    // LayerInput stores project layer id (integer as string) but backend expects layer_id (UUID)
    // This handles both top-level layer inputs and layer inputs inside repeatable-object arrays
    if (projectLayers) {
      const convertProjectLayerIdToLayerId = (projectLayerId: string): string | undefined => {
        const numericId = parseInt(projectLayerId, 10);
        if (isNaN(numericId)) return undefined;
        const layer = projectLayers.find((l) => l.id === numericId);
        return layer?.layer_id;
      };

      for (const input of allInputs) {
        if (input.inputType === "layer" && visibleValues[input.name]) {
          // Top-level layer input
          const layerId = convertProjectLayerIdToLayerId(visibleValues[input.name] as string);
          if (layerId) {
            visibleValues[input.name] = layerId;
          }
        } else if (input.inputType === "repeatable-object" && Array.isArray(visibleValues[input.name])) {
          // Repeatable object array - check for layer inputs inside each item
          // Layer inputs inside repeatable objects use x-ui.widget = "layer-selector"
          const itemSchema = input.schema?.items;
          const itemsAnyOf = input.schema?.anyOf?.find(
            (v: { type?: string; items?: unknown }) => v.type === "array" && v.items
          );
          const resolvedItemSchema = itemSchema || itemsAnyOf?.items;

          if (resolvedItemSchema?.properties) {
            // Find layer field names in the item schema
            const layerFieldNames: string[] = [];
            for (const [fieldName, fieldSchema] of Object.entries(resolvedItemSchema.properties)) {
              const schema = fieldSchema as Record<string, unknown>;
              const uiMeta = schema["x-ui"] as { widget?: string } | undefined;
              if (uiMeta?.widget === "layer-selector") {
                layerFieldNames.push(fieldName);
              }
            }

            // Convert layer IDs in each array item
            if (layerFieldNames.length > 0) {
              const items = visibleValues[input.name] as Record<string, unknown>[];
              visibleValues[input.name] = items.map((item) => {
                const convertedItem = { ...item };
                for (const fieldName of layerFieldNames) {
                  if (convertedItem[fieldName]) {
                    const layerId = convertProjectLayerIdToLayerId(convertedItem[fieldName] as string);
                    if (layerId) {
                      convertedItem[fieldName] = layerId;
                    }
                  }
                }
                // Remove internal _id field used for React keys
                delete convertedItem._id;
                return convertedItem;
              });
            }
          }
        }
      }
    }

    // Determine scenario_id: use form value if present (from scenario selector widget),
    // otherwise fall back to active project scenario
    const scenarioId =
      visibleValues.scenario_id !== undefined
        ? visibleValues.scenario_id
        : project?.active_scenario_id || null;

    // Build full payload with hidden fields and filters
    const payload = {
      ...visibleValues,
      ...filterFields,
      user_id: userProfile.id,
      project_id: projectId,
      scenario_id: scenarioId,
      save_results: true,
    };

    // Validate
    const errors = validateInputs(process, payload);
    if (errors.length > 0) {
      errors.forEach((error) => toast.error(error));
      return;
    }

    try {
      const result = await execute(processId, payload);

      if (result?.jobID) {
        toast.info(`${process.title} - ${t("job_started")}`);
        mutateJobs();
        dispatch(setRunningJobIds([...runningJobIds, result.jobID]));
      }

      // Reset form after successful submission
      handleReset();
    } catch (error) {
      console.error("Process execution error:", error);
      toast.error(t("error_running_tool"));
    }
  };

  // Get icon for section
  const getSectionIcon = (section: ProcessedSection): ICON_NAME => {
    if (section.icon && SECTION_ICON_MAP[section.icon]) {
      return SECTION_ICON_MAP[section.icon];
    }
    return ICON_NAME.LAYERS;
  };

  // Loading state
  if (isLoadingProcess) {
    return (
      <Container
        disablePadding={false}
        header={<ToolsHeader onBack={onBack} title={t("loading")} />}
        close={onClose}
        body={
          <Box sx={{ display: "flex", justifyContent: "center", py: 4 }}>
            <CircularProgress />
          </Box>
        }
      />
    );
  }

  // Error state
  if (processError || !process) {
    return (
      <Container
        disablePadding={false}
        header={<ToolsHeader onBack={onBack} title={t("error")} />}
        close={onClose}
        body={
          <Typography color="error" variant="body2">
            {t("error_loading_tool")}
          </Typography>
        }
      />
    );
  }

  return (
    <Container
      disablePadding={false}
      header={<ToolsHeader onBack={onBack} title={process.title} />}
      close={onClose}
      body={
        <Box sx={{ display: "flex", flexDirection: "column" }}>
          {/* Description */}
          <Typography variant="body2" sx={{ fontStyle: "italic", mb: theme.spacing(4) }}>
            {process.description}
            <LearnMore docsPath={`/toolbox/geoprocessing/${processId}`} />
          </Typography>

          {/* Render sections dynamically */}
          {sections.map((section) => {
            // Merge defaults with user values and computed layer geometry for visibility checks
            const effectiveValues = { ...defaultValues, ...values, ...layerGeometryValues };
            const visibleInputs = getVisibleInputs(section.inputs, effectiveValues);
            const sectionEnabled = isSectionEnabled(section, effectiveValues);

            // Skip empty sections
            if (visibleInputs.length === 0) {
              return null;
            }

            // Split into base and advanced inputs
            const baseInputs = visibleInputs.filter((input) => !input.advanced);
            const advancedInputs = visibleInputs.filter((input) => input.advanced);
            const hasAdvancedOptions = advancedInputs.length > 0;

            const isCollapsed = collapsedSections[section.id] ?? section.collapsed;
            const isAdvancedCollapsed = advancedCollapsed[section.id] ?? true;
            const isFirstSection = sections.indexOf(section) === 0;
            const isDisabled = !sectionEnabled;

            return (
              <Box
                key={section.id}
                sx={{
                  opacity: isDisabled ? 0.5 : 1,
                  pointerEvents: isDisabled ? "none" : "auto",
                  transition: "opacity 0.2s ease",
                }}>
                <SectionHeader
                  active={!isCollapsed && !isDisabled}
                  alwaysActive={!section.collapsible || isFirstSection}
                  label={section.label}
                  icon={getSectionIcon(section)}
                  disableAdvanceOptions={!hasAdvancedOptions}
                  collapsed={hasAdvancedOptions ? isAdvancedCollapsed : isCollapsed || isDisabled}
                  setCollapsed={
                    hasAdvancedOptions
                      ? () => toggleAdvanced(section.id)
                      : section.collapsible
                        ? () => toggleSection(section.id)
                        : undefined
                  }
                  onToggleChange={
                    section.collapsible && !isFirstSection ? () => toggleSection(section.id) : undefined
                  }
                />
                {!isCollapsed && !isDisabled && (
                  <SectionOptions
                    active={true}
                    collapsed={isAdvancedCollapsed}
                    baseOptions={
                      <Stack spacing={2}>
                        {baseInputs.map((input) => (
                          <GenericInput
                            key={input.name}
                            input={input}
                            value={effectiveValues[input.name]}
                            onChange={(value) => handleInputChange(input.name, value)}
                            onFilterChange={
                              input.inputType === "layer"
                                ? (filter) => handleFilterChange(input.name, filter)
                                : undefined
                            }
                            disabled={isExecuting}
                            formValues={effectiveValues}
                            schemaDefs={process.$defs}
                          />
                        ))}
                      </Stack>
                    }
                    advancedOptions={
                      hasAdvancedOptions ? (
                        <Stack spacing={2}>
                          {advancedInputs.map((input) => (
                            <GenericInput
                              key={input.name}
                              input={input}
                              value={effectiveValues[input.name]}
                              onChange={(value) => handleInputChange(input.name, value)}
                              onFilterChange={
                                input.inputType === "layer"
                                  ? (filter) => handleFilterChange(input.name, filter)
                                  : undefined
                              }
                              disabled={isExecuting}
                              formValues={effectiveValues}
                              schemaDefs={process.$defs}
                            />
                          ))}
                        </Stack>
                      ) : undefined
                    }
                  />
                )}
              </Box>
            );
          })}
        </Box>
      }
      action={
        <ToolboxActionButtons
          runDisabled={!isValid || isExecuting}
          resetFunction={handleReset}
          runFunction={handleRun}
          isBusy={isExecuting}
        />
      }
    />
  );
}
