---
sidebar_position: 7
---
import thematicIcon from "/img/toolbox/data_management/join/toolbox.webp";
import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';


# PT Nearby Stations

The **PT Nearby Stations** analysis is used to find public transport stops accessible by walking or cycling within a given time. For each stop, departure information by mode and route is provided.

<iframe width="100%" height="500" src="https://www.youtube.com/embed/7RUNllvOBZw?si=wUB9NXBJo03QUYFu" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>

## 1. Explanation

The Public Transport (PT) Nearby Stations access analysis is a suitable tool to **visualize public transport stops and their connections** that are accessible by walking/cycling from one or more starting point(s). The nearest stops, the public transport lines available there, their frequency, and the journey time to reach the stop on foot and by bike are provided as a result.

**Proximity to nearby stations** is essential for various aspects of urban life and is important in urban planning. The availability of public transport connections significantly improves accessibility for residents, workers, and visitors.


![Nearby Stations in GOAT](/img/toolbox/accessibility_indicators/nearby_stations/nearby_stations_example.png "Nearby Stations in GOAT")

import MapViewer from '@site/src/components/MapViewer';

:::info 
The calculation of the nearby stations is only available for areas where the public transport network is integrated into GOAT.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
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
        { label: "Coverage for nearby stations calculation", color: "#ffffff" }
      ]}
  />

</div> 

In case you need to perform analysis beyond this geofence, feel free to contact the [Support](https://plan4better.de/en/contact/ "Contact Support") and we will check what is possible. 
:::


## 2. Example use cases 

- Which public transport stations are nearby and provide convenient access to key attractions and landmarks for tourists exploring a new city?
- When considering daily commuting to work, which nearby public transport stations offer optimal routes and schedules for a seamless journey?
- What are the nearby public transport stations for convenient access to shopping centers?



## 3. How to use the indicator?

<div class="step">
  <div class="step-number">1</div>
  <div class="content">Click on <code>Toolbox</code> <img src={thematicIcon} alt="toolbox" style={{width: "25px"}}/>. </div>
</div>

<div class="step">
  <div class="step-number">2</div>
  <div class="content">Under the <code>Accessibility Indicators</code> menu, click on <code>PT Nearby Stations</code>.</div>
</div>

![Menu Overview for Public Transport Nearby Stations](/img/toolbox/accessibility_indicators/nearby_stations/nearby_stations_overview.png "Menu Overview for Public Transport Nearby Stations")

### Station Access

<div class="step">
  <div class="step-number">3</div>
  <div class="content">Select the <code>Station Access</code> mode (<i>walk, bicycle, or pedelec</i>), which shall be used for the way to the PT station.</div>
</div>

<div class="step">
  <div class="step-number">4</div>
  <div class="content">Set the configurations for the Station Access by choosing <code>Travel time limit (min)</code> and <code>Travel speed (km/h)</code>.</div>
</div>

### Station Configuration

<div class="step">
  <div class="step-number">5</div>
  <div class="content">Pick which <code>Public transport modes</code> shall be considered for the nearby stations.</div>
</div>

<div class="step">
  <div class="step-number">6</div>
  <div class="content">Select for which <code>Day</code>, <code>Start Time</code> and <code>End Time</code> you would like to see the public transport connections.</div>
</div>

![Configurations for Public Transport Nearby Stations](/img/toolbox/accessibility_indicators/nearby_stations/nearby_stations_config.png "Configurations for Public Transport Nearby Stations")

### Starting Points

<div class="step">
  <div class="step-number">7</div>
  <div class="content">Select the <code>Starting point method</code> to define how you like to define the starting point(s) for the trip(s). You can either <b>Select on map</b> or <b>Select from layer</b>.</div>
</div>

<Tabs>
  <TabItem value="Select on map" label="Select on map" default className="tabItemBox">
 
  Click on <code>Select on map</code>. Select the starting point(s) by clicking on the respective location(s) in the map. You can add as many starting points as you like.

  </TabItem>

  <TabItem value="Select from layer" label="Select from layer" className="tabItemBox">
  
  Click on <code>Select from layer</code>. Select the <code>Point layer</code> which contains the starting point(s) you would like to use.
  
  </TabItem>
</Tabs>

<div class="step">
  <div class="step-number">8</div>
  <div class="content">Click on <code>Run</code>. This starts the capturing of the Nearby Stations from the selected starting point(s).</div>
</div>

:::tip Hint

Depending on the number of the selected starting points, the calculation might take some minutes. The [status bar](../../workspace/home#status-bar) shows the current progress.

:::

### Results

<div class="step">
  <div class="step-number">9</div>
  <div class="content">As soon as the calculation process is finished, the resulting layers will be added to the map. The results consist of one layer called <b>"Nearby Stations"</b>, showing the Nearby PT Stations, and one layer called <b>"Starting Points - Nearby Stations"</b> which provides all starting points that were used for the calculation of this indicator. 
  <p></p>
  When clicking on a point in the map, further details, such as <b>stop name</b>, <b>access time [min]</b> and <b>aggregate frequency of PT service [min]</b>, become visible.
</div>
</div>


![Result of Public Transport Nearby Stations](/img/toolbox/accessibility_indicators/nearby_stations/nearby_stations_result.png "Result of Public Transport Nearby Stations")



:::tip Tip
Want to style your results and create nice-looking maps? See [Styling](../../map/layer_style/styling).
:::

## 4. Technical details

Similar to the Public Transport Quality Classes <i>(German: ÖV-Güteklassen)</i>, this indicator is calculated based on **GTFS data** (see [Inbuilt Datasets](../../data/data_basis)). Based on the selected modes, day, and time window, the PT Nearby Stations are received.
