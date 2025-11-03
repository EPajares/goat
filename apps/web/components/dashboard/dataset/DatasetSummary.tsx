import { Divider, Link, Stack, Typography, styled, useTheme } from "@mui/material";
import React from "react";
import ReactMarkdown from "react-markdown";

import { Icon } from "@p4b/ui/components/Icon";

import { useTranslation } from "@/i18n/client";

import { type Layer, datasetMetadataAggregated } from "@/lib/validations/layer";
import type { ProjectLayer } from "@/lib/validations/project";

import { useGetMetadataValueTranslation } from "@/hooks/map/DatasetHooks";

import { METADATA_HEADER_ICONS } from "@/components/dashboard/catalog/CatalogDatasetCard";

interface DatasetSummaryProps {
  dataset: Layer | ProjectLayer;
  hideEmpty?: boolean; // Prop to control empty field display
  hideMainSection?: boolean; // Prop to control main section display
}

const ContainerWrapper = styled("div")({
  containerType: "inline-size",
  width: "100%",
});

const LayoutContainer = styled("div")({
  display: "flex",
  flexDirection: "row",
  gap: "16px",
  width: "100%",
  "@container (max-width: 600px)": {
    flexDirection: "column",
  },
});

const MetadataSection = styled("div")({
  flex: 4,
  order: 1,

  "@container (max-width: 600px)": {
    order: 2,
    flex: "1 1 100%",
  },
});

const MainContentSection = styled("div")({
  flex: 1,
  order: 2,

  "@container (max-width: 600px)": {
    order: 1,
    flex: "1 1 100%",
  },
});

const DatasetSummary: React.FC<DatasetSummaryProps> = ({
  dataset,
  hideEmpty = false,
  hideMainSection = false,
}) => {
  const theme = useTheme();
  const { t, i18n } = useTranslation(["common", "countries"]);
  const getMetadataValueTranslation = useGetMetadataValueTranslation();
  const metadataSummaryFields = [
    {
      field: "description",
      heading: t("metadata.headings.description"),
      noMetadataAvailable: t("metadata.no_metadata_available.description"),
      type: "markdown",
    },
    {
      field: "data_reference_year",
      heading: t("metadata.headings.data_reference_year"),
      noMetadataAvailable: t("metadata.no_metadata_available.data_reference_year"),
      type: "text",
    },
    {
      field: "lineage",
      heading: t("metadata.headings.lineage"),
      noMetadataAvailable: t("metadata.no_metadata_available.lineage"),
      type: "markdown",
    },
    {
      field: "positional_accuracy",
      heading: t("metadata.headings.positional_accuracy"),
      noMetadataAvailable: t("metadata.no_metadata_available.positional_accuracy"),
      type: "text",
    },
    {
      field: "attribute_accuracy",
      heading: t("metadata.headings.attribute_accuracy"),
      noMetadataAvailable: t("metadata.no_metadata_available.attribute_accuracy"),
      type: "text",
    },
    {
      field: "completeness",
      heading: t("metadata.headings.completeness"),
      noMetadataAvailable: t("metadata.no_metadata_available.completeness"),
      type: "text",
    },
    {
      field: "distributor_name",
      heading: t("metadata.headings.distributor_name"),
      noMetadataAvailable: t("metadata.no_metadata_available.distributor_name"),
      type: "text",
    },
    {
      field: "distributor_email",
      heading: t("metadata.headings.distributor_email"),
      noMetadataAvailable: t("metadata.no_metadata_available.distributor_email"),
      type: "email",
    },
    {
      field: "distribution_url",
      heading: t("metadata.headings.distribution_url"),
      noMetadataAvailable: t("metadata.no_metadata_available.distribution_url"),
      type: "url",
    },
    {
      field: "attribution",
      heading: t("metadata.headings.attribution"),
      noMetadataAvailable: t("metadata.no_metadata_available.attribution"),
      type: "text",
    },
  ];

  const hasAnyMetadata = metadataSummaryFields.some(({ field }) => !!dataset[field]);
  const shouldRenderMetadataSection = !hideEmpty || hasAnyMetadata;

  return (
    <ContainerWrapper>
      <LayoutContainer>
        {shouldRenderMetadataSection && (
          <MetadataSection>
            <Stack spacing={4} sx={{ width: "100%" }}>
              {metadataSummaryFields.map(({ field, heading, noMetadataAvailable, type }) => {
                if (hideEmpty && !dataset[field]) return null;
                return (
                  <Stack key={field} spacing={1}>
                    <Typography variant="caption">{heading}</Typography>
                    <Divider />
                    {!dataset[field] && (
                      <Typography variant="body2" sx={{ fontStyle: "italic" }}>
                        {noMetadataAvailable}
                      </Typography>
                    )}
                    {type === "markdown" && dataset[field] && (
                      <ReactMarkdown
                        components={{
                          img: ({ node: _, ...props }) => {
                            const hasSize =
                              props.width !== undefined ||
                              props.height !== undefined ||
                              (props.style && (props.style.width || props.style.height));

                            const style = hasSize ? props.style : { width: "100%" };

                            // eslint-disable-next-line jsx-a11y/alt-text
                            return <img {...props} style={style} />;
                          },
                          a: ({ node: _, href, children, ...props }) => (
                            <a href={href} target="_blank" rel="noopener noreferrer" {...props}>
                              {children}
                            </a>
                          ),
                        }}>
                        {dataset[field]}
                      </ReactMarkdown>
                    )}
                    {type === "email" && dataset[field] && (
                      <Link href={`mailto:${dataset[field]}`} target="_blank" rel="noopener noreferrer">
                        {dataset[field]}
                      </Link>
                    )}
                    {type === "url" && dataset[field] && (
                      <Link href={dataset[field]} target="_blank" rel="noopener noreferrer">
                        {dataset[field]}
                      </Link>
                    )}
                    {type === "text" && dataset[field] && <Typography>{dataset[field]}</Typography>}
                  </Stack>
                );
              })}
            </Stack>
          </MetadataSection>
        )}

        {!hideMainSection && (
          <MainContentSection>
            <Stack spacing={2}>
              {Object.keys(datasetMetadataAggregated.shape).map((key) => (
                <div key={key} style={{ display: "flex", gap: "8px", alignItems: "center" }}>
                  <Icon
                    iconName={METADATA_HEADER_ICONS[key]}
                    style={{ fontSize: 14, flexShrink: 0 }}
                    htmlColor={theme.palette.text.secondary}
                  />
                  <div style={{ minWidth: 0 }}>
                    <Typography variant="caption" noWrap>
                      {i18n.exists(`common:metadata.headings.${key}`)
                        ? t(`common:metadata.headings.${key}`)
                        : key}
                    </Typography>
                    <Typography variant="body2" fontWeight="bold" noWrap>
                      {getMetadataValueTranslation(key, dataset[key])}
                    </Typography>
                  </div>
                </div>
              ))}
            </Stack>
          </MainContentSection>
        )}
      </LayoutContainer>
    </ContainerWrapper>
  );
};

export default DatasetSummary;
