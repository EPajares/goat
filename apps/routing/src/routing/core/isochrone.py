# type: ignore
# ruff: noqa

import heapq
import math

import numpy as np
from numba import njit
from numba.core import types
from numba.typed import Dict, List
from routing.utils import (
    coordinate_to_pixel,
    web_mercator_x_to_pixel_x,
    web_mercator_y_to_pixel_y,
)
from scipy import spatial


@njit(cache=True)  # type: ignore
def construct_adjacency_list_(
    n, edge_source, edge_target, edge_cost, edge_reverse_cost
) -> list[list[list[float]]]:
    """
    Construct adjacency list from edges
    :param n: Number of nodes
    :param edge_source: List of edge source nodes
    :param edge_target: List of edge target nodes
    :param edge_cost: List of edge costs
    :param edge_reverse_cost: List of edge reverse costs
    :return: Adjacency list
    """
    adj_list: list[list[list[float]]] = List([List([List([-1.001, -1.001])])] * n)
    for i in range(len(edge_source)):
        if edge_cost[i] >= 0.0:
            if adj_list[edge_source[i]][0][0] == -1.001:
                adj_list[edge_source[i]] = List([List([edge_target[i], edge_cost[i]])])
            else:
                adj_list[edge_source[i]].append(List([edge_target[i], edge_cost[i]]))
        if edge_reverse_cost[i] >= 0.0:
            if adj_list[edge_target[i]][0][0] == -1.001:
                adj_list[edge_target[i]] = List(
                    [List([edge_source[i], edge_reverse_cost[i]])]
                )
            else:
                adj_list[edge_target[i]].append(
                    List([edge_source[i], edge_reverse_cost[i]])
                )
    return adj_list


@njit(cache=True)
def dijkstra(start_vertices, adj_list, travel_time, use_distance=False):
    """
    Dijkstra's algorithm one-to-all shortest path search
    :param start_vertices: List of start vertices
    :param adj_list: Adjacency list
    :param travel_time: Travel time matrix
    :return: List of shortest paths and costs
    """
    n = len(adj_list)
    # distances = [np.Inf for _ in range(n)]
    distances = np.full(n, np.inf, np.double)
    # loop over all start vertices
    for start_vertex in start_vertices:
        distances[start_vertex] = 0.0
        # visited = [False for _ in range(n)]
        visited = np.full(n, False, np.bool_)
        # set up priority queue
        pq = [(0.0, start_vertex)]
        while len(pq) > 0:
            if pq[0][0] >= travel_time:
                break
            # get the root, discard current distance (!!!distances in the data are in seconds)
            _, u = heapq.heappop(pq)
            # if the node is visited, skip
            if visited[u]:
                continue
            # set the node to visited
            visited[u] = True
            # check the distance and node and distance
            for v, l in adj_list[u]:
                v = int(v)
                l = (
                    (l / 60.0) if not use_distance else l
                )  # convert cost to minutes if required
                # if the current node's distance + distance to the node we're visiting
                # is less than the distance of the node we're visiting on file
                # replace that distance and push the node we're visiting into the priority queue
                if distances[u] + l < distances[v]:
                    distances[v] = distances[u] + l
                    heapq.heappush(pq, (distances[v], v))
    return distances


@njit(cache=True)
def dijkstra_h3(start_vertices, adj_list, travel_time, use_distance=False):
    """
    Dijkstra's algorithm one-to-all shortest path search
    :param start_vertices: List of start vertices
    :param adj_list: Adjacency list
    :param travel_time: Travel time matrix
    :return: List of shortest paths and costs
    """
    distances_list = []
    n = len(adj_list)
    # distances = [np.inf for _ in range(n)]

    # loop over all start vertices
    for start_vertex in start_vertices:
        distances = np.full(n, np.inf, np.double)
        distances[start_vertex] = 0.0
        # visited = [False for _ in range(n)]
        visited = np.full(n, False, np.bool_)
        # set up priority queue
        pq = [(0.0, start_vertex)]
        while len(pq) > 0:
            if pq[0][0] >= travel_time:
                break
            # get the root, discard current distance (!!!distances in the data are in seconds)
            _, u = heapq.heappop(pq)
            # if the node is visited, skip
            if visited[u]:
                continue
            # set the node to visited
            visited[u] = True
            # check the distance and node and distance
            for v, l in adj_list[u]:
                v = int(v)
                l = (
                    (l / 60.0) if not use_distance else l
                )  # convert cost to minutes if required
                # if the current node's distance + distance to the node we're visiting
                # is less than the distance of the node we're visiting on file
                # replace that distance and push the node we're visiting into the priority queue
                if distances[u] + l < distances[v]:
                    distances[v] = distances[u] + l
                    heapq.heappush(pq, (distances[v], v))
        distances_list.append(distances)
    return distances_list


@njit(cache=True)
def array_equals(vertex, array):
    pointer = 0
    found = np.empty(100, np.int64)
    for i, value in enumerate(array):
        if value == vertex:
            found[pointer] = i
            pointer += 1
    return found[:pointer]


@njit(cache=True)
def get_adj_list(vertex, edge_source, edge_target):
    forward_adjacency = array_equals(vertex, edge_source)
    backward_adjacency = array_equals(vertex, edge_target)
    return forward_adjacency, backward_adjacency


@njit(cache=True)
def get_adj_count(edge_source, edge_target):
    concat = np.concatenate((edge_source, edge_target))
    unique = np.unique(concat)
    return len(unique)


@njit(cache=True)
def filter_nodes(node_coords_list, node_costs_list, zoom, width, west, north):
    """
    Filter out nodes that fall inside the same pixel (keep the one with the lowest cost)
    :param node_coords_list: List of node coordinates
    :param node_costs_list: List of node costs
    :param zoom: Zoom level
    :param width: Width of the grid
    :param west: West coordinate of the grid
    :param north: North coordinate of the grid
    :return: List of filtered nodes and costs
    """
    index_cost = {}
    for idx, node_coord in enumerate(node_coords_list):
        node_coord_pixel = [
            round(web_mercator_x_to_pixel_x(node_coord[0], zoom)),
            round(web_mercator_y_to_pixel_y(node_coord[1], zoom)),
        ]
        pixel_x = node_coord_pixel[0]
        pixel_y = node_coord_pixel[1]
        x = pixel_x - west
        y = pixel_y - north
        index = y * width + x
        if node_costs_list[idx] != np.inf and (
            index not in index_cost or node_costs_list[idx] < index_cost[index]
        ):
            index_cost[index] = idx
    node_coords_list = [node_coords_list[idx] for idx in index_cost.values()]
    node_costs_list = [node_costs_list[idx] for idx in index_cost.values()]
    return node_coords_list, node_costs_list


def check_extent(extent, coord):
    """
    Check and update extent
    :param extent: Extent
    :param coord: Coordinate
    """
    if coord[0] < extent[0]:
        extent[0] = coord[0]

    if coord[1] < extent[1]:
        extent[1] = coord[1]

    if coord[0] > extent[2]:
        extent[2] = coord[0]

    if coord[1] > extent[3]:
        extent[3] = coord[1]


def get_extent(geom_array):
    extent = np.empty((2, 2), np.double)  # [min_x, min_y, max_x, max_y]
    geom_array.min(0, extent[0])
    geom_array.max(0, extent[1])
    return extent.flat


@njit(cache=True)
def remap_edges(edge_source, edge_target, geom_address, geom_array):
    """
    Remap edges to start from 0
    :param edge_source: List of source nodes
    :param edge_target: List of target nodes
    :param edge_geom: List of edge geometries
    """
    unordered_map = Dict.empty(
        key_type=types.int64,
        value_type=types.int64,
    )
    node_coords = np.empty((int((len(edge_source) * 1.5)), 2), np.double)
    id = 0
    for i in range(len(edge_source)):
        edge_geom = geom_array[geom_address[i] : geom_address[i + 1], :]
        # source
        if unordered_map.get(edge_source[i]) is None:
            unordered_map[edge_source[i]] = id
            edge_source[i] = id
            node_coords[id] = edge_geom[0]
            id += 1
        else:
            edge_source[i] = unordered_map.get(edge_source[i])
        # target
        if unordered_map.get(edge_target[i]) is None:
            unordered_map[edge_target[i]] = id
            edge_target[i] = id
            node_coords[id] = edge_geom[-1]
            id += 1
        else:
            edge_target[i] = unordered_map.get(edge_target[i])
    return unordered_map, node_coords[: len(unordered_map)]


@njit(cache=True)
def estimate_split_edges_size(edge_length, geom_array, split_distance):
    full_edge_length = np.sum(edge_length)
    number_of_geoms = len(geom_array) - 2 * len(edge_length)
    minimum_size = full_edge_length / split_distance + 1
    maximum_size = minimum_size + number_of_geoms
    return int(maximum_size)


@njit(cache=True)
def split_edges(
    edge_source,
    edge_target,
    edge_length,
    geom_address,
    geom_array,
    agg_costs,
    split_distance,
):
    """
    Split edges into multiple edges
    :param edge_source: List of source nodes
    :param edge_target: List of target nodes
    :param edge_length: List of edge lengths
    :param edge_geom: List of edge geometries
    :param agg_costs: List of aggregated costs from dijkstra algorithm
    :param split_distance: Distance to split edges in meters
    :return: List of interpolated coordinates and costs along the line every x meters, including vertices
    """
    # start_time = time()
    est_size = estimate_split_edges_size(edge_length, geom_array, split_distance)
    coords = np.empty((est_size, 2), np.double)
    costs = np.empty(est_size, np.double)

    counter = -1
    for i in range(len(edge_source)):
        source_id = edge_source[i]
        target_id = edge_target[i]
        source_cost = agg_costs[source_id]
        target_cost = agg_costs[target_id]
        total_length = edge_length[i]
        geom = geom_array[geom_address[i] : geom_address[i + 1], :]
        if np.inf not in [source_cost, target_cost]:
            if total_length > split_distance or len(geom) > 2:
                # split edge into multiple edges
                previous_agg_dist = 0.0
                for idx, coord in enumerate(geom[:-1]):
                    # find distance between current and next point
                    next_coord = geom[idx + 1]
                    dist = math.sqrt(
                        (coord[0] - next_coord[0]) ** 2
                        + (coord[1] - next_coord[1]) ** 2
                    )
                    agg_dist = previous_agg_dist + dist

                    n_splits = math.floor(dist / split_distance)
                    for n in range(1, n_splits + 1):
                        counter += 1
                        distance_to_next = n * split_distance
                        x = coord[0] - (
                            (distance_to_next * (coord[0] - next_coord[0])) / dist
                        )
                        y = coord[1] - (
                            (distance_to_next * (coord[1] - next_coord[1])) / dist
                        )
                        coords[counter] = [x, y]
                        cost = source_cost + (
                            (previous_agg_dist + distance_to_next) / total_length
                        ) * (target_cost - source_cost)
                        costs[counter] = cost
                    # if next point is vertex, add it and update previous
                    if idx + 1 <= len(geom) - 2:
                        counter += 1
                        coords[counter] = geom[idx + 1]
                        cost = source_cost + (agg_dist / total_length) * (
                            target_cost - source_cost
                        )
                        costs[counter] = cost
                        previous_agg_dist = agg_dist

    # print(f"estimated size: {est_size}, calculated size: {counter}")
    if counter == -1:
        counter = 0
    return coords[:counter, :], costs[:counter]


def get_single_depth_grid_(zoom, west, north, data):
    """
    Get single depth grid
    :param zoom: Zoom level
    :param west: West coordinate
    :param north: North coordinate
    :param data: Data to be gridded
    :return: Gridded data
    """
    grid_data = {}
    Z = np.ravel(data)
    Z = np.rint(Z)
    Z = np.nan_to_num(Z, nan=np.iinfo(np.intc).max, posinf=np.iinfo(np.intc).max)
    grid_data["version"] = 0
    grid_data["zoom"] = zoom
    grid_data["west"] = west
    grid_data["north"] = north
    grid_data["width"] = data.shape[1]
    grid_data["height"] = data.shape[0]
    grid_data["depth"] = 1
    grid_data["data"] = Z
    return grid_data


def get_geom_array(edges_geom):
    geom_count = np.empty(len(edges_geom) + 1, dtype=np.intc)
    geom_count[0] = 0
    address = 1
    for geom in edges_geom:
        geom_count[address] = len(geom)
        address += 1

    all_geom_count = np.sum(geom_count)
    geom_array = np.empty([all_geom_count, 2], dtype=np.double)
    address = 0
    for geom in edges_geom:
        for point in geom:
            geom_array[address] = point
            address += 1

    geom_address = np.cumsum(geom_count)

    return geom_address, geom_array


def build_grid_interpolate_(
    points,
    costs,
    extent,
    step_x,
    step_y,
    speed,
    max_traveltime,
    is_distance_based: bool,
):
    """
    Build grid interpolate
    :param points: List of points
    :param costs: List of costs
    :param extent: Extent of the grid
    :param step_x: Step size in x direction
    :param step_y: Step size in y direction
    :return: Grid interpolate
    """
    X = np.arange(start=extent[0], stop=extent[2], step=step_x)
    Y = np.arange(start=extent[1], stop=extent[3], step=step_y)
    X, Y = np.meshgrid(X, Y)  # 2D grid for interpolation

    tree = spatial.KDTree(points)
    grid_points = np.stack((X.flatten(), Y.flatten()), axis=1)
    distances, indices = tree.query(
        grid_points, k=1, distance_upper_bound=200, workers=-1
    )
    distances[distances == np.inf] = np.nan
    additional_costs = (
        distances
        if is_distance_based
        else 0
        if speed is None
        else ((distances / speed) / 60)
    )
    indices_flatten = indices.flatten()

    unvalid_indices = np.asarray(indices_flatten == len(costs)).nonzero()[0]
    mapped_costs = np.take(costs, indices_flatten, mode="clip")
    np.put(mapped_costs, unvalid_indices, np.nan)
    mapped_costs = np.rint(mapped_costs + additional_costs)
    distances[distances > max_traveltime] = np.nan
    Z = mapped_costs
    Z = Z.reshape(len(X), len(X[0]))

    return np.flip(Z, 0)


def build_grid_interpolate_h3(
    points,
    costs,
    centroid_x,
    centroid_y,
    speed,
    max_traveltime,
    is_distance_based: bool,
):
    """
    Build grid interpolate
    :param points: List of points
    :param costs: List of costs
    :param centroid_x: X coordinate of H3 cell centroids
    :param centroid_y: Y coordinate of H3 cell centroids
    :return: Grid interpolate (mapped cost for each centroid)
    """

    # Combine centroid x and y coordinates into a grid
    grid_points = np.stack((centroid_x, centroid_y), axis=1)

    # Use K-nearest-neighbors function to find the nearest node to each centroid
    tree = spatial.KDTree(points)
    distances, indices = tree.query(
        grid_points, k=1, distance_upper_bound=200, workers=1
    )

    # Map cost of nearest node to each centroid
    mapped_costs = np.take(costs, indices, mode="clip")

    # Discard cost of centroids which are too far from any node
    invalid_indices = np.asarray(indices == len(costs)).nonzero()[0]
    np.put(mapped_costs, invalid_indices, np.nan)

    # Account for additional cost of travel from node to centroid
    distances[distances == np.inf] = np.nan
    additional_costs = (
        distances
        if is_distance_based
        else 0
        if speed is None
        else ((distances / speed) / 60)
    )
    mapped_costs = np.rint(mapped_costs + additional_costs)

    # Discard cost of centroids which are further than the max travel time
    invalid_costs = np.asarray(mapped_costs > max_traveltime).nonzero()[0]
    np.put(mapped_costs, invalid_costs, np.nan)

    return mapped_costs


def prepare_network_isochrone(edge_network_input):
    edge_network = edge_network_input.copy()
    # remap edges
    edges_source = edge_network["source"]
    edges_target = edge_network["target"]
    edges_cost = edge_network["cost"]
    edges_reverse_cost = edge_network["reverse_cost"]
    # time()
    geom_address, geom_array = get_geom_array(edge_network["geom"])
    # time()
    # print(f"Convert geom array time: \t {end_time - start_time} s")
    edges_length = np.array(edge_network["length"])
    # time()
    unordered_map, node_coords = remap_edges(
        edges_source, edges_target, geom_address, geom_array
    )
    # time()
    # print(f"Remap edges time: \t\t {end_time-start_time} s")

    extent = get_extent(geom_array)
    extent[0] -= 200
    extent[1] -= 200
    extent[2] += 200
    extent[3] += 200
    return (
        edges_source,
        edges_target,
        edges_cost,
        edges_reverse_cost,
        edges_length,
        unordered_map,
        node_coords,
        extent,
        geom_address,
        geom_array,
    )


def network_to_grid(
    extent,
    zoom,
    edges_source,
    edges_target,
    edges_length,
    geom_address,
    geom_array,
    distances,
    node_coords,
    speed,
    max_traveltime,
    is_distance_based: bool,
):
    # minx, miny, maxx, maxy
    width_meter = extent[2] - extent[0]
    height_meter = extent[3] - extent[1]

    # Pixel coordinates origin is at the top left corner of the image. (y of top right/left corner is smaller than y of bottom right/left corner)
    xy_bottom_left = [
        math.floor(x)
        for x in coordinate_to_pixel(
            [extent[0], extent[1]], zoom=zoom, return_dict=False, web_mercator=True
        )
    ]
    xy_top_right = [
        math.floor(x)
        for x in coordinate_to_pixel(
            [extent[2], extent[3]], zoom=zoom, return_dict=False, web_mercator=True
        )
    ]
    # pixel x, y distances
    width_pixel = xy_top_right[0] - xy_bottom_left[0]
    height_pixel = xy_bottom_left[1] - xy_top_right[1]

    # calculate step in web mercator size
    web_mercator_x_step = width_meter / width_pixel
    web_mercator_y_step = height_meter / height_pixel

    # split edges based on resolution
    interpolated_coords = []
    interpolated_costs = []
    interpolated_coords, interpolated_costs = split_edges(
        edges_source,
        edges_target,
        edges_length,
        geom_address,
        geom_array,
        distances,
        min([web_mercator_x_step, web_mercator_y_step]),
    )

    node_coords_list = np.concatenate((node_coords, interpolated_coords))
    node_costs_list = np.concatenate((distances, interpolated_costs))

    node_coords_list, node_costs_list = filter_nodes(
        node_coords_list,
        node_costs_list,
        zoom,
        width_pixel,
        xy_bottom_left[0],
        xy_top_right[1],
    )

    Z = build_grid_interpolate_(
        node_coords_list,
        node_costs_list,
        extent,
        step_x=web_mercator_x_step,
        step_y=web_mercator_y_step,
        speed=speed,
        max_traveltime=max_traveltime,
        is_distance_based=is_distance_based,
    )

    # build grid data (single depth)
    grid_data = get_single_depth_grid_(zoom, xy_bottom_left[0], xy_top_right[1], Z)

    return grid_data


def network_to_grid_h3(
    extent,
    zoom,
    edges_source,
    edges_target,
    edges_length,
    geom_address,
    geom_array,
    distances,
    node_coords,
    speed,
    max_traveltime,
    centroid_x,
    centroid_y,
    is_distance_based: bool,
):
    # Pixel coordinates origin is at the top left corner of the image. (y of top right/left corner is smaller than y of bottom right/left corner)
    xy_bottom_left = [
        math.floor(x)
        for x in coordinate_to_pixel(
            [extent[0], extent[1]], zoom=zoom, return_dict=False, web_mercator=True
        )
    ]
    xy_top_right = [
        math.floor(x)
        for x in coordinate_to_pixel(
            [extent[2], extent[3]], zoom=zoom, return_dict=False, web_mercator=True
        )
    ]
    # pixel x, y distances
    width_pixel = xy_top_right[0] - xy_bottom_left[0]

    # split edges based on resolution
    interpolated_coords = []
    interpolated_costs = []
    interpolated_coords, interpolated_costs = split_edges(
        edges_source,
        edges_target,
        edges_length,
        geom_address,
        geom_array,
        distances,
        150.0,
    )

    node_coords_list = np.concatenate((node_coords, interpolated_coords))
    node_costs_list = np.concatenate((distances, interpolated_costs))

    node_coords_list, node_costs_list = filter_nodes(
        node_coords_list,
        node_costs_list,
        zoom,
        width_pixel,
        xy_bottom_left[0],
        xy_top_right[1],
    )

    mapped_cost = build_grid_interpolate_h3(
        node_coords_list,
        node_costs_list,
        centroid_x,
        centroid_y,
        speed,
        max_traveltime,
        is_distance_based,
    )

    return mapped_cost


def compute_isochrone(
    edge_network_input,
    start_vertices,
    travel_time,
    speed,
    zoom,
    return_network: bool = True,
    is_distance_based: bool = False,
):
    """
    Compute isochrone for a given start vertices

    :param edge_network: Edge Network DataFrame
    :param start_vertices: List of start vertices
    :param travel_time: Travel time in minutes
    :return: R5 Grid
    """
    (
        edges_source,
        edges_target,
        edges_cost,
        edges_reverse_cost,
        edges_length,
        unordered_map,
        node_coords,
        extent,
        geom_address,
        geom_array,
    ) = prepare_network_isochrone(edge_network_input=edge_network_input)

    # run dijkstra
    adj_list = construct_adjacency_list_(
        len(unordered_map), edges_source, edges_target, edges_cost, edges_reverse_cost
    )
    start_vertices_ids = np.array([unordered_map[v] for v in start_vertices])
    distances = dijkstra(start_vertices_ids, adj_list, travel_time, is_distance_based)

    # convert results to grid
    grid_data = network_to_grid(
        extent,
        zoom,
        edges_source,
        edges_target,
        edges_length,
        geom_address,
        geom_array,
        distances,
        node_coords,
        speed,
        travel_time,
        is_distance_based,
    )

    # Convert network to geojson
    if return_network is True:
        edges_length = range(len(edges_source))
        network = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "LineString",
                        "coordinates": geom_array[
                            geom_address[idx] : geom_address[idx + 1], :
                        ].tolist(),
                    },
                    "properties": {"cost": distances[edges_target[idx]]},
                }
                for idx in edges_length
                if distances[edges_target[idx]] != np.inf
                and distances[edges_target[idx]] <= travel_time
            ],
        }
    else:
        network = None

    return grid_data, network


def compute_isochrone_h3(
    edge_network_input,
    start_vertices,
    travel_time,
    speed,
    centroid_x,
    centroid_y,
    zoom,
    is_distance_based: bool = False,
):
    """
    Compute isochrone for a given start vertices

    :param edge_network: Edge Network DataFrame
    :param start_vertices: List of start vertices
    :param travel_time: Travel time in minutes
    :return: R5 Grid
    """
    (
        edges_source,
        edges_target,
        edges_cost,
        edges_reverse_cost,
        edges_length,
        unordered_map,
        node_coords,
        extent,
        geom_address,
        geom_array,
    ) = prepare_network_isochrone(edge_network_input=edge_network_input)

    # run dijkstra
    adj_list = construct_adjacency_list_(
        len(unordered_map), edges_source, edges_target, edges_cost, edges_reverse_cost
    )
    start_vertices_ids = np.array([unordered_map[v] for v in start_vertices])
    distances = dijkstra(start_vertices_ids, adj_list, travel_time, is_distance_based)

    # convert results to grid
    grid_data = network_to_grid_h3(
        extent,
        zoom,
        edges_source,
        edges_target,
        edges_length,
        geom_address,
        geom_array,
        distances,
        node_coords,
        speed,
        travel_time,
        centroid_x,
        centroid_y,
        is_distance_based,
    )

    return grid_data
