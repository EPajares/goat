---
sidebar_position: 4
---
import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';


# Filter

**Filter** limits data visibility on your map using **logical expressions** (e.g., supermarkets with specific names) or **spatial expressions** (e.g., points within a bounding box).

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>

  <img src={require('/img/map/filter/filter_clicking.gif').default} alt="Filter tool in GOAT" style={{ maxHeight: "auto", maxWidth: "auto", objectFit: "cover"}}/>

</div> 

## 1. Explanation

<code>Filter</code> <img src={require('/img/map/filter/filter_icon.png').default} alt="Filter Icon" style={{ maxHeight: "20px", maxWidth: "20px"}}/> **displays only selected elements** from larger datasets based on specific criteria. Focus on relevant information without altering original data.

Works with **point layers** and **polygon layers** containing `number` and `string` data types.

:::info

**Filter does not alter original data**. Reset the filter to restore all original layer data.

:::

## 2. Example use cases

- Cities in Germany with more than 50,000 inhabitants
- Carsharing stations from specific operators  
- Regions with multiple airports

## 3. How to use the filter?

### Single Expression Filtering

<div class="step">
  <div class="step-number">1</div>
  <div class="content">Select the layer to filter and click on the <code>Filter</code> <img src={require('/img/map/filter/filter_icon.png').default} alt="Filter Icon" style={{ maxHeight: "20px", maxWidth: "20px"}}/> icon on the tools bar on the right.</div>
</div>

<div class="step">
  <div class="step-number">2</div>
  <div class="content">The <code>Active Layer</code> selector shows the currently selected layer for filtering.</div>
</div>

<div class="step">
  <div class="step-number">3</div>
  <div class="content">Click <code>+ Add Expression</code>.</div>
</div>

<div class="step">
  <div class="step-number">4</div>
  <div class="content">Choose **Logical Expression** or **Spatial Expression**.</div>
</div>

<Tabs>
  <TabItem value="Logical expression" label="Logical expression" default className="tabItemBox">

<div class="step">
  <div class="step-number">5</div>
  <div class="content">Select the <code>Field</code> (attribute) to filter by.</div>
</div>

<div class="step">
  <div class="step-number">6</div>
  <div class="content">Choose the <code>Operator</code>. Available options vary by data type: **number** and **string**.</div>
</div>

| Expressions for `number` | Expressions for `string` |
| -------|----|
| is  | is |
| is not  | is not |
| includes  | includes  |
| excludes  |  excludes |
| is at least  | starts with |
| is less than | ends with |
| is at most | contains the text |
| is greater than | doesn't contain the text |
| is between | is empty string |
|  | is not empty string |


:::tip Hint
For the expressions **"includes"** and **"excludes"**, multiple values can be selected.
:::

<div class="step">
  <div class="step-number">7</div>
  <div class="content">Set your filter criteria. The map updates automatically and shows a filter icon on the filtered layer.</div>
</div>

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/map/filter/filter_atlayer.webp').default} alt="Filter Result in GOAT" style={{ maxHeight: "auto", maxWidth: "auto", objectFit: "cover"}}/>
</div> 
</TabItem>

<TabItem value="Spatial expression" label="Spatial expression" default className="tabItemBox">
<div class="step">
  <div class="step-number">5</div>
  <div class="content">Select the <code>intersection method</code> for spatial boundary.</div>
</div>

<Tabs>
  <TabItem value="Map extent" label="Map extent" default className="tabItemBox">
<div class="step">
  <div class="step-number">6</div>
  <div class="content">Layer automatically crops to current map extent. To change the filter, zoom in/out and refresh the map extent.</div>
</div>

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>

  <img src={require('/img/map/filter/Map_extend.gif').default} alt="Attribute Selection" style={{ maxHeight: "auto", maxWidth: "auto", objectFit: "cover"}}/>

</div> 
</TabItem>

<TabItem value="Boundary" label="Boundary" default className="tabItemBox">

:::info coming soon

This feature is currently under development. 🧑🏻‍💻

:::
</TabItem>
</Tabs>

</TabItem>
</Tabs>

### Multiple Expressions Filtering

**Combine multiple filters** by repeating steps 3-7 for each expression. In <code>Filter results</code>, choose **Match all filters** (AND) or **Match at least one filter** (OR).

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/map/filter/filter-results.png').default} alt="Logic Operators" style={{ maxHeight: "300px", maxWidth: "300px", objectFit: "cover"}}/>
</div>
  
### Delete Expressions and Filters

- **Remove single expressions**: Click on the more options menu <img src={require('/img/map/filter/3dots_horizontal.png').default} alt="Options" style={{ maxHeight: "25px", maxWidth: "25px", objectFit: "cover"}}/> next to the expression, then click <code>Delete</code>.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/map/filter/filter_delete.png').default} alt="Delete" style={{ maxHeight: "300px", maxWidth: "300px", objectFit: "cover"}}/>
</div>

<p></p>
- **Remove whole filter**: Click <code>Clear Filter</code> at the bottom of the Filter menu.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>

  <img src={require('/img/map/filter/filter_clear.png').default} alt="Clear Filters" style={{ maxHeight: "300px", maxWidth: "300px", objectFit: "cover"}}/>

</div>

