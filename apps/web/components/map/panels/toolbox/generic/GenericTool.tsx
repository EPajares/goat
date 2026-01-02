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
import { useUserProfile } from "@/lib/api/users";
import { setRunningJobIds } from "@/lib/store/jobs/slice";
import {
  getDefaultValues,
  getVisibleInputs,
  processInputsWithSections,
  validateInputs,
} from "@/lib/utils/ogc-utils";

import type { ProcessedSection } from "@/types/map/ogc-processes";
import type { IndicatorBaseProps } from "@/types/map/toolbox";

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

  // Form state
  const [values, setValues] = useState<Record<string, unknown>>({});

  // Section collapse state
  const [collapsedSections, setCollapsedSections] = useState<Record<string, boolean>>({});

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
      for (const section of sections) {
        collapsed[section.id] = section.collapsed;
      }
      setCollapsedSections(collapsed);
    }
  }, [process, sections]);

  // Update a single input value
  const handleInputChange = useCallback((name: string, value: unknown) => {
    setValues((prev) => ({
      ...prev,
      [name]: value,
    }));
  }, []);

  // Toggle section collapse
  const toggleSection = useCallback((sectionId: string) => {
    setCollapsedSections((prev) => ({
      ...prev,
      [sectionId]: !prev[sectionId],
    }));
  }, []);

  // Reset form to defaults
  const handleReset = useCallback(() => {
    if (process) {
      const defaults = getDefaultValues(process);
      setValues(defaults);
    }
  }, [process]);

  // Validate and check if form is ready
  const isValid = useMemo(() => {
    if (!process) return false;

    // Check required fields across all sections
    for (const section of sections) {
      const visibleInputs = getVisibleInputs(section.inputs, values);
      for (const input of visibleInputs) {
        if (input.required) {
          const value = values[input.name];
          if (value === undefined || value === null || value === "") {
            return false;
          }
        }
      }
    }

    return true;
  }, [process, sections, values]);

  // Execute the process
  const handleRun = async () => {
    if (!process || !userProfile) {
      toast.error(t("error_running_tool"));
      return;
    }

    // Build full payload with hidden fields
    const payload = {
      ...values,
      user_id: userProfile.id,
      project_id: projectId,
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
            const visibleInputs = getVisibleInputs(section.inputs, values);

            // Skip empty sections
            if (visibleInputs.length === 0) {
              return null;
            }

            const isCollapsed = collapsedSections[section.id] ?? section.collapsed;
            const isFirstSection = sections.indexOf(section) === 0;

            return (
              <Box key={section.id}>
                <SectionHeader
                  active={!isCollapsed}
                  alwaysActive={!section.collapsible || isFirstSection}
                  label={section.label}
                  icon={getSectionIcon(section)}
                  disableAdvanceOptions={!section.collapsible}
                  collapsed={isCollapsed}
                  setCollapsed={section.collapsible ? () => toggleSection(section.id) : undefined}
                />
                {!isCollapsed && (
                  <SectionOptions
                    active={true}
                    baseOptions={
                      <Stack spacing={2}>
                        {visibleInputs.map((input) => (
                          <GenericInput
                            key={input.name}
                            input={input}
                            value={values[input.name]}
                            onChange={(value) => handleInputChange(input.name, value)}
                            disabled={isExecuting}
                            formValues={values}
                          />
                        ))}
                      </Stack>
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
