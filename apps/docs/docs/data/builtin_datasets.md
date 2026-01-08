---
sidebar_position: 3
---

# Built-in Datasets

## The foundation behind GOAT's Indicators

GOAT's powerful accessibility indicators and analysis tools rely on high-quality built-in datasets that work behind the scenes. **These datasets are not directly accessible to users, but they power all routing calculations and accessibility analyses within GOAT.**

Understanding these underlying datasets helps you:
- **Know what data quality** to expect from GOAT's indicators
- **Understand the geographic coverage** of different analysis tools
- **Interpret results** with knowledge of the data sources

:::info User Data vs Built-in Data
**Built-in datasets** (described on this page) power GOAT's internal calculations and indicators. For datasets you can upload your own data or use existing datasets from our [Catalog](../workspace/catalog.md).
:::

## Network Datasets for Routing

GOAT includes comprehensive network datasets that power all routing-based accessibility indicators and analysis tools.

### Public Transport Network

Our public transport network covers multiple modes including buses, trams, subways, trains, and ferries. This network enables GOAT's [Public Transport](../routing/public_transport) routing capabilities.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/data/data_basis/pt_network_banner.png').default} alt="Public Transport Network" style={{ maxHeight: "auto", maxWidth: "auto", objectFit: "cover"}}/>
</div>

**What's Included:**
- **Stops**: Names, locations, types, and accessibility information
- **Routes**: Service types, accessibility details, and route information  
- **Schedules**: Departure times, service frequency, and operating days
- **Transfers**: Interchange specifications and station connections
- **Trip Patterns**: Stop sequences and timing information
- **Route Shapes**: Geospatial representation of transit lines

**Data Sources:**
- **Germany**: [DELFI](https://www.delfi.de/) - Germany's national public transport data platform
- **Street-level Data**: [OpenStreetMap (OSM)](https://wiki.openstreetmap.org/) - For station access, pedestrian connections, and multi-modal routing

**How We Process the Data:**
1. **Import**: Data is collected in [GTFS (General Transit Feed Specification)](https://gtfs.org/) format
2. **Verify & Correct**: We validate stop relationships, platform connections, and service type classifications
3. **Optimize**: Networks are streamlined to include only the most representative service patterns for each route
4. **Schedule Types**: Analysis supports three day types - **Weekday** (typically Tuesday), **Saturday**, and **Sunday**

### Street Network and Topography

Our street network represents real-world transportation infrastructure including roads, highways, bike paths, and pedestrian ways. This powers GOAT's [Walking](../routing/walking), [Cycling](../routing/bicycle), [E-bike](../routing/bicycle), and [Car](../routing/car) routing.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/data/data_basis/street_network_banner.png').default} alt="Street Network" style={{ maxHeight: "auto", maxWidth: "auto", objectFit: "cover"}}/>
</div>

**Network Components:**
- **Segments (Edges)**: Continuous path sections between intersections
- **Intersections (Nodes)**: Points where different paths meet or cross

**Data Sources:**
- **Street Networks**: [Overture Maps Foundation](https://overturemaps.org/) - High-quality, Europe-wide transportation data
- **Elevation Data**: [Copernicus](https://www.copernicus.eu/en) Digital Elevation Model (DEM) for accurate slope calculations

**Processing Workflow:**
1. **Data Import**: Street network data is imported in Geoparquet format from Overture Maps' [Transportation theme](https://docs.overturemaps.org/guides/transportation/)
2. **Elevation Processing**: European DEM tiles are processed to extract topographical information
3. **Spatial Indexing**: Network segments are organized using [Uber's H3 grid system](../further_reading/glossary#h3-grid) for efficient processing
4. **Slope Calculation**: Surface gradients and slope impedance are computed for each street segment
5. **Attribute Parsing**: Street classifications, speed limits, turning restrictions, and one-way designations are identified and standardized
6. **Speed Limit Interpolation**: Missing speed limits are estimated based on street type and modal speeds

:::info Coming Soon
While GOAT currently uses built-in networks for public transport and street routing, we're working on allowing users to upload their own custom networks. Interested in this feature? [Contact us](https://plan4better.de/en/contact/ "Contact Support") to learn more.
:::
