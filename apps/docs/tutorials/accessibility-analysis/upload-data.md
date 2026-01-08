---
sidebar_position: 3
---

# Upload Data

Now that you have a project, let's add some data. GOAT supports various formats including GeoJSON, Shapefile, CSV, and more.

## Supported Data Formats

| Format     | Extension                            | Best For                      |
| ---------- | ------------------------------------ | ----------------------------- |
| GeoJSON    | `.geojson`, `.json`                  | Web-friendly vector data      |
| Shapefile  | `.zip` (containing .shp, .dbf, etc.) | Traditional GIS data          |
| GeoPackage | `.gpkg`                              | Modern, single-file format    |
| CSV        | `.csv`                               | Tabular data with coordinates |
| KML        | `.kml`                               | Google Earth data             |

## Step-by-Step Instructions

### 1. Open the Data Catalog

Navigate to the **Datasets** section in your workspace.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/workspace/workspace_datasets.png').default} alt="Datasets View" style={{ maxHeight: "500px", maxWidth: "100%", objectFit: "cover", borderRadius: "8px", boxShadow: "0 4px 12px rgba(0,0,0,0.15)"}}/>
  <p><em>The Datasets management view</em></p>
</div>

### 2. Upload Your File

1. Click **"Upload Dataset"** or drag and drop your file
2. GOAT will automatically detect the file format
3. Preview your data to ensure it loaded correctly
4. Assign a name and optional description

### 3. Verify the Data

After upload, check that:
- All features are visible on the map preview
- Attribute columns are correctly detected
- Geometry types match your expectations

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/data/data-table.png').default} alt="Data Table View" style={{ maxHeight: "400px", maxWidth: "100%", objectFit: "cover", borderRadius: "8px", boxShadow: "0 4px 12px rgba(0,0,0,0.15)"}}/>
  <p><em>Reviewing your data in table view</em></p>
</div>

## Sample Data for This Tutorial

For this tutorial, you can use POI (Points of Interest) data. Here's what makes good input for catchment analysis:

- **Schools** - Analyze walking accessibility for students
- **Supermarkets** - Check grocery store coverage
- **Public Transit Stops** - Evaluate transit accessibility
- **Healthcare Facilities** - Map healthcare access

:::tip Download Sample Data
Don't have data? Use GOAT's built-in **Data Catalog** to access ready-to-use datasets for your region.
:::

## Data Quality Checklist

Before proceeding, verify:

- [ ] Data has valid geometries (points for POIs)
- [ ] Coordinate system is correct (WGS84 / EPSG:4326)
- [ ] Attributes are meaningful for your analysis
- [ ] No duplicate features

## Next Step

Your data is ready! Let's move on to the exciting part: [Running the Catchment Analysis](./run-analysis).

---

**Progress:** 2 of 5 steps completed
