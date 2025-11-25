---
sidebar_position: 1
---

import thematicIcon from "/img/toolbox/data_management/join/toolbox.webp";


# Join & Group

This tool allows you to **combine and summarize data from two layers by matching an attribute in both**. This is essential for spatial analysis, data enrichment, and creating comprehensive datasets.


## 1. Explanation

This tool allows you to combine two datasets by linking their features through a common attribute (for example, an ID or name). **The result is a new layer that keeps all attributes from the Target Layer, plus an additional column that summarizes selected information from the Join Layer.**

**GOAT uses an Inner Join to combine the data**. This means it matches features (rows) from the Target Layer and the Join Layer wherever they share the same value in the chosen matching field (column).
**Only features that exist in both layers with the same value will be included in the output.** If a feature in the Target Layer doesn’t have a matching one in the Join Layer, it won’t appear in the result.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>

  <img src={require('/img/toolbox/data_management/join/join_and_group.png').default} alt="Join Tool in GOAT" style={{ maxHeight: "auto", maxWidth: "auto", objectFit: "cover"}}/>

</div> 

## 2. Example use cases

- Add population data to zip code areas (matching on zip code).
- Combine survey data with census tract boundaries (matching on tract ID).
- Join commuter numbers to city boundaries (matching on city name).

## 3. How to use the tool?

<div class="step">
  <div class="step-number">1</div>
  <div class="content">Click on <code>Toolbox</code> <img src={thematicIcon} alt="toolbox" style={{width: "25px"}}/>. </div>
</div>

<div class="step">
  <div class="step-number">2</div>
  <div class="content">Under the <code>Data Management</code> menu, click on <code>Join & Group</code>.</div>
</div>

### Select layers to join 

<div class="step">
  <div class="step-number">3</div>
  <div class="content">  Select your <code>Target layer</code>: the primary table or layer <strong>to which you want to add additional data.</strong> </div>
</div>

<div class="step">
  <div class="step-number">4</div>
  <div class="content">Select your <code>Join layer</code>: the secondary table or dataset that <strong>contains the records and attributes to be inserted into the Target Layer.</strong> </div>
</div>

### Fields to match

<div class="step">
  <div class="step-number">5</div>
  <div class="content">Select the <code>Target field</code> of the target layer, which you like <strong>to use for matching the records of both layers</strong>.</div>
</div>

<div class="step">
  <div class="step-number">6</div>
  <div class="content"> Select the matching attribute of the Join Layer as the <code>Join field</code>. </div>
</div>

### Statistics

<div class="step">
  <div class="step-number">7</div>
  <div class="content"> Select the <code>Statistic Method</code> to be used to join the attribute. </div>
</div>

**You can choose between several statistical operations**. Some methods are only available for specific data types. The following list provides an overview of the available methods:

| Method | Data Types | Description |
| -------|------| ------------|
| Count  | `string`,`number`    | Counts the number of non-null values in the selected column|
| Sum    | `number`   | Calculates the sum of all the numbers in the selected column|
| Mean   | `number`   | Calculates the average (mean) value of all numeric values in the selected column|
| Median | `number`   | Yields the middle value in the selected column's sorted list of numeric values|
| Min    | `number`   | Yields the minimum value of the selected column|
| Max    | `number`   | Yields the maximum value of the selected column|

<div class="step">
  <div class="step-number">8</div>
  <div class="content">Select the <code>Field Statistics</code> for which you like to apply the statistical operation.</div>
</div>

<div class="step">
  <div class="step-number">9</div>
  <div class="content">Click on <code>Run</code>.</div>
</div>


### Results
  
The resulting layer **"Join"** will be added to your project and to the [Datasets](../../workspace/datasets) in your workspace. This layer contains all information from the target layer plus an **additional column** with the results from the **statistical operation**. You can view the attributes by clicking on any feature in the map.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>

  <img src={require('/img/toolbox/data_management/join/result.png').default} alt="Join Result in GOAT" style={{ maxHeight: "auto", maxWidth: "auto", objectFit: "cover"}}/>

</div> 

<p></p>


:::tip Tip

Want to adjust the appearance of the result layer? Check out the [attribute-based styling](../../map/layer_style/style/attribute_based_styling.md).

:::
