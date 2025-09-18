---
sidebar_position: 2

---

import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';
import thematicIcon from "/img/toolbox/data_management/join/toolbox.webp";
import MathJax from 'react-mathjax';

# Heatmap - Connectivity
A color-coded map to visualize the connectivity of locations within an area of interest ([AOI](../../further_reading/glossary#area-of-interest-aoi "What is an AOI?")).

<iframe width="100%" height="500" src="https://www.youtube.com/embed/W1NDJlzR_gM?si=wR19yHToaAeZG0kY" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>

## 1. Explanation

Visualized as a color-coded hexagonal grid, the heatmap takes into account real-world transport and street networks to compute connectivity. After specifying a *routing type* (Walk, Bicycle, etc.) and *travel time limit*, the result will display a color-coded hexagonal grid representing the relative connectivity of all locations within the specified AOI.

Unlike our other heatmaps which focus on visualizing the accessibility to specific points (such as [POI](../../further_reading/glossary#point-of-interest-poi "What is a POI?")) or amenities from surrounding areas, connectivity-based heatmaps represent the overall connectivity of an area. This means that all locations within your AOI are considered to be destinations, and for each location, its "connectivity" represents the geographic area (within and outside the AOI) from which the location is accessible, considering the specified *routing type* and *travel time limit*.

![Connectivity-based Heatmap in GOAT](/img/toolbox/accessibility_indicators/heatmaps/connectivity_based/connectivity.png "Connectivity-based Heatmap in GOAT")

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
        { label: "Coverage for Connectivity-based Heatmaps", color: "#ffffff" }
      ]}
  />
</div>


If you would like to perform analyses beyond this geofence, feel free to [contact us](https://plan4better.de/en/contact/ "Contact us"). We would be happy to discuss further options.

:::

## 2. Example use cases

 - How well connected is the street, footpath, or cycle lane network in a specific area?

 - How do locations within an AOI compare in terms of connectivity across the different modes of transport?

 - Are there barriers, gaps, or islands within the street network that hinder connectivity?

 - Does the existing transport network provide equitable access across the AOI?

## 3. How to use the indicator?

<div class="step">
  <div class="step-number">1</div>
  <div class="content">Click on <code>Toolbox</code> <img src={thematicIcon} alt="toolbox" style={{width: "25px"}}/>. </div>
</div>

<div class="step">
  <div class="step-number">2</div>
  <div class="content">Under the <code>Accessibility Indicators</code> menu, click on <code>Heatmap Connectivity</code>.</div>
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

### Configuration

<div class="step">
  <div class="step-number">4</div>
  <div class="content">Choose a <code>Travel Time Limit</code> for your heatmap. This will be used in the context of your previously selected <i>Routing Type</i>.</div>
</div>

:::tip Hint

Need help choosing a suitable travel time limit for various common amenities? The ["Standort-Werkzeug"](https://www.chemnitz.de/chemnitz/media/unsere-stadt/verkehr/verkehrsplanung/vep2040_standortwerkzeug.pdf) of the City of Chemnitz can provide helpful guidance.

:::

<div class="step">
  <div class="step-number">5</div>
  <div class="content">Select the <code>Reference Layer</code> (layer containing your AOI) for which you would like to calculate the heatmap. This can be any polygon feature layer.</div>
</div>


<div class="step">
  <div class="step-number">6</div>
  <div class="content">Click <code>Run</code> to start the calculation of the heatmap.</div>
</div>

:::tip Hint

Depending on your configuration, the calculation might take a few minutes. The [status bar](../../workspace/home#status-bar) displays current progress.

:::

### Results

<div class="step">
  <div class="step-number">10</div>
  <div class="content">Once the calculation is complete, a result layer will be added to the map. This <i>Heatmap Connectivity</i> layer will contain your color-coded heatmap.
  <p></p>
  Clicking on any of the heatmap's hexagonal cells will reveal the computed connectivity value for this cell.</div>
</div>


![Connectivity-based Heatmap Result in GOAT](/img/toolbox/accessibility_indicators/heatmaps/connectivity_based/connectivity_heatmap_result.png "Connectivity-based Heatmap Result in GOAT")


:::tip Tip

Want to style your heatmaps and create nice-looking maps? See [Styling](../../map/layer_style/styling).

:::

## 4. Technical details

### Calculation

For each cell of the hexagonal grid (within your AOI), the full extent of surrounding cells from which it is accessible are identified. These surrounding cells may be located outside of your AOI but must be within areas accessible according to the specified `Travel time limit` and `Routing type`.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/toolbox/accessibility_indicators/heatmaps/connectivity_based/heatmap_connectivity_infographic.png').default} alt="Extent of cells from where destination cell within AOI is accessible." style={{ maxHeight: "400px", maxWidth: "500px", alignItems:'center'}}/>
</div>

Connectivity formula:

<MathJax.Provider>
  <div style={{ marginTop: '20px', fontSize: '24px' }}>
    <MathJax.Node formula={"\\text{connectivity} = \\sum_{i=1}^{n} (\\text{number of cells}_i \\times \\text{cell area})"} />
  </div>
</MathJax.Provider>



Where ***i*** is a travel time step, ***n*** is the travel time limit and ***number cells*** is the number of cells origins reaching the considered location in i minutes. This function computes the total geographic area (in sq. meters) from which the destination cell in your AOI is accessible.

### Classification
To classify the connectivity levels that were computed for each grid cell (for color-coded visualization), a classification based on quantiles is used by default. However, various other classification methods may be used instead. Read more in the **[Data Classification Methods](../../map/layer_style/attribute_based_styling#data-classification-methods)** section of the *Attribute-based Styling* page.

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

The following example illustrates the computation of a connectivity-based heatmap for a specific AOI. The heatmap is computed for a `Travel time limit` of 15 minutes and a `Routing type` of `Walk`.

<img src={require('/img/toolbox/accessibility_indicators/heatmaps/connectivity_based/connectivity-calculation.gif').default} alt="Options" style={{ maxHeight: "800px", maxWidth: "800px"}}/>
