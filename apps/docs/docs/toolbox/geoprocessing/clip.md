---
sidebar_position: 2
---

# Clip

This tool allows you to **extract input features that fall within the clip layer**.

## 1. Explanation

Refers to the process of **extracting a portion of a vector dataset based on the boundary of another polygon layer.** It acts like a "cookie cutter"—only the features (or parts of features) from the input layer that fall inside the clip layer are retained. The attributes of the input features are preserved, but the clip layer's attributes are not transferred.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>

  <img src={require('/img/toolbox/geoprocessing/clip.png').default} alt="Buffer Types" style={{ maxHeight: "400px", maxWidth: "400px", objectFit: "cover"}}/>

</div> 

## 2. Example use cases 

- Extract a subset of city roads based on a specific neighborhood boundary.
- Clip a land use map to a project area of interest.

## 3. How to use the tool?

<div class="step">
  <div class="step-number">1</div>
  <div class="content">Click on <code>Toolbox</code> <img src={require('/img/icons/toolbox.png').default} alt="Options" style={{ maxHeight: "20px", maxWidth: "20px", objectFit: "cover"}}/>. </div>
</div>

<div class="step">
  <div class="step-number">2</div>
  <div class="content">Under the <code>Geoprocessing</code> menu, click on <code>Clip</code>.</div>
</div>

<div class="step">
  <div class="step-number">3</div>
  <div class="content">Select the <code>Input layer</code> you want to clip.</div>
</div>

<div class="step">
  <div class="step-number">4</div>
  <div class="content">Select the <code>Overlay layer</code> you want to use as the clip layer.</div>
</div>

<div class="step">
  <div class="step-number">5</div>
  <div class="content">Click <code>Run</code> to execute the tool. The result will be added to the map.</div>
</div>
