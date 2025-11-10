---
sidebar_position: 4
---
import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';
import thematicIcon from "/img/toolbox/data_management/join/toolbox.webp";
import MathJax from 'react-mathjax';

# Heatmap - Gravity

The Heatmap - Gravity indicator **produces a color-coded map to visualize the accessibility of points, such as POIs from surrounding areas**.

<div style={{ display: 'flex', justifyContent: 'center' }}>
<iframe width="674" height="378" src="https://www.youtube.com/embed/yteOnb6N7hA?si=SYStNhRCpZidqY0p" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>
</div>

## 1. Explanation

The heatmap Gravity displays a **color-coded hexagonal grid showing the accessibility of destinations (opportunities) based on travel time and destination attractiveness**. Accessibility is calculated using real-world transport networks and a gravity-based formula that reflects how people’s willingness to travel decreases with distance.

You can specify the **routing type**, **opportunity layer**, **travel time limit**, and adjust **sensitivity** and **destination potential** to fine-tune how accessibility is calculated.

The **Opportunity layer** contains point-based destination data (such as POIs, transit stops, schools, amenities, or custom points). You can select multiple opportunity layers, which will be combined into a single unified heatmap.

The **Sensitivity** controls how quickly accessibility decreases with increasing travel time, while the **Destination potential** lets you give more weight to destinations with higher capacity or quality (e.g., a larger supermarket or a bus stop with more departures). Together with the chosen **Impedance function**, these settings define how accessibility is calculated.

Using **Destination potential** helps prioritize certain opportunities over others. For example, a larger but farther supermarket can be valued more than a smaller nearby one. This allows you to include qualitative information—such as size, frequency, or service level—when computing accessibility, resulting in a more realistic heatmap.

Influenced by all these properties, the accessibility of a point can model complex real-world human behavior and is a powerful measure for transport and accessibility planning.

**Key difference:** Unlike the *Closest-Average* heatmap, which measures travel effort, the *Gravity-based Heatmap* measures **attractiveness** — showing how accessible and appealing destinations are when both distance and quality are considered.

import MapViewer from '@site/src/components/MapViewer';

:::info 

Heatmaps are available in certain regions. Upon selecting a `Routing type`, a **geofence** will be displayed on the map to highlight supported regions.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <MapViewer
      geojsonUrls={[
        "https://assets.plan4better.de/other/geofence/geofence_heatmap.geojson"
      ]}
      styleOptions={{
        fillColor: "#808080",
        outlineColor: "#808080",
        fillOpacity: 0.8
      }}
      legendItems={[
        { label: "Coverage for Gravity-based Heatmaps", color: "#ffffff" }
      ]}
  />
</div> 


If you would like to perform analyses beyond this geofence, feel free to [contact us](https://plan4better.de/en/contact/ "Contact us"). We would be happy to discuss further options.

:::

## 2. Example use cases

 - Which neighborhoods or areas have limited access to public amenities, such as parks, recreational facilities, or cultural institutions, and may require targeted interventions to improve accessibility?

 - Are there areas with high potential for transit-oriented development or opportunities for improving non-motorized transportation infrastructure, such as bike lanes or pedestrian-friendly streets?

 - What is the impact of a new amenity on local accessibility?

 - Is there potential to expand the availability of services such as bike sharing or car sharing stations?

## 3. How to use the indicator?

<div class="step">
  <div class="step-number">1</div>
  <div class="content">Click on <code>Toolbox</code> <img src={thematicIcon} alt="toolbox" style={{width: "25px"}}/>. </div>
</div>

<div class="step">
  <div class="step-number">2</div>
  <div class="content">Under the <code>Accessibility Indicators</code> menu, click on <code>Heatmap Gravity</code>.</div>
</div>

### Routing

<div class="step">
  <div class="step-number">3</div>
  <div class="content">Pick the <code>Routing Type</code> you would like to use for the heatmap.</div>
</div>

<Tabs>

<TabItem value="walk" label="Walk" default className="tabItemBox">

#### Walk

Considers all paths accessible by foot. For heatmaps, a walking speed of 5 km/h is assumed.

</TabItem>
  
<TabItem value="cycling" label="Bicycle" className="tabItemBox">

#### Bicycle

Considers all paths accessible by bicycle. This routing mode takes into account the surface, smoothness and slope of streets while computing accessibility. For heatmaps, a cycling speed of 15 km/h is assumed.

</TabItem>

<TabItem value="pedelec" label="Pedelec" className="tabItemBox">

#### Pedelec

Considers all paths accessible by pedelec. This routing mode takes into account the surface and smoothness of streets while computing accessibility. For heatmaps, a pedelec speed of 23 km/h is assumed.

</TabItem>

<TabItem value="car" label="Car" className="tabItemBox">

#### Car

Considers all paths accessible by car. This routing mode takes into account speed limits and one-way access restrictions while computing accessibility.

</TabItem>

</Tabs>

### Configuration

<div class="step">
  <div class="step-number">4</div>
  <div class="content">Pick the <code>Impedance Function</code> you would like to use for the heatmap.</div>
</div>

<Tabs>

<TabItem value="gaussian" label="Gaussian" default className="tabItemBox">

#### Gaussian

This function calculates accessibilities based on a Gaussian curve, which is influenced by the `sensitivity` and `destination_potential` you define. For a more in-depth understanding, refer to the [Technical details](./gravity#4-technical-details) section.

</TabItem>
  
<TabItem value="linear" label="Linear" default className="tabItemBox">

#### Linear

This function maintains a direct correlation between travel time and accessibility, which is modulated by the `destination_potential` you specify. For a more in-depth understanding, refer to the [Technical details](./gravity#4-technical-details) section.

:::info Note
This feature is currently under development. 🧑🏻‍💻
:::

</TabItem>

<TabItem value="exponential" label="Exponential" default className="tabItemBox">

#### Exponential

This function calculates accessibilities based on an exponential curve, which is influenced by the `sensitivity` and `destination_potential` you define. For a more in-depth understanding, refer to the [Technical details](./gravity#4-technical-details) section.

:::info Note
This feature is currently under development. 🧑🏻‍💻
:::

</TabItem>

<TabItem value="power" label="Power" default className="tabItemBox">

#### Power

This function calculates accessibilities based on a power curve, which is influenced by the `sensitivity` and `destination_potential` you define. For a more in-depth understanding, refer to the [Technical details](./gravity#4-technical-details) section.

:::info Note
This feature is currently under development. 🧑🏻‍💻
:::

</TabItem>

</Tabs>

### Opportunities

<div class="step">
  <div class="step-number">5</div>
  <div class="content">Select your <code>Opportunity Layer</code> from the drop-down menu. This can be any previously created layer containing point-based data.</div>
</div>

<div class="step">
  <div class="step-number">6</div>
  <div class="content">Choose a <code>Travel Time Limit</code> for your heatmap. This will be used in the context of your previously selected <i>Routing Type</i>.</div>
</div>

:::tip Hint

Need help choosing a suitable travel time limit for various common amenities? The ["Standort-Werkzeug"](https://www.chemnitz.de/chemnitz/media/unsere-stadt/verkehr/verkehrsplanung/vep2040_standortwerkzeug.pdf) of the City of Chemnitz can provide helpful guidance.

:::

<div class="step">
  <div class="step-number">7</div>
  <div class="content">If required, choose a <code>Destination Potential Field</code>. This must be a numeric field from your <i>Opportunity Layer</i> which will be used as a coefficient by the accessibility function.</div>
</div>


<div class="step">
  <div class="step-number">8</div>
  <div class="content">Specify a <code>Sensitivity</code> value. This must be numeric and will be used by the heatmap function to determine how accessibility changes with increasing travel time.</div>
</div>


:::tip Hint

**How to choose the sensitivity value?**

The best **sensitivity (β)** value depends on your analysis — there’s no single correct number. It defines **how quickly accessibility decreases as travel time increases**.

- **Low β (urban scale):** Use a lower sensitivity for city-level analyses. This makes accessibility drop faster with distance, which fits urban contexts where many destinations are nearby and people usually choose the closest one.
- **High β (regional scale):** Use a higher sensitivity for regional or rural analyses. This makes accessibility decrease more slowly, which reflects that people are willing to travel longer distances when options are fewer.

For a visual explanation of how sensitivity affects the calculation, see the **[Calculation](#calculation)** section.

:::

<div class="step">
  <div class="step-number">9</div>
  <div class="content">Click <code>Run</code> to start the calculation of the heatmap.</div>
</div>

### Results

Once the calculation is complete, a result layer will be added to the map. This <i>Heatmap Gravity</i> layer will contain your color-coded heatmap. Clicking on any of the heatmap's hexagonal cells will reveal the computed accessibility value for this cell.

![Heatmap Gravity-Based Calculation Result in GOAT](/img/toolbox/accessibility_indicators/heatmaps/gravity_based/heatmap_gravity_result.png "Heatmap Gravity-Based Calculation Result in GOAT")


:::tip Tip

Want to create visually compelling maps that tell a clear story? Learn how to customize colors, legends, and styling in our [Styling section](../../map/layer_style/styling).

:::

### Example of calculation

The example below shows how the changes in the opportunity settings can affect the gravity heatmap. Its destination potential is based on the total number of hourly public transport departures from a stop.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
<img src={require('/img/toolbox/accessibility_indicators/heatmaps/gravity_based/gravity_calculation_comparison.png').default} alt="gravity-no-destination-potential" style={{ maxHeight: "500px", maxWidth: "auto"}}/>
</div>

<p></p>

The map on the back is calculated without destination potential. The second map used the same settings, but added destination potential based on the total number of departures. This altered the accessibility values of each hexagon and they returned in a wider range, because the highest value increased even more. **Higher accessibility values are more concentrated around the stops that have larger trip count (red points).**

## 4. Technical details

### Calculation
The accessibility value for each hexagonal cell is calculated using a **gravity-based formula**, which estimates how strongly destinations influence each location.

**Accessibility formula:**

<MathJax.Provider>
  <div style={{ marginTop: '20px', fontSize: '24px'  }}>
    <MathJax.Node formula={"A_i=\\sum_j O_jf(t_{i,j})"} />
  </div>
</MathJax.Provider>

In simple terms, the accessibility (**A**) of a cell (**i**) depends on:
- the **number or importance of destinations** (**O**) nearby, and  
- the **travel time** (**tᵢⱼ**) needed to reach them.

The function **f(tᵢⱼ)** reduces the influence of destinations that are farther away — this is called the **impedance function**. In GOAT you can choose between different impedance types: `gaussian`, `linear`, `exponential`, or `power`.

and adjust how strongly distance affects accessibility using the **sensitivity (β)** parameter. If **destination potential** is included, it further increases the weight of destinations with higher capacity or quality (e.g., larger stores or frequent transit stops).

#### GOAT uses the following formulas for its impedance functions:

*Modified Gaussian, (Kwan,1998):*

<MathJax.Provider>
  <div style={{ marginTop: '20px', fontSize: '24px'  }}>
    <MathJax.Node formula={"f(t_{i,j})=\\exp^{(-t_{i,j}^2/\\beta)}"} />
  </div>
</MathJax.Provider>

:::tip Pro tip

As studies have shown, the relationship between travel time and accessibility is often non-linear. This means that people may be willing to travel a short distance to reach an amenity, but as the distance increases, their willingness to travel rapidly decreases (often disproportionately).

Leveraging the *sensitivity* you define, the Gaussian function allows you to model this aspect of real-world behaviour more accurately.

:::


*Cumulative Opportunities Linear, (Kwan,1998):*
<div>
<MathJax.Provider>
  <div style={{ marginTop: '20px', fontSize: '24px' }}>
    <MathJax.Node formula={`
      f(t_{ij}) =
      \\begin{cases}
        1 - \\frac{t_{ij}}{\\bar{t}} & \\text{for } t_{ij} \\leq \\bar{t} \\\\
        0 & \\text{otherwise}
      \\end{cases}
    `} />
  </div>
</MathJax.Provider>
  </div>    

*Negative Exponential, (Kwan,1998):*


<div><MathJax.Provider>
  <div style={{ marginTop: '20px', fontSize: '24px'  }}>
    <MathJax.Node formula={"f(t_{i,j})=\\exp^{(-\\beta t_{i,j})}"} />
  </div>
</MathJax.Provider>
    </div>  

*Inverse Power, (Kwan,1998) (`power` in GOAT):*

<div>
<MathJax.Provider>
  <div style={{ marginTop: '20px', fontSize: '24px' }}>
    <MathJax.Node formula={`f(t_{ij}) = \\begin{cases}
      \\ 1 & \\text{for } t_{ij} \\leq 1 \\\\
      t_{i,j}^{-\\beta} & \\text{otherwise}
    \\end{cases}`} />
  </div>
</MathJax.Provider>
</div>  

Travel times are measured in minutes. For a maximum travel time of 30 minutes, destinations that are farther than 30 minutes are considered non-accessible and therefore not considered in the calculation of the accessibility. The *sensitivity* parameter determines how accessibility changes with increasing travel time. As the *sensitivity* parameter is decisive when measuring accessibility, GOAT allows you to adjust this. The graph shows how the willingness to walk decreases with increasing travel time based on the selected impedance function and sensitivity value (β).

import ImpedanceFunction from '@site/src/components/ImpedanceFunction';

<div style={{ display: 'block', textAlign: 'center'}}>
  <div style={{ maxHeight: "auto", maxWidth: "auto"}}>
    <ImpedanceFunction />
   </div> 
</div>

### Classification
In order to classify the accessibility levels that were computed for each grid cell (for color-coded visualization), a classification based on **8 quantile group is used by default**. That means, each color covers 12,5 % of the grid cells. The area outside of the computed layer has no access within the defined travel time.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
<img src={require('/img/toolbox/accessibility_indicators/heatmaps/gravity_based/gravity_default_classification.png').default} alt="gravity-default-classification" style={{ maxHeight: "250px", maxWidth: "auto"}}/>
</div>

However, various other classification methods may be used instead. Read more in the **[Data Classification Methods](../../map/layer_style/attribute_based_styling#data-classification-methods)** section of the *Attribute-based Styling* page.

### Visualization 

Heatmaps in GOAT utilize **[Uber's H3 grid-based](../further_reading/glossary#h3-grid)** solution for efficient computation and eacessibisy-to-understand visualization. Behind the scenes, a pre-computed travel time matrix for each *routing type* utilizes this solution and is queried and further processed in real-time to compute accessibility and produce a final heatmap.

The resolution and dimensions of the hexagonal grid used depend on the selected *routing type*:

<Tabs>

<TabItem value="walk" label="Walk" default className="tabItemBox">

#### Walk
- Resolution: 10
- Average hexagon area: 11285.6 m²
- Average hexagon edge length: 65.9 m

</TabItem>
  
<TabItem value="bicycle" label="Bicycle" className="tabItemBox">

#### Bicycle
- Resolution: 9
- Average hexagon area: 78999.4 m²
- Average hexagon edge length: 174.4 m

</TabItem>

<TabItem value="pedelec" label="Pedelec" className="tabItemBox">

#### Pedelec
- Resolution: 9
- Average hexagon area: 78999.4 m²
- Average hexagon edge length: 174.4 m

</TabItem>

<TabItem value="car" label="Car" className="tabItemBox">

#### Car
- Resolution: 8
- Average hexagon area: 552995.7 m²
- Average hexagon edge length: 461.4 m

</TabItem>

</Tabs>

:::tip Hint

For further insights into the Routing algorithm, visit [Routing](../../category/routing). In addition, you can check this [Publication](https://doi.org/10.1016/j.jtrangeo.2021.103080).
:::

## 5. References

Kwan, Mei-Po. 1998. “Space-Time and Integral Measures of Individual Accessibility: A Comparative Analysis Using a Point-Based Framework.” Geographical Analysis 30 (3): 191–216. [https://doi.org/10.1111/j.1538-4632.1998.tb00396.x](https://doi.org/10.1111/j.1538-4632.1998.tb00396.x).

Vale, D.S., and M. Pereira. 2017. “The Influence of the Impedance Function on Gravity-Based Pedestrian Accessibility Measures: A Comparative Analysis.” Environment and Planning B: Urban Analytics and City Science 44 (4): 740–63.  [https://doi.org/10.1177%2F0265813516641685](https://doi.org/10.1177%2F0265813516641685).

Higgins, Christopher D. 2019. “Accessibility Toolbox for R and ArcGIS.” Transport Findings, May.  [https://doi.org/10.32866/8416](https://doi.org/10.32866/8416).
