import { useMemo } from "react";

import type { Project, ProjectLayer } from "@/lib/validations/project";

import type { SearchSource } from "@/hooks/map/useUnifiedSearch";

import type { SearchLayersById } from "@/components/map/controls/search/SearchResultsList";
import { buildLayerIcon } from "@/components/map/panels/layer/legend/LayerIcon";

/**
 * Public-dashboard search scope. The client only reads `settings.search` to
 * decide whether places / layer search are offered — the searchable layers and
 * columns themselves are resolved server-side from the published snapshot.
 */
export function usePublicSearchSource(project: Project | undefined, projectLayers: ProjectLayer[]) {
  const searchSettings = project?.builder_config?.settings?.search;
  const configuredLayers = searchSettings?.layers;
  const placesEnabled = searchSettings?.places ?? true;
  const placeholder = searchSettings?.placeholder?.trim() || undefined;
  const projectId = project?.id;

  const source = useMemo<SearchSource | undefined>(() => {
    if (!projectId) return undefined;
    return {
      mode: "public",
      projectId,
      placesEnabled,
      hasLayers: (configuredLayers?.length ?? 0) > 0,
    };
  }, [projectId, placesEnabled, configuredLayers]);

  const layersById = useMemo<SearchLayersById>(() => {
    const map: SearchLayersById = new Map();
    const byProjectLayerId = new Map(projectLayers.map((layer) => [layer.id, layer]));
    const add = (layer: ProjectLayer | undefined) => {
      if (!layer || map.has(layer.layer_id)) return;
      map.set(layer.layer_id, {
        projectLayerId: layer.id,
        datasetId: layer.layer_id,
        name: layer.name ?? "",
        icon: buildLayerIcon(layer),
        layer,
      });
    };
    // Configured layers win the dataset key: the same dataset can back several
    // project layers, and the configured one owns the popup config to use.
    configuredLayers?.forEach((entry) => add(byProjectLayerId.get(entry.layer_project_id)));
    projectLayers.forEach(add);
    return map;
  }, [configuredLayers, projectLayers]);

  return { source, layersById, placeholder };
}
