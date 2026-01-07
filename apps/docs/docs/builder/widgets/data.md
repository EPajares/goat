---
sidebar_position: 2
---

# Data

**This section contains widgets that help you interact with and analyze your data**: **Filter** and **Numbers**. 

## Filter

This widget is an interactive element, which **allows the user to filter the data on the configured layer based on the selected attribute field**. Viewers can use this as a **cropping tool on the maps**.

<div class="step">
  <div class="step-number">1</div>
  <div class="content">Drag and drop the <code>Filter</code> widget on a panel.</div>
</div>

<div class="step">
  <div class="step-number">2</div>
  <div class="content">Select your <code>layer</code> and choose the <code>field</code> <b>you want to filter by</b>.</div>
</div>

<div class="step">
  <div class="step-number">3</div>
  <div class="content">Optionally add a <code>Placeholder</code> text which appears before the filtering is applied.</div>
</div>

<div class="step">
  <div class="step-number">4</div>
  <div class="content">Enable or disable <code>Cross filter</code> to make this <b>widget interact with other data widgets</b>. When enabled, filtering data in one widget will automatically update all other connected widgets on your dashboard.</div>
</div>

<div class="step">
  <div class="step-number">5</div>
  <div class="content">Enable or disable the option <code>Zoom to selection</code>, which will <b>automatically pan the map view to the filtered data</b>.</div>
</div>

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/builder/builder_filter.gif').default} alt="recent datasets" style={{ maxHeight: "500px", maxWidth: "auto", objectFit: "cover"}}/>
</div> 

## Numbers

Choose from different statistic methods to be computed on a layer.

<div class="step">
  <div class="step-number">1</div>
  <div class="content">Drag and drop the <code>Numbers</code> widget on a panel.</div>
</div>

<div class="step">
  <div class="step-number">2</div>
  <div class="content">Select your <code>layer</code>. </div>
</div>

<div class="step">
  <div class="step-number">3</div>
  <div class="content">Choose the <code>statistic method</code> you want to apply. It can be <code>Count</code>, <code>Sum</code>, <code>Min</code>, <code>Max</code>, or add your own [<code>Expression</code>](../expressions). </div>
</div>

<div class="step">
  <div class="step-number">4</div>
  <div class="content">Choose the <code>field</code> <b>onto which the statistics should be applied</b>. <i>Sum, min, and max can only be applied to numeric fields.</i></div>
</div>

<div class="step">
  <div class="step-number">5</div>
  <div class="content">Enable or disable <code>Cross filter</code> to make this <b>widget update depending on all other connected widgets </b> on your dashboard.</div>
</div>

<div class="step">
  <div class="step-number">6</div>
  <div class="content">Enable or disable the option to <code>Filter viewport</code>,  which <b>makes only the data within the current map view visible</b>.</div>
</div>

<div class="step">
  <div class="step-number">7</div>
  <div class="content">Set the <code>number format</code> from the dropdown list. The default number format is dynamic based on the language of the interface.</div>
</div>

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/builder/builder_number.gif').default} alt="recent datasets" style={{ maxHeight: "500px", maxWidth: "auto", objectFit: "cover"}}/>
</div> 