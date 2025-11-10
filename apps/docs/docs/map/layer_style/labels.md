---
sidebar_position: 3
---
import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';


# Labels

**Labels allow you to display text on your map features based on any attribute field.** This makes your maps more informative and easier to interpret by showing key information directly on the features.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
  <img src={require('/img/map/styling/labels.png').default} alt="Labels displayed on map features" style={{ maxHeight: "auto", maxWidth: "auto", objectFit: "cover"}}/>
</div>

## How to add and configure labels

### General settings

<div class="step">
  <div class="step-number">1</div>
  <div class="content">Select your layer and navigate to <code>Layer design</code> <img src={require('/img/map/styling/styling_icon.webp').default} alt="Styling Icon" style={{ maxHeight: "15px", maxWidth: "15px", objectFit: "cover"}}/> and find the <code>Labels section</code></div>
</div>

<div class="step">
  <div class="step-number">2</div>
  <div class="content">On <code>Label by</code> choose the **attribute field** whose values you want to display as labels</div>
</div>

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
  <img src={require('/img/map/styling/label_by.gif').default} alt="Selecting label attribute field" style={{ maxHeight: "auto", maxWidth: "500px", objectFit: "cover"}}/>
</div>

<div class="step">
  <div class="step-number">3</div>
  <div class="content">On <code>Size</code>, set the **label size** using the slider (5-100) or enter the value manually</div>
</div>

<div class="step">
  <div class="step-number">4</div>
  <div class="content">On <code>Color</code> choose a **label color** using the color picker or select from preset colors</div>
</div>

<div class="step">
  <div class="step-number">5</div>
  <div class="content">Set the <code>Placement</code> to define **where labels appear relative to features** (center, top, bottom, left, right, or corner positions)</div>
</div>

### Advanced settings

<div class="step">
  <div class="step-number">6</div>
  <div class="content">Click the <code>Advanced settings</code> <img src={require('/img/map/styling/options_icon.png').default} alt="Options" style={{ maxHeight: "15px", maxWidth: "15px", objectFit: "cover"}}/> button to access **additional options**</div>
</div>

<div class="step">
  <div class="step-number">7</div>
  <div class="content">Adjust <code>Offset X</code> and <code>Offset Y</code> to fine-tune **label position** by moving horizontally or vertically</div>
</div>

<div class="step">
  <div class="step-number">8</div>
  <div class="content">Configure <code>Allow overlap</code>: **Enable** to show all labels (may cause visual clutter) or **Disable** for automatic clustering at lower zoom levels (cleaner appearance)</div>
</div>

<div class="step">
  <div class="step-number">9</div>
  <div class="content">Add a <code>Halo color</code> to create a **colored outline** around text for better readability on busy backgrounds</div>
</div>

<div class="step">
  <div class="step-number">10</div>
  <div class="content">Set the <code>Halo width</code> to control **outline thickness** (maximum is one-quarter of font size)</div>
</div>

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
  <img src={require('/img/map/styling/labels_overlap.gif').default} alt="Label overlap and halo effects" style={{ maxHeight: "auto", maxWidth: "500px", objectFit: "cover"}}/>
</div>

## Best practices

- Use **smaller fonts** for dense layers to reduce visual clutter
- Add **halos** with contrasting colors (light halos on dark maps, dark halos on light maps) to improve text readability
- Keep **overlap disabled** by default for cleaner appearance, though some labels may be hidden in crowded areas
- Test your label settings at different zoom levels to ensure they remain readable and useful across all scales
