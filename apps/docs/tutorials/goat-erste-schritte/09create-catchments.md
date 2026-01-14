---
slug: /tutorials/goat-erste-schritte/create-catchment-areas
sidebar_position: 10
sidebar_label: ✏️ 10. Create Catchment Areas
---

# Create Catchment Areas

1. **Click on `Toolbox`** to the right of the left panel
2. **Under "Accessibility Indicators"** click on `Catchment Area`
3. **Select `Walking`** as routing type for the catchment area calculation
4. **Choose catchment area calculation based on `Time`**
5. **Configure the parameters:**
   - **Travel Time Limit:** 15 (minutes)
   - **Travel Speed:** 5km/h (keep default)
   - **Number of Breaks:** 3
6. **Select `Select from Layer`** as starting point method
7. **Choose the "Supermarkets" layer** as point layer
8. **Click `Run`** 

<div style={{ display: 'flex', justifyContent: 'center' }}>
<img src={require('/img/tutorials/01_erste_schritte/einzugsgebiet.gif').default} alt="Catchment Area Calculation Result in GOAT" style={{ maxHeight: "100%", maxWidth: "auto"}}/>
</div>

## Interpret Results

Once the calculation is complete, a new "Catchment Area" layer will be added to the map. You'll see colored polygons around each supermarket, and the different colors show different travel time zones.

**💡 Click on any catchment area polygon** - the `travel_cost` attribute shows the travel time in minutes based on our calculation settings.

Look at your map and note:

🔍 **Well-served areas:** Areas with strong overlap of catchment areas  
🔍 **Service gaps:** Areas in Mannheim not covered by any catchment area  
🔍 **Edge areas:** Neighborhoods at the edge of the 15-minute zones  

:::success Congratulations!
You have successfully created your first accessibility analysis in GOAT! The catchment areas now visually show which parts of Mannheim are well served by supermarkets.
:::