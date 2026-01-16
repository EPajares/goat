---
slug: /tutorials/goat-erste-schritte/data-preparation
sidebar_position: 6
sidebar_label: ✏️ 6. Prepare Data
---

# Prepare Data

To focus our analysis specifically on Mannheim, we will filter both layers.

### Filter the Boundaries Layer

1. **Click on the "Regiostar Raumtypisierung" layer** - a panel will appear on the right
2. **Select the `Filter` tab**
3. **Click `+ Add Expression`** and choose `Logical Expression`
4. **Configure the filter:**
   - **Field:** "name"
   - **Operator:** "is"  
   - **Value:** "mannheim" (search for this value)

<div style={{ display: 'flex', justifyContent: 'center' }}>
<img src={require('/img/tutorials/01_erste_schritte/filtern.gif').default} alt="Catchment Area Calculation Result in GOAT" style={{ maxHeight: "100%", maxWidth: "auto"}}/>
</div>

### Filter & Clip the "POI Shopping" Layer

1. **Click on the "POI Shopping" layer** - a panel will appear on the right
2. **Select the `Filter` tab**
3. **Click `+ Add Expression`** and choose `Logical Expression`
4. **Configure the filter:**
   - **Field:** "category"
   - **Operator:** "Contains"
   - **Value:** "supermarket", "discount_supermarket" and "hypermarket"
  
5. **Click on `Toolbox`** in the top menu bar
6. **Under the `Geoprocessing` menu click on `Clip`**
7. **Select the following settings:**
   - **Input layer:** "POI Shopping" (the layer you want to clip)
   - **Overlay layer:** "Regiostar Raumtypisierung" (Mannheim as the clipping layer)
8. **Click `Run`** to start the tool. The new clipped layer will be added to the map.
9. **Remove the original "POI Shopping" layer** and keep only the new clipped layer in the project.

### Rename Layers 

For better overview, let's rename the layers:

1. **Click on `More Options` (⋯)** next to the "Regiostar Raumtypisierung" layer 
2. **Select `Rename`** and enter "Mannheim"
3. **Repeat for the new clipped layer** and rename it to "Supermarkets"