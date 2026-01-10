---
sidebar_position: 7
---

# Erase

This tool allows you to **remove portions of input features that overlap with erase geometry**.

## 1. Explanation

The **Erase** tool removes portions of input features that overlap with the erase features. It is essentially the opposite of Clip. The output contains only the input features (or parts of them) that fall **outside** the extent of the erase layer.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>

  <img src={require('/img/toolbox/geoprocessing/erase.png').default} alt="Buffer Types" style={{ maxHeight: "400px", maxWidth: "400px", objectFit: "cover"}}/>

</div> 

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
  <div class="content">Under the <code>Geoprocessing</code> menu, click on <code>Erase</code>.</div>
</div>

<div class="step">
  <div class="step-number">3</div>
  <div class="content">Select the <code>Input layer</code>.</div>
</div>

<div class="step">
  <div class="step-number">4</div>
  <div class="content">Select the <code>Overlay layer</code> used as the erase mask.</div>
</div>

<div class="step">
  <div class="step-number">5</div>
  <div class="content">Click <code>Run</code> to execute the erase operation. Result will be added to the map.</div>
</div>
