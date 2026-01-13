---
slug: /tutorials/goat-erste-schritte/add-data
sidebar_position: 5
sidebar_label: ✏️ 5. Add Data
---

# Add Data to the Project

For our supermarket accessibility analysis, we need two important datasets: supermarket locations and city boundaries. We will add both from the GOAT Data Catalog.

## Add Supermarket Layer

1. **Click `+ Add Layer`** in the bottom left of the left panel
2. **Select `Data Catalog`**
3. **Search for the dataset "POI Shopping"**
4. **Click `Add Layer`** to add it to your project

## Add City Boundaries Layer

1. **Click `+ Add Layer` again** and select `Data Catalog`
2. **Search for the layer "Regiostar Raumtypisierung"**, which contains all boundaries in Germany
3. **Click `Add Layer`** to add the boundaries to your project

<div style={{ display: 'flex', justifyContent: 'center' }}>
<img src={require('/img/tutorials/01_erste_schritte/daten-hinzufugen.gif').default} alt="Catchment Area Calculation Result in GOAT" style={{ maxHeight: "100%", maxWidth: "auto"}}/>
</div>

<p></p>

:::tip Layer Order
For optimal map readability, we need to arrange the layers correctly:
**In the layer panel, select the newly added "Regiostar Raumtypisierung" layer and drag it below the "POI Shopping" layer**
:::




