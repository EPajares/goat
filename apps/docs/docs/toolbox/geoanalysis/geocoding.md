---
sidebar_position: 5
---

# Geocoding

This tool allows you to **geocode addresses from a layer using the Pelias geocoder service**.

## 1. Explanation

Geocoding is the process of **converting addresses (like "1600 Amphitheatre Parkway, Mountain View, CA") into geographic coordinates (latitude and longitude)**, which can be used to place markers on a map. This tool takes a table or layer with address fields and converts them into spatial point features.

## 2. Example use cases 

- Visualizing a list of customer addresses on a map.
- Converting a CSV file of store locations into a spatial dataset.

## 3. How to use the tool?

<div class="step">
  <div class="step-number">1</div>
  <div class="content">Click on <code>Toolbox</code> <img src={require('/img/icons/toolbox.png').default} alt="Options" style={{ maxHeight: "20px", maxWidth: "20px", objectFit: "cover"}}/>. </div>
</div>

<div class="step">
  <div class="step-number">2</div>
  <div class="content">Under the <code>Geoanalysis</code> menu, click on <code>Geocoding</code>.</div>
</div>

<div class="step">
  <div class="step-number">3</div>
  <div class="content">Select the input layer containing address data.</div>
</div>

<div class="step">
  <div class="step-number">4</div>
  <div class="content">Map the address fields (e.g., Street, City, Zip Code) to the corresponding columns in your data.</div>
</div>

<div class="step">
  <div class="step-number">5</div>
  <div class="content">Click <code>Run</code> to start the geocoding process. Result will be added to the map.</div>
</div>
