"use client";

import {
  Box,
  Button,
  Container,
  Divider,
  Grid,
  Pagination,
  Paper,
  Skeleton,
  Stack,
  Typography,
  debounce,
} from "@mui/material";
import { useRouter } from "next/navigation";
import { parseAsArrayOf, parseAsInteger, parseAsString, useQueryState } from "nuqs";
import { useCallback, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";

import { ICON_NAME } from "@p4b/ui/components/Icon";

import { useCatalogLayers, useMetadataAggregated } from "@/lib/api/layers";
import type { PaginatedQueryParams } from "@/lib/validations/common";
import type { GetDatasetSchema } from "@/lib/validations/layer";
import { datasetMetadataAggregated } from "@/lib/validations/layer";

import EmptySection from "@/components/common/EmptySection";
import CatalogDatasetCard, { METADATA_HEADER_ICONS } from "@/components/dashboard/catalog/CatalogDatasetCard";
import FilterPanel from "@/components/dashboard/catalog/FilterPanel";
import ContentSearchBar from "@/components/dashboard/common/ContentSearchbar";

const Catalog = () => {
  const { t } = useTranslation("common");
  const router = useRouter();
  const useQueryStateArray = (key: string) => useQueryState(key, parseAsArrayOf(parseAsString));
  const [typeValue, setTypeValue] = useQueryStateArray("type");
  const [dataCategoryValue, setDataCategoryValue] = useQueryStateArray("data_category");
  const [distributorNameValue, setDistributorNameValue] = useQueryStateArray("distributor_name");
  const [geographicalCodeValue, setGeographicalCodeValue] = useQueryStateArray("geographical_code");
  const [languageCodeValue, setLanguageCodeValue] = useQueryStateArray("language_code");
  const [licenseValue, setLicenseValue] = useQueryStateArray("license");
  const [searchText, setSearchText] = useQueryState("search", parseAsString);

  const filterOptions = useMemo(
    () => ({
      type: {
        value: typeValue,
        setValue: setTypeValue,
      },
      data_category: {
        value: dataCategoryValue,
        setValue: setDataCategoryValue,
      },
      distributor_name: {
        value: distributorNameValue,
        setValue: setDistributorNameValue,
      },
      geographical_code: {
        value: geographicalCodeValue,
        setValue: setGeographicalCodeValue,
      },
      language_code: {
        value: languageCodeValue,
        setValue: setLanguageCodeValue,
      },
      license: {
        value: licenseValue,
        setValue: setLicenseValue,
      },
    }),
    [
      typeValue,
      setTypeValue,
      dataCategoryValue,
      setDataCategoryValue,
      distributorNameValue,
      setDistributorNameValue,
      geographicalCodeValue,
      setGeographicalCodeValue,
      languageCodeValue,
      setLanguageCodeValue,
      licenseValue,
      setLicenseValue,
    ]
  );
  const datasetSchemaValues = useMemo(() => {
    const keys = Object.keys(filterOptions);
    return keys.reduce(
      (acc, key) => {
        if (filterOptions[key].value && filterOptions[key].value.length > 0) {
          acc[key] = filterOptions[key].value;
        }
        return acc;
      },
      {
        in_catalog: true,
      }
    );
  }, [filterOptions]);

  const [queryParamPage, setQueryParamPage] = useQueryState("page", parseAsInteger.withDefault(1));

  const [datasetSchema, setDatasetSchema] = useState<GetDatasetSchema>(datasetSchemaValues);
  const [queryParams, setQueryParams] = useState<PaginatedQueryParams>({
    order: "descendent",
    order_by: "updated_at",
    size: 10,
    page: queryParamPage || 1,
  });
  const { metadata, isLoading: filtersLoading } = useMetadataAggregated(datasetSchema);
  const { layers: datasets, isLoading: datasetsLoading } = useCatalogLayers(queryParams, datasetSchema);

  const resetPage = useCallback(() => {
    setQueryParamPage(1);
    setQueryParams({
      ...queryParams,
      page: 1,
    });
  }, [queryParams, setQueryParamPage]);

  const handleToggle = useCallback(
    (filterType: string, value: string) => {
      resetPage();
      const setFilterValues = filterOptions[filterType].setValue;
      const filterValues = filterOptions[filterType].value || [];
      const currentIndex = filterValues.indexOf(value);
      const newChecked = [...filterValues];
      if (currentIndex === -1) {
        newChecked.push(value);
      } else {
        newChecked.splice(currentIndex, 1);
      }
      setFilterValues(newChecked?.length ? newChecked : null);
      const newDatasetSchema = { ...datasetSchema };
      if (newChecked?.length > 0) {
        newDatasetSchema[filterType] = newChecked;
      } else {
        delete newDatasetSchema[filterType];
      }
      setDatasetSchema(newDatasetSchema);
    },
    [datasetSchema, filterOptions, resetPage]
  );

  const debouncedSetSearchText = debounce((value) => {
    resetPage();
    setSearchText(value || null);
    const newDatasetSchema = { ...datasetSchema };
    if (value) {
      newDatasetSchema.search = value;
    } else {
      delete newDatasetSchema.search;
    }
    setDatasetSchema(newDatasetSchema);
  }, 500);

  return (
    <Container sx={{ py: 10, px: 10 }} maxWidth="xl">
      <Box
        sx={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          mb: 8,
        }}>
        <Typography variant="h6">{t("catalog")}</Typography>
      </Box>
      <Grid container justifyContent="space-between" spacing={4}>
        <Grid item xs={3}>
          <Paper elevation={3}>
            <Stack sx={{ mt: 0 }}>
              {Object.keys(datasetMetadataAggregated.shape).map((key, index) => {
                return (
                  <Stack key={key}>
                    {index !== 0 && <Divider sx={{ py: 0, my: 0 }} />}
                    <FilterPanel
                      filterValues={filterOptions[key].value}
                      onToggle={(value) => handleToggle(key, value)}
                      filterType={key}
                      values={metadata ? metadata[key] : []}
                      isLoading={filtersLoading}
                      icon={METADATA_HEADER_ICONS[key]}
                    />
                  </Stack>
                );
              })}
            </Stack>
          </Paper>
        </Grid>
        <Grid item xs={9}>
          <Stack spacing={2}>
            <ContentSearchBar
              contentType="layer"
              searchText={searchText || ""}
              onSearchTextChange={(text) => {
                debouncedSetSearchText(text);
              }}
            />
            <Stack direction="row">
              {datasets && (
                <>
                  <Typography variant="body1" fontWeight="bold">
                    {`${datasets?.total} ${t("datasets")}`}
                  </Typography>
                </>
              )}
            </Stack>

            {datasets && datasets?.total > 0 && <Divider />}

            {datasets && datasets?.total === 0 && (
              <Stack sx={{ mt: 10 }} alignItems="center" spacing={4}>
                <EmptySection label={t("no_catalog_dataset_found")} icon={ICON_NAME.DATABASE} />
                <Typography variant="body1">{t("try_different_filters")}</Typography>
                <Stack spacing={2} direction="column">
                  <Divider />
                  <Typography variant="body1">{t("common:no_catalog_dataset_found_description")}</Typography>
                </Stack>
                <Button
                  variant="outlined"
                  color="primary"
                  sx={{ mt: 2 }}
                  onClick={() => {
                    window.open("https://plan4better.de/en/contact/", "_blank");
                  }}>
                  <Typography variant="body1" fontWeight="bold" color="inherit">
                    {t("contact_us")}
                  </Typography>
                </Button>
              </Stack>
            )}

            {datasetsLoading && !datasets && (
              <Stack spacing={4} direction="column" width="100%">
                {Array(queryParams.size)
                  .fill(0)
                  .map((_, index) => (
                    <Skeleton key={index} variant="rectangular" height={200} />
                  ))}
              </Stack>
            )}
            <Stack direction="column" spacing={4}>
              {!datasetsLoading &&
                datasets &&
                datasets?.items.length > 0 &&
                datasets.items.map((dataset) => (
                  <CatalogDatasetCard
                    key={dataset.id}
                    dataset={dataset}
                    onClick={(dataset) => {
                      router.push(`/datasets/${dataset.id}`);
                    }}
                  />
                ))}

              {!datasetsLoading && datasets && datasets?.items.length > 0 && (
                <Stack direction="row" justifyContent="center" alignItems="center" sx={{ p: 4 }}>
                  <Pagination
                    count={datasets.pages || 1}
                    size="large"
                    page={queryParams.page || 1}
                    onChange={(_e, page) => {
                      setQueryParamPage(page);
                      setQueryParams({
                        ...queryParams,
                        page,
                      });
                    }}
                  />
                </Stack>
              )}
            </Stack>
          </Stack>
        </Grid>
      </Grid>
    </Container>
  );
};

export default Catalog;
