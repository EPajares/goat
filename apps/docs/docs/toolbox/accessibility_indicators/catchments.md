---
sidebar_position: 1
---

import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';
import thematicIcon from "/img/toolbox/data_management/join/toolbox.webp";


# Catchment Area

Catchment Areas show **how far people can travel within a certain travel time or distance, using one or more transport modes.**

<div style={{ display: 'flex', justifyContent: 'center' }}>
<iframe width="674" height="378" src="https://www.youtube.com/embed/_clsR386b9w?si=ZInxlY_TjYiEda23" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>
</div>

## 1. Explanation

Based on specified starting point(s), maximum travel time or distance, and transport mode(s), **Catchment Areas visualize accessibility extent using real-world data.** This provides insights into transport network quality, density, and extensiveness.

The catchment area can be intersected with spatial datasets, such as population data, to assess reachable amenities and identify accessibility coverage for inhabitants.

import MapViewer from '@site/src/components/MapViewer';

:::info 
Catchment Area computation is available in specific regions.

When selecting a <code>Routing type</code>, GOAT displays a map overlay showing coverage.
For <code>Walk</code>, <code>Bicycle</code>, <code>Pedelec</code>, and <code>Car</code>: over 30 European countries are supported.
For <code>Public Transport</code>: Germany is supported.

<div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '20px', flexWrap: "nowrap", maxWidth: '100%', padding: '0 20px' }}>
  <div style={{ flex: '1', maxWidth: 'none', minWidth: '0' }}>
    <MapViewer
        geojsonUrls={[
          "https://assets.plan4better.de/other/geofence/geofence_street.geojson"
        ]}
        styleOptions={{
          fillColor: "#808080",
          outlineColor: "#808080",
          fillOpacity: 0.8
        }}
        legendItems={[
          { label: "Coverage for Walk, Bicycle, Pedelec & Car", color: "#ffffff" }
        ]}
    />
  </div>
  <div style={{ flex: '1', maxWidth: 'none', minWidth: '0' }}>
    <MapViewer
        geojsonUrls={[
          "https://assets.plan4better.de/other/geofence/geofence_gtfs.geojson"
        ]}
        styleOptions={{
          fillColor: "#808080",
          outlineColor: "#808080",
          fillOpacity: 0.8
        }}
        legendItems={[
          { label: "Coverage for Public Transport", color: "#ffffff" }
        ]}
    />
  </div>
</div>

<br />

If you need analyses beyond these regions, feel free to [contact us](https://plan4better.de/en/contact/) and we'll discuss further options.
:::

## 2. Example use cases

- Which amenities are reachable within a 15-minute walk?
- How many inhabitants have access to supermarkets within 10 minutes by bicycle?
- What share of the population has a general practitioner within 500m?
- How do workplace catchment areas compare between car and public transport? How many employees live within these areas? 
- How well are kindergartens distributed citywide? Which districts have accessibility deficits?


## 3. How to use the indicator?

<div class="step">
  <div class="step-number">1</div>
  <div class="content">Click on <code>Toolbox</code> <img src={thematicIcon} alt="toolbox" style={{width: "25px"}}/>.</div>
</div>

<div class="step">
  <div class="step-number">2</div>
  <div class="content">Under <code>Accessibility Indicators</code>, click on <code>Catchment Area</code>.</div>
</div>

### Routing

<div class="step">
  <div class="step-number">3</div>
  <div class="content">Select the <code>Routing Type</code> for your catchment area calculation.</div>
</div>

### Configuration

<Tabs>
<TabItem value="walk" label="Walk" default className="tabItemBox">

**Considers all paths accessible by foot.**

  <div class="step">
    <div class="step-number">4</div>
    <div class="content">Choose whether to calculate the catchment area <strong>based on time or distance</strong>.</div>
  </div>

  <Tabs>
  <TabItem value="time" label="Time" default className="tabItemBox">

  #### Time

  <div class="step">
    <div class="step-number">5</div>
    <div class="content">Configure <code>Travel time limit</code>, <code>Travel speed</code>, and <code>Number of breaks</code>.</div>
  </div>

  <img src={require('/img/toolbox/accessibility_indicators/catchments/walk_config_time.png').default} alt="walking-time configurations" style={{ maxHeight: "300px", maxWidth: "300px"}}/>

:::tip Hint

For suitable travel time limits by amenity type, see the [Location Tool](https://www.chemnitz.de/chemnitz/media/unsere-stadt/verkehr/verkehrsplanung/vep2040_standortwerkzeug.pdf) from the City of Chemnitz.

:::
  </TabItem>
  
  <TabItem value="distance" label="Distance" default className="tabItemBox">

  #### Distance

  <div class="step">
    <div class="step-number">5</div>
    <div class="content">Set the configurations for <code>Travel distance</code> and <code> Number of breaks</code>.</div>
  </div>

  <img src={require('/img/toolbox/accessibility_indicators/catchments/walk_config_distance.png').default} alt="walking-distance configurations" style={{ maxHeight: "300px", maxWidth: "300px"}}/>
  
  </TabItem>
  </Tabs>
</TabItem>

<TabItem value="cycling" label="Bicycle/Pedelec" className="tabItemBox">

**Considers all bicycle-accessible paths.** This routing mode accounts for surface, smoothness, and slope while computing accessibility. For Pedelec, slopes have lower impedance than standard bicycles.

<div class="step">
  <div class="step-number">4</div>
  <div class="content">Choose whether to calculate the catchment area <strong>based on time or distance</strong>.</div>
</div>

  <Tabs>
  <TabItem value="time" label="Time" default className="tabItemBox">

  #### Time

  <div class="step">
    <div class="step-number">5</div>
    <div class="content">Set the configurations for <code>Travel time limit</code>, <code>Travel speed</code>, and <code> Number of breaks</code>.</div>
  </div>

  <img src={require('/img/toolbox/accessibility_indicators/catchments/walk_config_time.png').default} alt="walking-time configurations" style={{ maxHeight: "300px", maxWidth: "300px"}}/>

:::tip Hint

For suitable travel time limits by amenity type, see the [Location Tool](https://www.chemnitz.de/chemnitz/media/unsere-stadt/verkehr/verkehrsplanung/vep2040_standortwerkzeug.pdf) from the City of Chemnitz.

:::

  </TabItem>
  
  <TabItem value="distance" label="Distance" default className="tabItemBox">

  #### Distance

  <div class="step">
    <div class="step-number">5</div>
    <div class="content">Set the configurations for <code>Travel distance</code> and <code> Number of breaks</code>.</div>
  </div>

  <img src={require('/img/toolbox/accessibility_indicators/catchments/walk_config_distance.png').default} alt="walking-distance configurations" style={{ maxHeight: "300px", maxWidth: "300px"}}/>

  </TabItem>

  </Tabs>

  </TabItem>

  <TabItem value="car" label="Car" className="tabItemBox">

 **Considers all car-accessible paths.** This routing mode accounts for speed limits and one-way restrictions while computing accessibility.

  <div class="step">
    <div class="step-number">4</div>
    <div class="content">Choose whether to calculate the catchment area <strong> based on time or distance</strong>.</div>
  </div>

  <Tabs>
  <TabItem value="time" label="Time" default className="tabItemBox">

  #### Time

  <div class="step">
    <div class="step-number">5</div>
    <div class="content">Set the configurations for <code>Travel time limit</code> and <code> Number of breaks</code>.</div>
  </div>

  <img src={require('/img/toolbox/accessibility_indicators/catchments/walk_config_time.png').default} alt="travel-time configurations" style={{ maxHeight: "300px", maxWidth: "300px"}}/>

:::tip Hint

For suitable travel time limits by amenity type, see the [Location Tool](https://www.chemnitz.de/chemnitz/media/unsere-stadt/verkehr/verkehrsplanung/vep2040_standortwerkzeug.pdf) from the City of Chemnitz.

:::

  </TabItem>
  <TabItem value="distance" label="Distance" default className="tabItemBox">

#### Distance

<div class="step">
  <div class="step-number">5</div>
  <div class="content">Set the configurations for <code>Travel distance</code> and <code> Number of breaks</code>.</div>
</div>

<img src={require('/img/toolbox/accessibility_indicators/catchments/walk_config_distance.png').default} alt="travel-distance configurations" style={{ maxHeight: "300px", maxWidth: "300px"}}/>

  </TabItem>
</Tabs>

  </TabItem>
  <TabItem value="public transport" label="Public Transport (PT)" className="tabItemBox">

**Considers all locations accessible by public transport, including inter-modal transfers and station access.**

<div class="step">
  <div class="step-number">4</div>
  <div class="content">Select the <code>Public transport modes</code> to analyze: Bus, Tram, Rail, Subway, Ferry, Cable Car, Gondola, and/or Funicular.</div>
</div>

<div>
  <img src={require('/img/toolbox/accessibility_indicators/catchments/pt_type.png').default} alt="Public Transport Modes in GOAT" style={{ maxHeight: "400px", maxWidth: "400px", objectFit: "cover"}}/>
</div>

<br />

<div class="step">
  <div class="step-number">5</div>
  <div class="content"> 
  <p>
  Configure the following parameters: <code>Travel time limit</code>, <code>Number of breaks</code>, <code>Day</code>, and <code>Start Time</code> and <code>End Time</code>.
    </p>
  </div>
</div>

<img src={require('/img/toolbox/accessibility_indicators/catchments/pt_config.png').default} alt="Public Transport Configurations" style={{ maxHeight: "400px", maxWidth: "400px"}}/>


:::tip Hint

For suitable travel time limits by amenity type, see the [Location Tool](https://www.chemnitz.de/chemnitz/media/unsere-stadt/verkehr/verkehrsplanung/vep2040_standortwerkzeug.pdf) from the City of Chemnitz.

:::


  </TabItem>

</Tabs>


### Advanced Configuration

  By default, catchment areas are calculated as polygons. To adjust this, use the advanced configurations.

  <div class="step">
    <div class="step-number">6</div>
    <div class="content">Click on <code>Advanced Configurations</code> <img src={require('/img/map/styling/options_icon.png').default} alt="Options Icon" style={{ maxHeight: "25px", maxWidth: "25px", objectFit: "cover"}}/> button. Here you can select the <code>Catchment area shape</code>. You can choose between <b>Polygon</b>, <b>Network</b> and <b>Rectangular Grid</b>.</div>
  </div>

<Tabs>
  <TabItem value="Polygon" label="Polygon" default className="tabItemBox">

- It is a **geometric representation** of the catchments.
- **Easy-to-understand** visualization
- **One polygon per step**

<img src={require('/img/toolbox/accessibility_indicators/catchments/pt_polygon.png').default} alt="Catchment Area Shape (Polygon) Public Transport in GOAT" style={{ maxHeight: "300px", maxWidth: "300px"}}/>

You can choose <code>Polygon Difference</code> **enabled** which creates an "incremental" polygons for each step. On the other hand, **disabled** creates "full" polygons including all previous steps.

  </TabItem>
  <TabItem value="Network" label="Network" className="tabItemBox">

- It is a **street-level representation** of the catchments.
- Enables **easy correlation to actual streets** and their accessibility within the catchment area.
- **Fine-grained detail** compared to the other catchment types.

<img src={require('/img/toolbox/accessibility_indicators/catchments/pt_network.png').default} alt="Catchment Area Shape (Network) Public Transport in GOAT" style={{ maxHeight: "300px", maxWidth: "300px"}}/>

  </TabItem>
  <TabItem value="Rectangular Grid" label="Rectangular Grid" className="tabItemBox">

- It is a **grid cell-based** representation of the catchments.
- Appears **similar to a “heatmap” visualization**, however, differs conceptually & computationally (this represents egress from a specified origin to various other locations while heatmaps represent access from various locations to a specified destination).

<img src={require('/img/toolbox/accessibility_indicators/catchments/pt_grid.png').default} alt="Catchment Area Shape (Grid) Public Transport in GOAT" style={{ maxHeight: "300px", maxWidth: "300px"}}/>

  </TabItem>
</Tabs>

### Starting Points

<div class="step">
  <div class="step-number">7</div>
  <div class="content">Select the <code>Starting point method</code>: <code>Select on map</code> or <code>Select from layer</code>.</div>
</div>

<Tabs>
  <TabItem value="Select on Map" label="Select on Map" default className="tabItemBox">

<div class="step">
  <div class="step-number">8</div>
  <div class="content">Choose <code>Select on map</code>. Click on the map to select starting point(s). You can add multiple starting points.</div>
</div>


  </TabItem>
  <TabItem value="Select From Layer" label="Select From Layer" className="tabItemBox">


 <div class="step">
  <div class="step-number">8</div>
  <div class="content">Click on <code>Select from layer</code>. Choose the <code>Point layer</code> containing your desired starting point(s).</div>
</div>


  </TabItem>
</Tabs>


<div class="step">
  <div class="step-number">9</div>
  <div class="content">Click on <code>Run</code>. This starts the catchment area calculation from the selected starting point(s).</div>
</div>

:::tip Hint

Calculation time varies by settings. Check the [status bar](../../workspace/home#status-bar) for progress.

:::

### Results

Once calculation finishes, the resulting layers are added to the map. The **"Catchment Area"** layer contains the calculated catchments. If starting points were created by map clicking, they're saved in the **"Starting Points"** layer.

Click on a catchment polygon to view details. The **travel_cost** attribute shows travel distance or time based on your calculation unit: **time in minutes** or **distance in meters**.

<div style={{ display: 'flex', justifyContent: 'center' }}>
<img src={require('/img/toolbox/accessibility_indicators/catchments/catchment_calculation.gif').default} alt="Catchment Area Calculation Result in GOAT" style={{ maxHeight: "auto", maxWidth: "80%"}}/>
</div>

## 4. Technical details

**Catchment areas are isolines connecting points reachable from starting point(s) within a time interval (*isochrones*) or distance (*isodistance*)**. The calculation uses the appropriate transport networks for routing based on the selected travel mode.

Catchment areas are dynamically created in the frontend from a travel time/distance grid, enabling fast creation with different intervals on-demand.

:::tip Hint

For further insights into the Routing algorithm, visit [Routing](../../rcategory/routing).

:::

### Scientific background

Catchments are *contour-based measures* (also *cumulative opportunities*), valued for their **easily interpretable results** ([Geurs and van Eck 2001](#6-references); [Albacete 2016](#6-references)). However, they don't distinguish between different travel times within the **cut-off range** ([Bertolini, le Clercq, and Kapoen 2005](#6-references)), unlike [heatmaps](../accessibility_indicators/closest_average.md).

### Visualization 

The catchment shape derives from the routing grid using the [Marching square contour line algorithm](https://en.wikipedia.org/wiki/Marching_squares), a computer graphics algorithm generating 2D contour lines from rectangular value arrays ([de Queiroz Neto et al. 2016](#6-references)). This transforms the grid from a 2D array to a shape for visualization or analysis. 

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/toolbox/accessibility_indicators/catchments/wiki.png').default} width="1000px" alt="marching square" style={{ width: "1000px", height: "400px", maxHeight: "400px", maxWidth: "400px", objectFit: "contain"}}/>
</div> 

## 5. Further readings

Further insights into catchment calculation and scientific background: [this publication](https://doi.org/10.1016/j.jtrangeo.2021.103080).

## 6. References

Albacete, Xavier. 2016. “Evaluation and Improvements of Contour-Based Accessibility Measures.” url: https://dspace.uef.fi/bitstream/handle/123456789/16857/urn_isbn_978-952-61-2103-1.pdf?sequence=1&isAllowed=y 

Bertolini, Luca, F. le Clercq, and L. Kapoen. 2005. “Sustainable Accessibility: A Conceptual Framework to Integrate Transport and Land Use Plan-Making. Two Test-Applications in the Netherlands and a Reflection on the Way Forward.” Transport Policy 12 (3): 207–20. https://doi.org/10.1016/j.tranpol.2005.01.006.

J. F. de Queiroz Neto, E. M. d. Santos, and C. A. Vidal. “MSKDE - Using
Marching Squares to Quickly Make High Quality Crime Hotspot Maps”. en.
In: 2016 29th SIBGRAPI Conference on Graphics, Patterns and Images (SIBGRAPI).
Sao Paulo, Brazil: IEEE, Oct. 2016, pp. 305–312. isbn: 978-1-5090-3568-7. doi:
10.1109/SIBGRAPI.2016.049. url: https://ieeexplore.ieee.org/document/7813048

https://fr.wikipedia.org/wiki/Marching_squares#/media/Fichier:Marching_Squares_Isoline.svg

Majk Shkurti, "Spatio-temporal public transport accessibility analysis and benchmarking in an interactive WebGIS", Sep 2022. url: https://www.researchgate.net/publication/365790691_Spatio-temporal_public_transport_accessibility_analysis_and_benchmarking_in_an_interactive_WebGIS 

Matthew Wigginton Conway, Andrew Byrd, Marco Van Der Linden. "Evidence-Based Transit and Land Use Sketch Planning Using Interactive Accessibility Methods on Combined Schedule and Headway-Based Networks", 2017. url: https://journals.sagepub.com/doi/10.3141/2653-06

Geurs, Karst T., and Ritsema van Eck. 2001. “Accessibility Measures: Review and Applications.” RIVM Report 408505 006. url: https://rivm.openrepository.com/handle/10029/259808