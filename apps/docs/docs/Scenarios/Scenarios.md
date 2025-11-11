---
sidebar_position: 4
slug: /Scenarios
---


import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';

 
# Scenarios

Scenarios **let you test "what-if" situations by modifying existing layers or creating new features**. Add, edit, or delete points, lines, and polygons, **then run accessibility indicators to analyze how these changes impact accessibility—all without altering your original data**.

You can also modify the **Street Network - Edges** base layer, which represents the road network and affects routing calculations.

:::info 
Only **geographical layers** can be modified in scenarios. Tables and rasters cannot be edited. Learn more about [data types](../data/data_types).
:::

## 1. How to create and edit scenarios?

<div class="step">
  <div class="step-number">1</div>
  <div class="content">Click on `Scenarios` <img src={require('/img/scenarios/compass-drafting.png').default} alt="Scenarios" style={{ maxHeight: "20px", maxWidth: "20px", objectFit: "cover"}}/>.</div>
</div>

<div class="step">
  <div class="step-number">2</div>
  <div class="content">Click `Create scenario` and name your scenario.</div>
</div>

<div class="step">
  <div class="step-number">3</div>
  <div class="content">Click on `More Options` <img src={require('/img/scenarios/3dots.png').default} alt="Options" style={{ maxHeight: "20px", maxWidth: "20px", objectFit: "cover"}}/> next to your scenario name, then select `Edit`.</div>
</div>

<div class="step">
  <div class="step-number">4</div>
  <div class="content">Choose a layer in `Select layer`, then pick from `Edit tools`: **draw** <img src={require('/img/scenarios/add.png').default} alt="Draw" style={{ maxHeight: "20px", maxWidth: "20px", objectFit: "cover"}}/>, **modify** <img src={require('/img/scenarios/edit.png').default} alt="Modify" style={{ maxHeight: "20px", maxWidth: "20px", objectFit: "cover"}}/>, or **delete** <img src={require('/img/scenarios/trash-solid.png').default} alt="Delete" style={{ maxHeight: "20px", maxWidth: "20px", objectFit: "cover"}}/> features.</div>
</div>




<Tabs>
  <TabItem value="Draw" label="Draw" default className="tabItemBox">
    <div class="step">
      <div class="step-number">5</div>
      <div class="content">
        Depending on the layer type, you can draw different geographical shapes:
        - **Point**: **Click** on the map where you want to add a point. Fill in attributes if required, then click `Save`. **New features appear in blue**.
        <p></p>
        -  **Line**: **Click** to start drawing, continue clicking to shape the line, **double-click** to finish. Fill in attributes if required, then click `Save`. **New features appear in blue**.
        <p></p>
        - **Polygon**: **Click** to start drawing, continue clicking for each corner, **click the starting point** to complete.
        Fill in attributes if required, then click `Save`. **New features appear in blue**.
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
          <img src={require('/img/scenarios/Polygon_drawing-final.gif').default} alt="Drawing polygons" style={{ maxHeight: '500px', maxWidth: '500px', objectFit: 'cover' }}/>
        </div>
      </div>
    </div>
  </TabItem>

  <TabItem value="Modify" label="Modify" default className="tabItemBox">
    <div class="step">
      <div class="step-number">5</div>
      <div class="content">**Click** a feature to select it, edit its attributes, then click `Save`. **Modified features appear in yellow**.</div>
    </div>
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
      <img src={require('/img/scenarios/modify_features.png').default} alt="Modifying features" style={{ maxHeight: '500px', maxWidth: '500px', objectFit: 'cover' }}/>
    </div>
  </TabItem>

  <TabItem value="Delete" label="Delete" default className="tabItemBox">
    <div class="step">
      <div class="step-number">5</div>
      <div class="content">**Click** the feature you want to remove, then click `Delete`. **Deleted features appear in red**.</div>
    </div>
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
      <img src={require('/img/scenarios/delete_feature.png').default} alt="Deleting features" style={{ maxHeight: '500px', maxWidth: '500px', objectFit: 'cover' }}/>
    </div>
  </TabItem>

</Tabs>


<div class="step">
  <div class="step-number">6</div>
  <div class="content">Click `Toolbox` and select an `indicator`.</div>  
</div>
  
<div class="step">
  <div class="step-number">7</div>
  <div class="content">Choose your `modified layer` and select the `scenario` from the dropdown to analyze your changes.</div>  
</div>

![Layer analysis with scenarios](/img/scenarios/layer_analysis.png "Layer analysis with scenarios")

## 2. Managing scenarios

Create multiple scenarios to test different configurations:

- **Select**: Click a scenario to view its changes
- **Modify**: Use the options menu <img src={require('/img/scenarios/3dots.png').default} alt="Options" style={{ maxHeight: "20px", maxWidth: "20px", objectFit: "cover"}}/> to rename, delete, or edit
- **Track changes**: Modified layers show <img src={require('/img/scenarios/compass-drafting.png').default} alt="Scenario indicator" style={{ maxHeight: "20px", maxWidth: "20px", objectFit: "cover"}}/> with a number
- **Deselect**: Click the active scenario again to return to the original map

## 3. Street Network - Edges

**Street Network - Edges** is a base layer representing the [road network](../data/data_basis#street-network-and-topography) available in all projects. You can only see this layer when editing scenarios at high zoom levels.

Use `Scenarios` to modify street lines—add new roads, close existing ones, or change road properties.

![Street network](/img/scenarios/street_network.png "Street network")

:::info
Street Network changes only affect **[Catchment Area](../further_reading/glossary#catchment-area)** calculations. Other indicators use the original network.
:::

