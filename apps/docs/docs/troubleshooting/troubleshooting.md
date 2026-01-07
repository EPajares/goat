---
sidebar_position: 10
slug: /troubleshooting
---

# Troubleshooting

This page is here to guide you through issues or constraints while using GOAT, making it easier to solve them and continue progressing with your analysis.
:::tip INFO
Feel free to [contact us](https://plan4better.de/en/contact/ "contact us") for support or any further questions you may have.
:::

## Job failure
You can find below common job failure and suggestions to solve them.

* Jobs cannot exceed two minutes length. There is also a limit on the number of features that can be analyzed for each indicator. 
<div style={{ display: "flex", alignItems: "center" }}>
  <img 
    src={require('/img/icons/arrow-right.png').default} 
    alt="Layers" 
    style={{ maxHeight: "20px", maxWidth: "20px", objectFit: "cover", marginRight: "8px" }} 
  />
  <span>
    <strong>To perform analysis on large area, you can use the  <a href="map/filter">Filter</a> to split your analysis into smaller areas.</strong>
  </span>
</div>

 ![Filtering to compute larger areas](/img/troubleshooting/filtering.jpg "Filtering to compute larger areas")

For example, if you use the public transport trip count indicator in an area and a time period where no trip is performed; the job fails with the error: **The Layer is None**
<div style={{ display: "flex", alignItems: "center" }}>
  <img 
    src={require('/img/icons/arrow-right.png').default} 
    alt="Layers" 
    style={{ maxHeight: "20px", maxWidth: "20px", objectFit: "cover", marginRight: "8px" }} 
  />
  <span>
    <strong>You can try expanding the spatial or temporal range of your analysis.</strong>
  </span>
</div>

## Accessibility Indicators

### Heatmap Gravity
 The sensitivity of a Gaussian impedance function cannot be higher than 1,000,000.
<div style={{ display: "flex", alignItems: "center" }}>
  <img 
    src={require('/img/icons/arrow-right.png').default} 
    alt="Layers" 
    style={{ maxHeight: "20px", maxWidth: "20px", objectFit: "cover", marginRight: "8px" }} 
  />
  <span>
    <strong>You can use the suggested sensitivities in GOAT as a reference.</strong>
  </span>
</div>

### Catchment area
 The starting points of the indicator must be within 100m of the road network.
<div style={{ display: "flex", alignItems: "center" }}>
  <img 
    src={require('/img/icons/arrow-right.png').default} 
    alt="Layers" 
    style={{ maxHeight: "20px", maxWidth: "20px", objectFit: "cover", marginRight: "8px" }} 
  />
  <span>
    <strong> To accurately set your starting points on the map, you can visualize the network either directly with the basemap or by using the street network layer in the scenario. </strong>
  </span>
</div>

 ![Routing start point](/img/troubleshooting/routing_start.jpeg "Routing start point")


## Uploading datasets

If you try to upload a dataset type that is not supported by GOAT, an error occurs. See supported [dataset types](data/dataset_types)

