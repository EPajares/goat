---
sidebar_position: 3
---

import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';

# Quickstart Guide
Welcome to GOAT! This quickstart guide will help you get up and running with GOAT in no time. Follow these simple steps to explore the workspace, and create your first analysis and interactive map.

## Create a new project


<div class="step">
  <div class="step-number">1</div>
  <div class="content">After signing in, you will land on the <code>Workspace</code> page. Click on the <code>+</code> button to create a new project.</div>
</div>

<div class="step">
  <div class="step-number">2</div>
  <div class="content">Choose a <b>Folder location</b>, fill the <b>project name</b> field and <b>description</b>, and click on the <code>Create</code> button.</div>
</div>

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/getting_started/new_project.gif').default} alt="Workspace at GOAT" style={{ maxHeight: "auto", maxWidth: "75%", objectFit: "cover"}}/>
</div>

## Add data to your project
You've landed in the map view of your new project. Now it's time to add some data.

<div class="step">
  <div class="step-number">3</div>
  <div class="content">Click on <code>+ Add Layer</code> on the bottom left of the left panel. </div>
</div>

<div class="step">
  <div class="step-number">4</div>
  <div class="content">Select if you like to integrate a dataset from your <b>data explorer</b>, <b>upload</b> a new dataset, browse the <b>catalog explorer</b> or add a dataset via an <b>external link</b>.</div>
</div>

<Tabs>
    <TabItem value="Dataset Explorer" label="Dataset Explorer" default className="tabItemBox">
<div class="step">
    <div class="step-number">5</div>
    <div class="content">Select the file you want to import.</div>
</div>
<div class="step">
    <div class="step-number">6</div>
    <div class="content">Click on <code>+ Add Layer</code>.</div>
</div>
    </TabItem>

<TabItem value="Dataset Upload" label="Dataset Upload" className="tabItemBox">
<div class="step">
  <div class="step-number">5</div>
  <div class="content">Select the file you want to import.</div>
</div>
<div class="step">
  <div class="step-number">6</div>
  <div class="content">Define the name of the dataset, description, and click on <code>Upload</code>.</div>
</div>
</TabItem>
  
<TabItem value="Catalog Explorer" label="Catalog Explorer" className="tabItemBox">
<div class="step">
  <div class="step-number">5</div>
  <div class="content">Browse GOAT Dataset Catalog.</div>
</div>
<div class="step">
  <div class="step-number">6</div>
  <div class="content">Select the Dataset you want to import and click on <code>+ Add Layer</code>.</div>
</div>
</TabItem>

<TabItem value="Dataset External" label="Dataset External" default className="tabItemBox">
<div class="step">
  <div class="step-number">5</div>
  <div class="content">Insert your external URL and follow the steps <b>depending on the type of dataset</b> you would like to add.</div>
</div>
<Tabs>
<TabItem value="WFS" label="WFS" default className="tabItemBox">
<div class="step">
    <div class="content"> <p>When you would like to add a WFS layer you need to have a <b>"GetCapabilities"</b> link. </p>
    In the next step you can choose which layer you would like to add to your dataset. <i>You can only choose one layer at a time.</i></div>
</div>
</TabItem>

<TabItem value="WMS" label="WMS" className="tabItemBox">
<div class="step">
    <div class="content"> <p>When you would like to add a WMS layer you need to have a <b>"GetCapabilities"</b> link.</p> Here you have the option to select multiple layers, but when added to GOAT it <i>will be merged onto one layer.</i> </div>
</div>
</TabItem>

<TabItem value="WMTS" label="WMTS" className="tabItemBox">
<div class="step">
    <div class="content"> <p>You can add a WMTS to your dataset via a <b>direct URL</b> or <b>"GetCapabilities"</b> link. You can only choose <i>one layer</i> at a time if your URL contains more than one layer.</p>
    The projection needs to be <i>WEB Mercator (EPSG:3857) and GoogleMaps compatible</i>. Because they have different zoom levels, the dataset would not show up in the list of available layers if it doesn't meet both requirements.</div>
</div>
</TabItem>

</Tabs>
</TabItem>
</Tabs>

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/getting_started/add_data.png').default} alt="Workspace at GOAT" style={{ maxHeight: "auto", maxWidth: "auto", objectFit: "cover"}}/>
</div>

## Explore the analysis tools
Depending on the layers you have added, you can run different analysis from the toolbox.
<div class="step">
  <div class="step-number">7</div>
  <div class="content"> Click on the <code>Toolbox</code> button on the right panel.</div>
</div>

<div class="step">
  <div class="step-number">8</div>
  <div class="content"> Select the analysis tool you want to use. You can choose between our <b> Accessibility indicators</b>, <b>Data management</b>, <b>Geoanalysis</b>, or <b>Geoprocessing</b> tools, and complete the settings.</div>
</div>

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/getting_started/toolbox.png').default} alt="Workspace at GOAT" style={{ maxHeight: "auto", maxWidth: "auto", objectFit: "cover"}}/>
</div>


## Style your map
Once you have added the layers to your map and computed the analysis, you can customize their appearance to enhance visualization.

<div class="step">
  <div class="step-number">9</div>
  <div class="content">Click on <code>Layer design <img src={require('/img/map/styling/styling_icon.webp').default} alt="Styling Icon" style={{ maxHeight: "15px", maxWidth: "21px", objectFit: "cover"}}/></code>, open the <code> Style</code> menu, select the color you want or if you want to style by attribute, click on <code>options <img src={require('/img/map/styling/options_icon.png').default} alt="Options Icon" style={{ maxHeight: "15px", maxWidth: "15px", objectFit: "cover"}}/></code>, and set the field you want on the <code>Color based on </code> menu.</div>
</div>

<div class="step">
  <div class="step-number">10</div>
  <div class="content">You can continue setting the <code>Style</code> by choosing the <b>color palette</b>, the <b>Stroke Color</b>, or choosing a <b>Custom Marker</b> if you are working with a point layer.</div>
</div>

<div class="step">
  <div class="step-number">11</div>
  <div class="content">Then you can turn on the <code>Labels</code> if you want, edit your <code>Popups</code> and <code>Legend</code>.</div>
</div>

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/getting_started/layer_design.png').default} alt="Workspace at GOAT" style={{ maxHeight: "auto", maxWidth: "auto", objectFit: "cover"}}/>
</div>

## Ready to share your work
Now that you have created your first project in GOAT, it's time to share it with others. You can easily share your project by generating a shareable link or inviting collaborators to work on the project with you.

<div class="step">
  <div class="step-number">12</div>
  <div class="content">Click on <code>Share</code> in the upper-right corner of the map.</div>
</div>

<div class="step">
  <div class="step-number">13</div>
  <div class="content">Go to the <code>Public</code> toggle and click on <code>Publish</code> to make your map public.</div>
</div>

<div class="step">
  <div class="step-number">14</div>
  <div class="content">Now you can click on <code>Copy URL</code> and <b> share the direct link </b> so others can open the map in their browser. Or click on <code>Copy iframe Code</code> and <b> embed the map </b> in websites or tools that support HTML and iframes.</div>
</div>


<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/getting_started/share.gif').default} alt="Workspace at GOAT" style={{ maxHeight: "auto", maxWidth: "75%", objectFit: "cover"}}/>
</div>
