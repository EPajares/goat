---
sidebar_position: 7
---
import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';


# PT Nearby Stations

The PT Nearby Stations indicator is used to **find public transport stops accessible by walking or cycling within a given time.** 

<div style={{ display: 'flex', justifyContent: 'center' }}>
<iframe width="674" height="378" src="https://www.youtube.com/embed/JHU9ty0HVVc?si=VTsQyLUdKxRcxA_B&amp;start=46" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>
</div>

## 1. Explanation

The tool identifies **public transport stations reachable from starting points within specified travel parameters.** It takes starting points, station access mode (walk, bicycle, or pedelec), travel time limit, and public transport modes as inputs. Using real-world street and transit networks, **it calculates which stations are accessible and provides detailed service information for each.**

For each accessible station, the analysis shows **available transport modes**, **service frequencies**, **departure schedules**, and **access times**. This comprehensive view helps evaluate transit connectivity and supports planning decisions.

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

- Which public transport stations are nearby and provide convenient access to key attractions and landmarks for tourists exploring the city?
- When considering daily commuting to work, which nearby public transport stations offer optimal routes and schedules for a seamless journey?
- What are the nearby public transport stations for convenient access to shopping centers?


## 3. How to use the indicator?

<div class="step">
  <div class="step-number">1</div>
  <div class="content">Click on <code>Toolbox</code> <img src={require('/img/icons/toolbox.png').default} alt="Options" style={{ maxHeight: "20px", maxWidth: "20px", objectFit: "cover"}}/>. </div>
</div>

<div class="step">
  <div class="step-number">2</div>
  <div class="content">Under the <code>Accessibility Indicators</code> menu, click on <code>PT Nearby Stations</code>.</div>
</div>

### Station Access

<div class="step">
  <div class="step-number">3</div>
  <div class="content">Choose the <code>Station Access</code> mode for reaching the stations: <strong>Walk</strong>, <strong>Bicycle</strong>, or <strong>Pedelec</strong>.</div>
</div>

<div class="step">
  <div class="step-number">4</div>
  <div class="content">Configure the access parameters by setting <code>Travel time limit</code> and <code>Travel speed</code>.</div>
</div>

### Station Configuration

<div class="step">
  <div class="step-number">5</div>
  <div class="content">Select which <code>Public transport modes</code> to include in the analysis.</div>
</div>

<div class="step">
  <div class="step-number">6</div>
  <div class="content">Choose the analysis timeframe by setting <code>Day</code>, <code>Start Time</code>, and <code>End Time</code>.</div>
</div>

### Starting Points

<div class="step">
  <div class="step-number">7</div>
  <div class="content">Choose the <code>Starting point method</code>: <code>Select on map</code> or <code>Select from layer</code>.</div>
</div>

<Tabs>
  <TabItem value="Select on map" label="Select on map" default className="tabItemBox">

  Click starting points directly on the map. You can add multiple starting points.

  </TabItem>

  <TabItem value="Select from layer" label="Select from layer" className="tabItemBox">

  Choose a <code>Point layer</code> containing your starting points.

  </TabItem>
</Tabs>

<div class="step">
  <div class="step-number">8</div>
  <div class="content">Click <code>Run</code> to start the analysis.</div>
</div>

### Results

Once calculation finishes, the resulting layers are added to the map:

- **"Nearby Stations"** layer showing accessible public transport stops
- **"Starting Points - Nearby Stations"** layer with analysis origins

Click on stations to view details including **stop name**, **access time**, and **service frequency**.

<div style={{ display: 'flex', justifyContent: 'center' }}>
<img src={require('/img/toolbox/accessibility_indicators/nearby_stations/nearby_stations_calculation.gif').default} alt="Calculation - Public Transport Nearby Stations" style={{ maxHeight: "auto", maxWidth: "80%"}}/>
</div>

<p></p>



:::tip Tip
Want to style your results and create nice-looking maps? See [Styling](../../map/layer_style/styling).
:::

## 4. Technical details

Similar to the Public Transport Quality Classes <i>(German: ÖV-Güteklassen)</i>, this indicator is calculated based on **GTFS data** (see [Inbuilt Datasets](../../data/data_basis)). Based on the selected modes, day, and time window, the PT Nearby Stations are received.