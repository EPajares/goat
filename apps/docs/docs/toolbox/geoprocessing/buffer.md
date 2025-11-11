---
sidebar_position: 1
---

import thematicIcon from "/img/toolbox/data_management/join/toolbox.webp"
import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';



# Buffer

This tool allows you to **create zones around points, lines, or polygons with a specified distance**.

<iframe width="674" height="378" src="https://www.youtube.com/embed/Yboi3CwOLPM?si=FuSPRmK6zTB-GVJ1" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>

## 1. Explanation

A buffer is a tool used to **delineate the catchment area around a specific point, line, or polygon illustrating the extent of influence or reach from that feature.** Users can define the ``distance`` of the buffer, thereby customizing the radius of the area covered.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>

  <img src={require('/img/toolbox/geoprocessing/buffer/buffer_types.png').default} alt="Buffer Types" style={{ maxHeight: "400px", maxWidth: "400px", objectFit: "cover"}}/>

</div> 

## 2. Example use cases 

- Analyze population within 500m of train stations
- Count shops accessible within 1000m of bus stops


## 3. How to use the tool?


<div class="step">
  <div class="step-number">1</div>
  <div class="content">Click on <code>Toolbox</code> <img src={thematicIcon} alt="toolbox" style={{width: "25px"}}/>. </div>
</div>

<div class="step">
  <div class="step-number">2</div>
  <div class="content">Under the <code>Geoprocessing</code> menu, click on <code>Buffer</code>.</div>
</div>

### Select layer to buffer 

<div class="step">
  <div class="step-number">3</div>
  <div class="content">Select the <code>Layer to buffer</code>, around which you like to create the buffer.</div>
</div>

### Buffer Settings 

<div class="step">
  <div class="step-number">4</div>
  <div class="content">Define via the <code>Buffer Distance</code>: how many meters from your points, lines, or shapes the buffer should extend.</div>
</div>

<div class="step">
  <div class="step-number">5</div>
  <div class="content">Define in how many <code>Buffer Steps</code> the buffer should be divided.</div>
</div>

<div class="step">
  <div class="step-number">6</div>
  <div class="content">If you keep the <code>Polygon Union</code> disabled, GOAT will generate single buffers around each input geometry. If you enable it, GOAT will create a **geometric union** of all steps of the buffer polygons. In this case, the buffer with the biggest extent also includes all buffer areas of the smaller extent. This approach is useful if you want to see the total area covered by all your buffer steps combined.</div>
</div>

<div class="step">
  <div class="step-number">7</div>
  <div class="content">If you enabled Polygon Union, you can enable the `Polygon Difference`. GOAT will create a **geometric difference** of the buffers. It subtracts one polygon from another, resulting in polygon shapes where the **buffers do not overlap**.</div>
</div>

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>

  <img src={require('/img/toolbox/geoprocessing/buffer/polygon_union_difference.png').default} alt="Polygon Union+ Polygon Difference Result in GOAT" style={{ maxHeight: "auto", maxWidth: "auto", objectFit: "cover"}}/>

</div> 
<div class="step">
  <div class="step-number">8</div>
  <div class="content">Click on <code>Run</code>. This starts the calculation of the buffer.</div>
</div>

### Results

As soon as this task is accomplished, the resulting layer called **"Buffer"** will be added to your map.

:::tip Tip

Want to style your buffers and create nice-looking maps? See [Styling](../../map/layer_style/style/styling.md).

:::
