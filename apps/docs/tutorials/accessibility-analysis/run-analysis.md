---
sidebar_position: 4
---

# Run Catchment Analysis

Catchment areas (isochrones) show you all the areas reachable from a point within a certain time or distance. This is the core of accessibility analysis!

## Watch How It Works

<div style={{ display: 'flex', justifyContent: 'center', marginBottom: '2rem' }}>
<iframe width="674" height="378" src="https://www.youtube.com/embed/GA_6PbhAA6k?si=4mA2OdTPGCl7iVRi" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>
</div>

## Understanding Catchment Areas

A catchment area answers: **"Where can I reach from this location within X minutes?"**

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/toolbox/accessibility_indicators/catchments/wiki.png').default} alt="Catchment Area Concept" style={{ maxHeight: "350px", maxWidth: "100%", objectFit: "cover", borderRadius: "8px", boxShadow: "0 4px 12px rgba(0,0,0,0.15)"}}/>
  <p><em>Catchment areas visualize reachable zones</em></p>
</div>

## Step-by-Step Instructions

### 1. Open the Toolbox

Click on the **Toolbox** icon in the sidebar to access all analysis tools.

### 2. Select Catchment Area Tool

Navigate to **Accessibility Indicators** → **Catchment Area**

### 3. Configure Your Analysis

#### Select Starting Points
Choose your uploaded POI layer as the starting points for the analysis.

#### Choose Transport Mode

| Mode             | Best For                              | Typical Speed  |
| ---------------- | ------------------------------------- | -------------- |
| 🚶 Walking        | Short distances, pedestrian access    | 5 km/h         |
| 🚴 Cycling        | Medium distances, bike infrastructure | 15 km/h        |
| 🚗 Car            | Longer distances, road network        | Variable       |
| 🚌 Public Transit | Urban areas with transit              | Schedule-based |

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/toolbox/accessibility_indicators/catchments/walk_config_time.png').default} alt="Walking Configuration" style={{ maxHeight: "400px", maxWidth: "100%", objectFit: "cover", borderRadius: "8px", boxShadow: "0 4px 12px rgba(0,0,0,0.15)"}}/>
  <p><em>Configuring walking catchments by time</em></p>
</div>

#### Set Travel Time/Distance

For this tutorial, try:
- **5 minutes** - Very close proximity
- **10 minutes** - Comfortable walking distance
- **15 minutes** - Extended walking range

### 4. Run the Analysis

Click **Run** and watch GOAT calculate your catchments!

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/toolbox/accessibility_indicators/catchments/catchment_calculation.gif').default} alt="Catchment Calculation" style={{ maxHeight: "400px", maxWidth: "100%", objectFit: "cover", borderRadius: "8px", boxShadow: "0 4px 12px rgba(0,0,0,0.15)"}}/>
  <p><em>Catchment areas being calculated</em></p>
</div>

## Understanding the Results

Your catchment results show:
- **Polygons** representing reachable areas
- **Multiple rings** for different time thresholds
- **Attribute data** with travel times and areas

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/toolbox/accessibility_indicators/catchments/polygon_difference.png').default} alt="Polygon Results" style={{ maxHeight: "400px", maxWidth: "100%", objectFit: "cover", borderRadius: "8px", boxShadow: "0 4px 12px rgba(0,0,0,0.15)"}}/>
  <p><em>Catchment polygons with time intervals</em></p>
</div>

:::info Pro Tip
Enable **Polygon Difference** to create non-overlapping rings, making it easier to see each time band distinctly.
:::

## Next Step

Your catchments are calculated! Now let's [style them beautifully](./style-results).

---

**Progress:** 3 of 5 steps completed
