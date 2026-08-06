#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include <chrono>

#include "pipeline.h"
#include "preprocessing/access_egress_table.h"
#include "types.h"

namespace py = pybind11;

PYBIND11_MODULE(_routing, m)
{
    m.doc() = "C++ routing engine with Python bindings";

    auto elapsed_ms = [](std::chrono::steady_clock::time_point start,
                         std::chrono::steady_clock::time_point end) -> double
    {
        return std::chrono::duration_cast<std::chrono::duration<double, std::milli>>(
                   end - start)
            .count();
    };

    py::enum_<routing::RoutingMode>(m, "RoutingMode")
        .value("Walking", routing::RoutingMode::Walking)
        .value("Bicycle", routing::RoutingMode::Bicycle)
        .value("Pedelec", routing::RoutingMode::Pedelec)
        .value("Car", routing::RoutingMode::Car)
        .value("PublicTransport", routing::RoutingMode::PublicTransport);

    py::enum_<routing::CostType>(m, "CostType")
        .value("Time", routing::CostType::Time)
        .value("Distance", routing::CostType::Distance);

    py::enum_<routing::CatchmentType>(m, "CatchmentType")
        .value("Polygon", routing::CatchmentType::Polygon)
        .value("Network", routing::CatchmentType::Network)
        .value("HexagonalGrid", routing::CatchmentType::HexagonalGrid)
        .value("PointGrid", routing::CatchmentType::PointGrid);

    py::enum_<routing::OutputFormat>(m, "OutputFormat")
        .value("GeoJSON", routing::OutputFormat::GeoJSON)
        .value("Parquet", routing::OutputFormat::Parquet);

    py::enum_<routing::ShapeStyle>(m, "ShapeStyle")
        .value("Combined", routing::ShapeStyle::Combined)
        .value("Separated", routing::ShapeStyle::Separated);

    py::class_<routing::Point3857>(m, "Point3857")
        .def(py::init<double, double>())
        .def_readwrite("x", &routing::Point3857::x)
        .def_readwrite("y", &routing::Point3857::y);

    py::class_<routing::RequestConfig>(m, "RequestConfig")
        .def(py::init<>())
        .def_readwrite("starting_points", &routing::RequestConfig::starting_points)
        .def_readwrite("mode", &routing::RequestConfig::mode)
        .def_readwrite("cost_type", &routing::RequestConfig::cost_type)
        .def_readwrite("max_cost", &routing::RequestConfig::max_cost)
        .def_readwrite("steps", &routing::RequestConfig::steps)
        .def_readwrite("speed_km_h", &routing::RequestConfig::speed_km_h)
        .def_readwrite("edge_dir", &routing::RequestConfig::edge_dir)
        .def_readwrite("node_dir", &routing::RequestConfig::node_dir)
        .def_readwrite("timetable_path", &routing::RequestConfig::timetable_path)
        .def_readwrite("output_path", &routing::RequestConfig::output_path)
        .def_readwrite("catchment_type", &routing::RequestConfig::catchment_type)
        .def_readwrite("output_format", &routing::RequestConfig::output_format)
        .def_readwrite("shape_style", &routing::RequestConfig::shape_style)
        .def_readwrite("polygon_difference", &routing::RequestConfig::polygon_difference)
        .def_readwrite("departure_time", &routing::RequestConfig::departure_time)
        .def_readwrite("max_transfers", &routing::RequestConfig::max_transfers)
        // PT access/egress
        .def_readwrite("access_mode", &routing::RequestConfig::access_mode)
        .def_readwrite("egress_mode", &routing::RequestConfig::egress_mode)
        .def_readwrite("access_cost_type", &routing::RequestConfig::access_cost_type)
        .def_readwrite("egress_cost_type", &routing::RequestConfig::egress_cost_type)
        .def_readwrite("access_max_cost", &routing::RequestConfig::access_max_cost)
        .def_readwrite("egress_max_cost", &routing::RequestConfig::egress_max_cost)
        .def_readwrite("access_speed_km_h", &routing::RequestConfig::access_speed_km_h)
        .def_readwrite("egress_speed_km_h", &routing::RequestConfig::egress_speed_km_h)
        .def_readwrite("transfer_cost", &routing::RequestConfig::transfer_cost)
        // Transit mode filter, departure window, and explicit cutoffs
        .def_readwrite("transit_modes", &routing::RequestConfig::transit_modes)
        .def_readwrite("departure_window", &routing::RequestConfig::departure_window)
        // PointGrid settings
        .def_readwrite("grid_points_path", &routing::RequestConfig::grid_points_path)
        .def_readwrite("grid_snap_distance", &routing::RequestConfig::grid_snap_distance)
        .def_readwrite("cutoffs", &routing::RequestConfig::cutoffs);

    py::class_<routing::MatrixConfig>(m, "MatrixConfig")
        .def(py::init<>())
        .def_readwrite("origins", &routing::MatrixConfig::origins)
        .def_readwrite("destinations", &routing::MatrixConfig::destinations)
        .def_readwrite("origin_ids", &routing::MatrixConfig::origin_ids)
        .def_readwrite("destination_ids", &routing::MatrixConfig::destination_ids)
        .def_readwrite("mode", &routing::MatrixConfig::mode)
        .def_readwrite("cost_type", &routing::MatrixConfig::cost_type)
        .def_readwrite("max_cost", &routing::MatrixConfig::max_cost)
        .def_readwrite("speed_km_h", &routing::MatrixConfig::speed_km_h)
        .def_readwrite("edge_dir", &routing::MatrixConfig::edge_dir)
        .def_readwrite("node_dir", &routing::MatrixConfig::node_dir)
        .def_readwrite("output_path", &routing::MatrixConfig::output_path)
        // PT settings
        .def_readwrite("timetable_path", &routing::MatrixConfig::timetable_path)
        .def_readwrite("departure_time", &routing::MatrixConfig::departure_time)
        .def_readwrite("max_transfers", &routing::MatrixConfig::max_transfers)
        .def_readwrite("departure_window", &routing::MatrixConfig::departure_window)
        .def_readwrite("transit_modes", &routing::MatrixConfig::transit_modes)
        .def_readwrite("access_mode", &routing::MatrixConfig::access_mode)
        .def_readwrite("egress_mode", &routing::MatrixConfig::egress_mode)
        .def_readwrite("access_cost_type", &routing::MatrixConfig::access_cost_type)
        .def_readwrite("egress_cost_type", &routing::MatrixConfig::egress_cost_type)
        .def_readwrite("access_max_cost", &routing::MatrixConfig::access_max_cost)
        .def_readwrite("egress_max_cost", &routing::MatrixConfig::egress_max_cost)
        .def_readwrite("access_speed_km_h", &routing::MatrixConfig::access_speed_km_h)
        .def_readwrite("egress_speed_km_h", &routing::MatrixConfig::egress_speed_km_h)
        .def_readwrite("transfer_cost", &routing::MatrixConfig::transfer_cost)
        .def_readwrite("reverse", &routing::MatrixConfig::reverse)
        .def_readwrite("sparse", &routing::MatrixConfig::sparse);

    py::enum_<routing::HeatmapType>(m, "HeatmapType")
        .value("Gravity",        routing::HeatmapType::Gravity)
        .value("ClosestAverage", routing::HeatmapType::ClosestAverage)
        .value("Connectivity",   routing::HeatmapType::Connectivity)
        .value("TwoSFCA",        routing::HeatmapType::TwoSFCA);

    py::enum_<routing::TwoSFCAType>(m, "TwoSFCAType")
        .value("Standard", routing::TwoSFCAType::Standard)
        .value("E2SFCA",   routing::TwoSFCAType::E2SFCA)
        .value("M2SFCA",   routing::TwoSFCAType::M2SFCA);

    py::enum_<routing::GravityDecay>(m, "GravityDecay")
        .value("Gaussian",    routing::GravityDecay::Gaussian)
        .value("Exponential", routing::GravityDecay::Exponential)
        .value("Linear",      routing::GravityDecay::Linear)
        .value("Power",       routing::GravityDecay::Power);

    py::class_<routing::Opportunity>(m, "Opportunity")
        .def(py::init<>())
        .def(py::init([](std::vector<routing::Point3857> seeds, double w,
                         routing::Point3857 const &rep) {
                 routing::Opportunity o;
                 o.seeds = std::move(seeds);
                 o.weight = w;
                 o.rep = rep;
                 return o;
             }),
             py::arg("seeds"), py::arg("weight"), py::arg("rep"))
        .def_readwrite("seeds",  &routing::Opportunity::seeds)
        .def_readwrite("weight", &routing::Opportunity::weight)
        .def_readwrite("rep",    &routing::Opportunity::rep);

    py::class_<routing::HeatmapConfig>(m, "HeatmapConfig")
        .def(py::init<>())
        .def_readwrite("opportunities",   &routing::HeatmapConfig::opportunities)
        .def_readwrite("mode",            &routing::HeatmapConfig::mode)
        .def_readwrite("cost_type",       &routing::HeatmapConfig::cost_type)
        .def_readwrite("max_cost",        &routing::HeatmapConfig::max_cost)
        .def_readwrite("speed_km_h",      &routing::HeatmapConfig::speed_km_h)
        .def_readwrite("edge_dir",        &routing::HeatmapConfig::edge_dir)
        .def_readwrite("node_dir",        &routing::HeatmapConfig::node_dir)
        // Formula
        .def_readwrite("heatmap_type",    &routing::HeatmapConfig::heatmap_type)
        .def_readwrite("decay",           &routing::HeatmapConfig::decay)
        .def_readwrite("sensitivity",     &routing::HeatmapConfig::sensitivity)
        .def_readwrite("max_sensitivity", &routing::HeatmapConfig::max_sensitivity)
        .def_readwrite("closest_k",       &routing::HeatmapConfig::closest_k)
        .def_readwrite("two_sfca_type",   &routing::HeatmapConfig::two_sfca_type)
        .def_readwrite("demand_path",     &routing::HeatmapConfig::demand_path)
        // PT (mode == PublicTransport)
        .def_readwrite("timetable_path",  &routing::HeatmapConfig::timetable_path)
        .def_readwrite("arrival_time",    &routing::HeatmapConfig::arrival_time)
        .def_readwrite("max_transfers",   &routing::HeatmapConfig::max_transfers)
        .def_readwrite("transit_modes",   &routing::HeatmapConfig::transit_modes)
        .def_readwrite("access_mode",     &routing::HeatmapConfig::access_mode)
        .def_readwrite("egress_mode",     &routing::HeatmapConfig::egress_mode)
        .def_readwrite("access_max_time", &routing::HeatmapConfig::access_max_time)
        .def_readwrite("egress_max_time", &routing::HeatmapConfig::egress_max_time)
        .def_readwrite("transfer_cost",   &routing::HeatmapConfig::transfer_cost)
        .def_readwrite("access_table_path", &routing::HeatmapConfig::access_table_path)
        .def_readwrite("egress_table_path", &routing::HeatmapConfig::egress_table_path)
        .def_readwrite("connectivity_output_resolution", &routing::HeatmapConfig::connectivity_output_resolution)
        // Output
        .def_readwrite("output_path",     &routing::HeatmapConfig::output_path);

    py::class_<routing::preprocessing::AccessEgressConfig>(m, "AccessEgressConfig")
        .def(py::init<>())
        .def_readwrite("timetable_path", &routing::preprocessing::AccessEgressConfig::timetable_path)
        .def_readwrite("edge_dir",       &routing::preprocessing::AccessEgressConfig::edge_dir)
        .def_readwrite("node_dir",       &routing::preprocessing::AccessEgressConfig::node_dir)
        .def_readwrite("output_path",    &routing::preprocessing::AccessEgressConfig::output_path)
        .def_readwrite("mode",           &routing::preprocessing::AccessEgressConfig::mode)
        .def_readwrite("max_min",        &routing::preprocessing::AccessEgressConfig::max_min)
        .def_readwrite("speed_km_h",     &routing::preprocessing::AccessEgressConfig::speed_km_h)
        .def_readwrite("chunk_size",     &routing::preprocessing::AccessEgressConfig::chunk_size)
        .def_readwrite("spacing_m",      &routing::preprocessing::AccessEgressConfig::spacing_m);

    m.def("compute_catchment",
          [elapsed_ms](routing::RequestConfig const &config)
          {
              auto t0 = std::chrono::steady_clock::now();
              auto result = routing::compute_catchment(config);
              auto t1 = std::chrono::steady_clock::now();
              py::print("[routing] compute_catchment total_ms=",
                        elapsed_ms(t0, t1));
              return result;
          },
          py::arg("config"),
          "Run the full routing pipeline and dispatch output by RequestConfig.output_format");

    m.def("compute_travel_cost_matrix",
          &routing::compute_travel_cost_matrix,
          py::arg("config"),
          "Compute many-to-many travel cost matrix between origins and destinations");

    m.def("compute_heatmap",
          [elapsed_ms](routing::HeatmapConfig const &config)
          {
              auto t0 = std::chrono::steady_clock::now();
              routing::compute_heatmap(config);
              auto t1 = std::chrono::steady_clock::now();
              py::print("[routing] compute_heatmap total_ms=",
                        elapsed_ms(t0, t1));
          },
          py::arg("config"),
          "Compute per-origin accessibility heatmap (Gravity / ClosestAverage) "
          "against a fixed opportunity layer");

    m.def("compute_od_costs",
          [elapsed_ms](routing::HeatmapConfig const &config)
          {
              auto t0 = std::chrono::steady_clock::now();
              routing::compute_od_costs(config);
              auto t1 = std::chrono::steady_clock::now();
              py::print("[routing] compute_od_costs total_ms=",
                        elapsed_ms(t0, t1));
          },
          py::arg("config"),
          "Emit the raw per-(cell, opportunity) OD cost relation "
          "(orig_cell, dest_cell, cost) from the reachability pipeline to "
          "config.output_path. Used by Huff v2 for its PT OD matrix.");

    m.def("build_access_egress_table",
          [elapsed_ms](routing::preprocessing::AccessEgressConfig const &config)
          {
              auto t0 = std::chrono::steady_clock::now();
              auto out = routing::preprocessing::build_access_egress_table(config);
              auto t1 = std::chrono::steady_clock::now();
              py::print("[routing] build_access_egress_table total_ms=",
                        elapsed_ms(t0, t1));
              return out;
          },
          py::arg("config"),
          "Precompute a PT access/egress lookup table for one mode "
          "(stop_idx, h3_index, cost_minutes). Writes ZSTD parquet to "
          "config.output_path and returns the path");
}
