---
sidebar_position: 3
---

# Centroid

This tool allows you to **create point features at the geometric center of each input feature**.

## 1. Explanation

Calculates the **geometric center (centroid) of polygon or line features and represents them as points.** For polygons, the centroid is the "center of mass". Note that for irregularly shaped polygons, the true centroid might fall outside the polygon boundary.

## 2. Example use cases 

- Convert building footprints to points for simplified visualization or analysis.
- Find the center point of city districts for labeling.

## 3. How to use the tool?

<div class="step">
  <div class="step-number">1</div>
  <div class="content">Click on <code>Toolbox</code> <img src={require('/img/icons/toolbox.png').default} alt="Options" style={{ maxHeight: "20px", maxWidth: "20px", objectFit: "cover"}}/>. </div>
</div>

<div class="step">
  <div class="step-number">2</div>
  <div class="content">Under the <code>Geoprocessing</code> menu, click on <code>Centroid</code>.</div>
</div>

<div class="step">
  <div class="step-number">3</div>
  <div class="content">Select the input layer.</div>
</div>

<div class="step">
  <div class="step-number">4</div>
  <div class="content">Click <code>Run</code> to generate the centroids. Result will be added to the map.</div>
</div>
