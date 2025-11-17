---
sidebar_position: 2

---

import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';
import thematicIcon from "/img/toolbox/data_management/join/toolbox.webp";
import MathJax from 'react-mathjax';

# Heatmap - Connectivity
Der Heatmap - Connectivity Indikator **erstellt eine farbkodierte Karte zur Visualisierung der Konnektivität von Orten innerhalb eines Interessengebiets** ([**AOI**](../../further_reading/glossary#area-of-interest-aoi "Was ist ein AOI?")).

<div style={{ display: 'flex', justifyContent: 'center' }}>
<iframe width="674" height="378" src="https://www.youtube.com/embed/PzWEIbcSf4Y?si=MB4LNSEkMmnzccuX" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>
</div>

## 1. Erklärung

Die Heatmap verwendet ein farbkodiertes sechseckiges Gitter, um **zu zeigen, wie gut verschiedene Gebiete miteinander verbunden sind.** Als Eingabeparameter werden ein **Interessengebiet** (AOI), ein **Routing-Typ** (zu Fuß, Radfahren usw.) und ein **Reisezeitlimit** benötigt. Unter Berücksichtigung der realen Verkehrs- und Straßennetze berechnet sie die Konnektivität jedes Sechsecks innerhalb der AOI.

import MapViewer from '@site/src/components/MapViewer';

:::info 

Heatmaps sind in bestimmten Regionen verfügbar. Bei der Auswahl eines `Routing-Typs` wird auf der Karte ein **Geofence** angezeigt, um die unterstützten Regionen hervorzuheben.

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
        { label: "Abdeckung für konnektivitätsbasierte Heatmaps", color: "#ffffff" }
      ]}
  />
</div>


Wenn Sie Analysen über diesen Geofence hinaus durchführen möchten, wenden Sie sich bitte an uns. Wir besprechen mit Ihnen gerne weitere Möglichkeiten. [Kontaktieren Sie uns](https://plan4better.de/en/contact/ "Kontaktieren Sie uns").

:::

## 2. Anwendungsbeispiele

 - Bietet das bestehende Verkehrsnetz einen gleichberechtigten Zugang innerhalb der AOI?
 - Wie gut ist das Straßen-, Fuß- oder Radwegenetz in einem bestimmten Gebiet vernetzt?
 - Wie schneiden die Orte innerhalb einer AOI in Bezug auf die Konnektivität über die verschiedenen Verkehrsmittel ab?
 - Gibt es Barrieren, Lücken oder Inseln im Straßennetz, die die Konnektivität behindern?

## 3. Wie verwendet man den Indikator?

<div class="step">
  <div class="step-number">1</div>
  <div class="content">Klicken Sie auf <code>Werkzeuge</code> <img src={thematicIcon} alt="toolbox" style={{width: "25px"}}/>.</div>
</div>

<div class="step">
  <div class="step-number">2</div>
  <div class="content">Unter dem <code>Erreichbarkeitsindikatoren</code> Menü klicken Sie auf <code>Heatmap Connectivity</code>.</div>
</div>

### Routing 

<div class="step">
  <div class="step-number">3</div>
  <div class="content">Wählen Sie den <code>Routing-Typ</code>, den Sie für die Heatmap verwenden möchten:</div>
</div>

### Konfiguration 

<div style={{ marginLeft: '60px' }}>
<Tabs>

<TabItem value="walk" label="Walk" default className="tabItemBox">

**Berücksichtigt alle zu Fuß begehbaren Wege**. Für Heatmaps wird eine Gehgeschwindigkeit von 5 km/h angenommen.

</TabItem>
  
<TabItem value="cycling" label="Bicycle" className="tabItemBox">

**Berücksichtigt alle mit dem Fahrrad befahrbaren Wege**. Dieser Routing-Modus berücksichtigt bei der Berechnung der Erreichbarkeit die Oberfläche, Glätte und Steigung der Straßen. Für Heatmaps wird eine Fahrradgeschwindigkeit von 15 km/h angenommen.

</TabItem>

<TabItem value="pedelec" label="Pedelec" className="tabItemBox">

**Berücksichtigt alle mit dem Pedelec befahrbaren Wege**. Dieser Routing-Modus berücksichtigt bei der Berechnung der Erreichbarkeit die Oberfläche und Glätte der Straßen. Für Heatmaps wird eine Pedelec-Geschwindigkeit von 23 km/h angenommen.

</TabItem>

<TabItem value="car" label="Auto" className="tabItemBox">

**Berücksichtigt alle mit dem Auto befahrbaren Wege**. Dieser Routing-Modus berücksichtigt bei der Berechnung der Erreichbarkeit Geschwindigkeitsbegrenzungen und Einbahnstraßenbeschränkungen.

</TabItem>

</Tabs>
</div>

:::tip Hinweis

Für weitere Einblicke in den Routing-Algorithmus besuchen Sie [Routing](../../category/routing). Darüber hinaus können Sie diese [Publikation](https://doi.org/10.1016/j.jtrangeo.2021.103080) lesen.

:::

<div class="step">
  <div class="step-number">4</div>
  <div class="content">
  Wählen Sie ein <code>Reisezeitlimit</code> für Ihre Heatmap. Dies wird im Kontext Ihres zuvor ausgewählten <code>Routing-Typs</code> verwendet.
  </div>
</div>

:::tip Hinweis
Benötigen Sie Hilfe bei der Auswahl eines geeigneten Reisezeitlimits für verschiedene gängige Einrichtungen? Das ["Standort-Werkzeug"](https://www.chemnitz.de/chemnitz/media/unsere-stadt/verkehr/verkehrsplanung/vep2040_standortwerkzeug.pdf) der Stadt Chemnitz kann hilfreiche Orientierung bieten.
:::


<div class="step">
  <div class="step-number">5</div>
  <div class="content">Wählen Sie den <code>Referenz-Layer</code> (Layer, der Ihre AOI enthält) **für den Sie die Heatmap berechnen möchten**. Dies kann jeder Polygon-Feature-Layer sein.</div>
</div>


<div class="step">
  <div class="step-number">6</div>
  <div class="content">Klicken Sie auf <code>Ausführen</code>, um die Berechnung der Heatmap zu beginnen.</div>
</div>

### Ergebnisse 

Sobald die Berechnung abgeschlossen ist, wird ein Ergebnislayer zur Karte hinzugefügt. Dieser Heatmap Connectivity Layer enthält Ihre farbkodierte Heatmap. **Durch Klicken auf eine der sechseckigen Zellen der Heatmap wird der berechnete Konnektivitätswert für diese Zelle angezeigt.**

![Connectivity-basierte Heatmap Ergebnis in GOAT](/img/toolbox/accessibility_indicators/heatmaps/connectivity_based/connectivity_calculation.gif "Connectivity-basierte Heatmap Ergebnis in GOAT")


:::tip Tipp

Möchten Sie Ihre Heatmaps gestalten und schöne Karten erstellen? Siehe [Styling](../../map/layer_style/styling).

:::

## 4. Technische Details

### Berechnung

Für jedes Sechseck im Raster innerhalb des Interessengebiets (AOI) identifiziert das Tool alle umgebenden Sechsecke, die es erreichen können. Diese umgebenden Sechsecke können sich außerhalb der AOI befinden, müssen aber innerhalb der angegebenen **Reisezeit** und mit der gewählten **Reisemethode** erreichbar sein.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/toolbox/accessibility_indicators/heatmaps/connectivity_based/heatmap_connectivity_infographic.png').default} alt="Extent of cells from where destination cell within AOI is accessible." style={{ maxHeight: "400px", maxWidth: "500px", alignItems:'center'}}/>
</div>

Konnektivitäts-Formel:

<MathJax.Provider>
  <div style={{ marginTop: '20px', fontSize: '24px' }}>
    <MathJax.Node formula={"\\text{Zellen-Konnektivität} = \\sum_{i=1}^{n} (\\text{Anzahl erreichbarer Zellen}_i \\times \\text{Zellfläche})"} />
  </div>
</MathJax.Provider>

Die Konnektivitäts-Formel berechnet die Gesamtfläche (in Quadratmetern), von der aus eine Zielzelle innerhalb des Interessengebiets (AOI) erreicht werden kann. Sie berücksichtigt dabei die **Anzahl der Zellen**, die die Zielzelle innerhalb jedes **Reisezeitschritts** ***i*** bis zum angegebenen **Reisezeitlimit** ***n*** erreichen können. **Die Summe aller dieser erreichbaren Bereiche ergibt den endgültigen Konnektivitätswert für diese Zelle.**

### Rasterzellen 

Heatmaps in GOAT nutzen **[Ubers H3-rasterbasierte](../../further_reading/glossary#h3-grid)** Lösung für effiziente Berechnungen und leicht verständliche Visualisierung. Im Hintergrund wird eine vorberechnete Reisezeitmatrix für jeden *Routing-Typ* abgefragt und in Echtzeit weiterverarbeitet, um die Erreichbarkeit zu berechnen und eine endgültige Heatmap zu erstellen.

Die Auflösung und Abmessungen des verwendeten sechseckigen Rasters hängen vom gewählten *Routing-Typ* ab:

<div style={{ marginLeft: '20px' }}>

<Tabs>

<TabItem value="walk" label="Walk" default className="tabItemBox">

<li parentName="ul">{`Auflösung: 10`}</li>
<li parentName="ul">{`Durchschnittliche Sechseckfläche: 11285.6 m²`}</li>
<li parentName="ul">{`Durchschnittliche Sechseck-Kantenlänge: 65.9 m`}</li>
</TabItem>
  
<TabItem value="cycling" label="Bicycle" className="tabItemBox">

<li parentName="ul">{`Auflösung: 9`}</li>
<li parentName="ul">{`Durchschnittliche Sechseckfläche: 78999.4 m²`}</li>
<li parentName="ul">{`Durchschnittliche Sechseck-Kantenlänge: 174.4 m`}</li>
</TabItem>

<TabItem value="pedelec" label="Pedelec" className="tabItemBox">

<li parentName="ul">{`Auflösung: 9`}</li>
<li parentName="ul">{`Durchschnittliche Sechseckfläche: 78999.4 m²`}</li>
<li parentName="ul">{`Durchschnittliche Sechseck-Kantenlänge: 174.4 m`}</li> 
</TabItem>

<TabItem value="car" label="Car" className="tabItemBox">

<li parentName="ul">{`Auflösung: 8`}</li>
<li parentName="ul">{`Durchschnittliche Sechseckfläche: 552995.7 m²`}</li>
<li parentName="ul">{`Durchschnittliche Sechseck-Kantenlänge: 461.4 m`}</li>

</TabItem>

</Tabs>
</div>

:::tip Tipp

Für weitere Einblicke in den Routing-Algorithmus, besuchen Sie [Routing](../../category/routing). Außerdem können Sie diese [Publikation](https://doi.org/10.1016/j.jtrangeo.2021.103080) lesen.

:::

### Visualisierung

Zur Visualisierung verwendet das Ergebnis der Konnektivitätsanalyse standardmäßig eine Klassifizierungsmethode basierend auf Quantilen. Es können jedoch auch verschiedene andere Klassifizierungsmethoden verwendet werden. Lesen Sie mehr im Abschnitt **[Datenklassifizierungsmethoden](../../map/layer_style/attribute_based_styling#data-classification-methods)** der Seite *Attribut-basiertes Styling*.