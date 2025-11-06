---
sidebar_position: 4
---
import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';
import thematicIcon from "/img/toolbox/data_management/join/toolbox.webp";
import MathJax from 'react-mathjax';

# Heatmap - Gravity

A color-coded map to visualize the accessibility of points (such as [POI](../../further_reading/glossary#point-of-interest-poi "What is a POI?")) from surrounding areas.

<iframe width="100%" height="500" src="https://www.youtube.com/embed/ghXzZUCDsJ4?si=mUnoHHQZsRS1C9kf" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>


## 1. Explanation

Visualized as a color-coded hexagonal grid, the heatmap takes into account real-world transport and street networks to compute accessibility. After specifying a *routing type* (Walk, Bicycle, etc.), *opportunity layer* and *travel time limit*, the result will display a color-coded hexagonal grid for all areas accessible under these conditions. The color scale refers to local accessibility.

:::info INFO

An `Opportunity layer` contains [geographic point](../../data/data_types "What are geographic points?") data. Select one or more such layers containing your destination points (opportunities) as input to the heatmap.

:::

Unique to the gravity-based heatmap, customizable properties such as *sensitivity*, the *impedance function* and *destination potential* give you minute control over the method used and metadata taken into account while computing the accessibility value for an area. Influenced by these properties, the accessibility of a point can model complex real-world human behavior and is a powerful measure for transport and accessibility planning.

:::tip Pro tip

Described shortly, accessibility heatmaps are a visualization representing *access* from various unspecified origins, to one or more specified destinations. This is in contrast to catchment areas which represent *egress* from one or more specified origins to various unspecified destinations.

:::

![Gravity-based Heatmap in GOAT](/img/toolbox/accessibility_indicators/heatmaps/gravity_based/heatmap_gravity_based.webp "Gravity-based Heatmap in GOAT")

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

 - How does the accessibility in various neighborhoods compare when taking into account the qualitative aspects of amenities (such as frequency of service at bus stops, size of supermarkets, capacity of schools, etc)?

 - What is the real-world accessibility of public transport stations when travel times to these stations impact their accessibility in a non-linear way?



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

:::tip Hint

For further insights into the Routing algorithm, visit [Routing/Walk](../../routing/walking).

:::

</TabItem>
  
<TabItem value="cycling" label="Bicycle" className="tabItemBox">

#### Bicycle

Considers all paths accessible by bicycle. This routing mode takes into account the surface, smoothness and slope of streets while computing accessibility. For heatmaps, a cycling speed of 15 km/h is assumed.

:::tip Hint

For further insights into the Routing algorithm, visit [Routing/Bicycle](../../routing/bicycle). In addition, you can check this [Publication](https://doi.org/10.1016/j.jtrangeo.2021.103080).

:::

</TabItem>

<TabItem value="pedelec" label="Pedelec" className="tabItemBox">

#### Pedelec

Considers all paths accessible by pedelec. This routing mode takes into account the surface and smoothness of streets while computing accessibility. For heatmaps, a pedelec speed of 23 km/h is assumed.

:::tip Hint

For further insights into the Routing algorithm, visit [Routing/Bicycle](../../routing/bicycle). In addition, you can check this [Publication](https://doi.org/10.1016/j.jtrangeo.2021.103080).

:::

</TabItem>

<TabItem value="car" label="Car" className="tabItemBox">

#### Car

Considers all paths accessible by car. This routing mode takes into account speed limits and one-way access restrictions while computing accessibility.

:::tip Hint

For further insights into the Routing algorithm, visit [Routing/Car](../../routing/car).

:::

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

:::tip Pro tip

As studies have shown, the relationship between travel time and accessibility is often non-linear. This means that people may be willing to travel a short distance to reach an amenity, but as the distance increases, their willingness to travel rapidly decreases (often disproportionately).

Leveraging the *sensitivity* you define, the Gaussian function allows you to model this aspect of real-world behaviour more accurately.

:::

:::note Hint

**How to choose the sensitivity value?**

Selecting the best fitting sensitivity always *depends on the context of the analysis*, and there are no strict rules.

- **Low β:** A good strating point could be to use lower sensitivity on **urban scale analyses**, beacause it results in sharper accesssibility value drop with increasing travel time. In urban areas there are more opportunities available, and *people are more likely to choose the closest one*.
- **High β:** In contrast, higher sensitivity could be used in regional **scale analyses**, where opportunities are more sparse and *people are more likely to travel further* to reach them.

See the **[Calculation](#calculation)** section for a detailed visual explanations on the formula.

:::

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

Opportunities are essentially point-based data (such as [POI](../../further_reading/glossary#point-of-interest-poi "What is a POI?")) for which you would like to compute a heatmap. These are the "destinations" (such as transit stations, schools, other amenities, or your own custom point-based data) while surrounding areas are "origins" for which an accessibility value will be computed and visualized.

Additionally, you may create more opportunities via the `+ Add Opportunity` button at the bottom of the drawer. All opportunity layers will be combined to produce a unified heatmap.

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

:::tip Pro tip

**Destination potential** is a useful way to prioritize certain opportunities over others. For example, if there are two supermarkets and one is nearer than the other, it would typically receive a higher accessibility score due to its proximity. However, if the supermarket farther away is larger, you may want to give it a higher level of importance. *Destination potential* allows you to use an additional property (such as the size of supermarkets) to assign opportunities a "potential" and employ qualitative information while computing accessibility.

The example below shows how the destination potential can affect the gravity heatmap. Its destination potential is based on the total number of hourly public transport departures from a stop. It will result in a different accessibility distribution, because the area around point with a higher destination potential will be favored in the computation.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
<img src={require('/img/toolbox/accessibility_indicators/heatmaps/gravity_based/gravity_without_destination_potential.png').default} alt="gravity-no-destination-potential" style={{ maxHeight: "500px", maxWidth: "auto"}}/>
</div>

*The first map is calculated without destination potential.*

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
<img src={require('/img/toolbox/accessibility_indicators/heatmaps/gravity_based/gravity_with_destination_potential.png').default} alt="gravity-with-destination-potential" style={{ maxHeight: "500px", maxWidth: "auto"}}/>
</div>

*The second map used the same settings, but added destination potential based on the total number of departures. This altered the accessibility values of each hexagon and they returned in a wider range, because the highest value increased even more. Higher accessibility values are more concentrated around the stops that have larger trip count (red points).* 

:::

<div class="step">
  <div class="step-number">8</div>
  <div class="content">Specify a <code>Sensitivity</code> value. This must be numeric and will be used by the heatmap function to determine how accessibility changes with increasing travel time.</div>
</div>


<div class="step">
  <div class="step-number">9</div>
  <div class="content">Click <code>Run</code> to start the calculation of the heatmap.</div>
</div>

:::tip Hint

Depending on your configuration, the calculation might take a few minutes. The [status bar](../../workspace/home#status-bar) displays current progress.

:::

### Results

<div class="step">
  <div class="step-number">10</div>
  <div class="content">Once the calculation is complete, a result layer will be added to the map. This <i>Heatmap Gravity</i> layer will contain your color-coded heatmap.<p></p> Clicking on any of the heatmap's hexagonal cells will reveal the computed accessibility value for this cell.</div>
</div>


![Heatmap Gravity-Based Calculation Result in GOAT](/img/toolbox/accessibility_indicators/heatmaps/gravity_based/heatmap_gravity_result.png "Heatmap Gravity-Based Calculation Result in GOAT")


:::tip Tip

Want to style your heatmaps and create nice-looking maps? See [Styling](../../map/layer_style/styling).

:::

## 4. Technical details

### Calculation
The accessibility value of each hexagonal cell within a heatmap is calculated with the help of gravity-based measures and can be operationalized as:

*Accessibility Formula:*

<MathJax.Provider>
  <div style={{ marginTop: '20px', fontSize: '24px'  }}>
    <MathJax.Node formula={"A_i=\\sum_j O_jf(t_{i,j})"} />
  </div>
</MathJax.Provider>


where the accessibility **A** of origin **i** is the sum of all opportunities **O** available at destinations **j** weighted by some function of the travel time **tij** between **i** and **j**. The function **f(tij)** is the impedance function, which can be `gaussian`, `linear`, `exponential`, or `power`. The *sensitivity* parameter **β** and the *destination potential* are used to adjust the accessibility value.

#### GOAT uses the following formulas for its impedance functions:

*Modified Gaussian, (Kwan,1998):*

<MathJax.Provider>
  <div style={{ marginTop: '20px', fontSize: '24px'  }}>
    <MathJax.Node formula={"f(t_{i,j})=\\exp^{(-t_{i,j}^2/\\beta)}"} />
  </div>
</MathJax.Provider>

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

Travel times are measured in minutes. For a maximum travel time of 30 minutes, destinations that are farther than 30 minutes are considered non-accessible and therefore not considered in the calculation of the accessibility.
The *sensitivity* parameter determines how accessibility changes with increasing travel time. As the *sensitivity* parameter is decisive when measuring accessibility, GOAT allows you to adjust this The graph shows how the willingness to walk decreases with increasing travel time based on the selected impedance function and sensitivity value (β).

import ImpedanceFunction from '@site/src/components/ImpedanceFunction';

<div style={{ display: 'block', textAlign: 'center'}}>
  <div style={{ maxHeight: "auto", maxWidth: "auto"}}>
    <ImpedanceFunction />
   </div> 
</div>

Similarly, the *destination potential* can be changed. Thus, for example, one POI type (e.g. hypermarkets) can be assigned a higher accessibility effect than other POI types (e.g. discount supermarkets). In the [Opportunities](#opportunities) section, at **step 7**,  we cover the *destination potential* in detail.

:::tip

For a calculation example see our tutorial video.

:::


### Classification
In order to classify the accessibility levels that were computed for each grid cell (for color-coded visualization), a classification based on **8 quantile group is used by default**. That means, each color covers 12,5 % of the grid cells. The area outside of the computed layer has no access within the defined travel time.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
<img src={require('/img/toolbox/accessibility_indicators/heatmaps/gravity_based/gravity_default_classification.png').default} alt="gravity-default-classification" style={{ maxHeight: "250px", maxWidth: "auto"}}/>
</div>

However, various other classification methods may be used instead. Read more in the **[Data Classification Methods](../../map/layer_style/attribute_based_styling#data-classification-methods)** section of the *Attribute-based Styling* page.

### Visualization 

Heatmaps in GOAT utilize **[Uber's H3 grid-based](../further_reading/glossary#h3-grid)** solution for efficient computation and eacessibisy-to-understand visualization. Behind the scenes, a pre-computed travel time matrix for each *routing type* utilizes this solution and is queried and further processed in real-time to compute accessibility and produce a final heatmap.

The resolution and dimensions of the hexagonal grid used depend on the selected *routing type*:

#### Walk
- Resolution: 10
- Average hexagon area: 11285.6 m²
- Average hexagon edge length: 65.9 m

#### Bicycle
- Resolution: 9
- Average hexagon area: 78999.4 m²
- Average hexagon edge length: 174.4 m

#### Pedelec
- Resolution: 9
- Average hexagon area: 78999.4 m²
- Average hexagon edge length: 174.4 m

#### Car
- Resolution: 8
- Average hexagon area: 552995.7 m²
- Average hexagon edge length: 461.4 m


## 5. References

Kwan, Mei-Po. 1998. “Space-Time and Integral Measures of Individual Accessibility: A Comparative Analysis Using a Point-Based Framework.” Geographical Analysis 30 (3): 191–216. [https://doi.org/10.1111/j.1538-4632.1998.tb00396.x](https://doi.org/10.1111/j.1538-4632.1998.tb00396.x).

Vale, D.S., and M. Pereira. 2017. “The Influence of the Impedance Function on Gravity-Based Pedestrian Accessibility Measures: A Comparative Analysis.” Environment and Planning B: Urban Analytics and City Science 44 (4): 740–63.  [https://doi.org/10.1177%2F0265813516641685](https://doi.org/10.1177%2F0265813516641685).

Higgins, Christopher D. 2019. “Accessibility Toolbox for R and ArcGIS.” Transport Findings, May.  [https://doi.org/10.32866/8416](https://doi.org/10.32866/8416).
