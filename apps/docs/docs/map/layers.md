---
sidebar_position: 2
---


import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';


# Layers

**In the Layers section, layers can be added and organized**. Among others, the layer order can be adjusted, layers can be enabled/disabled, duplicated, renamed, downloaded, and removed.

<iframe width="100%" height="500" src="https://www.youtube.com/embed/McjAUSq2p_k?si=2hh0hU10l95Tkjqt" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>



## How to manage your Layers

### Add Layers

You can add layers from [different sources](../data/dataset_types) to your map. You can either integrate **datasets from your data explorer or the catalog explorer** or upload new **datasets from your local device** (GeoPackage, GeoJSON, Shapefile, KML, CSV, or XLSX). External layers can be added by inserting the **url of the external source** (WMS, WMTS, or MVT).

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/map/layers/add_layer.png').default} alt="Add layers in GOAT" style={{ maxHeight: "flex", maxWidth: "flex", objectFit: "cover"}}/>
</div>

<p></p>
<div class="step">
  <div class="step-number">1</div>
  <div class="content">Navigate to the <code>Layers</code> menu via the **left sidebar**.</div>
</div>

<div class="step">
  <div class="step-number">2</div>
  <div class="content">Click on <code>+ Add Layer</code> to **open the layer options**. </div>
</div>

<div class="step">
  <div class="step-number">3</div>
  <div class="content">Select if you like to integrate a dataset using the: <code>Data Explorer</code>, <code>Dataset Upload</code>, <code>Dataset External</code> or <code>Dataset Catalog</code> to **choose your data source**.</div>
</div>

<Tabs>
  <TabItem value="Dataset Explorer" label="Dataset Explorer" default className="tabItemBox">


<div class="step">
  <div class="step-number">4</div>
  <div class="content">Select the file you want to **import**.</div>
</div>

<div class="step">
  <div class="step-number">5</div>
  <div class="content">Click on <code>+ Add Layer</code> to **add the selected file**.</div>
</div>


</TabItem>
<TabItem value="Dataset Upload" label="Dataset Upload" className="tabItemBox">


<div class="step">
  <div class="step-number">4</div>
  <div class="content">Select the file you want to **import**.</div>
</div>

<div class="step">
  <div class="step-number">5</div>
  <div class="content">Define the name of the dataset and **add a description**, if you like.</div>
</div>

<div class="step">
  <div class="step-number">6</div>
  <div class="content">Check the information and click on <code>Upload</code> to **upload the dataset**.</div>
</div>


  </TabItem>
  <TabItem value="Catalog Explorer" label="Catalog Explorer" className="tabItemBox">

<div class="step">
  <div class="step-number">4</div>
  <div class="content">Browse <code>GOAT Dataset Catalog</code> to **explore available datasets**.</div>
</div>

<div class="step">
  <div class="step-number">5</div>
  <div class="content">Select the Dataset you want to **import**.</div>
</div>

<div class="step">
  <div class="step-number">6</div>
  <div class="content">Click on <code>+ Add Layer</code> to **add the selected dataset**.</div>
</div>


 </TabItem>
  <TabItem value="Dataset External" label="Dataset External" default className="tabItemBox">
  
<div class="step">
  <div class="step-number">4</div>
  <div class="content">Insert your <code>external URL</code> and **follow the steps** depending on the type of dataset you would like to add.</div>
</div>

<Tabs>
  <TabItem value="WFS" label="WFS" default className="tabItemBox">

  <div class="step">
      <div class="content"> <p>When you would like to add a WFS layer you need to have a **GetCapabilities** link. </p>
      In the next step you can choose which layer you would like to add to your dataset. *You can only choose one layer at a time.*</div>
      </div>
     </TabItem>

  <TabItem value="WMS" label="WMS" className="tabItemBox">
     
  <div class="step">
      <div class="content"> <p>When you would like to add a WMS layer you need to have a **GetCapabilities** link.</p> Here you have the option to select multiple layers, but when added to GOAT it *will be merged onto one layer.* </div>
      </div>
      </TabItem>

  <TabItem value="WMTS" label="WMTS" className="tabItemBox">

  <div class="step">
      <div class="content"> <p>You can add a WMTS to your dataset via a **direct URL** or **GetCapabilities** link. You can only choose *one layer* at a time if your URL contains more than one layer.</p>
      The projection needs to be *WEB Mercator (EPSG:3857) and GoogleMaps compatible*. Because they have different zoom levels, the dataset would not show up in the list of available layers if it doesn't meet both requirements.</div>
      </div>
    </TabItem>
  </Tabs>
</TabItem>
</Tabs>

:::tip tip

You can manage all your datasets on the [Datasets page](../workspace/datasets). 

:::

### Organize Layers

Once you have added a dataset to the map, it will be visible in the **Layer List**. From there you can organize the different layers.

#### Layer Order

When visualizing several data sets at once, the layer order is crucial for creating clear, readable maps. Therefore, **the layer order can be changed interactively**.

Hover over the **left border** of the layer in the layer list until an arrow symbol appears, then **drag and drop to move** the layer to your desired position.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
  <img src={require('/img/map/layers/layer_order.gif').default} alt="Layer Order" style={{ maxHeight: "flex", maxWidth: "flex", objectFit: "cover"}}/>
</div> 

#### Show / Hide Layers

Click the <code>eye icon</code> for that layer in the layer list to temporarily **hide** a layer from the map view. Clicking the eye again will **make the layer visible** again.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
  <img src={require('/img/map/layers/hide_layers.gif').default} alt="Hide Layer" style={{ maxHeight: "flex", maxWidth: "flex", objectFit: "cover"}}/>
</div> 

#### Options

By clicking on <code>more options</code> <img src={require('/img/map/filter/3dots.png').default} alt="Options" style={{ maxHeight: "25px", maxWidth: "25px", objectFit: "cover"}}/> icon you have further options to **manage and organize** the selected layer.

<div style={{ display: 'flex', justifyContent: 'center' }}>
<img src={require('/img/map/layers/layer_options.png').default} alt="Layer Options" style={{ maxHeight: "250px", maxWidth: "250px", objectFit: "cover", alignItems: 'center'}}/>
</div>

<p></p>

:::tip tip

Want to change the design of your layers? See [Layer Style](../category/layer-styling).  
Only want to visualize parts of your dataset? See [Filter](../map/filter). 

:::