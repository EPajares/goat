---
sidebar_position: 5
---
import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';


# Legend

Legends help users understand the symbology and meaning of your map layers. GOAT automatically displays legends for all visible layers, but you can customize their appearance and add descriptive captions to make your maps more informative.

## How to manage layer legends

<div class="step">
  <div class="step-number">1</div>
  <div class="content">Select your layer and navigate to <strong>Layer design</strong> and find the <strong>Legend</strong> section</div>
</div>

<div class="step">
  <div class="step-number">2</div>
  <div class="content">Toggle the <strong>Show</strong> checkbox to enable or disable the legend display</div>
</div>

<div class="step">
  <div class="step-number">3</div>
  <div class="content">You can add a <strong>Caption</strong> field explaining the layer's content</div>
</div>

<div class="step">
  <div class="step-number">4</div>
  <div class="content">Click <strong>Save</strong> to apply your changes. The caption will appear below the layer name in the legend list</div>
</div>

<p></p>
<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
  <img src={require('/img/map/styling/legend.png').default} alt="Legend configuration with caption settings" style={{ maxHeight: "auto", maxWidth: "auto", objectFit: "cover"}}/>
</div>

## Best practices

- **Use clear, descriptive captions** that explain what the layer represents
- **Keep captions concise** but informative
- **Disable legends** for layers that don't need visual explanation (e.g., reference layers)
- **Review legend visibility** to avoid cluttering the map interface
