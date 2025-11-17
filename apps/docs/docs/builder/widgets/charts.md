---
sidebar_position: 3
---

# Charts

Display your data in a visual format using different types of charts: **Categories**, **Histogram**, and **Pie chart**. Simply **drag and drop** widgets from the right sidebar to any panel on your dashboard. Customize each widget by clicking on it, which opens the **widget settings** in the right panel.

## Categories

The categories widget allows you to visualize the distribution of a categorical field from a selected layer by computing statistical analyses and generating **groups by the selected field.**

<div class="step">
  <div class="step-number">1</div>
  <div class="content">Select your <code>layer</code>. </div>
</div>

<div class="step">
  <div class="step-number">2</div>
  <div class="content">Choose the <code>statistic method</code> you want to apply. It can be <code>Count</code>, <code>Sum</code>, <code>Min</code>, <code>Max</code>, or add your own [<code>Expression</code>](/data/expressions.md).</div>
</div>

<div class="step">
  <div class="step-number">3</div>
  <div class="content">Choose the <code>field</code> onto which the statistics should be applied. <i>Sum, min, and max can only be applied to numeric fields.</i></div>
</div>

<div class="step">
  <div class="step-number">4</div>
  <div class="content">On <code>Group by field</code>, select the field you want your results to be grouped by.</div>
</div>

<div class="step">
  <div class="step-number">5</div>
  <div class="content">Enable or disable <code>Cross filter</code> to make this widget update depending on all other connected widgets on your dashboard.</div>
</div>

<div class="step">
  <div class="step-number">6</div>
  <div class="content">Enable or disable the option to <code>Filter viewport</code>,  which makes only the data within the current map view visible.</div>
</div>

<div class="step">
  <div class="step-number">7</div>
  <div class="content">Set the <code>number format</code> from the dropdown list. The <code>default number format</code> is dynamic based on the language of the interface. </div>
</div>

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/builder/builder_categories.gif').default} alt="recent datasets" style={{ maxHeight: "500px", maxWidth: "auto", objectFit: "cover"}}/>
</div> 

::::info
The value with the **highest number will jump to the top** of the chart.
::::

## Histogram

The histogram widget allows you to visualize the **distribution of a numeric field from a selected layer by `count`**.

<div class="step">
  <div class="step-number">1</div>
  <div class="content">Select your <code>layer</code>. </div>
</div>

<div class="step">
  <div class="step-number">2</div>
  <div class="content">Choose the <code>numeric field</code> which you want to visualize. The statistical method applied will be <code>count</code>.  </div>
</div>

<div class="step">
  <div class="step-number">3</div>
  <div class="content">Enable or disable <code>Cross filter</code> to make this widget update depending on all other connected widgets on your dashboard.</div>
</div>

<div class="step">
  <div class="step-number">4</div>
  <div class="content">Enable or disable the option to <code>Filter viewport</code>,  which makes only the data within the current map view visible.</div>
</div>

<div class="step">
  <div class="step-number">5</div>
  <div class="content">Set the <code>number format</code> from the dropdown list. The <code>default number format</code> is dynamic based on the language of the interface. </div>
</div>

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/builder/builder_histogram.gif').default} alt="recent datasets" style={{ maxHeight: "500px", maxWidth: "auto", objectFit: "cover"}}/>
</div> 

## Pie chart

Pie chart widget allows you to visualize the distribution of a **field** from a selected layer.

<div class="step">
  <div class="step-number">1</div>
  <div class="content">Select your <code>layer</code>. </div>
</div>

<div class="step">
  <div class="step-number">2</div>
  <div class="content">Choose the <code>statistic method</code> you want to apply. It can be <code>Count</code>, <code>Sum</code>, <code>Min</code>, <code>Max</code>, or add your own [<code>Expression</code>](/data/expressions.md).  </div>
</div>

<div class="step">
  <div class="step-number">3</div>
  <div class="content">Choose the <code>field</code> onto which the statistics should be applied. <i>Sum, min, and max can only be applied to numeric fields.</i></div>
</div>

<div class="step">
  <div class="step-number">4</div>
  <div class="content">Select the <code>field</code> you want your results to be <code>grouped by</code>.</div>
</div>

<div class="step">
  <div class="step-number">5</div>
  <div class="content">Enable or disable <code>Cross filter</code> to make this widget update depending on all other connected widgets on your dashboard.</div>
</div>

<div class="step">
  <div class="step-number">6</div>
  <div class="content">Enable or disable the option to <code>Filter viewport</code>,  which makes only the data within the current map view visible.</div>
</div>

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/builder/builder_pie_chart.gif').default} alt="recent datasets" style={{ maxHeight: "500px", maxWidth: "auto", objectFit: "cover"}}/>
</div> 

::::info
Results will be visualized in **percentage**.
::::

::::tip
Where **statistical methods can be applied**, *count, sum, min, max and [expression](/data/expressions.md)* are the available options. Check out our **[Expressions documentation](/data/expressions.md)** for more information.
::::