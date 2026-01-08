---
sidebar_position: 5
---

# Advanced Styling

Transform your heatmap into a publication-ready visualization with advanced styling techniques.

## Styling for Impact

### Watch: Attribute-Based Styling

<div style={{ display: 'flex', justifyContent: 'center', marginBottom: '2rem' }}>
<iframe width="100%" height="500" src="https://www.youtube.com/embed/cLIPMCOu4FQ?si=aydSJN_Pf0fusO9x" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>
</div>

## Color Classification Methods

Choose the right classification for your story:

### Quantile
Divides data into equal-count groups.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/map/styling/quantile.png').default} alt="Quantile Classification" style={{ maxHeight: "200px", maxWidth: "100%", objectFit: "cover", borderRadius: "8px"}}/>
</div>

**Best for:** Showing relative ranking (top 20%, bottom 20%, etc.)

### Equal Interval
Divides range into equal-width groups.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/map/styling/equal_interval.png').default} alt="Equal Interval Classification" style={{ maxHeight: "200px", maxWidth: "100%", objectFit: "cover", borderRadius: "8px"}}/>
</div>

**Best for:** Showing actual value differences

### Standard Deviation
Groups based on distance from mean.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/map/styling/standard_deviation.png').default} alt="Standard Deviation Classification" style={{ maxHeight: "200px", maxWidth: "100%", objectFit: "cover", borderRadius: "8px"}}/>
</div>

**Best for:** Identifying outliers and normal ranges

## Recommended Color Palettes

### For Accessibility Heatmaps

**Sequential (Single-Hue):**

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/map/styling/singlehue_palette.png').default} alt="Single Hue Palette" style={{ maxHeight: "80px", maxWidth: "100%", objectFit: "cover", borderRadius: "8px"}}/>
</div>

- Light = Low accessibility
- Dark = High accessibility
- Clean, easy to read

**Diverging (Two-Hue):**

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/map/styling/diverging_palette.png').default} alt="Diverging Palette" style={{ maxHeight: "80px", maxWidth: "100%", objectFit: "cover", borderRadius: "8px"}}/>
</div>

- Two contrasting colors
- Neutral middle value
- Good for above/below average

## Fine-Tuning Your Style

### Adjusting Transparency

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/map/styling/attribute-based-fill-color.gif').default} alt="Fill Color Adjustment" style={{ maxHeight: "400px", maxWidth: "100%", objectFit: "cover", borderRadius: "8px", boxShadow: "0 4px 12px rgba(0,0,0,0.15)"}}/>
</div>

Set opacity to 60-80% so the basemap context is visible.

### Stroke Settings

For hexagonal grids:
- **Stroke Width:** 0 or 0.5px (thin borders)
- **Stroke Color:** Match fill or use subtle gray
- Avoid thick borders that distract from patterns

### Interactive Popups

Configure popups to show:
- Accessibility score
- Travel time statistics
- Opportunity count
- Comparison to average

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/map/styling/popup.png').default} alt="Popup Configuration" style={{ maxHeight: "300px", maxWidth: "100%", objectFit: "cover", borderRadius: "8px", boxShadow: "0 4px 12px rgba(0,0,0,0.15)"}}/>
</div>

## Publication-Ready Export Tips

1. **Choose a clean basemap** - Grayscale or minimal style
2. **Add a clear legend** - Include units and classification method
3. **Use consistent color schemes** - Match organizational branding
4. **Include scale and north arrow** - For print materials
5. **Test at print size** - Colors may look different on paper

## 🎉 Tutorial Complete!

Congratulations! You've mastered heatmap accessibility analysis in GOAT.

### What You Learned

- ✅ How gravity models calculate accessibility
- ✅ Configuring heatmap analysis parameters
- ✅ Interpreting spatial accessibility patterns
- ✅ Creating professional visualizations

### Continue Learning

- **[Tutorial 3: Scenario Planning](../scenario-planning/intro)** - Model future scenarios and compare alternatives

---

**🏆 You're now a heatmap pro!**
