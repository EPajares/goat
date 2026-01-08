---
sidebar_position: 1
---

# Dataset Types

On GOAT, you can work with datasets from Plan4Better’s catalog or upload your own from your computer. It accepts various formats for both **Feature Datasets** and **Raster Datasets**. Here we explain the different types of datasets you can use in GOAT.

## Feature Datasets

### 1.1 Spatial Features

Feature datasets store **spatial features like points, lines, or polygons**. On GOAT you can upload data from **Shapefiles**, **Geopackages**, **GeoJSON**, or **KML** files, or add a **WFS** link from an external URL. You can visualize, style, and analyze these datasets using the different tools from the toolbox.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/data/spatial.png').default} alt="Spatial features in GOAT" style={{ maxHeight: "750px", maxWidth: "750px", objectFit: "cover"}}/>
  <p style={{ textAlign: 'center', fontStyle: 'italic', marginTop: '8px', color: '#666' }}> Example of spatial features displayed in GOAT</p>
</div>

<p></p>

GOAT recognizes two types of feature datasets based on their source:

- **Feature Dataset Standard**: These are the datasets you upload yourself (like GeoJSON, GPKG, KML, and ZIP files). Think of these as your "raw materials" - the original data you bring into GOAT to work with.

- **Feature Dataset Tool**: These are datasets created by GOAT's analysis tools. When you run an analysis (like creating catchment areas or heatmaps), the results become this type of dataset.

### 1.2 Non-Spatial Datasets

**Tables** are **non-spatial datasets** without geographic reference points, so they can't be visualized on the map. Import them in **CSV** or **XLSX** formats for analysis and data management.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/data/table.png').default} alt="Non-spatial datasets in GOAT" style={{ maxHeight: "750px", maxWidth: "750px", objectFit: "cover"}}/>
  <p style={{ textAlign: 'center', fontStyle: 'italic', marginTop: '8px', color: '#666' }}> Example of a table displayed in GOAT</p>
</div>

## Rasters Datasets

Raster datasets can come from external sources like **WMS** (Web Map Service) or **WMTS** (Web Map Tile Service). They provide georeferenced map images, such as topographic maps, but on GOAT they’re static, so they don’t support analysis or editing.

:::tip Note
Raster styling depends on the external service (e.g., GeoServer). You can’t change the color scheme or feature representation in GOAT.
:::

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/data/raster.png').default} alt="Raster datasets in GOAT" style={{ maxHeight: "750px", maxWidth: "750px", objectFit: "cover"}}/>
  <p style={{ textAlign: 'center', fontStyle: 'italic', marginTop: '8px', color: '#666' }}> Example of a raster layer displayed in GOAT</p>

</div>

- **WMS (Web Map Service)**: Supports zooming and panning, ideal for basemaps, but outputs static images and loads slower.

- **WMTS (Web Map Tile Service)**: Uses pre-rendered tiles for fast loading and smooth zooming. Best for large areas and consistent map styles.

- **XYZ Tiles**: Offers fast zooming and panning with tiles defined by X (longitude), Y (latitude), and Z (zoom level) coordinates. Ideal for fast-loading maps with consistent performance at different zoom levels.

|   | WMS | WMTS and XYZ Tiles |
|----|-------------|--------------|
| **Type of URL in GOAT**    | Capabilities URL | Capabilities (only WMTS), Direct URL |
| **Data output** | Dynamic map images | Pre-rendered, cached map tiles |
| **Structure** | No tiles - images generated on-the-fly | Structured tiles based on grid |
| **Performance** | Slower (images generated per request) | Faster (tiles cached) |
| **Customization** | Limited | Limited |
| **Scalability** | Less scalable | Highly scalable |
| **Zoom level** | Variable, set by request parameters | Fixed zoom level, predetermined by server |