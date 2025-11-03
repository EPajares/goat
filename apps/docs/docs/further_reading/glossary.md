---
sidebar_position: 4
---

# Glossary



### Accessibility
**Accessibility** was first defined in 1959 as “the potential of opportunities for interaction”, which refers to the ease with which people or goods can be reached from a particular location ([Hansen, 1959](https://doi.org/10.1080/01944365908978307 "Visit Reference")). In the context of GIS and urban planning, it refers to the ease with which people can access essential services, such as healthcare facilities, schools, or supermarkets. 

Generally, ensuring appropriate accessibility is a critical aspect of urban and transport planning, as it profoundly influences individuals' quality of life and transportation decisions. Accessibility can be expressed through diverse indicators that aim to model accessibility at different spatial scales and transport modes.

### Accessibility Instrument
An **accessibility instrument** is a tool used to calculate and analyze the accessibility of a particular location or region. It takes into account factors such as transportation options, distance, and travel time to determine how easily people can access essential services such as healthcare and education. Usually, an accessibility instrument is technically based on GIS technology, routing algorithms, and different data sources.

### Active Mobility
**Active mobility** refers to the use of human-powered modes of transport, such as walking, and cycling. It is an important part of sustainable transport as it reduces car dependency and is emission-free. Active mobility also has many health benefits, such as reducing the risk of obesity and cardiovascular disease. 

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/literature/glossary/active_mobility_freepik.webp').default} alt="Active Mobility" style={{ mixBlendMode: 'multiply'}}/>
  <p style={{ textAlign: 'center' }}>Image: Designed by pch.vector / <a href="http://www.freepik.com">Freepik</a></p>
</div>


### Area of Interest (AOI)
An **Area of Interest (AOI)** is a specific geographical region or boundary that is of particular interest or importance to a particular study or analysis. It can be a watershed, a forest, a park, or any other geographic area relevant to the study. The AOI is usually defined by a set of coordinates or a polygonal boundary that encompasses the region of interest. 

### Connectivity
**Connectivity** refers to the degree to which paths are connected. The higher the path and intersection density, the higher the connectivity. The main obstacles to connectivity are, for example, rivers, railway lines, and highways.

Connectivity has a direct impact on accessibility, as it is decisive for the travel time to reach a certain destination. High connectivity is especially important for active modes, as these modes are particularly sensitive to detours. Thus, high connectivity is key to ensuring accessibility to services and amenities and promote sustainable mobility. 

### Geospatial Data

**Geospatial data** refers to data that is associated with specific geographic locations on the Earth's surface. This data typically includes information such as coordinates, attributes, and sometimes even metadata about the geographic features being represented. Geospatial data is used in various applications such as mapping, navigation, urban planning, environmental monitoring, and more. They are crucial for analyzing and understanding spatial relationships and patterns in the real world.

### H3 Grid

The **H3 grid** <img src={require('/img/literature/glossary/H3_grid_logo.webp').default} width="1000px" alt="H3 grid logo" style={{width: "100px", height: "170px", maxHeight: "50px", maxWidth: "50px", objectFit: "cover"}}/> 
is a geospatial indexing system by [Uber Technologies](https://investor.uber.com/home/default.aspx "About Uber Technologies") that partitions the Earth's surface into a hierarchical grid of hexagonal cells for more efficient and accurate representation and analysis of geospatial data. It uses a hexagonal tiling approach based on an icosahedron, creating a hierarchical structure with multiple levels of resolution. The hexagonal shape allows for equidistant and consistent spatial representation, with different resolutions. The resolution of H3 grids is typically described in terms of the edge length of the hexagon at each level. For example, at resolution 3, the hexagons cover a relatively large area (approx. edge length of 69km), similar to the size of countries or large states/provinces, whereas, at resolution 10 (approx. 75m edge length), the hexagons are much smaller and are suited for localized analyses.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/literature/glossary/H3_grid.webp').default}  alt="H3 Grid" style={{ width: "600px", height: "200px", objectFit: "cover", mixBlendMode: 'multiply'}}/>
  <p style={{ textAlign: 'center' }}>Image: <a href="https://www.uber.com/en-TR/blog/h3/">UBER</a></p>
</div>

### Heatmap
A **heatmap** is a graphical visualization form that uses different colors to indicate the different values of a dataset. This allows for a quick understanding of the data presented. 

In GOAT, we use - amongst other indicators - heatmaps to analyze the local accessibility of different amenities, such as cafes, restaurants, or supermarkets. The heatmap utilizes a range of colors to represent various accessibility values. By analyzing this data, we can gain insights into the distribution of destinations and the quality of infrastructure available.

### Indicator
An **indicator** is a means to analyze a specific attribute or topic quantitatively. Usually, a standardized procedure is applied for this, e.g. by using a formula. In planning, indicators can be used to assess the current situation, to compare different locations with each other, as well as to monitor the progress towards specific goals or objectives, such as improving accessibility. 

### Isochrone
An **isochrone** or catchment area is an indicator that shows how far people can travel in a given time at a given speed from a selected location. Isochrones can be calculated for any mode such as walking, cycling, car, or public transport. Depending on the selected mode, the corresponding routing network is used.  

You can find further information on how we perform isochrone calculations in our [indicator documentation](../toolbox/accessibility_indicators/catchments "Isochrone documentation"). 


### Land Use
**Land use** is the categorization and management of land according to its functional role within a specific area. This includes a range of purposes such as residential, commercial, industrial, and natural or conservation uses. Additionally, land use incorporates aspects of urban planning and environmental management, as how land is utilized significantly influences factors like population density and the distribution of destinations. Consequently, land use has a direct and substantial impact on accessibility, affecting the availability of services, transport connectivity, and liveability of an area.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/literature/glossary/landuse.webp').default}  alt="Landuse" style={{ width: "350px", height: "300px", objectFit: "cover"}}/>
<p style={{ textAlign: 'center' }}>Image: <a href="https://accelerator.chathamhouse.org/article/land-use-challenges">Chatham House Sustainability Accelerator</a></p>
</div>


### Local Accessibility
**Local accessibility**, also known as neighborhood-level accessibility, refers to the ease with which people can access essential services within a specific neighborhood or area ([Handy, 1992](http://www.jstor.org/stable/23288518 "Visit Reference")). It usually refers to active modes of transport and focuses on short travel distances. 

### Micromobility
**Micromobility** is a growing trend in urban transportation, involving small, lightweight vehicles like electric scooters and skateboards. These compact modes of transport offer convenient solutions for short-distance travel. 

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/literature/glossary/micromobility_freepik.webp').default} 
  alt="Micromobility" style={{ width: "600px", height: "300px", mixBlendMode: 'multiply'}} />
  <p style={{ textAlign: 'center' }}>Image: Designed by pch.vector / <a href="http://www.freepik.com">Freepik</a></p>
</div>

### Open Source 
**Open source** <img src={require('/img/literature/glossary/open_source.webp').default} width="1000px" alt="opensource" style={{width: "100px", height: "170px", maxHeight: "50px", maxWidth: "50px", objectFit: "cover"}}/> refers to software or other products that are made available to the public with their source code freely accessible and modifiable. This allows individuals and organizations to modify and improve the product as needed, without restrictions on use or distribution. 

### Planning Support System (PSS)
A **planning support system** is a digital tool used to support the planning and decision-making process for urban and regional development. It uses data and models to provide information on various aspects of planning, such as land use, transportation, and environmental impact. A PPS allows planners to explore different scenarios and evaluate the potential outcomes of their decisions. 

### Point of Interest (POI)
A **Point of Interest (POI)** refers to a distinct location or site that holds significant relevance or value within a specific context, study, or analysis. In the context of GOAT, POIs mainly refer to amenities of daily need, such as supermarkets, kindergartens, or restaurants. 

### Quantile Classification
**Quantile classification** is a commonly used method in Geographic Information Systems (GIS) to divide data into equal groups based on their values. This method is useful for analyzing and visualizing patterns in data and can help identify trends and patterns that may not be obvious easily. 

In GIS, quantile classification is often used to create choropleth maps, which are maps that use color to represent different values of a variable. For example, a choropleth map of the population density of a city. The map would be divided into e.g. five color-coded categories, with each category representing a different range of population densities. 

The quantile classification can be used for [attribute-based styling](../map/layer_style/style/attribute_based_styling.md) in GOAT. 

### Routing 
**Routing** <img src={require('/img/literature/glossary/routing_logo.webp').default} width="1000px" alt="routing" style={{width: "100px", height: "170px", maxHeight: "50px", maxWidth: "50px", objectFit: "cover"}}/> refers to the process of finding the fastest or shortest path from one location to another. This is commonly used in transportation planning and navigation systems to help people get from point A to point B but is also crucial to accessibility analysis.

### Sustainability  
**Sustainability** <img src={require('/img/literature/glossary/sustainability.webp').default} width="1000px" alt="sustainability" style={{width: "100px", height: "200px", maxHeight: "50px", maxWidth: "100px", objectFit: "cover"}}/> refers to meeting the needs of the present without compromising the ability of future generations to meet their own needs. In the context of urban and regional development, sustainability involves balancing economic, social, and environmental factors to create livable and resilient communities. This includes reducing carbon emissions, promoting active mobility, and preserving natural resources. 

### Transport Mode
**Transport mode** refers to the type of transportation used for a particular trip or journey. This can include modes such as transit (bus, train, subway), cycling (pedelec, bike), walking, and driving. The choice of transport mode can have a significant impact on factors such as travel time, cost, and environmental impact. 

______________________________________________________________________________

### References
Hansen, W.G. (1959). How accessibility shapes land use. Journal of the American Institute of Planners. 25, 73–76.
https://doi.org/10.1080/01944365908978307 

Handy, S. L. (1992). Regional Versus Local Accessibility: Neo-Traditional Development and its Implications for Non-work Travel. Built Environment (1978-), 18(4), 253–267. http://www.jstor.org/stable/23288518 


