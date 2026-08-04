#include "pipeline.h"

#include "input/request_config.h"
#include "input/validation.h"
#include "kernel/dijkstra.h"
#include "kernel/reachability_field.h"
#include "output/geojson.h"
#include "output/grid_contour_common.h"
#include "output/parquet.h"
#include "output/sql_export.h"
#include "geometry/grid_surface_builder.h"
#include "heatmap/heatmap.h"
#include "network/network_prep.h"
#include "pt/pt_pipeline.h"

#include <chrono>
#include <cmath>
#include <cstdio>
#include <duckdb.hpp>
#include <filesystem>
#include <functional>
#include <limits>
#include <sstream>
#include <stdexcept>

namespace routing
{

    namespace
    {
        // Build a RequestConfig from a MatrixConfig for reusing
        // edge loading, cost computation, and snapping infrastructure.
        RequestConfig matrix_to_request_config(
            MatrixConfig const &cfg,
            std::vector<Point3857> const &starting_points)
        {
            RequestConfig rcfg;
            rcfg.mode = cfg.mode;
            rcfg.cost_type = cfg.cost_type;
            rcfg.max_cost = cfg.max_cost;
            rcfg.speed_km_h = cfg.speed_km_h;
            rcfg.edge_dir = cfg.edge_dir;
            rcfg.node_dir = cfg.node_dir;
            rcfg.starting_points = starting_points;
            rcfg.steps = 1; // unused by matrix, but required by validation
            // PT fields
            rcfg.timetable_path = cfg.timetable_path;
            rcfg.departure_time = cfg.departure_time;
            rcfg.max_transfers = cfg.max_transfers;
            rcfg.departure_window = cfg.departure_window;
            rcfg.transit_modes = cfg.transit_modes;
            rcfg.access_mode = cfg.access_mode;
            rcfg.egress_mode = cfg.egress_mode;
            rcfg.access_cost_type = cfg.access_cost_type;
            rcfg.egress_cost_type = cfg.egress_cost_type;
            rcfg.access_max_cost = cfg.access_max_cost;
            rcfg.egress_max_cost = cfg.egress_max_cost;
            rcfg.access_speed_km_h = cfg.access_speed_km_h;
            rcfg.egress_speed_km_h = cfg.egress_speed_km_h;
            rcfg.transfer_cost = cfg.transfer_cost;
            return rcfg;
        }

        struct PreparedNetwork
        {
            SubNetwork net;
            std::vector<int32_t> valid_starts;
        };

        void ensure_required_extensions_loaded(duckdb::Connection &con)
        {
            auto install_h3 = con.Query("INSTALL h3 FROM community");
            if (install_h3->HasError())
            {
                throw std::runtime_error("Failed to install DuckDB H3 extension: " +
                                         install_h3->GetError());
            }
            auto load_h3 = con.Query("LOAD h3");
            if (load_h3->HasError())
            {
                throw std::runtime_error("Failed to load DuckDB H3 extension: " +
                                         load_h3->GetError());
            }

            auto install_spatial = con.Query("INSTALL spatial");
            if (install_spatial->HasError())
            {
                throw std::runtime_error("Failed to install DuckDB spatial extension: " +
                                         install_spatial->GetError());
            }
            auto load_spatial = con.Query("LOAD spatial");
            if (load_spatial->HasError())
            {
                throw std::runtime_error("Failed to load DuckDB spatial extension: " +
                                         load_spatial->GetError());
            }
        }

        void validate_request(RequestConfig &cfg)
        {
            input::validate(cfg);
        }

        // Radial street-network prep for catchment: runs the shared loading
        // core (edges → costs → SubNetwork → snap) and applies catchment's
        // policy of keeping only the snapped (connected) starting points.
        PreparedNetwork prepare_catchment_network(RequestConfig const &cfg,
                                                  duckdb::Connection &con,
                                                  bool load_geometry = false)
        {
            auto prep = network::prepare_radial_network(con, cfg, load_geometry);

            PreparedNetwork prepared{.net = std::move(prep.net),
                                     .valid_starts = {}};
            prepared.valid_starts.reserve(prep.snapped_nodes.size());
            for (auto s : prep.snapped_nodes)
            {
                if (s >= 0)
                {
                    prepared.valid_starts.push_back(s);
                }
            }
            if (prepared.valid_starts.empty())
            {
                throw std::runtime_error(
                    "Starting point(s) are disconnected from the street network.");
            }

            return prepared;
        }

        std::vector<double> run_reachability_dijkstra(
            SubNetwork const &net,
            std::vector<int32_t> const &valid_starts,
            RequestConfig const &cfg)
        {
            bool use_distance = (cfg.cost_type == CostType::Distance);
            auto adj = kernel::build_adjacency_list(net);
            return kernel::dijkstra(adj, valid_starts, cfg.cost_budget(),
                                    use_distance);
        }

        std::string dispatch_geojson_output(std::vector<ReachabilityField> const &fields,
                                            RequestConfig const &cfg,
                                            duckdb::Connection &con)
        {
            return output::build_geojson_output(fields, cfg, con);
        }

        std::string dispatch_parquet_output(std::vector<ReachabilityField> const &fields,
                                            RequestConfig const &cfg,
                                            duckdb::Connection &con)
        {
            output::write_parquet_output(fields, cfg, con);
            return "";
        }

        ReachabilityField build_reachability_field(
            RequestConfig &cfg,
            duckdb::Connection &con)
        {
            validate_request(cfg);

            // Load geometry into C++ when output needs edge polylines:
            // - Jsolines polygon (non-car) for grid surface interpolation
            // - Network output for edge clipping + WKT construction
            // Car polygon (concave hull), hexagon, and point grid use node coords only.
            bool load_geom = (cfg.catchment_type == CatchmentType::Network) ||
                             (cfg.catchment_type == CatchmentType::Polygon &&
                              cfg.mode != RoutingMode::Car);

            ReachabilityField field;

            if (cfg.mode == RoutingMode::PublicTransport)
            {
                field = pt::run_pt_pipeline(cfg, con);
            }
            else
            {
                auto prepared = prepare_catchment_network(cfg, con, load_geom);
                auto costs = run_reachability_dijkstra(prepared.net,
                                                       prepared.valid_starts,
                                                       cfg);
                field = kernel::make_reachability_field(std::move(costs),
                                                        std::move(prepared.net));
            }


            return field;
        }

        // Streaming path for shape_style=Separated grid contours: produce one
        // reachability field at a time, build its grid + jsolines features,
        // discard the field before moving to the next origin. Caps cost-vector
        // memory at 1× node_count instead of N× node_count.
        std::string compute_catchment_separated_streaming(
            RequestConfig &cfg,
            duckdb::Connection &con,
            std::function<double()> const &elapsed)
        {
            validate_request(cfg);
            bool const load_geom = true;  // jsolines needs edge geometry

            auto prepared = prepare_catchment_network(cfg, con, load_geom);
            auto net_ptr = std::make_shared<SubNetwork const>(std::move(prepared.net));
            bool const use_distance = (cfg.cost_type == CostType::Distance);
            auto adj = kernel::build_adjacency_list(*net_ptr);

            std::fprintf(stderr,
                         "[Pipeline] Separated infra (n_origins=%zu, %d nodes, %zu edges): %.0f ms\n",
                         prepared.valid_starts.size(),
                         net_ptr->node_count,
                         net_ptr->source.size(),
                         elapsed());

            auto const cutoffs = output::compute_step_cutoffs(cfg);
            int const zoom = geometry::grid_zoom_for_mode(cfg.mode);

            std::vector<output::TaggedFeature> features;
            for (size_t oi = 0; oi < prepared.valid_starts.size(); ++oi)
            {
                auto costs = kernel::dijkstra(adj,
                                              std::vector<int32_t>{prepared.valid_starts[oi]},
                                              cfg.cost_budget(), use_distance);
                ReachabilityField field;
                field.costs = std::move(costs);
                field.node_count = net_ptr->node_count;
                field.network = net_ptr;
                output::append_field_grid_features(features, field,
                                                    static_cast<int32_t>(oi),
                                                    zoom, cutoffs, cfg);
                // `field` (and its costs vector) destructed here.
            }
            std::fprintf(stderr,
                         "[Pipeline] Streamed %zu origins into %zu contour features: %.0f ms\n",
                         prepared.valid_starts.size(), features.size(), elapsed());

            if (cfg.output_format == OutputFormat::GeoJSON)
                return output::build_grid_contour_geojson_from_features(features, cfg, con);
            output::write_grid_contour_parquet_from_features(features, cfg, con,
                                                              cfg.output_path);
            return "";
        }

        bool wants_separated_streaming(RequestConfig const &cfg)
        {
            return cfg.shape_style == ShapeStyle::Separated &&
                   cfg.catchment_type == CatchmentType::Polygon &&
                   cfg.mode != RoutingMode::PublicTransport &&
                   cfg.mode != RoutingMode::Car;
        }

        // Export the reachability relation as a raw OD cost matrix:
        // (orig_cell, dest_cell, cost), one row per reachable (cell,
        // opportunity) pair. dest_cell is the opportunity's cell from
        // _hm_opp_meta. `con` holds the temp tables built by the shared
        // reachability engine (see heatmap::build_reachability_relation).
        void export_od_costs(HeatmapConfig const &cfg, duckdb::Connection &con)
        {
            std::ostringstream sql;
            sql << "COPY (SELECT p.cell AS orig_cell, om.opp_cell AS dest_cell, "
                << "CAST(ROUND(p.min_cost) AS INTEGER) AS cost "
                << "FROM _hm_per_opp p JOIN _hm_opp_meta om USING (opp_idx)) "
                << "TO '" << output::sql_escape(cfg.output_path)
                << "' (FORMAT PARQUET)";
            auto r = con.Query(sql.str());
            if (r->HasError())
                throw std::runtime_error("OD cost export failed: " +
                                         r->GetError());
        }
    } // namespace

    std::string compute_catchment(RequestConfig const &cfg_in)
    {
        auto cfg = cfg_in; // mutable copy for validation defaults

        auto t0 = std::chrono::steady_clock::now();
        auto elapsed = [&]() {
            auto now = std::chrono::steady_clock::now();
            double ms = std::chrono::duration<double, std::milli>(now - t0).count();
            t0 = now;
            return ms;
        };

        duckdb::DuckDB db(nullptr);
        duckdb::Connection con(db);
        ensure_required_extensions_loaded(con);
        std::fprintf(stderr, "[Pipeline] DuckDB init: %.0f ms\n", elapsed());

        if (wants_separated_streaming(cfg))
        {
            auto result = compute_catchment_separated_streaming(cfg, con, elapsed);
            std::fprintf(stderr, "[Pipeline] %s output: %.0f ms\n",
                         cfg.output_format == OutputFormat::GeoJSON
                             ? "GeoJSON" : "Parquet",
                         elapsed());
            return result;
        }

        std::vector<ReachabilityField> fields;
        fields.push_back(build_reachability_field(cfg, con));
        std::fprintf(stderr, "[Pipeline] Reachability field (%d nodes, %zu edges): %.0f ms\n",
                     fields[0].node_count,
                     fields[0].network ? fields[0].network->source.size() : 0,
                     elapsed());

        if (cfg.output_format == OutputFormat::GeoJSON)
        {
            auto result = dispatch_geojson_output(fields, cfg, con);
            std::fprintf(stderr, "[Pipeline] GeoJSON output: %.0f ms\n", elapsed());
            return result;
        }

        if (cfg.output_format == OutputFormat::Parquet)
        {
            auto result = dispatch_parquet_output(fields, cfg, con);
            std::fprintf(stderr, "[Pipeline] Parquet output: %.0f ms\n", elapsed());
            return result;
        }

        return "";
    }

    void compute_travel_cost_matrix(MatrixConfig const &cfg)
    {
        if (cfg.origins.empty())
            throw std::runtime_error("At least one origin is required");
        if (cfg.destinations.empty())
            throw std::runtime_error("At least one destination is required");
        if (cfg.edge_dir.empty())
            throw std::runtime_error("edge_dir is required");
        if (cfg.output_path.empty())
            throw std::runtime_error("output_path is required");

        size_t n_origins = cfg.origins.size();
        size_t n_dests = cfg.destinations.size();

        duckdb::DuckDB db(nullptr);
        duckdb::Connection con(db);
        ensure_required_extensions_loaded(con);

        std::vector<double> matrix(n_origins * n_dests,
                                    std::numeric_limits<double>::quiet_NaN());

        // Helper: read destination costs from a cost array into the matrix row.
        auto read_dest_costs = [&](size_t oi,
                                    std::vector<double> const &costs,
                                    std::vector<int32_t> const &dest_nodes)
        {
            for (size_t di = 0; di < n_dests; ++di)
            {
                int32_t node = dest_nodes[di];
                if (node < 0 || node >= static_cast<int32_t>(costs.size()))
                    continue;
                double cost = costs[node];
                if (std::isfinite(cost) && cost <= cfg.max_cost)
                    matrix[oi * n_dests + di] = cost;
            }
        };

        if (cfg.mode == RoutingMode::PublicTransport)
        {
            if (cfg.reverse)
                throw std::runtime_error(
                    "Reverse PT is not supported by the matrix; use "
                    "compute_od_costs.");
            // Load timetable once for all origins.
            auto tt = nigiri::timetable::read(
                std::filesystem::path{cfg.timetable_path});

            // PT: run the pipeline per origin, sharing the timetable.
            for (size_t oi = 0; oi < n_origins; ++oi)
            {
                auto rcfg = matrix_to_request_config(
                    cfg, {cfg.origins[oi]});
                input::validate(rcfg);

                auto pt_result = pt::run_pt_pipeline_with_destinations(
                    rcfg, con, cfg.destinations, &*tt);

                read_dest_costs(oi, pt_result.field.costs,
                                pt_result.extra_node_ids);
            }
        }
        else
        {
            network::StreetMatrixPrepInput prep_in{
                .origins = cfg.origins,
                .destinations = cfg.destinations,
                .mode = cfg.mode,
                .cost_type = cfg.cost_type,
                .max_cost = cfg.max_cost,
                .speed_km_h = cfg.speed_km_h,
                .edge_dir = cfg.edge_dir,
                .node_dir = cfg.node_dir,
            };
            auto prep = network::prepare_street_matrix_network(con, prep_in);

            bool use_distance = (cfg.cost_type == CostType::Distance);
            if (!cfg.reverse)
            {
                for (size_t oi = 0; oi < n_origins; ++oi)
                {
                    int32_t start = prep.origin_nodes[oi];
                    if (start < 0)
                        continue;
                    auto costs = kernel::dijkstra(
                        prep.adj, std::vector<int32_t>{start},
                        cfg.max_cost, use_distance);
                    read_dest_costs(oi, costs, prep.destination_nodes);
                }
            }
            else
            {
                // Reverse: one Dijkstra per destination on the transposed
                // graph → cost[n→d] for all n; scatter into column di.
                for (size_t di = 0; di < n_dests; ++di)
                {
                    int32_t start = prep.destination_nodes[di];
                    if (start < 0)
                        continue;
                    auto costs = kernel::dijkstra(
                        prep.rev_adj, std::vector<int32_t>{start},
                        cfg.max_cost, use_distance);
                    for (size_t oi = 0; oi < n_origins; ++oi)
                    {
                        int32_t node = prep.origin_nodes[oi];
                        if (node < 0 || node >= static_cast<int32_t>(costs.size()))
                            continue;
                        double cost = costs[node];
                        if (std::isfinite(cost) && cost <= cfg.max_cost)
                            matrix[oi * n_dests + di] = cost;
                    }
                }
            }
        }

        // Stage the matrix in a TEMP TABLE via the Appender, then export to
        // parquet (write_query_to_parquet creates the parent directory).
        {
            bool const has_origin_ids = cfg.origin_ids.size() == n_origins;
            bool const has_dest_ids = cfg.destination_ids.size() == n_dests;

            con.Query("DROP TABLE IF EXISTS _matrix_tmp");
            con.Query("CREATE TEMP TABLE _matrix_tmp "
                      "(origin VARCHAR, destination VARCHAR, travel_cost INTEGER)");

            {
                duckdb::Appender appender(con, "_matrix_tmp");
                for (size_t oi = 0; oi < n_origins; ++oi)
                {
                    std::string const &o_id = has_origin_ids
                        ? cfg.origin_ids[oi]
                        : std::to_string(oi);

                    for (size_t di = 0; di < n_dests; ++di)
                    {
                        double c = matrix[oi * n_dests + di];
                        if (cfg.sparse && std::isnan(c))
                            continue;
                        std::string const &d_id = has_dest_ids
                            ? cfg.destination_ids[di]
                            : std::to_string(di);

                        appender.BeginRow();
                        appender.Append(duckdb::Value(o_id));
                        appender.Append(duckdb::Value(d_id));
                        if (std::isnan(c))
                            appender.Append(duckdb::Value());
                        else
                            appender.Append(static_cast<int32_t>(std::round(c)));
                        appender.EndRow();
                    }
                }
            }

            output::write_query_to_parquet(
                con, "SELECT * FROM _matrix_tmp", cfg.output_path,
                "Travel cost matrix parquet export failed");
            con.Query("DROP TABLE _matrix_tmp");
        }
    }

    void compute_heatmap(HeatmapConfig const &cfg)
    {
        heatmap::compute_heatmap(cfg);
    }

    // OD cost matrix: an extension of the travel cost matrix that routes from
    // an opportunity layer (supporting reverse PT via the arrive-by pipeline)
    // and emits every reachable (orig_cell, dest_cell, cost) pair. Reuses the
    // shared reachability engine, then exports its relation raw.
    void compute_od_costs(HeatmapConfig const &cfg)
    {
        heatmap::build_reachability_relation(cfg, [&](duckdb::Connection &con) {
            export_od_costs(cfg, con);
        });
    }

} // namespace routing
