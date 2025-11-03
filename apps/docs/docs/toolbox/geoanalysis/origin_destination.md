---
sidebar_position: 4
---

import thematicIcon from "/img/toolbox/data_management/join/toolbox.webp";

# Origin Destination

The **Origin-Destination** analysis is used in various fields such as transport planning and urban planning to study **movements or flows between different locations**.

<iframe width="100%" height="500" src="https://www.youtube.com/embed/VmHe1NfApRw?si=xzUGIkh2IHn6DTTl" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>


## 1. Explanation

The Origin-Destination (OD) tool is suited for studying **movement patterns between locations**, such as commuter flows, providing insights into spatial interactions. This analytical process thereby visualizes the relationships between **starting points (origins)** and **endpoints (destinations)** by **connecting them with a straight line**. Such analyses help understand how and why movement occurs in different contexts and assist in the assessment and planning of transport networks and urban infrastructure. It supports data-driven decision-making by **highlighting patterns and trends in spatial interactions**, which can help improve the efficiency and sustainability of transport systems and urban layouts.

The example below shows an *Input Table (Matrix Layer)* and the resulting *Origin-Destination Lines* based on the *Zipcode Areas (Geometry Layer)*.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
  <img src={require('/img/toolbox/geoanalysis/origin_destination/od_example.png').default} alt="Origin Destination Tool in GOAT" style={{ maxHeight: "700px", maxWidth: "700px", objectFit: "cover"}}/>
</div> 


## 2. Example use cases

- Visualizing the commuter flows between residential areas (origins) and workplaces (destinations).
- Assessing the public transport passenger flows between different stations.
- Analyzing the flow of people from residential areas (origins)  to shopping locations (destinations).


## 3. How to use the tool?

<div class="step">
  <div class="step-number">1</div>
  <div class="content">Click on <code>Toolbox</code> <img src={thematicIcon} alt="toolbox" style={{width: "25px"}}/>. </div>
</div>

<div class="step">
  <div class="step-number">2</div>
  <div class="content">Under the <code>Geoanalysis</code> menu, click on <code>Origin Destination</code>.</div>
</div>


<img src={require('/img/toolbox/geoanalysis/origin_destination/overview.png').default} alt="Origin Destination Tool Overview" style={{ maxHeight: "auto", maxWidth: "auto", objectFit: "cover"}}/>


### Layer

<div class="step">
  <div class="step-number">3</div>
  <div class="content">Select your <code>Geometries Layer</code> (this should be a feature layer containing the geometries of the origins and destinations and an attribute that can be used as an identifier to match the OD-connections with the geometries) and <code>Unique Id Field</code>.</div>
</div>

### Matrix

<div class="step">
  <div class="step-number">4</div>
  <div class="content">Select the <code>Matrix Table</code> (the table with the origin-destination-matrix) and <code>Origin Field</code>.</div>
</div>



<div class="step">
  <div class="step-number">5</div>
  <div class="content">Select your <code>Destination Field</code> (the field that contains the destinations in the origin-destination matrix).</div>
</div>

<div class="step">
  <div class="step-number">6</div>
  <div class="content">Select your <code>Weight Field</code> (the field that contains the weights in the origin-destination matrix).</div>
</div>

<div class="step">
  <div class="step-number">7</div>
  <div class="content">Click on <code>Run</code>.</div>
</div>

:::tip Hint

Depending on the complexity of the OD-matrix, the calculation might take some minutes. The [status bar](../../workspace/home#status-bar) shows the current progress.

:::

### Results 

<div class="step">
  <div class="step-number">8</div>
  <div class="content">As soon as the calculation process is finished, the resulting layers will be added to the map. The results consist of one layer called <b>"O-D Relation"</b>, showing the lines between the origins and destinations, and one layer called <b>"O-D Point"</b> which provides all origins and destination points (for polygon geometries, the centroids are used).<p></p>
  If you click on an "O-D Relation" item on the map, you can view the attribute details, such as the <b>origin</b>, <b>destination</b> and <b>weight</b> of this relation.</div>
</div>


<img src={require('/img/toolbox/geoanalysis/origin_destination/result.png').default} alt="Origin Destination Result in GOAT" style={{ maxHeight: "auto", maxWidth: "auto", objectFit: "cover"}}/>

:::tip Tip
Want to style your result layer and create nice-looking maps? See [Styling](../../map/layer_style/styling).
:::