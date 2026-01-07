---
sidebar_position: 1
---

import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';



# Buffer

This tool allows you to **create zones around points, lines, or polygons with a specified distance**.

<div style={{ display: 'flex', justifyContent: 'center' }}>
<iframe width="674" height="378" src="https://www.youtube.com/embed/Yboi3CwOLPM?si=FuSPRmK6zTB-GVJ1" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>
</div>

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
  <div class="content">Click on <code>Toolbox</code> <img src={require('/img/icons/toolbox.png').default} alt="Options" style={{ maxHeight: "20px", maxWidth: "20px", objectFit: "cover"}}/>. </div>
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
  <div class="content">Define via the <code>Buffer Distance</code>: <b>how many meters from your points, lines, or shapes the buffer should extend</b>.</div>
</div>

<div class="step">
  <div class="step-number">5</div>
  <div class="content">Define in how many <code>Buffer Steps</code> the buffer should be divided.</div>
</div>

<div class="step">
  <div class="step-number">6</div>
  <div class="content">Configure the <code>Polygon Union</code> setting:
    <ul>
      <li><b>Disabled</b>: GOAT will generate single buffers around each input geometry</li>
      <li><b>Enabled</b>: GOAT will create a <b>geometric union of all steps of the buffer polygons</b>. The buffer with the biggest extent also includes all buffer areas of the smaller extent. This approach is useful if you want to see the total area covered by all your buffer steps combined.</li>
    </ul>
  </div>
</div>

<div class="step">
  <div class="step-number">7</div>
  <div class="content">If you <b>enabled Polygon Union</b>, you can enable the <code>Polygon Difference</code>. GOAT will create a <b>geometric difference of the buffers</b>. It subtracts one polygon from another, resulting in polygon shapes where the <b>buffers do not overlap</b>.</div>
</div>

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/toolbox/geoprocessing/buffer/polygon_union_difference.png').default} alt="Polygon Union+ Polygon Difference Result in GOAT" style={{ maxHeight: "auto", maxWidth: "60%", objectFit: "cover"}}/>
</div> 

<p></p>

<div class="step">
  <div class="step-number">8</div>
  <div class="content">Click on <code>Run</code>. This starts the calculation of the buffer. As soon as this task is accomplished, the resulting layer called <b>"Buffer"</b> will be added to your map.</div>
</div>

<p></p>

:::tip Tip

Want to style your buffers and create nice-looking maps? See [Styling](../../map/layer_style/style/styling.md).

:::
