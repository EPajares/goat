---
sidebar_position: 5
---
import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';

# Geocoding

This tool allows you to **geocode addresses from a layer using the Pelias geocoder service**.

## 1. Explanation

Geocoding is the process of **converting addresses (like "Agnes-Pockels-Bogen 1, 80992 München, Germany") into geographic coordinates (latitude and longitude)**, which can be used to place markers on a map. This tool takes a table or layer with address fields and converts them into spatial point features.

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
  <div class="content">Select the <code>Input layer</code> containing address data.</div>
</div>

<div class="step">
  <div class="step-number">4</div>
  <div class="content">Choose the input mode for your addresses:
    <ul>
      <li><code>Full Address:</code> Use this if you have a single column containing complete addresses (e.g., "Marienplatz 1, Munich, Germany")</li>
      <li><code>Structured:</code> Use this if your address components are in separate columns (street, city, postal code, etc.)</li>
    </ul>
  </div>
</div>

<div class="step">
  <div class="step-number">5</div>
  <div class="content">Configure the address mapping based on your chosen input mode:

<Tabs>
  <TabItem value="full-address" label="Full Address" default>
    <ul>
      <li>Select the column containing the complete address</li>
    </ul>
  </TabItem>
  <TabItem value="structured" label="Structured">
    <ul>
      <li>Select the <code>Street Address</code> field to the column containing street information</li>
      <li>Select the <code>Postal Code</code> from a column (optional)</li>
      <li>Select the <code>City/Town</code> from a column (optional)</li>
      <li>Select the <code>Country</code> either from a column or set a constant value (defaults to "Germany")</li>
      <li>By clicking on <img src={require('/img/icons/options.png').default} alt="Options Icon" style={{ maxHeight: "25px", maxWidth: "25px", objectFit: "cover"}}/> <code>Advanced options</code>, you can select the <code>State/Province</code> from a column (optional)</li>
    </ul>

:::tip Note

None of the fields are mandatory except for the street address, but providing more details will improve geocoding accuracy.

:::
  </TabItem>
</Tabs>
  </div>
</div>

<div class="step">
  <div class="step-number">6</div>
  <div class="content">Click <code>Run</code> to start the geocoding process. The result will be added to the map.</div>
</div>
