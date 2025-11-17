"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import LoadingButton from "@mui/lab/LoadingButton";
import {
  Alert,
  Box,
  Button,
  Checkbox,
  FormControlLabel,
  Stack,
  Step,
  StepLabel,
  Stepper,
  TextField,
  Typography,
  useTheme,
} from "@mui/material";
import { useSession } from "next-auth/react";
import { useRouter } from "next/navigation";
import { useMemo, useRef, useState } from "react";
import { Controller, useForm } from "react-hook-form";
import type * as z from "zod";

import AuthContainer from "@p4b/ui/components/AuthContainer";
import AuthLayout from "@p4b/ui/components/AuthLayout";

import { createOrganization } from "@/lib/api/organizations";
import { ORG_DEFAULT_AVATAR } from "@/lib/constants";
import { postOrganizationSchema } from "@/lib/validations/organization";

import type { ResponseResult } from "@/types/common";

import { useOrganizationSetup } from "@/hooks/onboarding/OrganizationCreate";

import { RhfAutocompleteField } from "@/components/common/form-inputs/AutocompleteField";
import { RhfSelectField } from "@/components/common/form-inputs/SelectField";

type FormData = z.infer<typeof postOrganizationSchema>;

const STEPS = ["new_organization", "organization_profile", "organization_contact"];

export default function OrganizationOnBoarding() {
  const theme = useTheme();
  const { status, update } = useSession();
  const router = useRouter();
  const {
    t,
    countriesOptions,
    regionsOptions,
    orgTypesOptions,
    orgIndustryOptions,
    orgSizeOptions,
    orgUseCaseOptions,
  } = useOrganizationSetup();

  const [isBusy, setIsBusy] = useState<boolean>(false);
  const [responseResult, setResponseResult] = useState<ResponseResult>({
    message: "",
    status: undefined,
  });
  const [activeStep, setActiveStep] = useState<number>(0);
  const handleNext = () => {
    setActiveStep((prevActiveStep) => prevActiveStep + 1);
  };

  const handleBack = () => {
    setActiveStep((prevActiveStep) => prevActiveStep - 1);
  };

  const submitButtonRef = useRef<HTMLButtonElement>(null);

  const {
    handleSubmit,
    register,
    watch,
    formState: { errors },
    control,
  } = useForm<FormData>({
    mode: "onChange",
    resolver: zodResolver(postOrganizationSchema),
    defaultValues: {
      region: "EU",
      avatar: ORG_DEFAULT_AVATAR,
    },
  });

  const watchFormValues = watch();

  const allowNextFirstStep = useMemo(() => {
    return watchFormValues.name && watchFormValues.region && !errors.name;
  }, [errors.name, watchFormValues]);

  const allowNextSecondStep = useMemo(() => {
    return (
      watchFormValues.type &&
      watchFormValues.industry &&
      watchFormValues.department &&
      watchFormValues.use_case &&
      !errors.type &&
      !errors.industry &&
      !errors.department &&
      !errors.use_case
    );
  }, [watchFormValues, errors.type, errors.industry, errors.department, errors.use_case]);

  const allowSubmit = useMemo(() => {
    return (
      watchFormValues.name &&
      watchFormValues.region &&
      watchFormValues.type &&
      watchFormValues.industry &&
      watchFormValues.department &&
      watchFormValues.phone_number &&
      watchFormValues.location
    );
  }, [watchFormValues]);

  async function onSubmit(data: FormData) {
    setResponseResult({ message: "", status: undefined });
    setIsBusy(true);
    try {
      await createOrganization(data);
    } catch (_error) {
      setResponseResult({
        message: t("common:organization_creation_error"),
        status: "error",
      });
    } finally {
      setIsBusy(false);
    }
    update();
    router.push("/");
  }

  return (
    <AuthLayout>
      {status == "authenticated" && (
        <AuthContainer
          headerTitle={
            <>
              <Stack sx={{ mb: 8 }} spacing={2}>
                <Typography variant="h5">{t(`common:${STEPS[activeStep]}_title`)}</Typography>
                <Typography variant="body2">{t(`common:${STEPS[activeStep]}_subtitle`)}</Typography>
              </Stack>
              <Box sx={{ width: "100%" }}>
                <Stepper activeStep={activeStep}>
                  {STEPS.map((label) => (
                    <Step key={label}>
                      <StepLabel>{t(`common:${label}_stepper`)}</StepLabel>
                    </Step>
                  ))}
                </Stepper>
              </Box>
            </>
          }
          headerAlert={
            responseResult.status && <Alert severity={responseResult.status}>{responseResult.message}</Alert>
          }
          body={
            <>
              <Box component="form" onSubmit={handleSubmit(onSubmit)}>
                <Stack spacing={theme.spacing(4)}>
                  <>
                    {activeStep == 0 && (
                      <>
                        <TextField
                          fullWidth
                          required
                          helperText={errors.name ? errors.name?.message : t("common:organization_name_desc")}
                          label={t("common:organization_name_label")}
                          id="name"
                          {...register("name")}
                          error={errors.name ? true : false}
                        />

                        <RhfSelectField
                          options={regionsOptions}
                          control={control}
                          name="region"
                          label={t("common:organization_region_label")}
                        />
                      </>
                    )}
                    {activeStep == 1 && (
                      <>
                        <RhfSelectField
                          options={orgTypesOptions}
                          control={control}
                          name="type"
                          required
                          label={t("common:organization_type_label")}
                        />

                        <RhfSelectField
                          options={orgSizeOptions}
                          control={control}
                          name="size"
                          required
                          label={t("common:organization_size_label")}
                        />

                        <RhfSelectField
                          options={orgIndustryOptions}
                          control={control}
                          name="industry"
                          required
                          label={t("common:organization_industry_label")}
                        />

                        <TextField
                          fullWidth
                          required
                          helperText={errors.name ? errors.name?.message : null}
                          label={t("common:organization_department_label")}
                          {...register("department")}
                          error={errors.name ? true : false}
                        />

                        <RhfSelectField
                          options={orgUseCaseOptions}
                          control={control}
                          name="use_case"
                          required
                          label={t("common:organization_use_case_label")}
                        />
                      </>
                    )}
                    {activeStep == 2 && (
                      <>
                        <TextField
                          disabled={isBusy}
                          fullWidth
                          required
                          type="number"
                          helperText={errors.name ? errors.name?.message : null}
                          label={t("common:organization_contact_phone_label")}
                          {...register("phone_number")}
                          error={errors.name ? true : false}
                        />
                        <RhfAutocompleteField
                          disabled={isBusy}
                          options={countriesOptions}
                          control={control}
                          name="location"
                          label={t("common:organization_location_label")}
                        />
                        <Controller
                          name="newsletter_subscribe"
                          control={control}
                          defaultValue={false}
                          render={({ field: { onChange, value } }) => {
                            return (
                              <FormControlLabel
                                control={<Checkbox sx={{ ml: -3 }} onChange={onChange} checked={value} />}
                                label={t("common:organization_subscribe_to_newsletter")}
                              />
                            );
                          }}
                        />
                        <Stack spacing={3}>
                          <Typography variant="body1">
                            {t("common:organization_onboarding_trial_note")}
                          </Typography>
                          <Typography variant="body2">{t("common:organization_accept_terms")}</Typography>
                        </Stack>
                      </>
                    )}
                  </>
                </Stack>
                {activeStep == 2 && (
                  <LoadingButton
                    loading={isBusy}
                    variant="contained"
                    sx={{ mt: theme.spacing(4) }}
                    fullWidth
                    ref={submitButtonRef}
                    aria-label="finish-org-creation"
                    name="organization-submit"
                    type="submit"
                    disabled={!allowSubmit}>
                    {t("common:lets_get_started")}
                  </LoadingButton>
                )}

                <Stack>
                  {activeStep < 2 && (
                    <Button
                      fullWidth
                      sx={{
                        mt: theme.spacing(8),
                      }}
                      disabled={activeStep == 0 ? !allowNextFirstStep : !allowNextSecondStep}
                      onClick={handleNext}>
                      {t("common:next")}
                    </Button>
                  )}
                  {activeStep > 0 && (
                    <Button
                      sx={{
                        mt: theme.spacing(2),
                      }}
                      fullWidth
                      disabled={isBusy}
                      onClick={handleBack}
                      variant="text">
                      {t("common:back")}
                    </Button>
                  )}
                </Stack>
              </Box>
            </>
          }
        />
      )}
    </AuthLayout>
  );
}
