---
sidebar_position: 5
---
import thematicIcon from "/img/toolbox/data_management/join/toolbox.webp";

# ÖV-Güteklassen

The ÖV-Güteklassen indicator **classifies the quality of public transport services in a given area**, helping planners and stakeholders quickly identify well-served and underserved locations.

<div style={{ display: 'flex', justifyContent: 'center' }}>
<iframe width="674" height="378" src="https://www.youtube.com/embed/7YMhKkg2mtU?si=Wy1-ZjKGeJWt-K-I&amp;start=46" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>
</div>

## 1. Explanation

ÖV-Güteklassen (Public Transport Quality Classes) provide a standardized way to **evaluate and visualize the attractiveness of public transport services**. The classes range from **A** (very good) to **F** (very poor), based on service frequency, station type, and spatial coverage.

The ÖV-Güteklassen indicator is decisive and can be used to highlight deficits in the public transport offer and to identify well-serviced locations as attractive areas for development.

import MapViewer from '@site/src/components/MapViewer';

:::info 
The calculation of the public transport quality classes is only available for areas where the transport network is integrated into GOAT.

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
        { label: "Coverage for ÖV-Güteklassen", color: "#ffffff" }
      ]}
  />
</div> 

In case you need to perform analysis beyond this geofence, feel free to contact the [Support](https://plan4better.de/en/contact/ "Contact Support") and we will check what is possible. 
:::

## 2. Example use cases

- How good is public transport supply in different parts of the city?
- How many people are underserved by public transport? Where is the need for further supply?
- How does the quality of public transport services differ at different times of the week and day?

## 3. How to use the indicator?

<div class="step">
  <div class="step-number">1</div>
  <div class="content">Click on <code>Toolbox</code> <img src={thematicIcon} alt="toolbox" style={{width: "25px"}}/>. </div>
</div>

<div class="step">
  <div class="step-number">2</div>
  <div class="content">Under <code>Accessibility Indicators</code>, select <code>ÖV-Güteklassen</code> to open the settings menu.</div>
</div>

### Calculation Time

<div class="step">
  <div class="step-number">3</div>
  <div class="content">Set the <code>Day</code>, <code>Start Time</code>, and <code>End Time</code> for your analysis.</div>
</div>

### Reference Layer

<div class="step">
  <div class="step-number">4</div>
  <div class="content">Select the <code>Reference Layer</code> (polygon feature layer) for the area you want to analyze.</div>
</div>

### Configuration

<div class="step">
  <div class="step-number">5</div>
  <div class="content">Choose the <code>Catchment area type</code>: <b>Buffer</b> or <b>Network</b>.</div>
</div>

:::info

**Buffers** represent areas around public transport stations measured "as the crow flies", while **network** catchment areas account for the same distances along real-world streets and paths.

:::

<div class="step">
  <div class="step-number">6</div>
  <div class="content">Click <code>Run</code> to start the calculation.</div>
</div>

### Results


After calculation, two layers are added to the map:
- **ÖV-Güteklassen**: Shows the quality class for each area.
- **ÖV-Güteklassen Stations**: Shows all stations used in the calculation (grey points = too low frequency, don't contribute to any PT Quality Class).

If you click on a ÖV-Güteklassen result **your will see the further details, such as Public Transport Class and Public Transport Class Number**. Both represent the quality of public transport in that area (see [calculation](#calculation) for more details).

If you click on any station, **you can see details such as the stop name, average frequency, and station category**. 

<div style={{ display: 'flex', justifyContent: 'center' }}>
<img src={require('/img/toolbox/accessibility_indicators/gueteklassen/gueteklassen_calculation.gif').default} alt="Calculation - Public Transport Quality Classes" style={{ maxHeight: "auto", maxWidth: "80%"}}/>
</div>

## 4. Technical details

### Scientific Background

 The approach of Public Transport Quality Classes <i>(German: ÖV-Güteklassen)</i> is **methodologically superior compared to common catchment areas**. In 2011, the [Swiss Federal Office for Spatial Development (ARE)](https://www.are.admin.ch/are/de/home.html) started to use this indicator to **include the attractiveness of public transport services in the assessment of quality development**; since then, it has been considered an important instrument in formal planning processes in Switzerland. Later on, the Swiss model served as an inspiration for its application in Austria (e.g. Voralberg) and Germany (e.g. by [KCW](https://www.plan4better.de/en/references/calculation-of-public-transport-quality-classes-in-germany) and [Agora Verkehrswende](https://www.plan4better.de/en/references/accessibility-analyses-for-the-mobility-guarantee-and-public-transport-atlas-projects)).  

The institutionalization of the indicator in German-speaking countries, as well as the comprehensible and at the same time differentiated calculation methodology, are important advantages of the <i>ÖV-Güteklassen</i>. 

### Calculation

In the Swiss version of the indicator, the calculation of the quality classes is usually carried out for departures on weekdays between 6 AM and 8 PM. For the use in GOAT, the **calculation period** was made more flexible so that the indicator can be calculated **for any day of the week and time of day**. 

The calculations are carried out based on **GTFS data** (see [Inbuilt Datasets](../../data/data_basis)): 
First, the number of departures per public transport mode (train, metro, tram, and bus) is dynamically calculated for each station. The sum of the departures is divided by two to calculate the frequency, to eliminate the outward and return directions. In the next step, the **average frequency** for the selected time interval is calculated. The higher-value service is selected as the **station type** in the case of service by several means of transport. For example, in the case of buses and trains, this is the train. With the help of the table below, as well as the station type and the frequency, the station category can now be determined. 

### Calculation steps

1. **Departures per station**: Calculate the number of departures per mode (train, metro, tram, bus) for each station using **GTFS data** (see [Inbuilt Datasets](../../data/data_basis)).
2. **Frequency**: The sum of the departures is divided by two to eliminate the outward and return directions.
3. **Station type**: For each station, determine the highest-ranking mode of transport served (e.g., if both bus and train are available, the station is classified as a train station).
4. **Category assignment**: Use the station type and frequency to determine the category (see table below).
5. **Catchment areas**: Create buffers or network isochrones for each station category.
6. **Merge areas**: Overlapping areas are merged, with the higher-quality class taking precedence.


<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  
  <img src={require('/img/toolbox/accessibility_indicators/gueteklassen/classification_stations_en.webp').default} alt="Classification of transport stops" style={{ maxHeight: "auto", maxWidth: "60%", objectFit: "cover"}}/>

  <p></p>

  <img src={require('/img/toolbox/accessibility_indicators/gueteklassen/determination_oev_gueteklasse_en.webp').default} alt="Determination of Public Transport Quality Classes" style={{ maxHeight: "auto", maxWidth: "60%", objectFit: "cover"}}/>
 
  <p></p>

  <img src={require('/img/toolbox/accessibility_indicators/gueteklassen/oev_figure_en.png').default} alt="ÖV-Güteklassen Calculation" style={{ maxHeight: "auto", maxWidth: "30%", objectFit: "cover"}}/>
</div>

<div></div>

### Visualization

The created buffers/network catchment areas are visualized around the stations in the corresponding colors to highlight the **quality class** (<span style={{color: "#199741"}}>A</span>-<span style={{color: "#E4696A"}}>F</span>).

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/toolbox/accessibility_indicators/gueteklassen/visualization.png').default} alt="Visualization of the ÖV-Güteklassen" style={{ maxHeight: "400px", maxWidth: "100%", objectFit: "cover"}}/>
</div>


## 5. Further readings

Sample projects where ÖV-Güteklassen was used:

- [Germany-Wide Assessment of Public Transport Accessibility Through Public Transport Quality Classes white paper](https://www.plan4better.de/en/whitepapers/ov-erschliessung)
- [Accessibility analyses for the "Mobility Guarantee" and "Public Transport Atlas" projects](https://www.plan4better.de/en/references/accessibility-analyses-for-the-mobility-guarantee-and-public-transport-atlas-projects) 
- [Calculation of public transport quality classes in Austria](https://www.plan4better.de/en/references/guteklassen-osterreich)
- [Calculation of public transport quality classes in Germany](https://www.plan4better.de/en/references/calculation-of-public-transport-quality-classes-in-germany)

## 6. References

- Bundesamt für Raumentwicklung ARE, 2022. [ÖV-Güteklassen Berechnungsmethodik ARE (Grundlagenbericht)](https://www.are.admin.ch/are/de/home/medien-und-publikationen/publikationen/verkehr/ov-guteklassen-berechnungsmethodik-are.html "Open Reference").

- Hiess, H., 2017. [Entwicklung eines Umsetzungskonzeptes für österreichweite ÖV-Güteklassen](https://www.oerok.gv.at/fileadmin/user_upload/Bilder/2.Reiter-Raum_u._Region/1.OEREK/OEREK_2011/PS_RO_Verkehr/OeV-G%C3%BCteklassen_Bericht_Final_2017-04-12.pdf "Open Reference").

- metron, 2017. [Bedienungsqualität und Erschließungsgüte im Öffentlichen Verkehr](https://vorarlberg.at/documents/302033/472144/1-+Schlussbericht.pdf/81c5f0d7-a0f0-54c7-e951-462cd5cf2831?t=1616147848364 "Open Reference").

- Shkurti, Majk, 2022. "Spatio-temporal public transport accessibility analysis and benchmarking in an interactive WebGIS". url: https://www.researchgate.net/publication/365790691_Spatio-temporal_public_transport_accessibility_analysis_and_benchmarking_in_an_interactive_WebGIS 
