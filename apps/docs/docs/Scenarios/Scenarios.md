---
sidebar_position: 4
slug: /Scenarios
---


import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';

 
# Scenarios
Besides analyzing existing real-world data & situations, GOAT allows you to create custom scenarios such as network changes or new infrastructure projects. Ways, points and polygons can be added, edited or removed and their impact on accessibility analyzed.


## 1. Explanation

With the scenario feature you can edit your layers and compute indicators based on the changes you made. The biggest advantage of this tool is that you keep your original layer intact: none of your original data gets deleted, so do not need to re-upload a modified layer in order to compute the different analyses.
In addition to your layers, you can change the [**Street Network - Edges**](#4-street-network---edges). This layer is a base layer available in all projects representing the road network and can be modified as a line layer in the scenarios.

:::info INFO
You can only modify **geographical layers**: Tables and rasters cannot be modified in scenarios. Learn more about the data types in the [data types documentation](data/data_types).
:::


## 2. How to edit a scenario?

<div class="step">
  <div class="step-number">1</div>
  <div class="content">Click on <code>Scenarios</code>   <img src={require('/img/scenarios/compass-drafting.png').default} alt="Layers" style={{ maxHeight: "20px", maxWidth: "20px", objectFit: "cover"}}/>. </div>
</div>

<div class="step">
  <div class="step-number">2</div>
  <div class="content">Click on <code>Create scenario</code> and name your scenario. The scenario is added to the scenario list. </div>
</div>

<div class="step">
  <div class="step-number">3</div>
  <div class="content">  
    Click on the three dots <img src={require('/img/scenarios/3dots.png').default} alt="Layers" style={{ maxHeight: "20px", maxWidth: "20px", objectFit: "cover"}}/> next to the scenario name, select <code>Edit</code> to edit the layers in a scenario.
  </div>
</div>

<div class="step">
  <div class="step-number">4</div>
  <div class="content">  In  <code>Select layer</code>, choose a layer to edit.  In  <code>Edit tool</code>,  you can draw <img src={require('/img/scenarios/add.png').default} alt="Layers" style={{ maxHeight: "20px", maxWidth: "20px", objectFit: "cover"}}/>, modify <img src={require('/img/scenarios/edit.png').default} alt="Layers" style={{ maxHeight: "20px", maxWidth: "20px", objectFit: "cover"}}/>, or delete <img src={require('/img/scenarios/trash-solid.png').default} alt="Layers" style={{ maxHeight: "20px", maxWidth: "20px", objectFit: "cover"}}/> features  </div>
</div>


<Tabs>
  <TabItem value="Draw" label="Draw" default className="tabItemBox">
    <div class="step">
      <div class="step-number">5</div>
      <div class="content">
        Depending on the layer type, you can draw different geographical shapes:
      </div>
    </div>
    <Tabs>
      <TabItem value="Point" label="Point" default className="tabItemBox">
        Click on the desired location on the map.
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
          <img src={require('/img/scenarios/point_drawing-final.gif').default} alt="Custom Ordinal for strings" style={{ maxHeight: '500px', maxWidth: '500px', objectFit: 'cover' }}/>
        </div>
        Fill in the attributes of your new features when required. Click on save to update your data. The new features are in blue.
      </TabItem>
      <TabItem value="Line" label="Line" default className="tabItemBox">
        Click on the map to start drawing a new line. Continue clicking to shape the line, and double-click to finish.
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}><img src={require('/img/scenarios/line_drawing-final.gif').default} alt="Custom Ordinal for strings" style={{ maxHeight: '500px', maxWidth: '500px', objectFit: 'cover' }}/></div>
        Fill in the attributes of your new features when required. Click on save to update your data. The new features are in blue.
      </TabItem>
      <TabItem value="Polygon" label="Polygon" default className="tabItemBox">
        Click on the map to start drawing a new polygon. Continue clicking to define each corner, and click on the starting point to complete the shape.
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
          <img src={require('/img/scenarios/Polygon_drawing-final.gif').default} alt="Custom Ordinal for strings" style={{ maxHeight: '500px', maxWidth: '500px', objectFit: 'cover' }}/>
        </div>
        Fill in the attributes of your new features when required. Click on save to update your data. The new features are in blue.
      </TabItem>
    </Tabs>
  </TabItem>


  <TabItem value="Modify" label="Modify" default className="tabItemBox">
    <div class="step">
      <div class="step-number">5</div>
      <div class="content">Select an initial feature or one you've created. You can edit any available attributes. Click Save to apply the updates. Edited features from the initial dataset are highlighted in yellow.</div>
    </div>
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
      <img src={require('/img/scenarios/modify_features.png').default} alt="Custom Ordinal for strings" style={{ maxHeight: '500px', maxWidth: '500px', objectFit: 'cover' }}/>
    </div>
  </TabItem>


  <TabItem value="Delete" label="Delete" default className="tabItemBox">
    <div class="step">
      <div class="step-number">5</div>
      <div class="content">Click on the feature you want to delete, then click the Delete button in the box that appears. Deleted features are highlighted in red.</div>
    </div>
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
      <img src={require('/img/scenarios/delete_feature.png').default} alt="Custom Ordinal for strings" style={{ maxHeight: '500px', maxWidth: '500px', objectFit: 'cover' }}/>
    </div>
  </TabItem>

</Tabs>


<div class="step">
  <div class="step-number">6</div>
  <div class="content">  Now, you can do analysis on your updated layer.
  Click on <code>Toolbox</code> and select an indicator. </div>  
</div>
  
<div class="step">
  <div class="step-number">7</div>
  <div class="content"> Select a layer associated with a scenario to perform your analysis on. At the bottom of the Indicator menu, under Scenario, select the associated scenario.</div>  
</div>

   ![layer analysis in scenario](/img/scenarios/layer_analysis.png "layer analysis in scenario")

## 3. Scenarios management
You can create multiple scenarios to test different configurations. To manage your scenarios, you can:

- **Select a scenario**: Click on  a scenario from the scenarios list to display its specific edits or added features.
- **Modify a scenario** Click on the three dots <img src={require('/img/scenarios/3dots.png').default} alt="Layers" style={{ maxHeight: "20px", maxWidth: "20px", objectFit: "cover"}}/>  next to a scenario name to rename or delete the scenario, or to edit the layers.
- **Edit a layer**: Layer associated with a scenario is marked by  <img src={require('/img/scenarios/compass-drafting.png').default} alt="Layers" style={{ maxHeight: "20px", maxWidth: "20px", objectFit: "cover"}}/> and a number, showing the modifications made.
- **Deselect a scenario**: Click on the selected scenario again and return to the default map view or choose another scenario.

## 4. Street Network - Edges

The “Street Network –Edges" is a base layer available in all projects representing the [real-world street network](data/data_basis#street-network-and-topography). You can only visualize the layer when selecting it in the scenario editing and zooming in the map. 
With **Scenarios**, you can modify the lines of this base layer representing streets.

   ![Street network](/img/scenarios/street_network.png "Street network")

Scenarios applied on the Street Network layer only apply to the **Catchment Area** area indicator.   Changing the street network does not impact the computation of other indicators. 

