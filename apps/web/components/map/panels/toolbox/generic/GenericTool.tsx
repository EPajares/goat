/**
 * Generic Tool Component
 *
 * Renders a tool form dynamically from OGC process description.
 * Handles input state, validation, and execution.
 */
import { Box, CircularProgress, Stack, Typography, useTheme } from "@mui/material";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { toast } from "react-toastify";

import { ICON_NAME } from "@p4b/ui/components/Icon";

import { useJobs } from "@/lib/api/jobs";
import { useUserProfile } from "@/lib/api/users";
import { setRunningJobIds } from "@/lib/store/jobs/slice";
import { getDefaultValues, processInputs, validateInputs } from "@/lib/utils/ogc-utils";

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
  const [showAdvanced, setShowAdvanced] = useState(false);

  // Process inputs into categorized groups
  const { mainInputs, advancedInputs } = useMemo(() => {
    if (!process) {
      return { mainInputs: [], advancedInputs: [], hiddenInputs: [] };
    }
    return processInputs(process);
  }, [process]);

  // Initialize default values when process loads
  useEffect(() => {
    if (process) {
      const defaults = getDefaultValues(process);
      setValues(defaults);
    }
  }, [process]);

  // Update a single input value
  const handleInputChange = useCallback((name: string, value: unknown) => {
    setValues((prev) => ({
      ...prev,
      [name]: value,
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

    // Check required fields
    for (const input of mainInputs) {
      if (input.required) {
        const value = values[input.name];
        if (value === undefined || value === null || value === "") {
          return false;
        }
      }
    }

    return true;
  }, [process, mainInputs, values]);

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

          {/* Main Inputs Section */}
          <SectionHeader
            active={true}
            alwaysActive={true}
            label={t("input_parameters")}
            icon={ICON_NAME.LAYERS}
            disableAdvanceOptions={true}
          />
          <SectionOptions
            active={true}
            baseOptions={
              <Stack spacing={2}>
                {mainInputs.map((input) => (
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

          {/* Advanced Settings (if any) */}
          {advancedInputs.length > 0 && (
            <>
              <SectionHeader
                active={showAdvanced}
                alwaysActive={false}
                label={t("advanced_settings")}
                icon={ICON_NAME.SETTINGS}
                disableAdvanceOptions={false}
                collapsed={!showAdvanced}
                setCollapsed={(collapsed) => setShowAdvanced(!collapsed)}
              />
              {showAdvanced && (
                <SectionOptions
                  active={true}
                  baseOptions={
                    <Stack spacing={2}>
                      {advancedInputs.map((input) => (
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
            </>
          )}
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
