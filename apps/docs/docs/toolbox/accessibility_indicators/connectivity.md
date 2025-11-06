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

The heatmap uses a color-coded hexagonal grid to show how well-connected different areas are. It takes an **Area of Interest** (AOI), a **routing type** (walking, cycling, etc.), and a **travel time limit** as inputs. Considering real-world transport and street networks, it calculates the connectivity of each hexagon within the AOI.

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

 - Does the existing transport network provide equitable access across the AOI?
 - How well connected is the street, footpath, or cycle lane network in a specific area?
 - How do locations within an AOI compare in terms of connectivity across the different modes of transport?
 - Are there barriers, gaps, or islands within the street network that hinder connectivity?

## 3. How to use the indicator?

<div class="step">
  <div class="step-number">1</div>
  <div class="content">Click on <code>Toolbox</code> <img src={thematicIcon} alt="toolbox" style={{width: "25px"}}/>. </div>
</div>

<div class="step">
  <div class="step-number">2</div>
  <div class="content">Under the <code>Accessibility Indicators</code> menu, click on <code>Heatmap Connectivity</code>.</div>
</div>

<div class="step">
  <div class="step-number">3</div>
  <div class="content">Pick the <code>Routing Type</code> you would like to use for the heatmap:</div>
</div>

<div style={{ marginLeft: '60px' }}>
<Tabs>

<TabItem value="walk" label="Walk" default className="tabItemBox">

**Considers all paths accessible by foot**. For heatmaps, a walking speed of 5 km/h is assumed.

</TabItem>
  
<TabItem value="cycling" label="Bicycle" className="tabItemBox">

**Considers all paths accessible by bicycle**. This routing mode takes into account the surface, smoothness and slope of streets while computing accessibility. For heatmaps, a cycling speed of 15 km/h is assumed.

</TabItem>

<TabItem value="pedelec" label="Pedelec" className="tabItemBox">

**Considers all paths accessible by pedelec**. This routing mode takes into account the surface and smoothness of streets while computing accessibility. For heatmaps, a pedelec speed of 23 km/h is assumed.

</TabItem>

<TabItem value="car" label="Car" className="tabItemBox">

**Considers all paths accessible by car**. This routing mode takes into account speed limits and one-way access restrictions while computing accessibility.

</TabItem>

</Tabs>

</div>
<div class="step">
  <div class="step-number">4</div>
  <div class="content">Choose a <code>Travel Time Limit</code> for your heatmap. This will be used in the context of your previously selected <i>Routing Type</i>.</div>
</div>

<div class="step">
  <div class="step-number">5</div>
  <div class="content">Select the <code>Reference Layer</code> (layer containing your AOI) for which you would like to calculate the heatmap. This can be any polygon feature layer.</div>
</div>


<div class="step">
  <div class="step-number">6</div>
  <div class="content">Click <code>Run</code> to start the calculation of the heatmap.</div>
</div>

<div class="step">
  <div class="step-number">7</div>
  <div class="content">Once the calculation is complete, a result layer will be added to the map. This <i>Heatmap Connectivity</i> layer will contain your color-coded heatmap.<p></p>
  Clicking on any of the heatmap's hexagonal cells will reveal the computed connectivity value for this cell.</div>
</div>

![Connectivity-based Heatmap Result in GOAT](/img/toolbox/accessibility_indicators/heatmaps/connectivity_based/connectivity_heatmap_result.gif "Connectivity-based Heatmap Result in GOAT")


:::tip Tip

Want to style your heatmaps and create nice-looking maps? See [Styling](../../map/layer_style/styling).

:::

## 4. Technical details

### Calculation

For each hexagon in the grid within the Area of Interest (AOI), the tool identifies all surrounding hexagons that can reach it. These surrounding hexagons can be outside the AOI but must be within the specified **travel time** and using the chosen **travel method**.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/toolbox/accessibility_indicators/heatmaps/connectivity_based/heatmap_connectivity_infographic.png').default} alt="Extent of cells from where destination cell within AOI is accessible." style={{ maxHeight: "400px", maxWidth: "500px", alignItems:'center'}}/>
</div>

Connectivity formula:

<MathJax.Provider>
  <div style={{ marginTop: '20px', fontSize: '24px' }}>
    <MathJax.Node formula={"\\text{cell connectivity} = \\sum_{i=1}^{n} (\\text{number of reachable cells}_i \\times \\text{cell area})"} />
  </div>
</MathJax.Provider>

The connectivity formula calculates the total area (in square meters) from which a destination cell within the Area of Interest (AOI) can be reached. It does this by considering the **number of cells** that can reach the destination cell within each **travel time step** ***i*** up to the specified **travel time limit** ***n***. **The sum of all these reachable areas gives the final connectivity value for that cell.**

### Grid cells 

Heatmaps in GOAT utilize **[Uber's H3 grid-based](../../further_reading/glossary#h3-grid)** solution for efficient computation and easy-to-understand visualization. Behind the scenes, a pre-computed travel time matrix for each *routing type* utilizes this solution and is queried and further processed in real-time to compute accessibility and produce a final heatmap.

The resolution and dimensions of the hexagonal grid used depend on the selected *routing type*:

<div style={{ marginLeft: '20px' }}>

<Tabs>

<TabItem value="walk" label="Walk" default className="tabItemBox">

<li parentName="ul">{`Resolution: 10`}</li>
<li parentName="ul">{`Average hexagon area: 11285.6 m²`}</li>
<li parentName="ul">{`Average hexagon edge length: 65.9 m`}</li>
</TabItem>
  
<TabItem value="cycling" label="Bicycle" className="tabItemBox">

<li parentName="ul">{`Resolution: 9`}</li>
<li parentName="ul">{`Average hexagon area: 78999.4 m²`}</li>
<li parentName="ul">{`Average hexagon edge length: 174.4 m`}</li>
</TabItem>

<TabItem value="pedelec" label="Pedelec" className="tabItemBox">

<li parentName="ul">{`Resolution: 9`}</li>
<li parentName="ul">{`Average hexagon area: 78999.4 m²`}</li>
<li parentName="ul">{`Average hexagon edge length: 174.4 m`}</li> 
</TabItem>

<TabItem value="car" label="Car" className="tabItemBox">

<li parentName="ul">{`Resolution: 8`}</li>
<li parentName="ul">{`Average hexagon area: 552995.7 m²`}</li>
<li parentName="ul">{`Average hexagon edge length: 461.4 m`}</li>

</TabItem>

</Tabs>
</div>

### Visualization

For visualization, the result form the connectivity analysis, uses a classification method based on quantiles by default. However, various other classification methods may be used instead. Read more in the **[Data Classification Methods](../../map/layer_style/attribute_based_styling#data-classification-methods)** section of the *Attribute-based Styling* page.

:::tip Hint

For further insights into the Routing algorithm, visit [Routing/Bicycle](../../routing/bicycle). In addition, you can check this [Publication](https://doi.org/10.1016/j.jtrangeo.2021.103080).
:::

:::tip Hint
Need help choosing a suitable travel time limit for various common amenities? The ["Standort-Werkzeug"](https://www.chemnitz.de/chemnitz/media/unsere-stadt/verkehr/verkehrsplanung/vep2040_standortwerkzeug.pdf) of the City of Chemnitz can provide helpful guidance.
:::
