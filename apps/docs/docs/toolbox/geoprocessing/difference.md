---
sidebar_position: 6
---

# Erase

This tool allows you to **create features by removing portions that overlap with erase geometry**.

## 1. Explanation

Removes **portions of the input features that overlap with the erase features.** It is essentially the opposite of Clip. The output contains only the input features (or parts of them) that fall **outside** the extent of the erase layer.

## 2. Example use cases 

- Remove water bodies from a land area map.
- Exclude protected areas from a map of potential development sites.

## 3. How to use the tool?

<div class="step">
  <div class="step-number">1</div>
  <div class="content">Click on <code>Toolbox</code> <img src={require('/img/icons/toolbox.png').default} alt="Options" style={{ maxHeight: "20px", maxWidth: "20px", objectFit: "cover"}}/>. </div>
</div>

<div class="step">
  <div class="step-number">2</div>
  <div class="content">Under the <code>Geoprocessing</code> menu, click on <code>Erase</code> (or Difference).</div>
</div>

<div class="step">
  <div class="step-number">3</div>
  <div class="content">Select the input layer.</div>
</div>

<div class="step">
  <div class="step-number">4</div>
  <div class="content">Select the layer to erase with (Erase Layer).</div>
</div>

<div class="step">
  <div class="step-number">5</div>
  <div class="content">Click <code>Run</code> to execute the tool. Result will be added to the map.</div>
</div>
