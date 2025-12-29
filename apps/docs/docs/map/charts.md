---
sidebar_position: 5
---

# Charts

The Charts feature allows you to **quickly visualize aggregated data**, result  from the tools **aggregate polygon** and **aggregate point**, without complex configuration showing the relationship between your source and target layers.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/map/charts/charts.gif').default} alt="Filter tool in GOAT" style={{ maxHeight: "auto", maxWidth: "80%", objectFit: "cover"}}/>
</div> 

## How to use charts

<div class="step">
  <div class="step-number">1</div>
  <div class="content">Locate your aggregated layer in the <code>Layers</code> panel and click on the <img src={require('/img/icons/3dots.png').default} alt="More options" style={{ maxHeight: "20px", maxWidth: "20px", verticalAlign: "middle", marginRight: "4px" }}/> <b>more options</b> menu next to the layer name.</div>
</div>

<div class="step">
  <div class="step-number">2</div>
  <div class="content">Select <code>View Chart</code> from the dropdown menu. A popup window will appear displaying your data visualization.</div>
</div>

<div class="step">
  <div class="step-number">3</div>
  <div class="content">Choose your preferred <code>Chart Type</code> from the available options:
    <ul>
      <li><b>Vertical Bar Chart</b>: Classic column chart format</li>
      <li><b>Horizontal Bar Chart</b>: Horizontal bars for better label visibility</li>
      <li><b>Line Chart</b>: Connected points showing data trends</li>
    </ul>
  </div>
</div>

<div class="step">
  <div class="step-number">4</div>
  <div class="content">Toggle the <code>Cumulative Sum</code> option if you want to display running totals instead of individual values.</div>
</div>

<div class="step">
  <div class="step-number">5</div>
  <div class="content">Hover over chart elements to view precise values and additional details for each data point.</div>
</div>

:::info Note

Chart axes are automatically determined based on your aggregation setup and cannot be manually configured. If you don't see the chart option, ensure your layer contains aggregated data from spatial analysis tools.

:::