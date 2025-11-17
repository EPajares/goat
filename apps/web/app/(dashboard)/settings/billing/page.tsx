"use client";

import "@mui/material";
import { Box, Divider, Grid, Stack, Typography, useTheme } from "@mui/material";
import { formatDistance } from "date-fns";
import React from "react";
import { Trans, useTranslation } from "react-i18next";

import { useDateFnsLocale } from "@/i18n/utils";

import { useAppPlans } from "@/lib/api/billing";
import { useOrganization } from "@/lib/api/users";
import { planNames } from "@/lib/validations/organization";

import PlanCard from "@/components/common/PlanCard";

export default function Billing() {
  const theme = useTheme();
  const { t } = useTranslation("common");
  const { organization } = useOrganization();
  const { plans } = useAppPlans();
  const dateLocale = useDateFnsLocale();

  return (
    <>
      <Box sx={{ p: 4 }}>
        <Stack spacing={theme.spacing(6)}>
          <Divider />
          <Box>
            <Typography variant="body1" fontWeight="bold">
              {t("your_current_plan")}
            </Typography>
            <Typography variant="caption">{t("app_plan_description")}</Typography>
          </Box>
          <Divider />
          <Grid container style={{ display: "flex", alignItems: "stretch" }}>
            {plans?.plans.map((plan) => (
              <Grid
                item
                xs={12}
                sm={6}
                md={4}
                key={plan.title}
                sx={{ px: 3, pb: 3 }}
                style={{ display: "flex" }}>
                <PlanCard
                  plan={{
                    ...plan,
                    featuresHeader: t("whats_included"),
                    featuresSubHeader:
                      plan.plan_name === planNames.ENTERPRISE
                        ? t("everything_in_professional_plus")
                        : plan.plan_name === planNames.PRO
                          ? t("everything_in_starter_plus")
                          : undefined,
                    buttonText:
                      organization?.plan_name === plan.plan_name ? t("current_plan") : t("get_a_quote"),
                    active: organization?.plan_name === plan.plan_name,
                    trialDaysLabel:
                      organization?.plan_name === plan.plan_name && organization?.on_trial ? (
                        <Trans
                          i18nKey="common:days_left_trial"
                          values={{
                            days_left: formatDistance(new Date(organization.plan_renewal_date), new Date(), {
                              locale: dateLocale,
                            }),
                          }}
                        />
                      ) : undefined,
                  }}
                />
              </Grid>
            ))}
          </Grid>
        </Stack>
      </Box>
    </>
  );
}
