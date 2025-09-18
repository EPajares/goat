---
sidebar_position: 1
---

import thematicIcon from "/img/toolbox/data_management/join/toolbox.webp"
import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';



# Buffer

The buffer creates a **zone around** given **points, lines, or polygons** with a specified buffer distance.

<iframe width="100%" height="500"src="https://www.youtube.com/embed/Yboi3CwOLPM?si=FuSPRmK6zTB-GVJ1" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>

## 1. Explanation

A **buffer** is a tool used to delineate the catchment area around a specific point, line, or polygon illustrating the extent of influence or reach from that point. Users can define the ``distance`` of the buffer, thereby customizing the radius of the area covered.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>

  <img src={require('/img/toolbox/geoprocessing/buffer/buffer_types.png').default} alt="Buffer Types" style={{ maxHeight: "500px", maxWidth: "500px", objectFit: "cover"}}/>

</div> 

## 2. Example use cases 

- How many people live within a 500m buffer distance from the train station? 
- How many shops are accessible within a 1000m buffer distance from a bus stop?


## 3. How to use the tool?


<div class="step">
  <div class="step-number">1</div>
  <div class="content">Click on <code>Toolbox</code> <img src={thematicIcon} alt="toolbox" style={{width: "25px"}}/>. </div>
</div>

<div class="step">
  <div class="step-number">2</div>
  <div class="content">Under the <code>Geoprocessing</code> menu, click on <code>Buffer</code>.</div>
</div>


<img src={require('/img/toolbox/geoprocessing/buffer/overview.png').default} alt="Buffer Tool in GOAT" style={{ maxHeight: "auto", maxWidth: "auto", objectFit: "cover"}}/>

### Select layer to buffer 


<div class="step">
  <div class="step-number">3</div>
  <div class="content">Select the <code>Layer to buffer</code>, around which you like to create the buffer.</div>
</div>

### Buffer Settings 


<div class="step">
  <div class="step-number">4</div>
  <div class="content">Define via the buffer <code>Buffer Distance</code> how many meters from your points, lines, or shapes the buffer should extend.</div>
</div>

<div class="step">
  <div class="step-number">5</div>
  <div class="content">Define in how many <code>Buffer Steps</code> the buffer should be divided.</div>
</div>

:::tip HINT
Depending on which geometric results you are aiming for, you can first select, if all geometries shall be combined (**Polygon Union**). This means, if e.g. a buffer is created around neighboring points, whether you like to have **single buffers** (**no union**) or **combined buffers** (**union**) as a result.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>

  <img src={require('/img/toolbox/geoprocessing/buffer/no_union_vs_union.png').default} alt="Buffer Union-No union Comparison" style={{ maxHeight: "400px", maxWidth: "400px", objectFit: "cover"}}/>

</div> 

In addition, if you decide on a Polygon Union, you can choose whether you like to have each buffer as a **filled polygon (no difference)** or if you like to apply a **geometric difference between each buffer step (difference)**.


<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>

  <img src={require('/img/toolbox/geoprocessing/buffer/union_vs_union+difference.png').default} alt="Buffer Union-Buffer Difference Comparison" style={{ maxHeight: "400px", maxWidth: "400px", objectFit: "cover"}}/>

</div> 


:::

<Tabs>
<TabItem value="nounion" label="No Union" default className="tabItemBox">

#### No Union
If you calculate buffers **without a union**, GOAT will generate single buffers around each input geometry. 

<div class="step">
  <div class="step-number">6</div>
  <div class="content">Disable <code>Polygon Union</code>.</div>
</div>

<div class="step">
  <div class="step-number">7</div>
  <div class="content">Click on <code>Run</code>. This starts the calculation of the buffer.</div>
</div>

### Results

<div class="step">
  <div class="step-number">8</div>
  <div class="content">As soon as this task is accomplished, the resulting layer called <b>"Buffer"</b> will be added to your map.</div>
</div>

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>

  <img src={require('/img/toolbox/geoprocessing/buffer/result_no_union.png').default} alt="No union Result in GOAT" style={{ maxHeight: "auto", maxWidth: "auto", objectFit: "cover"}}/>

</div> 

</TabItem>

  <TabItem value="polygonunion" label="Union" default className="tabItemBox">

#### Polygon Union
The  ``Polygon Union`` creates a **geometric union** of all steps of the buffer polygons. It **combines** multiple polygons into a single polygon that encompasses all the areas of the individual polygons, i.e. the buffer with the biggest extent also includes all buffer areas of the smaller extent. This approach is useful if you want to see the total area covered by all your buffer steps combined. 

<div style={{ display: 'flex', flexDirection: 'column' }}>

  <img src={require('/img/toolbox/geoprocessing/buffer/polygon_union.png').default} alt="Polygon Union in GOAT" style={{ maxHeight: "auto", maxWidth: "auto", objectFit: "cover"}}/>

</div> 


<div class="step">
  <div class="step-number">6</div>
  <div class="content">Enable <code>Polygon Union</code>.</div>
</div>

<div class="step">
  <div class="step-number">7</div>
  <div class="content">Click on <code>Run</code>. This starts the calculation of the buffer.</div>
</div>

### Results

<div class="step">
  <div class="step-number">8</div>
  <div class="content">As soon as this task is accomplished, the resulting layer called <b>"Buffer"</b> will be added to your map.</div>
</div>

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>

  <img src={require('/img/toolbox/geoprocessing/buffer/result_union.png').default} alt="Polygon Union Result in GOAT" style={{ maxHeight: "auto", maxWidth: "auto", objectFit: "cover"}}/>

</div> 


  </TabItem>
  <TabItem value="polygondifference" label="Union + Difference " className="tabItemBox">

#### Polygon Union + Polygon Difference 
The  ``Polygon Difference`` operation creates a **geometric difference** of the buffers. It subtracts one polygon from another, resulting in polygon shapes where the **buffers do not overlap**.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>

  <img src={require('/img/toolbox/geoprocessing/buffer/polygon_difference.png').default} alt="Polygon Union+ Polygon Difference Result in GOAT" style={{ maxHeight: "auto", maxWidth: "auto", objectFit: "cover"}}/>

</div> 

<div class="step">
  <div class="step-number">6</div>
  <div class="content">Enable <code>Polygon Difference</code>.</div>
</div>

<div class="step">
  <div class="step-number">7</div>
  <div class="content">Click on <code>Run</code>. This starts the calculation of the buffer.</div>
</div>

### Results

<div class="step">
  <div class="step-number">8</div>
  <div class="content">As soon as this task is accomplished, the resulting layer called <b>"Buffer"</b> will be added to your map.</div>
</div>

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>

  <img src={require('/img/toolbox/geoprocessing/buffer/result_union.png').default} alt="Polygon Difference Result in GOAT" style={{ maxHeight: "auto", maxWidth: "auto", objectFit: "cover"}}/>

</div> 



  </TabItem>
</Tabs>




:::tip Tip

Want to style your buffers and create nice-looking maps? See [Styling](../../map/layer_style/style/styling.md).

:::

