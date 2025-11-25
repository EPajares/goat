---
sidebar_position: 1
 
---
 
# Walk
 
The **Walk Routing** is used for all analyses in GOAT that contain walking trips. 

 
## 1. Objectives

Walk routing is used for many indicators in GOAT, such as [Catchment Areas](../toolbox/accessibility_indicators/catchments "Visit Docs on Catchment Areas"), [Heatmaps](../toolbox/accessibility_indicators/connectivity "Visit Docs on Heatmaps"), and [PT Nearby Stations](../toolbox/accessibility_indicators/nearby_stations "Visit Docs on PT Nearby Stations"). As GOAT also allows the creation of [Scenarios on the Street Network](../scenarios#4-street-network---edges), a **custom routing algorithm** is needed that also reflects the changes of the scenario in the accessibility analyses. For the mode of walking, we thereby **only consider paths that are suitable for pedestrians**. The walking `speed` can be adjusted by the user whenever an accessibility analysis is performed. 

## 2. Data

### Routing Network

Data from the **[Overture Maps Foundation](https://overturemaps.org/)** is used as a routing network in GOAT. It includes the transportation infrastructure with **edges** (for any continuous path not bisected by another) and **nodes** (for any point where two distinct paths intersect), representing real-world networks.


## 3. Technical Details

### Data Pre-processing

The following steps are performed on the data to enable **quick** and **accurate** routing for walking:

 1. **Attribute Parsing:** Categorizing attributes of edges (road `class`).
 2. **Geospatial Indexing:**  Utilizing **[Uber's H3 grid-based](../further_reading/glossary#h3-grid)** indexing for efficient routing.


### Routing Process Steps

#### Sub-network Extraction

1. **Buffer Region:** Based on user-origin, travel time, and speed.
2. **Edge Filtering:**  Include only relevant edges for walking.

For pedestrian routing, the edges of the following road classes are considered:

`secondary`, `tertiary`, `residential`, `living_street`, `trunk`, `unclassified`, `parking_aisle`, `driveway`, `alley`, `pedestrian`, `footway`, `sidewalk`, `crosswalk`, `steps`, `track`, `bridleway` and `unknown`.

You can find further information on this classification in the [Overture Wiki](https://docs.overturemaps.org/schema/reference/transportation/segment).

#### Artificial Edge Creation

User-provided origin points are typically located a short distance away from the street network. To account for the additional time (or cost) of walking from the origin to its nearest street, artificial (or simulated) edges are created.

#### Edge Cost Computation

For all edges in the sub-network, a cost value (represented as time) is calculated based on path length and walking speed.
The cost function for walking:
`cost = length / speed`

#### Network Propagation

To compute the shortest path from the origin point to various destinations, a custom implementation of the well-known [Dijkstra Algorithm](https://en.wikipedia.org/wiki/Dijkstra%27s_algorithm) is used.


<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/routing/walk/dijkstra.gif').default}  alt="Dijkstra Algorithm" style={{ width: "auto", height: "auto", objectFit: "cover"}}/>
<p style={{ textAlign: 'center' }}>GIF: <a href="https://en.wikipedia.org/wiki/Dijkstra%27s_algorithm">Dijkstra Algorithm</a></p>
</div>

The implementation has a time complexity of *O(ElogV)*, is written in **Python**, and uses the just-in-time compiler **Numba**.

