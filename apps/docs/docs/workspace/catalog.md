---
sidebar_position: 5
---

# Catalog

The **Data Catalog** is your gateway to exploring Plan4Better's comprehensive collection of high-quality [geospatial datasets](../further_reading/glossary#geospatial-data). **This curated library provides reliable, ready-to-use data from official open-data providers and other trusted sources**, enabling you to immediately start analysis and visualization within your GOAT projects. From the Catalog you can:

- **Explore our dataset collection** spanning multiple thematic areas and geographic regions
- **Search and filter through it** by keyword, spatial extent, and dataset attributes

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/workspace/catalog/catalog_general.png').default} alt="Data Catalog" style={{ maxHeight: "700px", maxWidth: "800px"}}/>
</div>

## Exploring the Catalog

Access the Data Catalog from the [Workspace](../category/workspace) or directly through the <code>+ Add layer</code> button in your GOAT projects. The catalog provides powerful discovery tools including:

- **Keyword search** for finding specific datasets or topics
- **Filters** to browse datasets by Type, [Data Category](#Data-Category) , Region, Language, Distributor Name, and Licence
- **Interactive preview** to assess data quality and content before use

### Dataset Category {#dataset-category}

One way of filtering the Catalog is through **Data Category**, which organizes datasets into clear thematic categories for easy navigation:

- **Boundary** - Administrative, political, and geographic boundaries including borders and districts
- **Land-use** - Classifications of land areas by usage type (residential, commercial, industrial, etc.)
- **People** - Demographic data including population density, age groups, and socio-economic characteristics
- **Places** - Points of interest such as schools, hospitals, tourist attractions, and services
- **Transportation** - Road networks, railways, airports, ports, and public transport infrastructure

### Dataset Metadata

Each dataset includes comprehensive metadata accessible by clicking on the dataset name. The metadata view provides:

- **Detailed descriptions** explaining dataset content and scope
- **Dataset type** classification and technical specifications
- **Geographic coverage** with **ISO 3166-1 alpha-2** country codes
- **Source information** including distributor name and contact details
- **License details** specifying usage rights and restrictions
- **Interactive map preview** for visual data exploration
- **Attribute information** showing available data fields and properties

### Available Dataset Types

The catalog includes diverse datasets managed as feature layers containing geospatial features (points, lines, polygons) or non-geospatial tabular data. These datasets can be directly added to your projects for analysis and visualization.

#### Points of Interest (POIs)
Strategic locations of amenities, facilities, and attractions essential for accessibility planning and urban analysis, such as Public transport stops and stations, Shopping centers and retail locations, Tourism and leisure facilities, Food and beverage establishments, Healthcare facilities and hospitals, Educational institutions and schools.

*Data Sources:* [Overture Maps Foundation](https://overturemaps.org/), [OpenStreetMap (OSM)](https://wiki.openstreetmap.org/), government departments, health insurance providers, and retail companies. Additional field data collection conducted when necessary.

#### Population and Buildings
Detailed demographic data disaggregated to building and local levels, enhanced with land-use information for improved accuracy. We provide Building-level population data for German districts and municipalities, local population data from German Census 2022, and European NUTS-3 level population statistics (Nomenclature of Territorial Units for Statistics).

*Data Sources:* [German Census 2022](https://ergebnisse.zensus2022.de/datenbank/online/), individual municipalities and districts, and 3D City Models from German federal states.

#### Administrative Boundaries
Comprehensive boundary datasets defining governmental and administrative jurisdictions at multiple scales, such as Municipal boundaries, District boundaries, Federal state boundaries, and Postal code regions.

*Data Sources:* [Federal Agency for Cartography and Geodesy (BKG)](https://www.bkg.bund.de/) and [OpenStreetMap (OSM)](https://wiki.openstreetmap.org/).

## Adding Catalog data to your projects

Follow these steps to add datasets from the catalog to your GOAT projects:

<div class="step">
  <div class="step-number">1</div>
  <div class="content">In your project, navigate to the <strong>Layers</strong> tab and click <code>+ Add Layer</code></div>
</div>

<div class="step">
  <div class="step-number">2</div>
  <div class="content">Select <code>Catalog Explorer</code> to browse the Data Catalog</div>
</div>

<div class="step">
  <div class="step-number">3</div>
  <div class="content">Browse or search for your desired dataset, then click <code>Add Layer</code> to include it in your project</div>
</div>

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/workspace/catalog/catalog_add-layer.gif').default} alt="Catalog Explorer" style={{ maxHeight: "700px", maxWidth: "800px"}}/>
</div>

<p></p>

:::tip Hint
After adding the layer, you can apply [Filters](../map/filter.md "Filter dataset")  to constrain large datasets to specific geographic extents or attributes needed for your analysis
:::


## Data quality and maintenance

Plan4Better ensures the reliability and currency of catalog data through comprehensive data management processes:

### Data collection and preparation

Our data collection process follows rigorous standards to ensure quality and reliability:

- **Source identification** - We prioritize official open data portals and publicly available initiatives
- **Format standardization** - Various formats (shapefiles, GeoJSON, etc.) are converted to consistent schemas
- **Data integration** - Multiple datasets are combined and adapted to local contexts through fusion workflows
- **Quality validation** - Comprehensive validation processes ensure accuracy and reliability
- **Continuous expansion** - We actively seek and integrate additional datasets based on user needs

### Update schedule

To maintain data currency and relevance:

- **Annual updates** - All datasets are refreshed at least once per year
- **Dynamic data** - Rapidly changing data (POIs, public transport) receives more frequent updates
- **On-demand updates** - Critical datasets can be updated as needed based on user requirements

