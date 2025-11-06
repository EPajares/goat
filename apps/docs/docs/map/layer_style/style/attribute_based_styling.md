---
sidebar_position: 2
---

# Attribute-based Styling

GOAT supports **attribute-based styling**. You can style layers based on data attributes to easily identify differences and trends. Each visualization aspect—**Fill Color**, **Stroke Color**, **Custom Marker**, and **Labels**—can be styled by any field in your layer's data.

<iframe width="100%" height="500" src="https://www.youtube.com/embed/cLIPMCOu4FQ?si=aydSJN_Pf0fusO9x" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>

## How to style?

<div class="step">
  <div class="step-number">1</div>
  <div class="content">Click <code>Layer Design <img src={require('/img/map/styling/styling_icon.webp').default} alt="Styling Icon" style={{ maxHeight: "15px", maxWidth: "21px", objectFit: "cover"}}/></code>, open <code>Style</code>, activate the attribute toggle, then click <code>Options <img src={require('/img/map/styling/options_icon.png').default} alt="Options Icon" style={{ maxHeight: "15px", maxWidth: "15px", objectFit: "cover"}}/></code>.</div>
</div>

<div class="step">
  <div class="step-number">2</div>
  <div class="content">In <code>Color based on</code>, select the **field** to style by.</div>
</div>

<div class="step">
  <div class="step-number">3</div>
  <div class="content">Now you can go up to <code>Palette</code>, and choose a **color palette** or keep the default. Learn more in the [Color Palette](#color-palette) section below.</div>
</div>

<div class="step">
  <div class="step-number">4</div>
  <div class="content">In <code>Color Scale</code>, choose your **data classification method**. See all methods in the [Data Classification](#data-classification-methods) section.</div>
</div>

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>

  <img src={require('/img/map/styling/attribute_selection.gif').default} alt="Attribute Selection" style={{ maxHeight: "auto", maxWidth: "auto", objectFit: "cover"}}/>

</div> 

## Color Palette

A **palette** is a set of colors representing your data values or categories.

Customize your palette by selecting the <code>Type</code>, adjusting <code>Steps</code>, <code>Reversing</code> colors, or enabling <code>Custom</code> for your own color range.

GOAT offers four predefined palette types:

<p></p>

| Palette Type| Example | Description |
| :-: | --- | ---|
| Diverging | <img src={require('/img/map/styling/diverging_palette.png').default} alt="diverging" style={{ maxHeight: "auto", maxWidth: "auto", objectFit: "cover"}}/> | **Useful for data with a central midpoint**, like positive and negative values. It helps show variations clearly around this midpoint. |
| Sequential | <img src={require('/img/map/styling/sequential_palette.png').default} alt="sequential" style={{ maxHeight: "auto", maxWidth: "auto", objectFit: "cover"}}/> | **Ideal for data that follows a natural progression or ordered sequence**, like increasing or decreasing values. It excels at visualising continuous data, showing gradual changes from one extreme to another.|
| Qualitative | <img src={require('/img/map/styling/qualitative_palette.png').default} alt="qualitative" style={{ maxHeight: "auto", maxWidth: "auto", objectFit: "cover"}}/> | **Designed for distinct categories or classes.** It helps distinguish between discrete categories without implying any order or importance.|
| Singlehue | <img src={require('/img/map/styling/singlehue_palette.png').default} alt="singlehue" style={{ maxHeight: "auto", maxWidth: "auto", objectFit: "cover"}}/> | **Uses different shades and tones of a single color.** It creates a harmonious look and is effective for conveying information without the distraction of multiple colors.|

## Data Classification Methods

The <code>Color Scale</code> determines how data values map to colors. GOAT offers six data classification methods: **Quantile, Standard Deviation, Equal Interval, Heads and Tails, Custom Breaks, and Custom Ordinal.** All the methods default to 7 classes, but you can adjust this number as needed.

### Quantile

**Divides data into classes with equal numbers of features**. **Ideal for linearly distributed data**, but creates uneven value ranges.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>

  <img src={require('/img/map/styling/quantile.png').default} alt="Quantile" style={{ maxHeight: "auto", maxWidth: "75%", objectFit: "cover"}}/>

</div>  

### Standard Deviation

**Classifies data by deviation from the average**. Shows **relative dispersion, distribution, and outliers** statistically, but requires normally distributed data.
<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>

  <img src={require('/img/map/styling/standard_deviation.png').default} alt="Standard Deviation" style={{ maxHeight: "auto", maxWidth: "75%", objectFit: "cover"}}/>

</div> 

### Equal Interval

**Divides data into equal-sized value ranges**. Works well for **evenly distributed data but can be misleading with skewed data** (some classes may be empty). 
<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>

  <img src={require('/img/map/styling/equal_interval.png').default} alt="Equal Interval" style={{ maxHeight: "auto", maxWidth: "75%", objectFit: "cover"}}/>

</div> 

### Heads and Tails

**Handles skewed data by highlighting extremes**. Focuses on 'heads' (very high values) and 'tails' (very low values). **Useful for datasets where extremes matter most and for highlighting disparities**.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>

  <img src={require('/img/map/styling/heads_tails.png').default} alt="Heads and Tails" style={{ maxHeight: "auto", maxWidth: "75%", objectFit: "cover"}}/>

</div> 

### Custom Ordinal (for **strings**)

**Sorts and visualizes string data** like categories or labels. Since strings lack natural order, **Custom Ordinal lets you define your own ordering rules** for tailored sequences.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>

  <img src={require('/img/map/styling/ordinal.png').default} alt="Custom Ordinal for strings" style={{ maxHeight: "auto", maxWidth: "75%", objectFit: "cover"}}/>

</div>

<p></p>

You can add more steps and select multiple string values per group from the dropdown menu, which lists all values from your dataset.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>

  <img src={require('/img/map/styling/custom_ordinal.gif').default} alt="Custom Ordinal for strings" style={{ maxHeight: "300px", maxWidth: "300px", objectFit: "cover"}}/>

</div> 

### Custom Breaks (for **numbers**)

**For numerical data with custom breakpoints or thresholds**. It provides tailored visualizations for specific contexts. **Helps maintain consistency across maps**. Gives full control over classifications aligned with real-world needs.


:::tip HINT
To reuse your dataset with the styling settings in other projects, [save your style as default](../layer_style/styling#default-settings).
:::