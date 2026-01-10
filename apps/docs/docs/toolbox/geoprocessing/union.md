---
sidebar_position: 6
---

# Union

This tool allows you to **compute the geometric union of features from two layers**.

## 1. Explanation

Combines **features from two polygon layers** into a single layer. The output includes all the geometry from both inputs (like a boolean OR operation). Where features overlap, they are split, and attributes from both layers are assigned to the overlapping portions. Non-overlapping areas retain attributes only from their original layer.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>

  <img src={require('/img/toolbox/geoprocessing/union.png').default} alt="Buffer Types" style={{ maxHeight: "400px", maxWidth: "400px", objectFit: "cover"}}/>

</div> 

## 2. Example use cases 

- Combine two different land use datasets into a single comprehensive map.
- Merge zoning districts with school districts to analyze all unique combinations of administrative boundaries.

## 3. How to use the tool?

<div class="step">
  <div class="step-number">1</div>
  <div class="content">Click on <code>Toolbox</code> <img src={require('/img/icons/toolbox.png').default} alt="Options" style={{ maxHeight: "20px", maxWidth: "20px", objectFit: "cover"}}/>. </div>
</div>

<div class="step">
  <div class="step-number">2</div>
  <div class="content">Under the <code>Geoprocessing</code> menu, click on <code>Union</code>.</div>
</div>

<div class="step">
  <div class="step-number">3</div>
  <div class="content">Select the first <code>Input layer</code>.</div>
</div>

<div class="step">
  <div class="step-number">4</div>
  <div class="content">Select the second layer on <code>Overlay layer</code>.</div>
</div>

<div class="step">
  <div class="step-number">5</div>
  <div class="content">Choose the <code>Overlay Fields Prefix</code> which will be added to the attributes from the overlay layer to distinguish them in the output.</div>
</div>

<div class="step">
  <div class="step-number">6</div>
  <div class="content">Click <code>Run</code> to execute the union. Result will be added to the map.</div>
</div>
