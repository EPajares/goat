---
sidebar_position: 4
---


import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';

 
# Scenarios

Scenarios **let you test "what-if" situations by modifying existing layers or creating new features**. Add, edit, or delete points, lines, and polygons, **then run accessibility indicators to analyze how these changes impact accessibility—all without altering your original data**.

You can also modify the **Street Network - Edges** base layer, which represents the road network and affects routing calculations.

:::info 
Only **geographical layers** can be modified in scenarios. Tables and rasters cannot be edited. You can learn more about [data types](../data/data_types).
:::

## 1. How to create and edit scenarios?

<div class="step">
  <div class="step-number">1</div>
  <div class="content">Click on <code>Scenarios</code> <img src={require('/img/icons/compass-drafting.png').default} alt="Scenarios" style={{ maxHeight: "20px", maxWidth: "20px", objectFit: "cover"}}/>.</div>
</div>

<div class="step">
  <div class="step-number">2</div>
  <div class="content">Click <code>Create scenario</code> and name your scenario.</div>
</div>

<div class="step">
  <div class="step-number">3</div>
  <div class="content">Click on <code>More Options</code> <img src={require('/img/icons/3dots.png').default} alt="Options" style={{ maxHeight: "20px", maxWidth: "20px", objectFit: "cover"}}/> next to your scenario name, then select <code>Edit</code>.</div>
</div>

<div class="step">
  <div class="step-number">4</div>
  <div class="content">Choose a layer in <code>Select layer</code>, then pick from <b>Edit tools</b>: <code>draw</code> <img src={require('/img/icons/plus.png').default} alt="Draw" style={{ maxHeight: "20px", maxWidth: "20px", objectFit: "cover"}}/>, <code>modify</code> <img src={require('/img/icons/edit.png').default} alt="Modify" style={{ maxHeight: "20px", maxWidth: "20px", objectFit: "cover"}}/>, or <code>delete</code> <img src={require('/img/icons/trash.png').default} alt="Delete" style={{ maxHeight: "20px", maxWidth: "20px", objectFit: "cover"}}/> features.</div>
</div>

<Tabs>
  <TabItem value="Draw" label="Draw" default className="tabItemBox">
    
Depending on the layer type, you can draw different geographical shapes:

- `Point`: **Click on the map where you want to add a point**. Fill in attributes if required, then click `Save`. **New features appear in blue**.

- `Line`: **Click to start drawing, continue clicking to shape the line, double-click to finish**. Fill in attributes if required, then click `Save`. **New features appear in blue**.

- `Polygon`: **Click to start drawing, continue clicking for each corner, click the starting point to complete**. Fill in attributes if required, then click `Save`. **New features appear in blue**.


  </TabItem>

  <TabItem value="Modify" label="Modify" default className="tabItemBox">

- **Click a feature** to select it, edit its attributes, then click `Save`. **Modified features appear in yellow**.



  </TabItem>

  <TabItem value="Delete" label="Delete" default className="tabItemBox">

- **Click the feature** you want to remove, then click `Delete`. **Deleted features appear in red**.


  </TabItem>

</Tabs>

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
  <img src={require('/img/scenarios/Polygon_drawing-final.gif').default} alt="Drawing polygons" style={{ maxHeight: '500px', maxWidth: '500px', objectFit: 'cover' }}/>
</div>

<p></p>
<div class="step">
  <div class="step-number">5</div>
  <div class="content">Click <code>Toolbox</code> and select an <code>indicator</code>.</div>  
</div>
  
<div class="step">
  <div class="step-number">6</div>
  <div class="content">After selecting all the settings, choose the <code>scenario</code> from the dropdown to analyze your changes.</div>  
</div>

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
  <img src={require('/img/scenarios/scenario_indicator.png').default} alt="Layer analysis with scenarios" style={{ maxHeight: 'auto', maxWidth: 'auto', objectFit: 'cover' }}/>
</div>

## 2. Managing scenarios

Create multiple scenarios to test different configurations:

- **Select**: Click a scenario to view its changes
- **Modify**: Use the options menu <img src={require('/img/icons/3dots.png').default} alt="Options" style={{ maxHeight: "20px", maxWidth: "20px", objectFit: "cover"}}/> to rename, delete, or edit
- **Track changes**: Modified layers show <img src={require('/img/icons/compass-drafting.png').default} alt="Scenario indicator" style={{ maxHeight: "20px", maxWidth: "20px", objectFit: "cover"}}/> with a number
- **Deselect**: Click the active scenario again to return to the original map

## 3. Street Network - Edges

**Street Network - Edges** is a base layer representing the [road network](../data/data_basis#street-network-and-topography) available in all projects. You can only see this layer when editing scenarios at high zoom levels.

Use `Scenarios` to modify street lines—add new roads, close existing ones, or change road properties.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
  <img src={require('/img/scenarios/street_network.png').default} alt="Drawing polygons" style={{ maxHeight: 'auto', maxWidth: '80%', objectFit: 'cover' }}/>
</div>
<p></p>

:::info
Street Network changes only affect **[Catchment Area](../further_reading/glossary#catchment-area)** calculations. Other indicators use the original network.
:::