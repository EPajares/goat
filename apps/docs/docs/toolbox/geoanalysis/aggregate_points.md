---
sidebar_position: 1
---
import thematicIcon from "/img/toolbox/data_management/join/toolbox.webp";
import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';

# Aggregate Points

The **Aggregate Points** tool performs statistical analysis of points, e.g. **count, sum, min, or max**, and aggregates the information on polygons.

<iframe width="100%" height="500" src="https://www.youtube.com/embed/_ybPf_fuMLA?si=mX1-uugIA5LiCKss" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>

## 1. Explanation

The Aggregate Points tool can be used to **analyze the characteristics of points within a given area**. It aggregates the information of the points and therewith allows calculation of the point **count**, the **sum** of point attributes, or derive e.g. the **maximum** value of a certain point attribute within a polygon. As a polygon layer, either a feature layer (e.g. city districts) or a hexagonal grid can be used. 


<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>

  <img src={require('/img/toolbox/geoanalysis/aggregate_points/point_aggregation.png').default} alt="Point Aggregation" style={{ maxHeight: "600px", maxWidth: "600px", objectFit: "cover"}}/>

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


<img src={require('/img/toolbox/geoanalysis/aggregate_points/aggregate_points.png').default} alt="Point Aggregation Tool in GOAT" style={{ maxHeight: "auto", maxWidth: "auto"}}/>

### Layer to aggregate

<div class="step">
  <div class="step-number">3</div>
  <div class="content">Select your <code> Source Layer</code>, which contains the data you like to aggregate.</div>
</div>

<div class="step">
  <div class="step-number">4</div>
  <div class="content">Select on which <code> Area Type</code> you like to aggregate the source layer. You can choose between <b>Polygon</b> or <b>H3 grid</b>.</div>
</div>

<Tabs>
  <TabItem value="Polygon" label="Polygon" default className="tabItemBox">

 #### Polygon

<div class="step">
  <div class="step-number">5</div>
  <div class="content">Select the <code>Area Layer</code> which contains the polygons on which you like to aggregate your point data.</div>
</div>


  </TabItem>
  <TabItem value="H3 Grid" label="H3 Grid" className="tabItemBox">

 #### H3 Grid

 <div class="step">
  <div class="step-number">5</div>
  <div class="content">Select the <code>H3 Grid Resolution</code>. You can choose resolutions between <b>3</b> (average edge length of 69km) and <b>10</b> (average edge length of 70m).</div>
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

:::tip Hint

Depending on the size of the datasets, the calculation might take some minutes. The [status bar](../../workspace/home#status-bar) shows the current progress.

:::

### Results

<div class="step">
  <div class="step-number">8</div>
  <div class="content">As soon as the calculation process is finished, the resulting layer <b>"Aggregation Point"</b> will be added to the map. This layer consists of the information of the source layer and an <b>additional column</b> showing the results from the <b>statistical operation</b>. You can see the table by clicking on the polygon on the map.</div>
</div>

<img src={require('/img/toolbox/geoanalysis/aggregate_points/aggregate_points_result.png').default} alt="Point Aggregation Result in GOAT" style={{ maxHeight: "auto", maxWidth: "auto"}}/>


:::tip Tip
Want to style your result layer and create nice-looking maps? See [Styling](../../map/layer_style/styling).
:::