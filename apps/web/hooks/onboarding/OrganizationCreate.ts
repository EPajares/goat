import { countries } from "country-flag-icons";
import getUnicodeFlagIcon from "country-flag-icons/unicode";
import { useMemo } from "react";

import { useTranslation } from 'react-i18next'

const regions = ["EU"];

const orgTypes = ["", "government", "private", "non_profit", "education", "other"];

const orgIndustry = [
  "",
  "archaeology",
  "architecture",
  "banking_and_finance",
  "civil_engineering",
  "consulting",
  "education_research",
  "emergency_management",
  "forestry",
  "gis_it",
  "government_and_public_services",
  "healthcare",
  "insurance",
  "location_planning",
  "marketing_and_advertising",
  "real_estate",
  "sports_and_entertainment",
  "surveying_and_geodesy",
  "telecommunication",
  "transportation_planning",
  "urban_planning",
  "other",
];

const orgSize = [
  "",
  "5-25",
  "25-50",
  "50-100",
  "100-500",
  "500-1.000",
  "1.000-10.000",
  "10.000-100.000",
  "100.000+",
];

const orgUseCase = [
  "",
  "site_analysis_and_design_decision_support",
  "market_analysis_and_location_optimization",
  "infrastructure_planning_and_design",
  "location_based_insights_for_clients",
  "geographic_studies_and_data_visualization",
  "geospatial_data_management_and_analysis",
  "site_selection_and_market_analysis",
  "network_planning_and_coverage_optimization",
  "route_optimization_and_traffic_management",
  "geo_marketing_and_customer_targeting",
  "property_valuation_and_market_analysis",
  "other",
];

export const useOrganizationSetup = () => {
  const { t } = useTranslation(["common", "countries"]);

  const countriesOptions = useMemo(() => {
    const filtered = ["EU"];
    const filteredCountries = countries.filter((code) => !filtered.includes(code));
    return filteredCountries.map((countryCode) => {
      return {
        value: countryCode,
        label: `${t(`countries:${countryCode}`)}`,
        icon: getUnicodeFlagIcon(countryCode),
      };
    });
  }, [t]);

  const regionsOptions = useMemo(() => {
    return regions.map((regionCode) => {
      return {
        value: regionCode,
        label: `${getUnicodeFlagIcon(regionCode)} ${t(`countries:${regionCode}`)}`,
      };
    });
  }, [t]);

  const orgTypesOptions = useMemo(() => {
    return orgTypes.map((type) => {
      return {
        value: type,
        label: type ? t(`common:organization_type_options.${type}`) : "",
      };
    });
  }, [t]);

  const orgIndustryOptions = useMemo(() => {
    return orgIndustry.map((industry) => {
      return {
        value: industry,
        label: industry ? t(`common:organization_industry_options.${industry}`) : "",
      };
    });
  }, [t]);

  const orgSizeOptions = useMemo(() => {
    return orgSize.map((code) => {
      return {
        value: code,
        label: code,
      };
    });
  }, []);

  const orgUseCaseOptions = useMemo(() => {
    return orgUseCase.map((useCase) => {
      return {
        value: useCase,
        label: useCase ? t(`common:organization_use_case_options.${useCase}`) : "",
      };
    });
  }, [t]);

  return {
    t,
    countriesOptions,
    regionsOptions,
    orgTypesOptions,
    orgIndustryOptions,
    orgSizeOptions,
    orgUseCaseOptions,
  };
};
