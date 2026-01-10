---
sidebar_position: 5
---

# Dissolve

This tool allows you to **merge features of one layer that share common attribute values** or dissolve all features into a single geometry.

## 1. Explanation

The **Dissolve** tool merges features based on shared attribute values or combines all features into a unified geometry. This operation eliminates internal boundaries between features that have the same characteristics, creating simplified output layers. It's commonly used for administrative boundary consolidation and data generalization.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>

  <img src={require('/img/toolbox/geoprocessing/dissolve.png').default} alt="Buffer Types" style={{ maxHeight: "400px", maxWidth: "400px", objectFit: "cover"}}/>

</div> 

## 2. Example use cases 

- Merge neighboring districts that belong to the same administrative unit.
- Combine adjacent parcels with the same land use classification.

## 3. How to use the tool?

<div class="step">
  <div class="step-number">1</div>
  <div class="content">Click on <code>Toolbox</code> <img src={require('/img/icons/toolbox.png').default} alt="Options" style={{ maxHeight: "20px", maxWidth: "20px", objectFit: "cover"}}/>. </div>
</div>

<div class="step">
  <div class="step-number">2</div>
  <div class="content">Under the <code>Geoprocessing</code> menu, click on <code>Dissolve</code>.</div>
</div>

<div class="step">
  <div class="step-number">3</div>
  <div class="content">Select the <code>Input layer</code> containing the features you want to dissolve.</div>
</div>

<div class="step">
  <div class="step-number">4</div>
  <div class="content">On <code>Dissolve Settings</code>, choose the fields to group by when dissolving. Features with matching values will be merged. If empty, all features are merged into one.</div>
</div>

<div class="step">
  <div class="step-number">5</div>
  <div class="content">If your layer has numeric fields, enable <code>Statistics</code> to calculate summary values. Select the <code>Operation</code> (sum, mean, count, etc.) and choose the <code>Field</code> to aggregate during dissolve.</div>
</div>

<div class="step">
  <div class="step-number">6</div>
  <div class="content">Click <code>Run</code> to execute the dissolve. Result will be added to the map.</div>
</div>
