#pragma once

#include "types.h"

#include <cstddef>
#include <string>

namespace routing
{

    /*
        Combined entrypoint for catchment area computation.
        The supplied RequestConfig allows specifying routing config options, 
        output formats and providing starting points.
    */
    std::string compute_catchment(RequestConfig const &cfg);

    /*
        Entrypoint for travel cost matrix computation.
        The supplied MatrixConfig allows specifying routing config options.
    */
    void compute_travel_cost_matrix(MatrixConfig const &cfg);

    /*
        Combined entrypoint for heatmap computation.
        The supplied HeatmapConfig allows selecting a heatmap type, 
        specifying routing config options and providing opportunities.
    */
    void compute_heatmap(HeatmapConfig const &cfg);

    /*
        OD cost matrix: an extension of the travel cost matrix that routes from
        an opportunity layer (supporting reverse PT via the arrive-by
        pipeline) and emits every reachable (orig_cell, dest_cell, cost) pair
        to cfg.output_path. Used by Huff v2 for its OD matrix.
    */
    void compute_od_costs(HeatmapConfig const &cfg);

} // namespace routing
