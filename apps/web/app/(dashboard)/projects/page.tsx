"use client";

import { Box, Button, Container, Grid, Pagination, Paper, Stack, Typography } from "@mui/material";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

import { ICON_NAME, Icon } from "@p4b/ui/components/Icon";

import { useProjects } from "@/lib/api/projects";
import type { GetProjectsQueryParams } from "@/lib/validations/project";

import { useAuthZ } from "@/hooks/auth/AuthZ";

import ContentSearchBar from "@/components/dashboard/common/ContentSearchbar";
import FoldersTreeView from "@/components/dashboard/common/FoldersTreeView";
import TileGrid from "@/components/dashboard/common/TileGrid";
import ProjectModal from "@/components/modals/Project";

const Projects = () => {
  const router = useRouter();
  const [queryParams, setQueryParams] = useState<GetProjectsQueryParams>({
    order: "descendent",
    order_by: "updated_at",
    size: 10,
    page: 1,
  });
  const [view, setView] = useState<"list" | "grid">("grid");
  const { t } = useTranslation("common");

  const { projects, isLoading: isProjectLoading, isError: _isProjectError } = useProjects(queryParams);

  const [openProjectModal, setOpenProjectModal] = useState(false);
  const { isOrgEditor } = useAuthZ();

  useEffect(() => {
    if (projects?.pages && queryParams?.page && projects?.pages < queryParams?.page) {
      setQueryParams({
        ...queryParams,
        page: projects.pages,
      });
    }
  }, [projects, queryParams]);

  return (
    <Container sx={{ py: 10, px: 10 }} maxWidth="xl">
      <ProjectModal type="create" open={openProjectModal} onClose={() => setOpenProjectModal(false)} />
      <Box
        sx={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          mb: 8,
        }}>
        <Typography variant="h6">{t("projects")}</Typography>
        {isOrgEditor && (
          <Button
            disableElevation={true}
            startIcon={<Icon iconName={ICON_NAME.PLUS} style={{ fontSize: 12 }} />}
            onClick={() => {
              setOpenProjectModal(true);
            }}>
            {t("new_project")}
          </Button>
        )}
      </Box>
      <Grid container justifyContent="space-between" spacing={4}>
        <Grid item xs={12}>
          <ContentSearchBar
            contentType="project"
            view={view}
            setView={setView}
            queryParams={queryParams}
            setQueryParams={(queryParams) => {
              setQueryParams({
                ...queryParams,
                page: 1,
              });
            }}
          />
        </Grid>
        <Grid item xs={3}>
          <Paper elevation={3}>
            <FoldersTreeView
              queryParams={queryParams}
              enableActions={isOrgEditor}
              hideMyContent={!isOrgEditor}
              setQueryParams={(params, teamId, organizationId) => {
                const newQueryParams = { ...params, page: 1 };
                delete newQueryParams?.["team_id"];
                delete newQueryParams?.["organization_id"];
                if (teamId) {
                  newQueryParams["team_id"] = teamId;
                } else if (organizationId) {
                  newQueryParams["organization_id"] = organizationId;
                }
                setQueryParams(newQueryParams);
              }}
            />
          </Paper>
        </Grid>
        <Grid item xs={9}>
          <TileGrid
            view={view}
            items={projects?.items ?? []}
            enableActions={isOrgEditor}
            isLoading={isProjectLoading}
            type="project"
            onClick={(item) => {
              if (item && item.id) {
                router.push(`/map/${item.id}`);
              }
            }}
          />
          {!isProjectLoading && projects && projects?.items.length > 0 && (
            <Stack direction="row" justifyContent="center" alignItems="center" sx={{ p: 4 }}>
              <Pagination
                count={projects.pages || 1}
                size="large"
                page={queryParams.page || 1}
                onChange={(_e, page) => {
                  setQueryParams({
                    ...queryParams,
                    page,
                  });
                }}
              />
            </Stack>
          )}
        </Grid>
      </Grid>
    </Container>
  );
};

export default Projects;
