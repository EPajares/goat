---
sidebar_position: 6
---
import thematicIcon from "/img/toolbox/data_management/join/toolbox.webp";

# PT Trip Count

This indicator displays the **average number of public transport departures** per hour for each public transport stop.

<iframe width="100%" height="500" src="https://www.youtube.com/embed/QUp0TYG0NG0?si=vAMTyyI5cG7N9HIf" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>

## 1. Explanation

The Public Transport (PT) Trip Count shows the **average number of public transport departures per hour** for a selected **time interval** for each public transport stop on a point layer. The results can be visualized either as a sum of all transport modes or by focusing on one dedicated mode (e.g. bus, tram, metro, rail).

This indicator serves as the foundation for the [ÖV-Güteklassen](./oev_gueteklassen.md), but can also be utilized on its own as a straightforward measure for public transport offer at a **station level**. It gives a summary of a station’s departures during a specific time window and day, providing a valuable overview of the public transport offered in a city. Thus, the indicator is often used in **weak point analyses of local transport plans** (see, among others, [Guideline for Local Transport Planning in Bavaria](https://www.demografie-leitfaden-bayern.de/index.html)).

![Public Transport Trip Count](/img/toolbox/accessibility_indicators/trip_count/sample.png "[Public Transport Trip Count")

import MapViewer from '@site/src/components/MapViewer';

:::info 
The public transport (PT) trip count is only available in areas where the transport network is integrated into GOAT. 

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
        { label: "Coverage for public transport trip count calculation", color: "#ffffff" }
      ]}
    />
</div> 

In case you need to perform analysis beyond this geofence, feel free to contact the [Support](https://plan4better.de/en/contact/ "Contact Support") and we will check what is possible. 
:::

## 2. Example use cases

- Which stations in the city serve as main hubs?
- Which stations have low service rates in comparison to others?
- How does the public transport quality vary over different times of the week or day?

## 3. How to use the indicator?

<div class="step">
  <div class="step-number">1</div>
  <div class="content">Click on <code>Toolbox</code> <img src={thematicIcon} alt="toolbox" style={{width: "25px"}}/>. </div>
</div>

<div class="step">
  <div class="step-number">2</div>
  <div class="content">Under the <code>Accessibility Indicators</code> menu, click on <code>PT Trip Count</code>. This opens the settings menu.</div>
</div>


![Menu Overview for Public Transport Trip Count](/img/toolbox/accessibility_indicators/trip_count/overview.png "[Menu Overview for Public Transport Trip Count")


### Calculation Time

<div class="step">
  <div class="step-number">3</div>
  <div class="content">Select for which <code>Day</code>, <code>Start Time</code>, and <code>End Time</code> you would like to calculate the public transport trip count.</div>
</div>

### Reference Layer

<div class="step">
  <div class="step-number">4</div>
  <div class="content">Select the <code>Reference Layer</code> that contains the area for which you like to calculate the indicator. This can be any polygon feature layer.</div>
</div>


<div class="step">
  <div class="step-number">5</div>
  <div class="content">Click on <code>Run</code>. This starts the calculation of the Public Transport Trip Count for the selected area and time interval.</div>
</div>

:::tip Hint

Depending on the size of the selected area, the calculation might take some minutes. The [status bar](../../workspace/home#status-bar) shows the current progress.

:::

### Results

<div class="step">
  <div class="step-number">6</div>
  <div class="content">As soon as the calculation process is finished, the resulting layer called <b>"Trip Count Station"</b> will be added to the map.</div>
</div>


![Menu Overview for Public Transport Trip Count](/img/toolbox/accessibility_indicators/trip_count/result.png "[Menu Overview for Public Transport Trip Count")

<div class="step">
  <div class="step-number">7</div>
  <div class="content">When clicking on a point in the map, you can see the <b>station name</b>, <b>total departure count</b>, and the <b>departure counts per mode</b>.</div>
</div>


<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>

  <img src={require('/img/toolbox/accessibility_indicators/trip_count/details.png').default} alt="Trip Count Further Details" style={{ maxHeight: "300px", maxWidth: "300px", objectFit: "cover"}}/>

</div> 


:::tip Hint

If you are interested in one specific mode, e.g. only busses, you can use the [attribute-based styling](../../map/layer_style/style/attribute_based_styling.md) to adjust the point color based on that desired column.

:::

## 4. Technical details

Similar to the Public Transport Quality Classes <i>(German: ÖV-Güteklassen)</i>, this indicator is calculated based on **GTFS data** (see [Inbuilt Datasets](../../data/data_basis)). Based on the selected day and time window, the average number of departures per hour (regardless of direction) is calculated.

## 5. References

Shkurti, Majk (2022). [Spatio-temporal public transport accessibility analysis and benchmarking in an interactive WebGIS](https://www.researchgate.net/publication/365790691_Spatio-temporal_public_transport_accessibility_analysis_and_benchmarking_in_an_interactive_WebGIS)
