---
sidebar_position: 4
---

# Datasets

The Datasets page is your **data management hub where you can upload, organize, and share all your spatial and non-spatial data in GOAT**. This centralized workspace provides an organized view of your datasets, categorized into Personal Datasets, Team Datasets, and Organization-wide Shared Datasets. Here you can:

- **Add new datasets**
- **Filter and organize datasets** for better data structure and management
- **Manage datasets** by sharing, moving, deleting, among others functions.
  
<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
  <img src={require('/img/workspace/datasets/datasets_general.png').default} alt="Datasets Page in Workspace of GOAT" style={{ maxHeight: "auto", maxWidth: "80%", objectFit: "cover"}}/>
</div> 

## Adding datasets

You can add datasets to GOAT by: 
- Uploading files from your computer
- Connecting to external data sources.

### Upload data

GOAT supports multiple file formats for upload: **GeoPackage**, **GeoJSON**, **Shapefile**, **KML**, **CSV**, and **XLSX** files.

<div class="step">
  <div class="step-number">1</div>
  <div class="content">Navigate to the <code>Datasets</code> page using the sidebar navigation.</div>
</div>

<div class="step">
  <div class="step-number">2</div>
  <div class="content">Click <code>+ Add Dataset</code> and select <code>Dataset Upload</code>.</div>
</div>

<div class="step">
  <div class="step-number">3</div>
  <div class="content">Select the file from your local device using the file browser.</div>
</div>

<div class="step">
  <div class="step-number">4</div>
  <div class="content">
    <p>Configure your dataset:</p>
    <ul> 
      <li><strong>Destination Folder</strong> - Choose where to organize your dataset</li>
      <li><strong>Name</strong> - Give your dataset a descriptive name</li>
      <li><strong>Description</strong> (optional) - Add details about your dataset's content and purpose</li>
    </ul>
  </div>
</div>

<div class="step">
  <div class="step-number">5</div>
  <div class="content">Click <code>Upload</code> to add the dataset to your workspace.</div>
</div>

### External data sources

Connect to external data services including **Web Feature Service (WFS)**, **Web Map Service (WMS)**, **Web Map Tile Service (WMTS)**, and **XYZ Tiles**.

<div class="step">
  <div class="step-number">1</div>
  <div class="content">Navigate to the <code>Datasets</code> page using the sidebar navigation.</div>
</div>

<div class="step">
  <div class="step-number">2</div>
  <div class="content">Click <code>+ Add Dataset</code> and select <code>Dataset External</code>.</div>
</div>

<div class="step">
  <div class="step-number">3</div>
  <div class="content">Enter the URL of the external data service.</div>
</div>

<div class="step">
  <div class="step-number">4</div>
  <div class="content">Select the specific layer you want to add from the available options and click <code>Next</code>.</div>
</div>

<div class="step">
  <div class="step-number">5</div>
  <div class="content">
  <p>Configure your dataset:</p>
    <ul>
      <li><strong>Destination Folder</strong> - Choose where to organize your dataset</li>
      <li><strong>Name</strong> - Give your dataset a descriptive name</li>
      <li><strong>Description</strong> (optional) - Add details about the external data source</li>
    </ul>
  </div>
</div>

<div class="step">
  <div class="step-number">6</div>
  <div class="content">Review your configuration and click <code>Save</code> to add the external dataset.</div>
</div>

:::tip Alternative Upload Method
You can also upload datasets directly while working in the [Map](../map/layers) interface for immediate use in your projects.
:::


## Filtering and organizing datasets

### Filter by Dataset Type

Easily filter your datasets by [dataset type](../data/dataset_types "What are the dataset types?") to find exactly what you need. Available filters include:

- **Features** - Spatial datasets with points, lines, or polygons
- **Tables** - Non-spatial tabular data
- **External Imagery** - Raster data from external sources  
- **External Vector Tiles** - Vector tiles from external services

Click the filter icon <img src={require('/img/icons/filter.png').default} alt="Filter Icon" style={{ maxHeight: "20px", maxWidth: "20px"}}/> to select your desired dataset type.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
  <img src={require('/img/workspace/datasets/dataset_filter.gif').default} alt="Datasets filtering in Workspace of GOAT" style={{ maxHeight: "auto", maxWidth: "auto", objectFit: "cover"}}/>
</div>

### Create and manage folders

Organize your datasets into folders for better structure and easier navigation.

**To create a new folder:**

<div class="step">
  <div class="step-number">1</div>
  <div class="content">Click the <img src={require('/img/icons/folder.png').default} alt="Folder Icon" style={{ maxHeight: "20px", maxWidth: "20px"}}/> folder icon.</div>
</div>

<div class="step">
  <div class="step-number">2</div>
  <div class="content">Enter a descriptive name for your new folder</div>
</div>

<div class="step">
  <div class="step-number">3</div>
  <div class="content">Press <code>Create</code> to finalize the folder</div>
</div>

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
  <img src={require('/img/workspace/datasets/new_folder.gif').default} alt="Create new folders in Workspace of GOAT" style={{ maxHeight: "auto", maxWidth: "auto", objectFit: "cover"}}/>
</div>

<p></p>

**To move datasets to folders:**

<div class="step">
  <div class="step-number">1</div>
  <div class="content">Click the <img src={require('/img/icons/3dots.png').default} alt="Options" style={{ maxHeight: "20px", maxWidth: "20px"}}/> <code>more options</code> button next to your dataset</div>
</div>

<div class="step">
  <div class="step-number">2</div>
  <div class="content">Select <code>Move to folder</code> from the menu</div>
</div>

<div class="step">
  <div class="step-number">3</div>
  <div class="content">Choose your destination folder from the dropdown menu and press <code>Move</code>.</div>
</div>

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
  <img src={require('/img/workspace/datasets/move_to_folder.gif').default} alt="Move your datasets to the folders in Workspace of GOAT" style={{ maxHeight: "auto", maxWidth: "auto", objectFit: "cover"}}/>
</div>

## Dataset management

Access comprehensive dataset management options through the <img src={require('/img/icons/3dots.png').default} alt="Options" style={{ maxHeight: "20px", maxWidth: "20px", objectFit: "cover"}}/> <code>More Options</code> menu next to each dataset. Available actions include:

- <code>Edit metadata</code> - Access and edit dataset metadata
- <code>Move to folder</code> - Reorganize your dataset location
- <code>Download</code> - Export datasets to your local device
- <code>Update</code> - Update datasets with new data
- <code>Share</code> - Collaborate by sharing datasets with team members or your organization
- <code>Delete</code> - Remove datasets you no longer need


<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/workspace/datasets/managing_datasets.png').default} alt="Dataset management options" style={{ maxHeight: "auto", maxWidth: "80%"}}/>
</div>

#### Dataset metadata and preview

View detailed information about your datasets to better understand their content and structure. Access metadata by clicking directly on the dataset name.

The metadata view provides:

- <code>Summary</code> - Overview of dataset properties and statistics
- <code>Data</code> - Detailed view of all data fields and values  
- <code>Map</code> - Spatial visualization with interactive legend

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
  <img src={require('/img/workspace/datasets/metadata.gif').default} alt="Metadata of the datasets in Workspace of GOAT" style={{ maxHeight: "auto", maxWidth: "auto", objectFit: "cover"}}/>
</div> 
