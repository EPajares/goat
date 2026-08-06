---
sidebar_position: 2

---

# Bicycle/Pedelec


The **Bicycle/Pedelec Routing** is used for all analyses in GOAT that contain cycling trips. 


 
## 1. Objectives

Bicycle/Pedelec routing is used for many indicators in GOAT, such as [Catchment Areas](../toolbox/accessibility_indicators/catchments "Visit Docs on Catchment Areas"), [Heatmaps](../toolbox/accessibility_indicators/connectivity "Visit Docs on Heatmaps") and [PT Nearby Stations](../toolbox/accessibility_indicators/nearby_stations "Visit Docs on PT Nearby Stations"). As GOAT also allows the creation of [Scenarios on the Street Network](../scenarios#4-street-network---edges), a **custom routing algorithm** is needed that also reflects the changes of the scenario in the accessibility analyses. For the mode of bicycle/pedelec, we thereby **only consider paths that are suitable for cycling**. Furthermore, the `surface` and `slope` have an impact on the cycling speed and are therefore considered in the routing. The average cycling `speed` can be adjusted by the user whenever an accessibility analysis is performed. Depending on the slope and surface of a path segment, the speed is adjusted accordingly. 


## 2. Data

### Routing Network

Data from the **[Overture Maps Foundation](https://overturemaps.org/)** is used as a routing network in GOAT. It includes the transportation infrastructure with **edges** (for any continuous path not bisected by another) and **nodes** (for any point where two distinct paths intersect), representing real-world networks.


### Topography and Elevation

Elevation data is sourced from **[Copernicus](https://www.copernicus.eu/en)** as **Digital Elevation Model (DEM)** tiles.


## 3. Technical Details

### Data Pre-processing

The following steps are performed on the data to enable **quick** and **accurate** routing for bicycle/pedelec:

 1. **Attribute Parsing:** Categorizing attributes of edges (street `class` and `surface`).
 2. **Geospatial Indexing:**  Utilizing **[Uber's H3 grid-based](../further_reading/glossary#h3-grid)** indexing for efficient routing.
 3. **Surface Impedance Computation:** Calculating impedance considering surface properties.
 4. **Slope Impedance Computation:** Overlaying DEM on edges to compute slope profiles.


### Routing Process Steps

#### Sub-network Extraction

1. **Buffer Region:** Based on user-origin, travel time, and speed.
2. **Edge Filtering:**  Include only relevant edges for cycling.

For bicycle/pedelec routing, the edges of the following street classes are considered:

`secondary`, `tertiary`, `residential`, `living_street`, `trunk`, `unclassified`, `parking_aisle`, `driveway`, `alley`, `pedestrian`, `crosswalk`, `track`, `cycleway`, `bridleway` and `unknown`.

You can find further information on this classification in the [Overture Wiki](https://docs.overturemaps.org/schema/reference/transportation/segment).

#### Artificial Edge Creation

User-provided origin points are typically located a short distance away from the street network. To account for the additional time (or cost) of cycling from the origin to its nearest street, artificial (or simulated) edges are created.

#### Edge Cost Computation

For all edges in the sub-network, a cost value (represented as time) is calculated based on path length and cycling speed.

Cost function for **bicycle**:
`cost = (length * (1 + slope impedance + surface impedance)) / speed`

Cost function for **pedelec**:
`cost = (length * (1 + surface impedance)) / speed`

If an edge is of class `pedestrian` or `crosswalk`, we assume the rider would dismount and walk their bicycle/pedelec. The cost for this type of segment is: `cost = length / speed`

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', marginBottom: '0.75rem' }}>
  <img src={require('/img/routing/bicycle_edge_cost.png').default} alt="Cycling network edge cost by topology — surface and slope multipliers" style={{ maxWidth: "100%", objectFit: "contain"}}/>
</div>

:::note
Cost multiplier values are illustrative examples. Actual impedance values vary depending on the specific surface type and slope gradient of each path segment.
:::

#### Network Propagation

To compute the shortest path from the origin point to various destinations, a custom implementation of the well-known [Dijkstra Algorithm](https://en.wikipedia.org/wiki/Dijkstra%27s_algorithm) is used.


<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/routing/walk/dijkstra.gif').default}  alt="Dijkstra Algorithm" style={{ width: "auto", height: "auto", objectFit: "cover"}}/>
<p style={{ textAlign: 'center' }}>GIF: <a href="https://en.wikipedia.org/wiki/Dijkstra%27s_algorithm">Dijkstra Algorithm</a></p>
</div>


The implementation has a time complexity of *O(ElogV)*, is written in **Python**, and uses the just-in-time compiler **Numba**.


## 4. Further Readings

- E. Pajares, B. Büttner, U. Jehle, A. Nichols, and G. Wulfhorst, ‘Accessibility by proximity: Addressing the lack of interactive accessibility instruments for active mobility’, *Journal of Transport Geography*, Vol. 93, p. 103080, May 2021, [doi: 10.1016/j.jtrangeo.2021.103080](https://doi.org/10.1016/j.jtrangeo.2021.103080).
