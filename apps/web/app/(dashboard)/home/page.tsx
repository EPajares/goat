"use client";

import { Box, Button, Container, Divider, Stack, Typography } from "@mui/material";
import React from "react";
import { useTranslation } from "react-i18next";

import { ICON_NAME, Icon } from "@p4b/ui/components/Icon";

import { useLayers } from "@/lib/api/layers";
import { useProjects } from "@/lib/api/projects";
import type { PaginatedQueryParams } from "@/lib/validations/common";
import type { Layer } from "@/lib/validations/layer";

import { useAuthZ } from "@/hooks/auth/AuthZ";
import { useJobStatus } from "@/hooks/jobs/JobStatus";

import BlogSection from "@/components/dashboard/home/BlogSection";
import DataSection from "@/components/dashboard/home/DataSection";
import ProjectSection from "@/components/dashboard/home/ProjectSection";

const Home = () => {
  const { t } = useTranslation("common");

  const queryParams: PaginatedQueryParams = {
    order: "descendent",
    order_by: "updated_at",
    size: 3,
  };
  const {
    projects,
    isLoading: isProjectLoading,
    isError: _isProjectError,
  } = useProjects({
    ...queryParams,
  });
  const {
    mutate,
    layers,
    isLoading: isLayerLoading,
    isError: _isLayerError,
  } = useLayers({
    ...queryParams,
  });

  useJobStatus(mutate, mutate);

  const { isOrgEditor } = useAuthZ();

  return (
    <Container sx={{ py: 10, px: 10 }} maxWidth="xl">
      <Stack direction="column" spacing={24}>
        <Stack>
          <Box
            sx={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
            }}>
            <Typography variant="h6">{t("recent_project")}</Typography>
            <Button
              variant="text"
              size="small"
              endIcon={<Icon iconName={ICON_NAME.CHEVRON_RIGHT} style={{ fontSize: 12 }} />}
              href="/projects"
              sx={{
                borderRadius: 0,
              }}>
              {t("see_all")}
            </Button>
          </Box>
          <Divider sx={{ mb: 4 }} />
          <ProjectSection
            projects={projects?.items ?? []}
            isLoading={isProjectLoading}
            hideCreate={!isOrgEditor}
          />
        </Stack>
        <DataSection
          layers={(layers?.items as Layer[]) ?? []}
          isLoading={isLayerLoading}
          hideCreate={!isOrgEditor}
        />
        <BlogSection />
      </Stack>
    </Container>
  );
};

export default Home;
