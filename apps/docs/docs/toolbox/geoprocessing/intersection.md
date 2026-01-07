---
sidebar_position: 4
---

# Intersect

This tool allows you to **compute the geometric intersection of features from two layers**.

## 1. Explanation

Computes the **geometric intersection of two vector layers.** The output contains only the areas where both input layers overlap. Unlike Clip, the attributes from **both** layers are combined and retained in the output features.

## 2. Example use cases 

- Find areas where a proposed development overlaps with protected environmental zones.
- Identify properties that are within a specific flood risk zone.

## 3. How to use the tool?

<div class="step">
  <div class="step-number">1</div>
  <div class="content">Click on <code>Toolbox</code> <img src={require('/img/icons/toolbox.png').default} alt="Options" style={{ maxHeight: "20px", maxWidth: "20px", objectFit: "cover"}}/>. </div>
</div>

<div class="step">
  <div class="step-number">2</div>
  <div class="content">Under the <code>Geoprocessing</code> menu, click on <code>Intersect</code>.</div>
</div>

<div class="step">
  <div class="step-number">3</div>
  <div class="content">Select the first input layer.</div>
</div>

<div class="step">
  <div class="step-number">4</div>
  <div class="content">Select the second input layer (Overlay Layer).</div>
</div>

<div class="step">
  <div class="step-number">5</div>
  <div class="content">Click <code>Run</code> to execute the intersection. Result will be added to the map.</div>
</div>
