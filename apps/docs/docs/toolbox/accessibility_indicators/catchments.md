---
sidebar_position: 1
---

import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';
import thematicIcon from "/img/toolbox/data_management/join/toolbox.webp";


# Catchment Area

**Catchment Areas** show how far people can travel within a certain travel time or distance, using one or more modes of transport.

<iframe width="100%" height="500" src="https://www.youtube.com/embed/AhQXTjxjhZY?si=cWaLkivPtvWNAByW" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>

## 1. Explanation

Based on the specified starting point(s), maximum travel time or distance, and mode(s) of transport, **Catchment Areas** visualize the extent of accessibility. This is calculated using **real-world data** and provides useful insights into the quality, density, and extensiveness of an area's transport network.

Furthermore, the catchment area can be intersected with spatial datasets, such as population and [POI](../../further_reading/glossary#point-of-interest-poi "What is a POI?") data. This allows you to assess - for example - how many POIs can be reached from a certain location and therefore identify what share of inhabitants has access to important amenities within a specific travel time.

![Catchment Area in GOAT](/img/toolbox/accessibility_indicators/catchments/catchment_sample.png "Catchment Area in GOAT")
  

:::tip Hint
You might know this feature from our previous software versions under the terms *Single-Isochrone* and *Multi-Isochrone*. With the release of GOAT version 2.0, we combined these two indicators in the same flow and enriched it with further calculation options. 
:::

import MapViewer from '@site/src/components/MapViewer';


:::info 
The computation of Catchment Areas is possible in specific regions.

Upon selecting a <code>Routing type</code>, GOAT will display a map overlay indicating this.
For <code>Walk</code>, <code>Bicycle</code>, <code>Pedelec</code>, and <code>Car</code>, over 30 European countries are supported, while <code>Public Transport</code> Catchment Areas may be computed for Germany.




<div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '20px', flexWrap: "wrap" }}>
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

<br />

If you need to perform analyses beyond these regions, feel free to [contact us](https://plan4better.de/en/contact/ "contact us") and we would be happy to discuss further options.
:::

## 2. Example use cases

- Which amenities can be reached from a certain point in a 15-minute walk?
- How many inhabitants have access to a supermarket within 10 minutes of cycling?
- What share of the population has a general practitioner (GP) within 500m distance?
- How big is the catchment area of a workplace by car vs. by public transport? How many employees live within these catchment areas? 
- How well are kindergartens currently distributed across the city? In which districts are there accessibility deficits?


## 3. How to use the indicator?

<div class="step">
  <div class="step-number">1</div>
  <div class="content">Click on <code>Toolbox</code> <img src={thematicIcon} alt="toolbox" style={{width: "25px"}}/>. </div>
</div>

<div class="step">
  <div class="step-number">2</div>
  <div class="content">Under the <code>Accessibility Indicators</code> menu, click on <code>Catchment Area</code>.</div>
</div>

### Routing


<div class="step">
  <div class="step-number">3</div>
  <div class="content">Pick for which <code>Routing Type</code> you would like to calculate a catchment area.</div>
</div>


### Configuration

<Tabs>
  <TabItem value="walk" label="Walk" default className="tabItemBox">

#### Walk

Considers all paths accessible by foot.

:::tip Hint

For further insights into the Routing algorithm, visit [Routing/Walk](../../routing/walking).

:::

<div class="step">
  <div class="step-number">4</div>
  <div class="content">Pick if you like to calculate the catchment area based on <b>time</b> or <b>distance</b>.</div>
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

For defining which travel time limits are suitable for which amenity, the ["Standort-Werkzeug"](https://www.chemnitz.de/chemnitz/media/unsere-stadt/verkehr/verkehrsplanung/vep2040_standortwerkzeug.pdf) of the City of Chemnitz can provide helpful guidance.

:::

#### Advanced Configurations

Per default, the catchment areas are calculated in polygon shape. In case you want to adjust that, you find further options in the advanced configurations. 

<div class="step">
  <div class="step-number">6</div>
  <div class="content">Click on <b>options button</b> <img src={require('/img/map/styling/options_icon.png').default} alt="Options Icon" style={{ maxHeight: "25px", maxWidth: "25px", objectFit: "cover"}}/>. Here you can select the <code> Catchment area shape</code>. You can choose between <b>Polygon</b>, <b>Network</b> and <b>Rectangular Grid</b>.</div>
</div>

  </TabItem>
  <TabItem value="distance" label="Distance" default className="tabItemBox">

#### Distance

<div class="step">
  <div class="step-number">5</div>
  <div class="content">Set the configurations for <code>Travel distance</code> and <code> Number of breaks</code>.</div>
</div>

<img src={require('/img/toolbox/accessibility_indicators/catchments/walk_config_distance.png').default} alt="walking-distance configurations" style={{ maxHeight: "300px", maxWidth: "300px"}}/>

:::tip Hint

For defining which travel distances are suitable for which amenity, the ["Standort-Werkzeug"](https://www.chemnitz.de/chemnitz/media/unsere-stadt/verkehr/verkehrsplanung/vep2040_standortwerkzeug.pdf) of the City of Chemnitz can provide helpful guidance.

:::


#### Advanced Configurations

Per default, the catchment areas are calculated in polygon shape. In case you want to adjust that, you find further options in the advanced configurations. 

<div class="step">
  <div class="step-number">6</div>
  <div class="content">Click on <b>options button</b> <img src={require('/img/map/styling/options_icon.png').default} alt="Options Icon" style={{ maxHeight: "25px", maxWidth: "25px", objectFit: "cover"}}/>. Here you can select the <code> Catchment area shape</code>. You can choose between <b>Polygon</b>, <b>Network</b> and <b>Rectangular Grid</b>.</div>
</div>

  </TabItem>

</Tabs>

  </TabItem>
  <TabItem value="cycling" label="Bicycle/Pedelec" className="tabItemBox">

    
#### Bicycle/Pedelec

Considers all paths accessible by bicycle. This routing mode takes into account the surface, smoothness, and slope of streets while computing accessibility. For Pedelec, slopes are considered with a lower impedance than for standard bicycles.

:::tip Hint

For further insights into the Routing algorithm, visit [Routing/Bicycle](../../routing/bicycle). In addition, you can check this [Publication](https://doi.org/10.1016/j.jtrangeo.2021.103080).

:::

<div class="step">
  <div class="step-number">4</div>
  <div class="content">Pick if you like to calculate the catchment area based on <b>time</b> or <b>distance</b>.</div>
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

For defining which travel time limits are suitable for which amenity, the ["Standort-Werkzeug"](https://www.chemnitz.de/chemnitz/media/unsere-stadt/verkehr/verkehrsplanung/vep2040_standortwerkzeug.pdf) of the City of Chemnitz can provide helpful guidance.

:::


#### Advanced Configurations

Per default, the catchment areas are calculated in polygon shape. In case you want to adjust that, you find further options in the advanced configurations. 

<div class="step">
  <div class="step-number">6</div>
  <div class="content">Click on <b>options button</b> <img src={require('/img/map/styling/options_icon.png').default} alt="Options Icon" style={{ maxHeight: "25px", maxWidth: "25px", objectFit: "cover"}}/>. Here you can select the <code> Catchment area shape</code>. You can choose between <b>Polygon</b>, <b>Network</b> and <b>Rectangular Grid</b>.</div>
</div>

  </TabItem>
  <TabItem value="distance" label="Distance" default className="tabItemBox">

#### Distance

<div class="step">
  <div class="step-number">5</div>
  <div class="content">Set the configurations for <code>Travel distance</code> and <code> Number of breaks</code>.</div>
</div>

<img src={require('/img/toolbox/accessibility_indicators/catchments/walk_config_distance.png').default} alt="walking-distance configurations" style={{ maxHeight: "300px", maxWidth: "300px"}}/>

:::tip Hint

For defining which travel distances are suitable for which amenity, the ["Standort-Werkzeug"](https://www.chemnitz.de/chemnitz/media/unsere-stadt/verkehr/verkehrsplanung/vep2040_standortwerkzeug.pdf) of the City of Chemnitz can provide helpful guidance.

:::


#### Advanced Configurations

Per default, the catchment areas are calculated in polygon shape. In case you want to adjust that, you find further options in the advanced configurations. 

<div class="step">
  <div class="step-number">6</div>
  <div class="content">Click on <b>options button</b> <img src={require('/img/map/styling/options_icon.png').default} alt="Options Icon" style={{ maxHeight: "25px", maxWidth: "25px", objectFit: "cover"}}/>. Here you can select the <code> Catchment area shape</code>. You can choose between <b>Polygon</b>, <b>Network</b> and <b>Rectangular Grid</b>.</div>
</div>

  </TabItem>

</Tabs>


  </TabItem>

  <TabItem value="car" label="Car" className="tabItemBox">

#### Car

Considers all paths accessible by car. This routing mode takes into account speed limits and one-way access restrictions while computing accessibility.

:::tip Hint

For further insights into the Routing algorithm, visit [Routing/Car](../../routing/car).

:::

<div class="step">
  <div class="step-number">4</div>
  <div class="content">Pick if you like to calculate the catchment area based on <b>time</b> or <b>distance</b>.</div>
</div>

<Tabs>
  <TabItem value="time" label="Time" default className="tabItemBox">

#### Time

<div class="step">
  <div class="step-number">5</div>
  <div class="content">Set the configurations for <code>Travel time limit</code> and <code> Number of breaks</code>.</div>
</div>

<img src={require('/img/toolbox/accessibility_indicators/catchments/walk_config_time.png').default} alt="travel-time configurations" style={{ maxHeight: "300px", maxWidth: "300px"}}/>



#### Advanced Configurations

Per default, the catchment areas are calculated in polygon shape. In case you want to adjust that, you find further options in the advanced configurations. 

<div class="step">
  <div class="step-number">6</div>
  <div class="content">Click on <b>options button</b> <img src={require('/img/map/styling/options_icon.png').default} alt="Options Icon" style={{ maxHeight: "25px", maxWidth: "25px", objectFit: "cover"}}/>. Here you can select the <code> Catchment area shape</code>. You can choose between <b>Polygon</b>, <b>Network</b> and <b>Rectangular Grid</b>.</div>
</div>

  </TabItem>
  <TabItem value="distance" label="Distance" default className="tabItemBox">

#### Distance

<div class="step">
  <div class="step-number">5</div>
  <div class="content">Set the configurations for <code>Travel distance</code> and <code> Number of breaks</code>.</div>
</div>

<img src={require('/img/toolbox/accessibility_indicators/catchments/walk_config_distance.png').default} alt="travel-distance configurations" style={{ maxHeight: "300px", maxWidth: "300px"}}/>



#### Advanced Configurations

Per default, the catchment areas are calculated in polygon shape. In case you want to adjust that, you find further options in the advanced configurations. 

<div class="step">
  <div class="step-number">6</div>
  <div class="content">Click on <b>options button</b> <img src={require('/img/map/styling/options_icon.png').default} alt="Options Icon" style={{ maxHeight: "25px", maxWidth: "25px", objectFit: "cover"}}/>. Here you can select the <code> Catchment area shape</code>. You can choose between <b>Polygon</b>, <b>Network</b> and <b>Rectangular Grid</b>.</div>
</div>

  </TabItem>
</Tabs>

  </TabItem>
  <TabItem value="public transport" label="Public Transport (PT)" className="tabItemBox">

#### Public Transport (PT)

Considers all locations accessible by public transport. This routing mode considers inter-modal transfers including access to and from stations.


:::tip Hint

For further insights into the Routing algorithm, visit [Routing/Public Transport](../../routing/public_transport).

:::

<div class="step">
  <div class="step-number">4</div>
  <div class="content">Select the <code>Public transport modes</code> you want to analyze (<i>Bus, Tram, Rail, Subway, Ferry, Cable Car, Gondola</i> and/or <i>Funicular</i>).</div>
</div>

<div>
  <img src={require('/img/toolbox/accessibility_indicators/catchments/pt_type.png').default} alt="Public Transport Modes in GOAT" style={{ maxHeight: "400px", maxWidth: "400px", objectFit: "cover"}}/>
</div>

<br />

<div class="step">
  <div class="step-number">5</div>
  <div class="content">
    <code>Travel time limit</code> - the maximum allowed duration of journeys considered for the analysis
    <br />
    <code>Number of breaks</code> - determines the resolution of the resulting catchment area isochrone
    <br />
    <code>Day</code> - the weekday type on which the analysis is performed: <i>Weekday, Saturday</i> or <i>Sunday</i>
    <br />
    <code>Start Time</code> and <code>End Time</code> - the fastest possible journeys within this time window are considered for the analysis
    <br />
    <p>
      Read more about routing options {" "}
      <a href="../../routing/public_transport#routing-options">here</a>.
    </p>
  </div>
</div>

<img src={require('/img/toolbox/accessibility_indicators/catchments/pt_config.png').default} alt="Public Transport Configurations" style={{ maxHeight: "400px", maxWidth: "400px"}}/>

:::tip Hint

The ["Standort-Werkzeug"](https://www.chemnitz.de/chemnitz/media/unsere-stadt/verkehr/verkehrsplanung/vep2040_standortwerkzeug.pdf) of the City of Chemnitz can provide helpful guidance on suitable travel time limits for assessing accessibility to various amenities.

:::


#### Advanced Configurations

Per default, the catchment areas are calculated in polygon shape. In case you want to adjust that, you find further options in the advanced configurations. 

<div class="step">
  <div class="step-number">6</div>
  <div class="content">Click on <b>options button</b> <img src={require('/img/map/styling/options_icon.png').default} alt="Options Icon" style={{ maxHeight: "25px", maxWidth: "25px", objectFit: "cover"}}/>. Here you can select the <code> Catchment area shape</code>. You can choose between <b>Polygon</b>, <b>Network</b> and <b>Rectangular Grid</b>.</div>
</div>

  </TabItem>
</Tabs>


<Tabs>
  <TabItem value="Polygon" label="Polygon" default className="tabItemBox">

 #### Polygon
- It is the *geometric representation* of the catchments.
- Provides an easy-to-understand visualization of the catchment area.
- One polygon is produced for each <code>step</code>.

<img src={require('/img/toolbox/accessibility_indicators/catchments/pt_polygon.png').default} alt="Catchment Area Shape (Polygon) Public Transport in GOAT" style={{ maxHeight: "300px", maxWidth: "300px"}}/>

:::tip NOTE

If you enable **Polygon Difference**, only the "incremental" (or differential) polygon will be created for each step, but if you disable **Polygon Difference**, a "full" polygon will be created for each step (including the areas covered by all previous steps).

<img src={require('/img/toolbox/accessibility_indicators/catchments/polygon_difference.png').default} alt="Public Transport Configurations" style={{ maxHeight: "400px", maxWidth: "400px"}}/>

:::

  </TabItem>
  <TabItem value="Network" label="Network" className="tabItemBox">

 #### Network
- It is a *street-level representation* of the catchments.
- Enables easy correlation to actual streets and their accessibility within the catchment area.
- Fine-grained detail compared to the other catchment types.

<img src={require('/img/toolbox/accessibility_indicators/catchments/pt_network.png').default} alt="Catchment Area Shape (Network) Public Transport in GOAT" style={{ maxHeight: "300px", maxWidth: "300px"}}/>

  </TabItem>
  <TabItem value="Rectangular Grid" label="Rectangular Grid" className="tabItemBox">

#### Rectangular Grid
- It is a *grid cell-based representation* of the catchments.
- Appears similar to a “heatmap” visualization, however, differs conceptually & computationally (this represents egress from a specified origin to various other locations while heatmaps represent access from various locations to a specified destination).

<img src={require('/img/toolbox/accessibility_indicators/catchments/pt_grid.png').default} alt="Catchment Area Shape (Grid) Public Transport in GOAT" style={{ maxHeight: "300px", maxWidth: "300px"}}/>

  </TabItem>
</Tabs>

### Starting Points

<div class="step">
  <div class="step-number">7</div>
  <div class="content">Select the <code>Starting point method</code> to define how you like to define the starting point(s) for the catchment areas. You can either <b>Select on map</b> or <b>Select from layer</b>.</div>
</div>

<Tabs>
  <TabItem value="Select on Map" label="Select on Map" default className="tabItemBox">

 #### Select on Map

<div class="step">
  <div class="step-number">8</div>
  <div class="content">Choose <code>Select on map</code>. Select the starting point(s) by clicking on the respective location(s) in the map. You can add <b>as many starting points</b> as you like.</div>
</div>


  </TabItem>
  <TabItem value="Select From Layer" label="Select From Layer" className="tabItemBox">

 #### Select From Layer

 <div class="step">
  <div class="step-number">8</div>
  <div class="content">Click on <code>Select from layer</code>. Select the <code>Point layer</code> which contains the starting point(s) you like to use.</div>
</div>


  </TabItem>
</Tabs>


<div class="step">
  <div class="step-number">9</div>
  <div class="content">Click on <code>Run</code>. This starts the calculation of the <b>catchment areas</b> from the selected starting point(s).</div>
</div>

:::tip Hint

Depending on the chosen settings, the calculation might take some minutes. The [status bar](../../workspace/home#status-bar) shows the current progress.

:::

### Results

<div class="step">
  <div class="step-number">10</div>
  <div class="content">As soon as the calculation process is finished, the resulting layer(s) will be added to the map. The layer called <b>"Catchment Area"</b> contains the calculated catchments. If the starting points were created by clicking on the map, they will also be saved in a layer called <b>"Starting Points"</b>. <p></p>
  If you click on a catchment polygon on the map, you will see further details in its attribute table. The attribute <b>travel_cost</b> shows the travel distance or time, depending on which unit you picked for the calculation. If you have selected travel time, the travel_cost will show the <b>time in minutes</b>. If you have selected distance, the travel_cost will show the <b>distance in meters</b>.</div>
</div>

![Catchment Area Calculation Result in GOAT](/img/toolbox/accessibility_indicators/catchments/catchment_result.png "Catchment Area Calculation Result in GOAT")

:::tip Tip
Want to style your catchment areas and create nice looking maps? See [Styling](../../map/layer_style/styling).
:::

## 4. Technical details

Catchment areas are **isolines** connecting all points that can be reached from one or more starting points within a certain time interval (called *isochrones*) or distance (called *isodistance*). Depending on the chosen travel mode, the according transport networks are used for the [routing](../../routing/walking). 

The catchment areas are dynamically created in the front end based on a travel time/distance grid. Therefore, catchment areas can be created fast and for different intervals on the fly.

### Scientific background

From the scientific background, catchments are _contour-based measures_ (also known as _cumulative opportunities_). They are valued for their **easily interpretable results** ([Geurs and van Eck 2001](#6-references); [Albacete 2016](#6-references)), but have the drawback of not distinguishing between different travel times within the **cut-off range** ([Bertolini, le Clercq, and Kapoen 2005](#6-references)), as it is done by [heatmaps](../accessibility_indicators/closest_average.md).

### Visualization 

The catchment shape is derived from the routing grid using the [Marching square contour line algorithm](https://en.wikipedia.org/wiki/Marching_squares "Wikipedia: Marching Squares"), a computer graphics algorithm that can generate two-dimensional contour lines from a rectangular array of values ([de Queiroz Neto et al. 2016](#6-references)). This algorithm transforms the grid from a 2D array to a shape to visualize or analyze. An illustration of 2D image processing is shown in the figure. 

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/toolbox/accessibility_indicators/catchments/wiki.png').default} width="1000px" alt="marching square" style={{ width: "1000px", height: "400px", maxHeight: "400px", maxWidth: "400px", objectFit: "contain"}}/>
</div> 

## 5. Further readings

Further insights into the catchment calculation and its scientific background can be found in this [publication](https://doi.org/10.1016/j.jtrangeo.2021.103080).

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
