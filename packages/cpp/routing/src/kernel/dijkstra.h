#pragma once

#include "../types.h"

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <limits>
#include <queue>
#include <vector>

namespace routing::kernel
{

    // Reusable scratch for running many bounded single-source Dijkstras over
    // the *same* graph (e.g. one per opportunity in a heatmap). Avoids the
    // dominant cost of the naive version — reallocating and zero-filling two
    // node_count-sized arrays per call — by generation-stamping: `dist[v]` is
    // valid only when `gen[v] == cur`, so resetting a run is O(1) (++cur).
    struct DijkstraScratch
    {
        std::vector<double> dist;
        std::vector<std::uint32_t> gen;   // gen[v]==cur ⟺ dist[v] set this run
        std::vector<std::uint32_t> done;  // done[v]==cur ⟺ v settled this run
        std::uint32_t cur = 0u;

        explicit DijkstraScratch(std::size_t n)
            : dist(n), gen(n, 0u), done(n, 0u) {}

        void begin()
        {
            // ++cur invalidates all prior stamps in O(1). On the (4-billionth)
            // wraparound, clear the stamps once so cur==0 entries don't alias.
            if (++cur == 0u)
            {
                std::fill(gen.begin(), gen.end(), 0u);
                std::fill(done.begin(), done.end(), 0u);
                cur = 1u;
            }
        }
        bool reached(std::int32_t v) const { return gen[v] == cur; }
    };

    // Bounded single-source Dijkstra using reusable scratch. Returns the list
    // of settled nodes (final cost < travel_budget); their cost is in
    // scratch.dist[v]. Work is O(reached · log reached), not O(node_count).
    inline std::vector<std::int32_t>
    dijkstra_reuse(std::vector<std::vector<AdjEntry>> const &adj,
                   std::int32_t start, double travel_budget, bool use_distance,
                   DijkstraScratch &s)
    {
        s.begin();
        std::vector<std::int32_t> settled;
        if (start < 0 || start >= static_cast<std::int32_t>(adj.size()))
            return settled;

        using PQEntry = std::pair<double, std::int32_t>;
        std::priority_queue<PQEntry, std::vector<PQEntry>, std::greater<>> pq;
        s.dist[start] = 0.0;
        s.gen[start] = s.cur;
        pq.push({0.0, start});

        while (!pq.empty())
        {
            auto [d, u] = pq.top();
            pq.pop();
            if (d >= travel_budget)
                break;
            if (s.done[u] == s.cur)
                continue;  // stale / already settled
            s.done[u] = s.cur;
            settled.push_back(u);

            for (auto const &[v, w] : adj[u])
            {
                double const edge_cost = use_distance ? w : (w / 60.0);
                double const new_dist = d + edge_cost;
                if (s.gen[v] != s.cur || new_dist < s.dist[v])
                {
                    s.dist[v] = new_dist;
                    s.gen[v] = s.cur;
                    pq.push({new_dist, v});
                }
            }
        }
        return settled;
    }

    // Multi-source variant: all starts seeded at cost 0, so dist[v] is the cost
    // to the nearest start.
    inline std::vector<std::int32_t>
    dijkstra_reuse(std::vector<std::vector<AdjEntry>> const &adj,
                   std::vector<std::int32_t> const &starts, double travel_budget,
                   bool use_distance, DijkstraScratch &s)
    {
        s.begin();
        std::vector<std::int32_t> settled;
        using PQEntry = std::pair<double, std::int32_t>;
        std::priority_queue<PQEntry, std::vector<PQEntry>, std::greater<>> pq;
        for (std::int32_t start : starts)
        {
            if (start < 0 || start >= static_cast<std::int32_t>(adj.size()))
                continue;
            if (s.gen[start] != s.cur)
            {
                s.dist[start] = 0.0;
                s.gen[start] = s.cur;
                pq.push({0.0, start});
            }
        }
        while (!pq.empty())
        {
            auto [d, u] = pq.top();
            pq.pop();
            if (d >= travel_budget)
                break;
            if (s.done[u] == s.cur)
                continue;
            s.done[u] = s.cur;
            settled.push_back(u);
            for (auto const &[v, w] : adj[u])
            {
                double const edge_cost = use_distance ? w : (w / 60.0);
                double const new_dist = d + edge_cost;
                if (s.gen[v] != s.cur || new_dist < s.dist[v])
                {
                    s.dist[v] = new_dist;
                    s.gen[v] = s.cur;
                    pq.push({new_dist, v});
                }
            }
        }
        return settled;
    }

    // Build adjacency list from flat SubNetwork arrays.
    inline std::vector<std::vector<AdjEntry>>
    build_adjacency_list(SubNetwork const &net)
    {
        std::vector<std::vector<AdjEntry>> adj(net.node_count);
        for (size_t i = 0; i < net.source.size(); ++i)
        {
            if (net.cost[i] >= 0.0 && net.cost[i] < 99999.0)
                adj[net.source[i]].push_back(
                    {net.target[i], net.cost[i]});
            if (net.reverse_cost[i] >= 0.0 && net.reverse_cost[i] < 99999.0)
                adj[net.target[i]].push_back(
                    {net.source[i], net.reverse_cost[i]});
        }
        return adj;
    }

    // Build the reverse-graph adjacency list. For every directed edge u→v
    // in the original graph G, the reverse graph G^T contains v→u with the
    // same cost. So a Dijkstra from node s on G^T gives, for every node v,
    // the shortest path cost v→s in the original G. For symmetric modes
    // (walking/bicycle/pedelec where cost == reverse_cost), G^T is
    // structurally identical to G; for car, edges with reverse_cost=99999
    // (one-way restrictions) drop out of the appropriate direction.
    inline std::vector<std::vector<AdjEntry>>
    build_reverse_adjacency_list(SubNetwork const &net)
    {
        std::vector<std::vector<AdjEntry>> adj(net.node_count);
        for (size_t i = 0; i < net.source.size(); ++i)
        {
            // Forward edge u→v in G becomes v→u in G^T.
            if (net.cost[i] >= 0.0 && net.cost[i] < 99999.0)
                adj[net.target[i]].push_back(
                    {net.source[i], net.cost[i]});
            // The reverse direction of an edge in G (encoded as reverse_cost
            // applied to v→u traversal) becomes a forward edge u→v in G^T.
            if (net.reverse_cost[i] >= 0.0 && net.reverse_cost[i] < 99999.0)
                adj[net.source[i]].push_back(
                    {net.target[i], net.reverse_cost[i]});
        }
        return adj;
    }

    // One-to-all Dijkstra from multiple start vertices.
    // travel_budget: maximum cost to explore (seconds for time mode, meters for
    // distance). Returns cost array of size node_count (unreachable = +inf).
    inline std::vector<double>
    dijkstra(std::vector<std::vector<AdjEntry>> const &adj,
             std::vector<int32_t> const &start_vertices,
             double travel_budget, bool use_distance)
    {
        int32_t n = static_cast<int32_t>(adj.size());
        constexpr double kInf = std::numeric_limits<double>::infinity();
        std::vector<double> dist(n, kInf);
        std::vector<bool> visited(n, false);

        // min-heap: (cost, node)
        using PQEntry = std::pair<double, int32_t>;
        std::priority_queue<PQEntry, std::vector<PQEntry>, std::greater<>> pq;

        for (auto s : start_vertices)
        {
            if (s >= 0 && s < n)
            {
                dist[s] = 0.0;
                pq.push({0.0, s});
            }
        }

        while (!pq.empty())
        {
            auto [d, u] = pq.top();
            pq.pop();
            if (d >= travel_budget)
                break;
            if (visited[u])
                continue;
            visited[u] = true;

            for (auto const &[v, w] : adj[u])
            {
                // Convert cost to minutes if time-based (costs stored in seconds)
                double edge_cost = use_distance ? w : (w / 60.0);
                double new_dist = dist[u] + edge_cost;
                if (new_dist < dist[v])
                {
                    dist[v] = new_dist;
                    pq.push({new_dist, v});
                }
            }
        }
        return dist;
    }

    // Multi-source Dijkstra where each source starts with a pre-set cost.
    // Used for egress: destination stops seed the search at their transit cost.
    inline std::vector<double>
    dijkstra(std::vector<std::vector<AdjEntry>> const &adj,
             std::vector<std::pair<int32_t, double>> const &starts_with_costs,
             double travel_budget, bool use_distance)
    {
        int32_t n = static_cast<int32_t>(adj.size());
        constexpr double kInf = std::numeric_limits<double>::infinity();
        std::vector<double> dist(n, kInf);
        std::vector<bool> visited(n, false);

        using PQEntry = std::pair<double, int32_t>;
        std::priority_queue<PQEntry, std::vector<PQEntry>, std::greater<>> pq;

        for (auto const &[s, initial_cost] : starts_with_costs)
        {
            if (s >= 0 && s < n && initial_cost < travel_budget)
            {
                if (initial_cost < dist[s])
                {
                    dist[s] = initial_cost;
                    pq.push({initial_cost, s});
                }
            }
        }

        while (!pq.empty())
        {
            auto [d, u] = pq.top();
            pq.pop();
            if (d >= travel_budget)
                break;
            if (visited[u])
                continue;
            visited[u] = true;

            for (auto const &[v, w] : adj[u])
            {
                double edge_cost = use_distance ? w : (w / 60.0);
                double new_dist  = dist[u] + edge_cost;
                if (new_dist < dist[v])
                {
                    dist[v] = new_dist;
                    pq.push({new_dist, v});
                }
            }
        }
        return dist;
    }

} // namespace routing::kernel
