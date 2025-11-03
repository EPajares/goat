---
sidebar_position: 1
---

# Basic Styling

When you add a new layer to your project, it is assigned a default style based on the type of data. By customizing options in the <code>Layer design <img src={require('/img/map/styling/styling_icon.webp').default} alt="Styling Icon" style={{ maxHeight: "15px", maxWidth: "15px", objectFit: "cover"}}/></code> menu, you can adjust the visualization of the layer and **create appealing maps**. The styling options available depend on the type of data contained by a layer, i.e. whether it is points, lines, or polygons. Thereby, multiple visual aspects, such as **colors**, **strokes**, and **opacities** can be adjusted.

<iframe width="100%" height="500" src="https://www.youtube.com/embed/R7nefHqPnBk?si=KWndAFlcb2uuC7CZ" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>

## Color Settings

### Fill Color

Fill color is used to represent the **interior** of **point or polygon features** on a map. Fill color is an aspect of cartography and GIS visualization because it helps to improve the overall readability of the map. The [Color Picker](#color-picker--preset-colors) provides different options to select the colors of your choice.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>

  <img src={require('/img/map/styling/fill_color.gif').default} alt="Fill-Stroke Color" style={{ maxHeight: "auto", maxWidth: "auto", objectFit: "cover"}}/>

</div> 

#### Opacity

To adjust the opacity of your layer styles for fill color, simply change the opacity to any **value between 0 and 1**. This numerical scale allows you to define the exact level of opacity you want, where **0 is transparent** and **1 is opaque**. Adjust the opacity to your preference, either by using the slider or by typing the exact level directly into the text box provided.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>

  <img src={require('/img/map/styling/opacity.gif').default} alt="Opacity" style={{ maxHeight: "auto", maxWidth: "auto", objectFit: "cover"}}/>

</div> 


### Stroke Color

Similar to the fill color, also the stroke color can be adjusted. Stroke color refers to the color applied to the **outlines or edges** of map features such as polygons, lines, and points. It is used to delineate the edges of spatial entities, distinguishing them from one another and enhancing their visibility on the map. The [Color Picker](#color-picker--preset-colors) provides different options to select the colors of your choice.


### Color Picker & Preset Colors

Whenever you want to change a color, may it be **Fill Color** or **Stroke Color**, the color menu opens. You can either set the colors from the <code>Color Picker</code> by **moving the picker** in the color field or by defining **hex code** or **RGB values**, or you can select one of the colors we provide in the <code>Preset Colors</code>.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>

  <img src={require('/img/map/styling/color_picker.gif').default} alt="Color Picker" style={{ maxHeight: "400px", maxWidth: "400px", objectFit: "cover"}}/>

</div> 


## Custom Marker

For point layers, Custom Markers can be used for the visualization. The marker can be selected from an **icon library** or you can **upload your own custom marker**. The **search bar** helps you to find the needed icons quickly. The Marker Size can be adjusted via the slider.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>

  <img src={require('/img/map/styling/custom_marker.gif').default} alt="Marker" style={{ maxHeight: "500px", maxWidth: "auto", objectFit: "cover"}}/>

</div> 

### Uploading a Custom Marker

After opening the list of markers, click on <code>Upload icon</code>. Then again select <code>Upload icon</code> then choose your **jpeg, png or svg file**. When naming your file, keep in mind that this name will be used to search for the icon. 

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>

  <img src={require('/img/map/styling/custom_marker_upload.png').default} alt="Marker" style={{ maxHeight: "600px", maxWidth: "auto", objectFit: "cover"}}/>

</div> 

At the <code>Manage icons</code> tab you can **rename** and **delete** your uploaded icons.

:::info

You can only edit the color of the icons added from the library.

:::

## Width & Radius

### Stroke Width

Besides the color, also the **line thickness** of strokes can be defined. Adjust the line width to your preference, either by using the width slider or by typing the exact size directly into the text box provided.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>

  <img src={require('/img/map/styling/stroke_width.png').default} alt="Stroke Width" style={{ maxHeight: "300px", maxWidth: "300px", objectFit: "cover"}}/>

</div> 


### Radius

For **point datasets**, the **radius** can be adjusted. Therefore, you can either use the Radius slider to make incremental changes or enter the desired radius size directly in the text box for precise control.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>

  <img src={require('/img/map/styling/radius.png').default} alt="Radius" style={{ maxHeight: "300px", maxWidth: "300px", objectFit: "cover"}}/>

</div> 


## Default Settings 

By clicking on the three dots <img src={require('/img/map/filter/3dots.png').default} alt="Options" style={{ maxHeight: "25px", maxWidth: "25px", objectFit: "cover"}}/>, the default style settings open. 

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>

  <img src={require('/img/map/styling/default.png').default} alt="Default Settings" style={{ maxHeight: "300px", maxWidth: "300px", objectFit: "cover"}}/>

</div> 

If you select <code>Save as default</code>, the current style settings will be attached to the dataset. Whenever you add this dataset to a project, this default style will be used (*Note: existing projects where this dataset is displayed will not be affected*). 

By clicking on <code>Reset</code>, you can reset the current style settings back to the default. 


:::tip HINT
Interested in **smart styling** options? Check our [Attribute-based Styling](../layer_style/attribute_based_styling).
:::