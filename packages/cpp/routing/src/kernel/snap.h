#pragma once

#include "../types.h"

#include <vector>

namespace routing::kernel
{

    // Snap origin points onto the nearest edge of the SubNetwork.
    // For each origin:
    //   1. KD-tree finds the k nearest nodes
    //   2. For each connected edge, project the origin onto the segment
    //   3. Pick the single closest projection, create a connector node + split edges
    // Returns node IDs for Dijkstra starts (-1 if unsnappable).
    // max_snap_distance is in GROUND metres (converted to EPSG:3857 per-origin).
    std::vector<int32_t> snap_origins(SubNetwork &net,
                                      std::vector<Point3857> const &origins,
                                      RequestConfig const &cfg,
                                      double max_snap_distance = 500.0,
                                      int k_nearest_nodes = 5);

} // namespace routing::kernel
