---
sidebar_position: 1
---
import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';


# Zoom Visibility

With the Zoom Visibility bar, you can set the zoom range at which each layer appears on the map. This helps you to **display the most relevant data at different zoom levels**: for example, showing detailed information when zoomed in.

::::info
By default, all layers are visible at the range of 1-22 zoom level unless changed.
::::

The range goes from **world view (0) to street-level detail (22)**, and the current zoom level is shown on the scale.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>

  <img src={require('/img/map/styling/zoom_scale.png').default} alt="zoom scale" style={{ maxHeight: "auto", maxWidth: "auto", objectFit: "cover"}}/>

</div> 

<br></br>

You can enter the zoom levels **manually** or adjust them directly **on the scale**.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>

  <img src={require('/img/map/styling/zoom_adjust.gif').default} alt="Color Picker" style={{ maxHeight: "400px", maxWidth: "400px", objectFit: "cover"}}/>

</div> 


## Tips

- Layers with *lots of detail* (e.g.: buildings or POIs) are often better viewed at **higher zoom levels**.
- **Narrower zoom ranges** helps to keep *dense layers uncluttered*.
- For *background or context layers*, a **wider range** usually works best.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>

  <img src={require('/img/map/styling/zooming_out.gif').default} alt="zoom scale screen" style={{ maxHeight: "auto", maxWidth: "auto", objectFit: "cover"}}/>

</div> 