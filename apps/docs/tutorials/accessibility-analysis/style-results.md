---
sidebar_position: 5
---

# Style Your Results

Raw analysis results are powerful, but well-styled maps tell a compelling story. Let's make your catchment areas look professional!

## Watch the Styling Tutorial

<div style={{ display: 'flex', justifyContent: 'center', marginBottom: '2rem' }}>
<iframe width="100%" height="500" src="https://www.youtube.com/embed/R7nefHqPnBk?si=KWndAFlcb2uuC7CZ" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>
</div>

## Styling Options in GOAT

### 1. Access Layer Styling

Right-click on your catchment layer in the Layer Panel and select **Style** or click the paint brush icon.

### 2. Choose a Color Palette

GOAT offers several color palette types:

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/map/styling/sequential_palette.png').default} alt="Sequential Palette" style={{ maxHeight: "100px", maxWidth: "100%", objectFit: "cover", borderRadius: "8px"}}/>
  <p><em>Sequential palette - great for time-based data</em></p>
</div>

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/map/styling/diverging_palette.png').default} alt="Diverging Palette" style={{ maxHeight: "100px", maxWidth: "100%", objectFit: "cover", borderRadius: "8px"}}/>
  <p><em>Diverging palette - shows deviation from a midpoint</em></p>
</div>

### 3. Apply Attribute-Based Styling

Style your catchments based on travel time values:

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/map/styling/attribute-based-fill-color.gif').default} alt="Attribute Based Fill" style={{ maxHeight: "400px", maxWidth: "100%", objectFit: "cover", borderRadius: "8px", boxShadow: "0 4px 12px rgba(0,0,0,0.15)"}}/>
  <p><em>Applying color based on travel time attribute</em></p>
</div>

### Recommended Settings for Catchments

| Setting      | Recommendation                   |
| ------------ | -------------------------------- |
| Fill Color   | Sequential green or blue palette |
| Fill Opacity | 50-70% (to see underlying map)   |
| Stroke Color | Darker shade of fill             |
| Stroke Width | 1-2 pixels                       |

### 4. Adjust Transparency

Lower the opacity to see the basemap underneath:

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/map/styling/color_palettes.gif').default} alt="Color Palette Selection" style={{ maxHeight: "400px", maxWidth: "100%", objectFit: "cover", borderRadius: "8px", boxShadow: "0 4px 12px rgba(0,0,0,0.15)"}}/>
  <p><em>Selecting and customizing color palettes</em></p>
</div>

### 5. Add Labels

Add informative labels to your catchments:

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/map/styling/label_by.gif').default} alt="Adding Labels" style={{ maxHeight: "400px", maxWidth: "100%", objectFit: "cover", borderRadius: "8px", boxShadow: "0 4px 12px rgba(0,0,0,0.15)"}}/>
  <p><em>Adding labels to show travel time values</em></p>
</div>

## Color Scheme Recommendations

For accessibility analysis, consider these combinations:

| Analysis Type      | Recommended Palette          |
| ------------------ | ---------------------------- |
| Walking catchments | Greens (nature, pedestrian)  |
| Cycling catchments | Blues (cool, active)         |
| Transit catchments | Purples (urban, transit)     |
| Car catchments     | Oranges/Reds (caution, auto) |

:::tip Accessibility Note
Avoid red-green combinations as they're difficult for colorblind users. Use blue-orange or purple-yellow alternatives.
:::

## Save Your Style

Once you're happy with the styling:

1. Click **Save Style** in the style panel
2. Your style will be saved with the layer
3. You can also save it as a default for future use

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/map/styling/save_default.png').default} alt="Save Default Style" style={{ maxHeight: "300px", maxWidth: "100%", objectFit: "cover", borderRadius: "8px", boxShadow: "0 4px 12px rgba(0,0,0,0.15)"}}/>
  <p><em>Save your style for future use</em></p>
</div>

## Next Step

Your map looks fantastic! Let's [export and share your work](./export-share).

---

**Progress:** 4 of 5 steps completed
