#pragma once

#include "../types.h"

#include <functional>

namespace duckdb
{
    class Connection;
}

namespace routing::heatmap
{

    // Compute per-cell accessibility scores against a fixed opportunity layer
    // and write a parquet of (h3_index BIGINT, score DOUBLE) to
    // cfg.output_path. The reverse pipeline routes outward *from* the
    // opportunities and reduces per origin cell via cfg.heatmap_type
    // (Gravity / ClosestAverage / Connectivity).
    //
    // Street modes (run_street): per-opportunity bounded reverse Dijkstra over
    // a radially-loaded network, sampled into H3 cells.
    //
    // Public transport (run_pt): arrive-by. Opportunities are grouped by their
    // H3 cell; per group a reverse RAPTOR (seeded from the egress stops) finds
    // boarding stops, which an access lookup table maps to origin cells; this
    // is MIN'd with a direct same-mode walk leg. Access/egress legs come from
    // precomputed per-mode lookup tables; transit from nigiri.
    void compute_heatmap(HeatmapConfig const &cfg);

    // Run the reachability pipeline (street reverse-Dijkstra or PT arrive-by
    // reverse-RAPTOR + access/egress lookups) for `cfg`, then invoke `emit`
    // with a DuckDB connection holding the per-(cell, opportunity) cost
    // relation as two temp tables:
    //   _hm_per_opp (cell BIGINT, opp_idx INTEGER, min_cost DOUBLE)
    //   _hm_opp_meta(opp_idx INTEGER, opp_cell BIGINT, weight DOUBLE, ...)
    // compute_heatmap reduces this relation to scores; the travel-cost-matrix
    // OD emitter exports it raw. This is the shared engine both entry points
    // build on, so neither reimplements the routing machinery.
    void build_reachability_relation(
        HeatmapConfig const &cfg,
        std::function<void(duckdb::Connection &)> const &emit);

} // namespace routing::heatmap
