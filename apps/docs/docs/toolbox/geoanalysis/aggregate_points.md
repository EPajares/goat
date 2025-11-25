---
sidebar_position: 1
---
import thematicIcon from "/img/toolbox/data_management/join/toolbox.webp";
import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';

# Aggregate Points

The Aggregate Points tool **performs statistical analysis of points, e.g. count, sum, min, or max, and aggregates the information on polygons.**

<div style={{ display: 'flex', justifyContent: 'center' }}>
<iframe width="674" height="378" src="https://www.youtube.com/embed/_ybPf_fuMLA?si=mX1-uugIA5LiCKss" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>
</div>

## 1. Explanation

The Aggregate Points tool can be used to **analyze the characteristics of points within a given area**. It aggregates the information of the points and therewith allows calculation of the point count, the sum of point attributes, or derive e.g. the maximum value of a certain point attribute within a polygon. As a polygon layer, either a feature layer (e.g. city districts) or a hexagonal grid can be used. 

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>

  <img src={require('/img/toolbox/geoanalysis/aggregate_points/point_aggregation.png').default} alt="Point Aggregation" style={{ maxHeight: "auto", maxWidth: "40%", objectFit: "cover"}}/>

</div> 


## 2. Example use cases

- Aggregating the population numbers on a hexagon grid.
- Deriving the sum of traffic accidents within a city district.
- Visualizing the average number of carsharing vehicles available per station on a district level. 

## 3. How to use the tool?

<div class="step">
  <div class="step-number">1</div>
  <div class="content">Click on <code>Toolbox</code> <img src={thematicIcon} alt="toolbox" style={{width: "25px"}}/>. </div>
</div>

<div class="step">
  <div class="step-number">2</div>
  <div class="content">Under the <code>Geoanalysis</code> menu, click on <code>Aggregate Points</code>.</div>
</div>

### Layer to aggregate

<div class="step">
  <div class="step-number">3</div>
  <div class="content">Select your <code> Source Layer</code>, which contains <strong>the data you like to aggregate</strong>.</div>
</div>

### Summary Areas

<div class="step">
  <div class="step-number">4</div>
  <div class="content">Select on which <code> Area Type</code> you like to aggregate the source layer. You can choose between <b>Polygon</b> or <b>H3 grid</b>.</div>
</div>

<Tabs>
  <TabItem value="Polygon" label="Polygon" default className="tabItemBox">

<div class="step">
  <div class="step-number">5</div>
  <div class="content">Select the <code>Area Layer</code> which contains the polygons on which you like to aggregate your point data.</div>
</div>


  </TabItem>
  <TabItem value="H3 Grid" label="H3 Grid" className="tabItemBox">

 <div class="step">
  <div class="step-number">5</div>
  <div class="content">Select the <code>H3 Grid Resolution</code>. You can choose resolutions between 3 (average edge length of 69km) and 10 (average edge length of 70m).</div>
</div>

:::tip NOTE

To learn more about the H3 grid, you can visit the [Glossary](../../further_reading/glossary#H3-grid).

:::

  </TabItem>
</Tabs>

### Statistics

<div class="step">
  <div class="step-number">6</div>
  <div class="content">Select the <code>Statistic Method</code>, and the field you like to use for the <code>Field Statistics</code> (the field in the source layer that is used to group the aggregated points for statistics).</div>
</div>

Available **Statistics Methods** are listed in the following. The available methods depend on the data type of the chosen attribute:

| Method | Type | Description |
| -------|------| ------------|
| Count  | `string`,`number`    | Counts the number of non-null values in the selected column|
| Sum    | `number`   | Calculates the sum of all the numbers in the selected column|
| Mean   | `number`   | Calculates the average (mean) value of all numeric values in the selected column|
| Median | `number`   | Yields the middle value in the selected column's sorted list of numeric values|
| Min    | `number`   | Yields the minimum value of the selected column|
| Max    | `number`   | Yields the maximum value of the selected column|


<div class="step">
  <div class="step-number">7</div>
  <div class="content">Click on <code>Run</code>.</div>
</div>

### Results

As soon as the calculation process is finished, the resulting layer **"Aggregation Point"** will be added to the map. This layer consists of the information of the source layer and an **additional column** showing the results from the **statistical operation**. You can see the table by clicking on the polygon on the map.

<img src={require('/img/toolbox/geoanalysis/aggregate_points/aggregate_points_result.png').default} alt="Point Aggregation Result in GOAT" style={{ maxHeight: "auto", maxWidth: "auto"}}/>

<p></p>

:::tip Tip
Want to style your result layer and create nice-looking maps? See [Styling](../../map/layer_style/styling).
:::