---
sidebar_position: 1
---

import thematicIcon from "/img/toolbox/data_management/join/toolbox.webp";


# Join & Group

Append and group fields from one layer to another using a matching field on both layers.

## 1. Explanation

This tool facilitates the combination of two datasets. By defining relationships, the tool aligns data from both layers. The resulting output is a new layer that contains the attributes from the *Target Layer* and a new column that summarizes a chosen attribute from the *Join Layer*. 

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>

  <img src={require('/img/toolbox/data_management/join/join.png').default} alt="Join Schema" style={{ maxHeight: "400px", maxWidth: "200px", objectFit: "cover"}}/>

</div> 

GOAT uses the **"Inner Join"** operation to calculate a join which combines rows from a target and a join layer based on a related column between them. It only selects records that have matching values in both tables. This means that for every row in the target layer, there must be at least one row in the source layer to realize a successful match. Any rows that do not match will not be returned as a result.

## 2. Example use cases

- Summarizing population numbers from a table to a feature layer of zip-code areas (related column: zip-codes).
- Merge and aggregate the data from a household survey with the geometries of the census tract (related column: census tract).
- Joining the number of commuters from a table to a feature layer with the city boundaries (related column: city name). 


## 3. How to use the tool?

<div class="step">
  <div class="step-number">1</div>
  <div class="content">Click on <code>Toolbox</code> <img src={thematicIcon} alt="toolbox" style={{width: "25px"}}/>. </div>
</div>

<div class="step">
  <div class="step-number">2</div>
  <div class="content">Under the <code>Data Management</code> menu, click on <code>Join & Group</code>.</div>
</div>

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>

  <img src={require('/img/toolbox/data_management/join/overview.png').default} alt="Join Tool in GOAT" style={{ maxHeight: "auto", maxWidth: "auto", objectFit: "cover"}}/>

</div> 

<p> </p>

### Select layers to join 

<div class="step">
  <div class="step-number">3</div>
  <div class="content">  Select your <code>Target layer</code> (the primary table or layer to which you want to add additional data). </div>
</div>

<div class="step">
  <div class="step-number">4</div>
  <div class="content">Select your <code>Join layer</code> (the secondary table or dataset that contains the records and attributes to be inserted into the Target Layer). </div>
</div>

### Fields to match

<div class="step">
  <div class="step-number">5</div>
  <div class="content">Select the <code>Target field</code> of the target layer, which you like to use for matching the records of both layers.</div>
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

You can choose between several statistical operations. Some methods are only available for specific data types. The following list provides an overview of the available methods:

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
  
<div class="step">
  <div class="step-number">10</div>
  <div class="content">The resulting layer <b>"Join"</b> will be added to the project, as well as to the <a href="../../workspace/datasets">Datasets</a> in your workspace. This layer consists of the information of the target layer and an <b>additional column</b> showing the results from the <b>statistical operation</b>. You can see the attributes by clicking on one of the features in the map.</div>
</div>



<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>

  <img src={require('/img/toolbox/data_management/join/result.png').default} alt="Join Result in GOAT" style={{ maxHeight: "auto", maxWidth: "auto", objectFit: "cover"}}/>

</div> 


:::tip Tip

Want to adjust the appearance of the result layer? Check out the [attribute-based styling](../../map/layer_style/style/attribute_based_styling.md).

:::
