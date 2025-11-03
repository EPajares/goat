---
sidebar_position: 2
---

# Attribute-based Styling

GOAT supports ***attribute-based styling*** to enhance the visualization of data on maps. This helps show differences and patterns in the data by basing their style on data attributes, making it simpler to understand complex spatial information. Each aspect of a layer's visualization, such as **Fill Color**, **Stroke Color**, **Custom Marker** and **Labels** can be individually styled according to a field of the layer's data.

<iframe width="100%" height="500" src="https://www.youtube.com/embed/cLIPMCOu4FQ?si=aydSJN_Pf0fusO9x" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>

## How to style?

<div class="step">
  <div class="step-number">1</div>
  <div class="content">Click on <code>Layer design <img src={require('/img/map/styling/styling_icon.webp').default} alt="Styling Icon" style={{ maxHeight: "15px", maxWidth: "21px", objectFit: "cover"}}/></code>, open the <code> Style</code> menu,  ensure its attribute toggle is activated, and then click on <code>options <img src={require('/img/map/styling/options_icon.png').default} alt="Options Icon" style={{ maxHeight: "15px", maxWidth: "15px", objectFit: "cover"}}/></code> to start styling.</div>
</div>

<div class="step">
  <div class="step-number">2</div>
  <div class="content">On the <code>Color based on</code> menu, select the <strong>Field</strong> you want to style by.</div>
</div>

<div class="step">
  <div class="step-number">3</div>
  <div class="content">Above on the <code>Palette</code> menu,  you can select a different <strong>Color Palette</strong> or keep the default one. You can learn more about the options available in GOAT on the Color Palette section on this page.</div>
</div>

<div class="step">
  <div class="step-number">4</div>
  <div class="content">Under the <code>Color Scale</code> menu, you can choose the <strong>Data Classification Method</strong> you need. You can learn more about the different methods we have <a href="#data-classification-methods"><strong>here</strong></a></div>
</div>

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>

  <img src={require('/img/map/styling/attribute_selection.gif').default} alt="Attribute Selection" style={{ maxHeight: "auto", maxWidth: "auto", objectFit: "cover"}}/>

</div> 

## Color Palette
A palette is a set of colors used to represent the scale of values or categories in your layer's data. 

In GOAT, you can customize your palette by selecting the <code>Type</code>, adjusting the number of <code>Steps</code>, and <code>Reversing</code> the colors. You can also create a custom range of colors by enabling the <code>Custom</code> toggle button.

GOAT offers a wide range of predefined palettes, categorized into four types, to make selection and application easier.

<p></p>

| Palette Type| Example | Description |
| :-: | --- | ---|
| Diverging | <img src={require('/img/map/styling/diverging_palette.png').default} alt="diverging" style={{ maxHeight: "auto", maxWidth: "auto", objectFit: "cover"}}/> | **Useful for data with a central midpoint**, like positive and negative values. It helps show variations clearly around this midpoint. |
| Sequential | <img src={require('/img/map/styling/sequential_palette.png').default} alt="sequential" style={{ maxHeight: "auto", maxWidth: "auto", objectFit: "cover"}}/> | **Ideal for data that follows a natural progression or ordered sequence**, like increasing or decreasing values. It excels at visualising continuous data, showing gradual changes from one extreme to another.|
| Qualitative | <img src={require('/img/map/styling/qualitative_palette.png').default} alt="qualitative" style={{ maxHeight: "auto", maxWidth: "auto", objectFit: "cover"}}/> | **Designed for distinct categories or classes.** It helps distinguish between discrete categories without implying any order or importance.|
| Singlehue | <img src={require('/img/map/styling/singlehue_palette.png').default} alt="singlehue" style={{ maxHeight: "auto", maxWidth: "auto", objectFit: "cover"}}/> | **Uses different shades and tones of a single color.** It creates a harmonious look and is effective for conveying information without the distraction of multiple colors.|

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>

  <img src={require('/img/map/styling/color_palettes.gif').default} alt="Color Palettes" style={{ maxHeight: "auto", maxWidth: "auto", objectFit: "cover"}}/>

</div> 

## Data Classification Methods

Under the <code>Color Scale</code>, you will find the **data classification method** and the **color scale** links data values to colors. It assigns a color to each data value based on its position within a range. GOAT offers six predefined **data classification methods**: [Quantile](#quantile), [Standard Deviation](#standard-deviation), [Equal Interval](#equal-interval), [Heads and Tails](#heads-and-tails), [Custom Breaks](#custom-breaks-for-numbers), and [Custom Ordinal](#custom-ordinal-for-strings).

### Quantile

**It divides data into classes with an equal number of observations**. This makes this approach **ideal for data that is linearly distributed**, but it can create uneven class ranges, making some categories much broader than others. Per default, the data is distributed into 7 classes.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>

  <img src={require('/img/map/styling/quantile.png').default} alt="Quantile" style={{ maxHeight: "auto", maxWidth: "75%", objectFit: "cover"}}/>

</div>  

<p></p>

:::tip HINT
Want to deeper understand what quantile classification is? Check our [Glossary](../../further_reading/glossary/#quantile-classification).
:::

### Standard Deviation

**It classifies data based on how much values deviate from the average**. This method is valuable for its ability to provide a statistical perspective on the data, allowing users to quickly grasp the **relative dispersion, distribution of values and outliers** within the dataset, but may not work well if the data isn’t normally distributed. Per default, the data is distributed into 7 classes. 
<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>

  <img src={require('/img/map/styling/standard_deviation.png').default} alt="Standard Deviation" style={{ maxHeight: "auto", maxWidth: "75%", objectFit: "cover"}}/>

</div> 

### Equal Interval

**It divides data into equal-sized ranges, making it easy to compare values**. This method works well for evenly distributed data but can be misleading if the data is skewed, as some classes may end up nearly empty. Per default, the data is distributed into 7 classes. 

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>

  <img src={require('/img/map/styling/equal_interval.png').default} alt="Equal Interval" style={{ maxHeight: "auto", maxWidth: "75%", objectFit: "cover"}}/>

</div> 

### Heads and Tails

**It handles datasets with a skewed distribution**. It's designed to highlight extremes in the data, focusing on the **'heads' (the very high values)** and the **'tails' (the very low values)**. This method is particularly useful for datasets where the most important information is found in the extremes, and where is important to highlight disparities or key areas for intervention. Per default, the data is distributed into 7 classes. 

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>

  <img src={require('/img/map/styling/heads_tails.png').default} alt="Heads and Tails" style={{ maxHeight: "auto", maxWidth: "75%", objectFit: "cover"}}/>

</div> 

### Custom Ordinal (for **strings**)

**It helps sort and visualize string data**, like categories, labels, or text-based variables. Since string data often doesn't have a natural order, the **Custom Ordinal method lets users define their own ordering rules**. This creates a custom sequence tailored to their specific needs.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>

  <img src={require('/img/map/styling/ordinal.png').default} alt="Custom Ordinal for strings" style={{ maxHeight: "auto", maxWidth: "75%", objectFit: "cover"}}/>

</div>

<p></p>

Therefore, you can add more steps and select multiple string values per group from a drop-down menu. The menu lists all attribute values from the dataset.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>

  <img src={require('/img/map/styling/custom_ordinal.gif').default} alt="Custom Ordinal for strings" style={{ maxHeight: "300px", maxWidth: "300px", objectFit: "cover"}}/>

</div> 

### Custom Breaks (for **numbers**)

**It is used for numerical data. It allows users to define custom breakpoints or thresholds** and therewith provides a tailored approach for context-specific visualizations. **It can also help maintain consistency across maps**. This method gives full control over classifications, ensuring they align with real-world contexts.

import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';

## Style Settings

<Tabs>
  <TabItem value="fill color" label="Fill Color" default> Fill Color can either be one single color or a color palette. GOAT offers a set of preset colors and palettes to style your map. 
    For attribute-based Fill Color select a Field from the selected <code>Layer</code>.
    GOAT applies a random color palette to your results. 
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>

   <img src={require('/img/map/layers/fill-color.gif').default} alt="Custom Ordinal for strings" style={{ maxHeight: "500px", maxWidth: "500px", objectFit: "cover"}}/>

   </div> 

  </TabItem>
  <TabItem value="stroke color" label="Stroke Color"> Stroke Color by default is one single color. Apply attribute-based styling to apply a color scale to the layer stroke. 
    For attribute-based Stroke Color select a Field from the selected <code>Layer</code>.
    GOAT applies a random color palette to your results. 

   <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>

   <img src={require('/img/map/layers/stroke-color.gif').default} alt="Custom Ordinal for strings" style={{ maxHeight: "500px", maxWidth: "500px", objectFit: "cover"}}/>

   </div> 



  </TabItem>
  <TabItem value="custom marker" label="Custom Marker"> When available, the custom marker has an icon library to best represent your data set. You can also use your own uploaded custom markers as well.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>

   <img src={require('/img/map/layers/attribute-based-custom-marker.gif').default} alt="Custom Ordinal for strings" style={{ maxHeight: "500px", maxWidth: "500px", objectFit: "cover"}}/>

   </div> 

  </TabItem>
</Tabs>


:::tip HINT
If you would like to save your styling settings and use them in further projects, you can do so by [saving a style as default](../layer_style/styling#default-settings). 
:::