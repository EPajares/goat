---
sidebar_position: 1
---

# Join

This tool allows you to **combine data from two layers based on attribute matching or spatial relationships**. This is essential for spatial analysis, data enrichment, and creating comprehensive datasets.

## 1. Explanation

Joining is the process of attaching fields from one layer (Join Layer) to another layer (Target Layer).

**GOAT supports three types of joins:**
1. **Attribute Join:** Matches features based on a common field (e.g., matching "Zip Code" in both layers).
2. **Spatial Join:** Matches features based on their geometric relationship (e.g., "features that intersect" or "features within a distance").
3. **Spatial & Attribute Join:** Requires **both** a spatial overlap and a matching attribute to join features.

The result is a new layer containing the Target Layer's geometry and attributes, plus the attributes from the Join Layer.

## 2. Example use cases

### Attribute Join
- Add population data to zip code areas (matching on zip code).
- Combine survey data with census tract boundaries (matching on tract ID).

### Spatial Join
- Count the number of schools within each city district (Points inside Polygons).
- Find the closest fire station to each building.
- Sum the total length of roads within a park.

## 3. How to use the tool?

<div class="step">
  <div class="step-number">1</div>
  <div class="content">Click on <code>Toolbox</code> <img src={require('/img/icons/toolbox.png').default} alt="Options" style={{ maxHeight: "20px", maxWidth: "20px", objectFit: "cover"}}/>. </div>
</div>

<div class="step">
  <div class="step-number">2</div>
  <div class="content">Under the <code>Data Management</code> menu, click on <code>Join</code>.</div>
</div>

### Select layers

<div class="step">
  <div class="step-number">3</div>
  <div class="content">Select your <code>Target Layer</code>: The main layer you want to keep.</div>
</div>

<div class="step">
  <div class="step-number">4</div>
  <div class="content">Select your <code>Join Layer</code>: The layer containing data you want to add.</div>
</div>

### Choose Join Method

<div class="step">
  <div class="step-number">5</div>
  <div class="content">Select the <code>Join Method</code>:</div>
</div>

- **Attribute:** Match based on fields.
- **Spatial:** Match based on location.
- **Spatial & Attribute:** Match based on both.

---

### Settings (depending on method)

**If Attribute Join:**
- Select the **Target Field** (key in matching layer).
- Select the **Join Field** (key in join layer).

**If Spatial Join:**
- Select the **Spatial Relationship** (e.g., Intersects, Within Distance, Completely Contains).
- If "Within Distance", specify the search distance and units.

---

### Join Options (Cardinality)

<div class="step">
  <div class="step-number">6</div>
  <div class="content">Select the <code>Join Operation</code> (One-to-One or One-to-Many).</div>
</div>

**One-to-One:**
If multiple features in the Join Layer match a single feature in the Target Layer, you must choose how to handle them:
- **First Record:** Takes the first matching record (arbitrary sort).
- **Calculate Statistics:** Aggregates the matching records (e.g., Sum, Mean, Min, Max).
- **Count Only:** Just counts how many matches were found.

**One-to-Many:**
Creates a separate feature in the output for *each* matching feature in the Join Layer (could duplicate target geometry).

### Run

<div class="step">
  <div class="step-number">7</div>
  <div class="content">Click <code>Run</code> to execute the join. Result will be added to the map.</div>
</div>
