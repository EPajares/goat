---
sidebar_position: 2
---


# Widgets

Widgets are the **building blocks** of the dashboard. They allow you to display various types of data and information in a visually appealing way. Each **widget can be costumized** to fit your needs, whether you want to show numbers, charts, or project elements like text and images.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/builder/widgets.png').default} alt="recent datasets" style={{ maxHeight: "350px", maxWidth: "auto", objectFit: "cover"}}/>
</div> 

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>

*Variety of widgets available in the Builder mode*

</div>



<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/builder/widget_drag.gif').default} alt="recent datasets" style={{ maxHeight: "400px", maxWidth: "auto", objectFit: "cover"}}/>
</div> 

Simply **drag and drop** the widgets from the right sidebar to any panel on your dashboard. You can further customize each widget by clicking on it, which will open the **Widget Settings**.

::::note

Further options available on the selected widget:
- Rearrange the widget by **dragging it** with the *dotted icon*.
- Click on the *bin icon* in right upper corner to **delete** the widget.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/builder/widget_delete.png').default} alt="recent datasets" style={{ maxHeight: "200px", maxWidth: "auto", objectFit: "cover"}}/>
</div> 

::::

<div></div>

::::info

- You can change the **Widget titel** (will appear on the top of the widget) and the **Description** (will appear on the bottom of the widget) of all of your widgets, **except for the Project elements**.
- Enabling **Cross filter** to your  **Data** and **Chart** widgets will make them *interact with each other*. This means that when you filter data on one widget, the other widget will update accordingly to the changes.
- The **Filter viewport** option can be enabled or disabled for all **Charts** elements and **Numbers** within the *Data*. Enabling it makes the information on the widget dynamic, meaning only the *data within the current map view will be visible.* 

::::

::::tip

Where **statistical methods can be applied**, *count, sum, min, max and expression* are the available options. Check out our **[Expressions documentation](/data/expressions.md)** for more information.

::::



## Information
### Layers

Add the legends of the layers to your dashboard.


- **Zoom to layer**: This will zoom the map view to the full extent of the layer. Available for the viewers as well.
- **Download**: Not available for the viewers.
- **Data source info**: Available for the viewers as well.
- **Hide/Show layer**: Set the default visibilty of the layers, the viewers can hide/show them. 

::::info
Viewers can hide/show the pre-selected layers, but once the dashboard is **reloaded**, they will **set back to the original visibility.**
::::

 

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/builder/builder_layer.png').default} alt="recent datasets" style={{ maxHeight: "500px", maxWidth: "auto", objectFit: "cover"}}/>
</div> 



## Data

### Filter

This widget is an **interactive element**, which allows the user to filter the data on the configured layer based on the selected attribute field.
The viewers can use this as a *cropping tool on the map*s - this is very similar to our [Filter tool](/map/filter.md) in the Data mode. 


<div class="step">
  <div class="step-number">1</div>
  <div class="content">Select your <b>layer</b>. </div>
</div>

<div class="step">
  <div class="step-number">2</div>
  <div class="content">Choose the <b>field</b> you want to filter by. </div>
</div>

<div class="step">
  <div class="step-number">3</div>
  <div class="content">Choose the layout option: <b>Dropdown</b> or <b>Button</b>.</div>
</div>

<div class="step">
  <div class="step-number">4</div>
  <div class="content">Optionally add a <b>Placeholder</b> text which appears before the filtering is applied.</div>
</div>

<div class="step">
  <div class="step-number">5</div>
  <div class="content">Enable or disable the option to <b>Allow multiple selection</b>. The selection will match <b>all</b> the chosen criteria.</div>
</div>

- You can enable **Zoom to selection**, which will automatically pan the map view to the filtered data.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/builder/builder_filter.gif').default} alt="recent datasets" style={{ maxHeight: "500px", maxWidth: "auto", objectFit: "cover"}}/>
</div> 

 

### Numbers

Choose from different statistic methods to be computed on a layer.

<div class="step">
  <div class="step-number">1</div>
  <div class="content">Select your <b>layer</b>. </div>
</div>

<div class="step">
  <div class="step-number">2</div>
  <div class="content">Choose the <b>statistic method</b> you want to apply. It can be <b>Count, Sum, Min, Max,</b> or add your own <b>Expression</b>.  </div>
</div>

<div class="step">
  <div class="step-number">3</div>
  <div class="content">Choose the <b>field</b> onto which the statistics should be applied. <i>Sum, min, and max can only be applied to numeric fields.</i></div>
</div>

<div class="step">
  <div class="step-number">4</div>
  <div class="content">Set the <b>number format</b> from the dropdown list. The <b>default number format</b> is dynamic based on the language of the interface.</div>
</div>

<div class="step">
  <div class="step-number">5</div>
  <div class="content">Enable or disable the option to <b>Allow multiple selection</b>. The selection will match <b>all</b> the chosen criteria.</div>
</div>


<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/builder/builder_number.gif').default} alt="recent datasets" style={{ maxHeight: "500px", maxWidth: "auto", objectFit: "cover"}}/>
</div> 



## Charts

Display your data in a visual format using different type of charts.

### Categories

Has similar setup logic as the [Numbers](#numbers) widget. On top of computing statistical analyses, it generates **groups by the selected filed.**

<div class="step">
  <div class="step-number">1</div>
  <div class="content">Select your <b>layer</b>. </div>
</div>

<div class="step">
  <div class="step-number">2</div>
  <div class="content">Choose the <b>statistic method</b> you want to apply. It can be <b>Count, Sum, Min, Max,</b> or add your own <b>Expression</b>.  </div>
</div>

<div class="step">
  <div class="step-number">3</div>
  <div class="content">Choose the <b>field</b> onto which the statistics should be applied. <i>Sum, min, and max can only be applied to numeric fields.</i></div>
</div>

<div class="step">
  <div class="step-number">4</div>
  <div class="content">Select the <b>field</b> you want your results to be <b>grouped by.</b></div>
</div>

<div class="step">
  <div class="step-number">5</div>
  <div class="content">Set the <b>number format</b> from the dropdown list. The <b>default number format</b> is dynamic based on the language of the interface. </div>
</div>


<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/builder/builder_categories.gif').default} alt="recent datasets" style={{ maxHeight: "500px", maxWidth: "auto", objectFit: "cover"}}/>
</div> 

::::info

The value with the <b>highest number will jump to the top</b> of the chart.

::::


### Histogram

The histogram widget allows you to visualize the distribution of a **numeric field** from a selected layer by <b>count.</b>

<div class="step">
  <div class="step-number">1</div>
  <div class="content">Select your <b>layer</b>. </div>
</div>

<div class="step">
  <div class="step-number">2</div>
  <div class="content">Choose the <b>numeric field</b> which you want to visualize. The statistical method applied will be <b>count.</b>  </div>
</div>

<div class="step">
  <div class="step-number">3</div>
  <div class="content">Set the <b>number format</b> from the dropdown list. The <b>default number format</b> is dynamic based on the language of the interface. </div>
</div>

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/builder/builder_histogram.gif').default} alt="recent datasets" style={{ maxHeight: "500px", maxWidth: "auto", objectFit: "cover"}}/>
</div> 


### Pie chart

Pie chart widget allows you to visualize the distribution of a **field** from a selected layer.

<div class="step">
  <div class="step-number">1</div>
  <div class="content">Select your <b>layer</b>. </div>
</div>

<div class="step">
  <div class="step-number">2</div>
  <div class="content">Choose the <b>statistic method</b> you want to apply. It can be <b>Count, Sum, Min, Max,</b> or add your own <b>Expression</b>.  </div>
</div>

<div class="step">
  <div class="step-number">3</div>
  <div class="content">Choose the <b>field</b> onto which the statistics should be applied. <i>Sum, min, and max can only be applied to numeric fields.</i></div>
</div>

<div class="step">
  <div class="step-number">4</div>
  <div class="content">Select the <b>field</b> you want your results to be <b>grouped by.</b></div>
</div>

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/builder/builder_chart.gif').default} alt="recent datasets" style={{ maxHeight: "500px", maxWidth: "auto", objectFit: "cover"}}/>
</div> 


::::info

Results will be visualized in <b>percentage.</b>

::::


## Project Elements

This section of widgets offer extra elements to make your dashboard rounded.

### Text

Add text to your dashboard. You can **costumize it with the appearing buttons**.

:::note
- Style your text with different **headings, lists,** or **code blocks.**
- Add **bold**, *italic*, <u>underline</u>, strikethrough (~~Lorem ipsum~~), subscript (X<sub>1</sub>) or superscript (X<sup>1</sup>) to your text.
- Change the **alignment, add links,** adjust the **letter color** or **add highlight.**
:::

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/builder/builder_text.gif').default} alt="recent datasets" style={{ maxHeight: "500px", maxWidth: "auto", objectFit: "cover"}}/>
</div> 


### Divider

The divider widget adds a **horizontal line** to your dashboard, which can be used to visually separate different sections or elements within the dashboard.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/builder/builder_divider.gif').default} alt="recent datasets" style={{ maxHeight: "500px", maxWidth: "auto", objectFit: "cover"}}/>
</div> 

### Image

Upload an image **from your computer** to your dashboard. When **padding** is enabled, it'll add a *thicker border around the image*.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/builder/builder_image.png').default} alt="recent datasets" style={{ maxHeight: "500px", maxWidth: "auto", objectFit: "cover"}}/>
</div> 

::::tip

Check out our **[Gallery](https://www.plan4better.de/en/gallery)** for further dashboard inspirations.

::::

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/builder/builder_viewer_dashboard.gif').default} alt="recent datasets" style={{ maxHeight: "500px", maxWidth: "auto", objectFit: "cover"}}/>
</div> 




