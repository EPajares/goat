---
sidebar_position: 3
---

import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';
import thematicIcon from "/img/toolbox/data_management/join/toolbox.webp";
import MathJax from 'react-mathjax';

# Heatmap - Closest Average
A color-coded map to visualize the average travel time to points (such as [POI](../../further_reading/glossary#point-of-interest-poi "What is a POI?")) from surrounding areas.

<iframe width="100%" height="500" src="https://www.youtube.com/embed/djd16SZJ-HA?si=vEKHhoI_2mQL2wxI" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>

## 1. Explanation

Visualized as a color-coded hexagonal grid, the heatmap takes into account real-world transport and street networks to compute travel times. After specifying a *routing type* (Walk, Bicycle, etc.), *opportunity layer* and *travel time limit*, the result will display a color-coded hexagonal grid for all areas accessible under these conditions. The color scale refers to average travel time.

:::info INFO

An `Opportunity layer` contains [geographic point](../../data/data_types "What are geographic points?") data. Select one or more such layers containing your destination points (opportunities) as input to the heatmap.

:::

With the configurable *number of destinations* property, you can restrict the calculation to consider only the *n* closest opportunities. This produces an easy-to-understand visualization which can be used to identify variation in average travel times even at a city or regional scale. The computed value for each cell in the heatmap represents the average travel time to the nearest *n* destinations.

:::tip Pro tip

Shortly, accessibility heatmaps are a visualization representing *access* from various unspecified origins, to one or more specified destinations. This is in contrast to catchment areas which represent *egress* from one or more specified origins to various unspecified destinations.

:::

![Closest Average-based Heatmap in GOAT](/img/toolbox/accessibility_indicators/heatmaps/closest_average_based/closest_avg.png "Closest Average-based Heatmap in GOAT")

import MapViewer from '@site/src/components/MapViewer';

:::info 

Heatmaps are available in certain regions. Upon selecting a `Routing type`, a **geofence** will be displayed on the map to highlight supported regions.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <MapViewer
      geojsonUrls={[
        "https://assets.plan4better.de/other/geofence/geofence_heatmap.geojson"
      ]}
      styleOptions={{
        fillColor: "#808080",
        outlineColor: "#808080",
        fillOpacity: 0.8
      }}
      legendItems={[
        { label: "Coverage for Closest-average-based Heatmaps", color: "#ffffff" }
      ]}
  />

</div> 


If you would like to perform analyses beyond this geofence, feel free to [contact us](https://plan4better.de/en/contact/ "Contact us"). We would be happy to discuss further options.

:::

## 2. Example use cases

 - Do residents in certain areas have longer average travel times to amenities than others?

 - Is there a significant difference in average travel times to amenities across different neighborhoods?

 - How does the average travel time to amenities vary across different modes of transport?

 - How does the average travel time vary across different types of amenities?
 
 - Are there areas with high average travel times to amenities that could benefit from improved transport infrastructure?

 - If standards require that a minimum number of amenities be accessible within a certain travel time, which areas meet these standards?

## 3. How to use the indicator?

<div class="step">
  <div class="step-number">1</div>
  <div class="content">Click on <code>Toolbox</code> <img src={thematicIcon} alt="toolbox" style={{width: "25px"}}/>. </div>
</div>

<div class="step">
  <div class="step-number">2</div>
  <div class="content">Under the <code>Accessibility Indicators</code> menu, click on <code>Heatmap Closest Average</code>.</div>
</div>

### Routing

<div class="step">
  <div class="step-number">3</div>
  <div class="content">Pick the <code>Routing Type</code> you would like to use for the heatmap.</div>
</div>

<Tabs>

<TabItem value="walk" label="Walk" default className="tabItemBox">

#### Walk

Considers all paths accessible by foot. For heatmaps, a walking speed of 5 km/h is assumed.

:::tip Hint

For further insights into the Routing algorithm, visit [Routing/Walk](../../routing/walking).

:::

</TabItem>
  
<TabItem value="cycling" label="Bicycle" className="tabItemBox">

#### Bicycle

Considers all paths accessible by bicycle. This routing mode takes into account the surface, smoothness and slope of streets while computing accessibility. For heatmaps, a cycling speed of 15 km/h is assumed.

:::tip Hint

For further insights into the Routing algorithm, visit [Routing/Bicycle](../../routing/bicycle). In addition, you can check this [Publication](https://doi.org/10.1016/j.jtrangeo.2021.103080).

:::

</TabItem>

<TabItem value="pedelec" label="Pedelec" className="tabItemBox">

#### Pedelec

Considers all paths accessible by pedelec. This routing mode takes into account the surface and smoothness of streets while computing accessibility. For heatmaps, a pedelec speed of 23 km/h is assumed.

:::tip Hint

For further insights into the Routing algorithm, visit [Routing/Bicycle](../../routing/bicycle). In addition, you can check this [Publication](https://doi.org/10.1016/j.jtrangeo.2021.103080).

:::

</TabItem>

<TabItem value="car" label="Car" className="tabItemBox">

#### Car

Considers all paths accessible by car. This routing mode takes into account speed limits and one-way access restrictions while computing accessibility.

:::tip Hint

For further insights into the Routing algorithm, visit [Routing/Car](../../routing/car).

:::

</TabItem>

</Tabs>

### Opportunities

Opportunities are essentially point-based data (such as [POI](../../further_reading/glossary#point-of-interest-poi "What is a POI?")) for which you would like to compute a heatmap. These are the "destinations" (such as transit stations, schools, other amenities, or your own custom point-based data) while surrounding areas are "origins" for which an accessibility value will be computed and visualized.

Additionally, you may create more opportunities via the `+ Add Opportunity` button at the bottom of the drawer. All opportunity layers will be combined to produce a unified heatmap.

<div class="step">
  <div class="step-number">4</div>
  <div class="content">Select your <code>Opportunity Layer</code> from the drop-down menu. This can be any previously created layer containing point-based data.</div>
</div>

<div class="step">
  <div class="step-number">5</div>
  <div class="content">Choose a <code>Travel Time Limit</code> for your heatmap. This will be used in the context of your previously selected <i>Routing Type</i>.</div>
</div>

:::tip Hint

Need help choosing a suitable travel time limit for various common amenities? The ["Standort-Werkzeug"](https://www.chemnitz.de/chemnitz/media/unsere-stadt/verkehr/verkehrsplanung/vep2040_standortwerkzeug.pdf) of the City of Chemnitz can provide helpful guidance.

:::

<div class="step">
  <div class="step-number">6</div>
  <div class="content">Specify the <code>Number of destinations</code> which should be considered while computing the average travel time.</div>
</div>

:::tip Hint

As the *Number of destinations* parameter is specified once per opportunity layer, you have the flexibility to supply different values for each opportunity layer. This can be useful if distinct types of amenities have varying standards for accessibility.

:::

<div class="step">
  <div class="step-number">7</div>
  <div class="content">Click <code>Run</code> to start the calculation of the heatmap.</div>
</div>

:::tip Hint

Depending on your configuration, the calculation might take a few minutes. The [status bar](../../workspace/home#status-bar) displays current progress.

:::

### Results

<div class="step">
  <div class="step-number">10</div>
  <div class="content">Once the calculation is complete, a result layer will be added to the map. This <i>Heatmap Closest Average</i> layer will contain your color-coded heatmap.<p></p>
  Clicking on any of the heatmap's hexagonal cells will reveal the computed average travel time value for this cell.</div>
</div>


<img src={require('/img/toolbox/accessibility_indicators/heatmaps/closest_average_based/clst-avg-calculation.gif').default} alt="Options" style={{ maxHeight: "800px", maxWidth: "800px"}}/>

:::tip Tip

Want to style your heatmaps and create nice-looking maps? See [Styling](../../map/layer_style/styling).

:::

## 4. Technical details

### Calculation

Once all input opportunity layers are combined, a grid of surrounding hexagonal cells is identified. This is done by considering cells where at least one opportunity is accessible taking into account the specified `Routing type` and `Travel time limit`. Next, the average travel time for each cell within this grid is computed, considering the nearest *n* opportunities as specified in the opportunity layer.

Average travel time formula:

<MathJax.Provider>
  <div style={{ marginTop: '20px', fontSize: '24px' }}>
    <MathJax.Node formula={"\\overline{t}_i = \\frac{\\sum_{j=1}^{n} t_{ij}}{n}"} />
  </div>
</MathJax.Provider>


where the average travel time for cell **i** is the sum of upto **n** travel times from cell **i** to opportunity **j** (**tij**) divided by the number of opportunities **n** which must be less than the `Number of destinations` parameter specified.

### Classification
In order to classify the accessibility levels that were computed for each grid cell (for color-coded visualization), a classification based on quantiles is used by default. However, various other classification methods may be used instead. Read more in the **[Data Classification Methods](../../map/layer_style/attribute_based_styling#data-classification-methods)** section of the *Attribute-based Styling* page.

### Visualization 

Heatmaps in GOAT utilize **[Uber's H3 grid-based](../../further_reading/glossary#h3-grid)** solution for efficient computation and easy-to-understand visualization. Behind the scenes, a pre-computed travel time matrix for each *routing type* utilizes this solution and is queried and further processed in real-time to compute accessibility and produce a final heatmap.

The resolution and dimensions of the hexagonal grid used depend on the selected *routing type*:

#### Walk
- Resolution: 10
- Average hexagon area: 11285.6 m²
- Average hexagon edge length: 65.9 m

#### Bicycle
- Resolution: 9
- Average hexagon area: 78999.4 m²
- Average hexagon edge length: 174.4 m

#### Pedelec
- Resolution: 9
- Average hexagon area: 78999.4 m²
- Average hexagon edge length: 174.4 m

#### Car
- Resolution: 8
- Average hexagon area: 552995.7 m²
- Average hexagon edge length: 461.4 m

### Example of calculation

The following examples illustrate the computation of a closest-average-based heatmap for the same opportunities, with a varying `Number of destinations` value.

![Closest Average Heatmaps for different destinations](/img/toolbox/accessibility_indicators/heatmaps/closest_average_based/cls-avg-destinations.png "Closest Average Heatmaps for different destinations")

In the first example, the average travel time is computed considering only the closest destination, while in the second example, the closest 5 destinations are considered.
