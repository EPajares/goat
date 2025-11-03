---
sidebar_position: 3
---
import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';


# Labels

You can display labels on your layers **based on any attribute**. Labels make your map easier to read and more informative.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
  <img src={require('/img/map/styling/style_label.png').default} alt="label font size" style={{ maxHeight: "Auto", maxWidth: "Auto", objectFit: "cover"}}/>
</div> 

## Label by

First, **choose the attribute field** whose values you want to display as labels on the map. Then proceed to create further settings.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
  <img src={require('/img/map/styling/label_by.gif').default} alt="label by function" style={{ maxHeight: "Auto", maxWidth: "500px", objectFit: "cover"}}/>
</div> 

## Label settings

### Size

Set the **size of the label text**. Values can range from 5 to 100. You can set it on the scale or type in the number manually.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
  <img src={require('/img/map/styling/label_size.gif').default} alt="label font size" style={{ maxHeight: "Auto", maxWidth: "600px", objectFit: "cover"}}/>
</div> 

### Color

Choose **any color** using the <code>Color Picker</code> or select one from our <code>Preset Colors</code>.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
  <img src={require('/img/map/styling/label_color.png').default} alt="label font size" style={{ maxHeight: "200px", maxWidth: "Auto", objectFit: "cover"}}/>
</div> 

### Placement

Define where the label appears **in relation to the feature**: center, top, bottom, left, right, top left, top right, bottom left, or bottom right.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
  <img src={require('/img/map/styling/label_placement.gif').default} alt="label font size" style={{ maxHeight: "Auto", maxWidth: "500px", objectFit: "cover"}}/>
</div> 

<br></br> 

---

::::info
Open more setting with the <b>Advanced Settings</b> <code><img src={require('/img/map/styling/options_icon.png').default} alt="Options Icon" style={{ maxHeight: "15px", maxWidth: "15px", objectFit: "cover"}}/></code> button.
::::

### Offset

**Adjust the label's position** by moving it horizontally (<code>Offset X</code>) or vertically (<code>Offset Y</code>). Use the scalebar to create settings, or type in the number manually.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
  <img src={require('/img/map/styling/offset.gif').default} alt="label font size" style={{ maxHeight: "Auto", maxWidth: "500px", objectFit: "cover"}}/>
</div> 

### Allow overlap

If **enabled**, labels will *appear on all zoom levels*. If **disabled**, the labels get *clustered at lower zoom levels*.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
  <img src={require('/img/map/styling/overlap.gif').default} alt="label font size" style={{ maxHeight: "Auto", maxWidth: "500px", objectFit: "cover"}}/>
</div> 

### Halo color

A halo is an **outline around the label**, which helps to improve readability against busy backgrounds. Choose any color using the <code>Color Picker</code> or select one from our <code>Preset Colors</code>.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
  <img src={require('/img/map/styling/halo_color.png').default} alt="label font size" style={{ maxHeight: "200px", maxWidth: "Auto", objectFit: "cover"}}/>
</div> 

### Halo width

Set the **thickness of the halo**. The maximum value is one-quarter of the label's font size. Use the scalebar to create the setting, or type in the number manually.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
  <img src={require('/img/map/styling/halo_width.gif').default} alt="label font size" style={{ maxHeight: "Auto", maxWidth: "500px", objectFit: "cover"}}/>
</div> 


## Tips

- Use **smaller fonts** for *dense layers* to reduce visual clutter.
- A **light halo** on **dark maps** (or vice versa) can make labels much *easier to read*.
- **By default label overlap is disabled**, which *improves clarity*, but some labels might not appear if space is limited.
