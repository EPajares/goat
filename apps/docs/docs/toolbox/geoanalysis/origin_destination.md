---
sidebar_position: 4
---


# Origin Destination

The Origin Destination tool allows you to **visualize movement flows between different locations by creating lines that connect origins to destinations**. Perfect for analyzing commuter patterns, transport flows, and spatial interactions.

<div style={{ display: 'flex', justifyContent: 'center' }}>
<iframe width="674" height="378" src="https://www.youtube.com/embed/VmHe1NfApRw?si=xzUGIkh2IHn6DTTl" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>
</div>

## 1. Explanation

The Origin-Destination tool creates **straight lines connecting starting points (origins) to endpoints (destinations)** based on your data. It takes a matrix table with flow data and a geometry layer with locations, then **visualizes the connections and their weights** as lines on the map.

The example below shows an *Input Table (Matrix Layer)* and the resulting *Origin-Destination Lines* based on the *Zipcode Areas (Geometry Layer)*.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
  <img src={require('/img/toolbox/geoanalysis/origin_destination/od_example.png').default} alt="Origin Destination Tool in GOAT" style={{ maxHeight: "auto", maxWidth: "500px", objectFit: "cover"}}/>
</div> 


## 2. Example use cases

- Visualizing the commuter flows between residential areas (origins) and workplaces (destinations).
- Assessing the public transport passenger flows between different stations.
- Analyzing the flow of people from residential areas (origins)  to shopping locations (destinations).


## 3. How to use the tool?

<div class="step">
  <div class="step-number">1</div>
  <div class="content">Click on <code>Toolbox</code> <img src={require('/img/icons/toolbox.png').default} alt="Options" style={{ maxHeight: "20px", maxWidth: "20px", objectFit: "cover"}}/>. </div>
</div>

<div class="step">
  <div class="step-number">2</div>
  <div class="content">Under the <code>Geoanalysis</code> menu, click on <code>Origin Destination</code>.</div>
</div>

### Layer

<div class="step">
  <div class="step-number">3</div>
  <div class="content">Select your <code>Geometries Layer</code>. This should be a <b>feature layer containing the geometries of the origins and destinations and an attribute that can be used as an identifier </b> to match the OD-connections with the geometries.</div>
</div>

<div class="step">
  <div class="step-number">4</div>
  <div class="content">Select your <code>Unique Id Field</code>.</div>
</div>

### Matrix

<div class="step">
  <div class="step-number">5</div>
  <div class="content">Select the <code>Matrix Table</code>. This is the table with the <b>origin-destination-matrix and the Origin Field</b>.</div>
</div>

<div class="step">
  <div class="step-number">6</div>
  <div class="content">Select your <code>Destination Field</code>. This is the <b>field that contains the destinations </b> in the origin-destination matrix.</div>
</div>

<div class="step">
  <div class="step-number">7</div>
  <div class="content">Select your <code>Weight Field</code>. This is the <b>field that contains the weights</b> in the origin-destination matrix.</div>
</div>

<div class="step">
  <div class="step-number">8</div>
  <div class="content">Click on <code>Run</code>.</div>
</div>

:::tip Hint

Depending on the complexity of the OD-matrix, the calculation might take some minutes. The [status bar](../../workspace/home#status-bar) shows the current progress.

:::

### Results 

As soon as the calculation process is finished, the resulting layers will be added to the map. The results consist of one layer called **"O-D Relation"**, showing the lines between the origins and destinations, and one layer called **"O-D Point"** which provides all origins and destination points (for polygon geometries, the centroids are used).

If you click on an "O-D Relation" item on the map, you can view the attribute details, such as the **origin**, **destination** and **weight** of this relation.

<div style={{ display: 'flex', justifyContent: 'center' }}>
<img src={require('/img/toolbox/geoanalysis/origin_destination/result.png').default} alt="Origin Destination Result in GOAT" style={{ maxHeight: "auto", maxWidth: "80%", objectFit: "cover"}}/>
</div>

<p></p>

:::tip Tip
Want to style your result layer and create nice-looking maps? See [Styling](../../map/layer_style/style/styling).
:::