---
sidebar_position: 4
---

import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';
import thematicIcon from "/img/toolbox/data_management/join/toolbox.webp";
import MathJax from 'react-mathjax';

# Heatmap - Gravity

Der Heatmap - Gravity Indikator **erzeugt eine farbkodierte Karte zur Visualisierung der Erreichbarkeit von Punkten, wie POIs aus umliegenden Gebieten**.

<div style={{ display: 'flex', justifyContent: 'center' }}>
<iframe width="674" height="378" src="https://www.youtube.com/embed/yteOnb6N7hA?si=SYStNhRCpZidqY0p" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>
</div>

## 1. Erklärung

Die Heatmap Gravity zeigt ein **farbkodiertes sechseckiges Raster, das die Erreichbarkeit von Zielen (Gelegenheiten) basierend auf Reisezeit und Zielattraktivität anzeigt**. Die Erreichbarkeit wird mithilfe realer Verkehrsnetze und einer schwerkraftbasierten Formel berechnet, die widerspiegelt, wie die Bereitschaft der Menschen zu reisen mit der Entfernung abnimmt.

Sie können den **Routing-Typ**, **Gelegenheits-Layer**, das **Reisezeitlimit** festlegen und **Sensitivität** und **Zielpotenzial** anpassen, um die Berechnung der Erreichbarkeit zu verfeinern.

Der **Gelegenheits-Layer** enthält punktbasierte Zieldaten (wie POIs, Haltestellen, Schulen, Einrichtungen oder benutzerdefinierte Punkte). Sie können mehrere Gelegenheits-Layer auswählen, die zu einer einheitlichen Heatmap kombiniert werden.

Die **Sensitivität** steuert, wie schnell die Erreichbarkeit mit zunehmender Reisezeit abnimmt, während das **Zielpotenzial** es Ihnen ermöglicht, Zielen mit höherer Kapazität oder Qualität mehr Gewicht zu verleihen (z.B. einem größeren Supermarkt oder einer Bushaltestelle mit mehr Abfahrten). Zusammen mit der gewählten **Impedanzfunktion** definieren diese Einstellungen, wie die Erreichbarkeit berechnet wird.

Die Verwendung des **Zielpotenzials** hilft dabei, bestimmte Gelegenheiten gegenüber anderen zu priorisieren. Beispielsweise kann ein größerer aber weiter entfernter Supermarkt höher bewertet werden als ein kleinerer in der Nähe. Dies ermöglicht es, qualitative Informationen—wie Größe, Häufigkeit oder Service-Level—bei der Berechnung der Erreichbarkeit einzubeziehen, was zu einer realistischeren Heatmap führt.

Beeinflusst von all diesen Eigenschaften kann die Erreichbarkeit eines Punktes komplexes menschliches Verhalten in der realen Welt modellieren und ist ein leistungsfähiges Maß für die Verkehrs- und Erreichbarkeitsplanung.

**Wichtiger Unterschied:** Anders als die *Closest-Average* Heatmap, die den Reiseaufwand misst, misst die *Gravity-basierte Heatmap* **Attraktivität** — sie zeigt, wie zugänglich und ansprechend Ziele sind, wenn sowohl Entfernung als auch Qualität berücksichtigt werden.

import MapViewer from '@site/src/components/MapViewer';

:::info 

Heatmaps sind in bestimmten Regionen verfügbar. Bei der Auswahl eines „Verkehrsmittels“ wird auf der Karte ein **Geofence** angezeigt, um die unterstützten Regionen hervorzuheben.

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
        { label: "Abdeckung für gravitationsbasierte Heatmaps", color: "#ffffff" }
      ]}
  />
</div> 


Wenn Sie Analysen über diesen Geofence hinaus durchführen möchten, wenden Sie sich bitte an unseren [Support](https://plan4better.de/de/contact/ "Support").

:::

## 2. Anwendungsbeispiele

 - Welche Stadtteile oder Gebiete haben nur begrenzte Erreichbarkeit zu öffentlichen Einrichtungen wie Parks, Freizeiteinrichtungen oder Kultureinrichtungen und erfordern möglicherweise gezielte Maßnahmen zur Verbesserung der Erreichbarkeit?

 - Gibt es Gebiete mit hohem Potenzial für eine verkehrsorientierte Entwicklung oder Möglichkeiten zur Verbesserung der Infrastruktur für den nicht motorisierten Verkehr, z. B. Radwege oder fußgängerfreundliche Straßen?

 - Wie wirkt sich eine neue Einrichtung auf die lokale Erreichbarkeit aus?

 - Besteht die Möglichkeit, die Verfügbarkeit von Dienstleistungen wie Bike-Sharing oder Car-Sharing-Stationen zu erweitern?



## 3. Wie verwendet man den Indikator?

<div class="step">
  <div class="step-number">1</div>
  <div class="content">Klicken Sie auf <code>Werkzeuge</code> <img src={thematicIcon} alt="toolbox" style={{width: "25px"}}/>.</div>
</div>

<div class="step">
  <div class="step-number">2</div>
  <div class="content">Unter dem <code>Erreichbarkeitsindikatoren</code> Menü klicken Sie auf <code>Heatmap Gravity</code>.</div>
</div>

### Routing

<div class="step">
  <div class="step-number">3</div>
  <div class="content">Wählen Sie den <code>Routing-Typ</code>, den Sie für die Heatmap verwenden möchten.</div>
</div>

<Tabs>

<TabItem value="walk" label="Zu Fuß" default className="tabItemBox">

#### Zu Fuß

Berücksichtigt alle zu Fuß begehbaren Wege. Für Heatmaps wird eine Gehgeschwindigkeit von 5 km/h angenommen.

</TabItem>
  
<TabItem value="cycling" label="Fahrrad" className="tabItemBox">

#### Fahrrad

Berücksichtigt alle mit dem Fahrrad befahrbaren Wege. Dieser Routing-Modus berücksichtigt bei der Berechnung der Erreichbarkeit die Oberfläche, die Glätte und die Steigung der Straßen. Für Heatmaps wird eine Fahrradgeschwindigkeit von 15 km/h angenommen.

</TabItem>

<TabItem value="pedelec" label="Pedelec" className="tabItemBox">

#### Pedelec

Berücksichtigt alle mit dem Pedelec befahrbaren Wege. Dieser Routing-Modus berücksichtigt bei der Berechnung der Erreichbarkeit die Oberfläche und Glätte der Straßen. Für Heatmaps wird eine Pedelec-Geschwindigkeit von 23 km/h angenommen.

</TabItem>

<TabItem value="car" label="Auto" className="tabItemBox">

#### Auto

Berücksichtigt alle mit dem Auto befahrbaren Wege. Dieser Routing-Modus berücksichtigt bei der Berechnung der Erreichbarkeit Geschwindigkeitsbegrenzungen und Einbahnstraßenbeschränkungen.

</TabItem>

</Tabs>

### Konfiguration

<div class="step">
  <div class="step-number">4</div>
  <div class="content">Wählen Sie die <code>Impedanzfunktion</code>, die Sie für die Heatmap verwenden möchten.</div>
</div>

<Tabs>

<TabItem value="gaussian" label="Gaussian" default className="tabItemBox">

#### Gaussian

Diese Funktion berechnet die Erreichbarkeiten auf der Grundlage einer Gaußschen Kurve, die durch die von Ihnen definierten Parameter `Sensitivität` und `Zielpotenzial` beeinflusst wird. Ein ausführlicheres Verständnis finden Sie im Abschnitt [Technische Details](./gravity#4-technische-details).

</TabItem>
  
<TabItem value="linear" label="Linear" default className="tabItemBox">

#### Linear

Diese Funktion stellt eine direkte Korrelation zwischen Reisezeit und Erreichbarkeit her, die durch das von Ihnen angegebene `Zielpotenzial` moduliert wird. Ein ausführlicheres Verständnis finden Sie im Abschnitt [Technische Details](./gravity#4-technische-details).

:::info Hinweis
Diese Funktion befindet sich derzeit in der Entwicklung. 🧑🏻‍💻
:::

</TabItem>

<TabItem value="exponential" label="Exponential" default className="tabItemBox">

#### Exponential

Diese Funktion berechnet die Erreichbarkeiten auf der Grundlage einer Exponentialkurve, die von der von Ihnen definierten `Sensitivität` und dem `Zielpotenzial` beeinflusst wird. Ein ausführlicheres Verständnis finden Sie im Abschnitt [Technische Details](./gravity#4-technische-details).

:::info Hinweis
Diese Funktion befindet sich derzeit in der Entwicklung. 🧑🏻‍💻
:::

</TabItem>

<TabItem value="power" label="Power" default className="tabItemBox">

#### Power

Diese Funktion berechnet die Erreichbarkeiten auf der Grundlage einer Leistungskurve, die durch die von Ihnen definierte `Sensitivität` und das `Zielpotenzial` beeinflusst wird. Ein ausführlicheres Verständnis finden Sie im Abschnitt [Technische Details](./gravity#4-technische-details).

:::info Hinweis
Diese Funktion befindet sich derzeit in der Entwicklung. 🧑🏻‍💻
:::

</TabItem>

</Tabs>

### Gelegenheiten

<div class="step">
  <div class="step-number">5</div>
  <div class="content">Wählen Sie Ihren <code>Gelegenheits-Layer</code> aus dem Dropdown-Menü aus. Dies kann ein zuvor erstellter Layer sein, der punktbasierte Daten enthält.</div>
</div>

<div class="step">
  <div class="step-number">6</div>
  <div class="content">Wählen Sie ein <code>Reisezeitlimit</code> für Ihre Heatmap aus. Dies wird im Kontext Ihres zuvor ausgewählten <i>Routing-Typs</i> verwendet.</div>
</div>

:::tip Tipp

Benötigen Sie Hilfe bei der Auswahl einer geeigneten Reisezeit für verschiedene Einrichtungen? Das [„Standort-Werkzeug“](https://www.chemnitz.de/chemnitz/media/unsere-stadt/verkehr/verkehrsplanung/vep2040_standortwerkzeug.pdf) der Stadt Chemnitz kann Ihnen dabei behilflich sein.

:::

<div class="step">
  <div class="step-number">7</div>
  <div class="content">Falls erforderlich, wählen Sie ein <code>Zielpotenzial-Feld</code> aus. Dies muss ein numerisches Feld aus Ihrem <i>Gelegenheits-Layer</i> sein, das als Koeffizient von der Erreichbarkeitsfunktion verwendet wird.</div>
</div>

<div class="step">
  <div class="step-number">8</div>
  <div class="content">Geben Sie einen <code>Sensitivitäts</code>-Wert an. Dieser muss numerisch sein und wird von der Heatmap-Funktion verwendet, um zu bestimmen, wie sich die Erreichbarkeit mit zunehmender Reisezeit ändert.</div>
</div>

:::tip Tipp

**Wie wählen Sie den Sensitivitätswert?**

Der beste **Sensitivitäts (β)** Wert hängt von Ihrer Analyse ab — es gibt keine einzig richtige Zahl. Er definiert **wie schnell die Erreichbarkeit mit zunehmender Reisezeit abnimmt**.

- **Niedriges β (städtischer Maßstab):** Verwenden Sie eine niedrigere Sensitivität für Analysen auf städtischer Ebene. Dies lässt die Erreichbarkeit schneller mit der Entfernung fallen, was zu städtischen Kontexten passt, wo viele Ziele in der Nähe sind und Menschen normalerweise das nächstgelegene wählen.
- **Hohes β (regionaler Maßstab):** Verwenden Sie eine höhere Sensitivität für regionale oder ländliche Analysen. Dies lässt die Erreichbarkeit langsamer abnehmen, was widerspiegelt, dass Menschen bereit sind, längere Strecken zu reisen, wenn weniger Optionen verfügbar sind.

Für eine visuelle Erklärung, wie die Sensitivität die Berechnung beeinflusst, siehe den **[Berechnung](#berechnung)** Abschnitt.

:::

<div class="step">
  <div class="step-number">9</div>
  <div class="content">Klicken Sie auf <code>Ausführen</code>, um die Berechnung der Heatmap zu starten.</div>
</div>

### Ergebnisse

Sobald die Berechnung abgeschlossen ist, wird ein Ergebnislayer zur Karte hinzugefügt. Dieser <i>Heatmap Gravity</i> Layer enthält Ihre farbkodierte Heatmap. Durch Klicken auf eine der sechseckigen Zellen der Heatmap wird der berechnete Erreichbarkeitswert für diese Zelle angezeigt.

![Heatmap Gravity-basierte Berechnung in GOAT](/img/toolbox/accessibility_indicators/heatmaps/gravity_based/gravity_calculation.gif "Heatmap Gravity-basierte Berechnung in GOAT")

:::tip Tipp

Möchten Sie visuell ansprechende Karten erstellen, die eine klare Geschichte erzählen? Lernen Sie, wie Sie Farben, Legenden und Styling in unserem [Styling-Bereich](../../map/layer_style/styling) anpassen.

:::

### Berechnungsbeispiel

Das folgende Beispiel zeigt, wie Änderungen in den Gelegenheits-Einstellungen die Gravity-Heatmap beeinflussen können. Das Zielpotenzial basiert auf der Gesamtzahl der stündlichen öffentlichen Verkehrs-Abfahrten von einer Haltestelle.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
<img src={require('/img/toolbox/accessibility_indicators/heatmaps/gravity_based/gravity_calculation_comparison.png').default} alt="gravity-no-destination-potential" style={{ maxHeight: "500px", maxWidth: "auto"}}/>
</div>

<p></p>

Die Karte im Hintergrund wird ohne Zielpotenzial berechnet. Die zweite Karte verwendete die gleichen Einstellungen, fügte aber Zielpotenzial basierend auf der Gesamtzahl der Abfahrten hinzu. Dies veränderte die Erreichbarkeitswerte jedes Hexagons und sie ergaben einen größeren Bereich, da der höchste Wert noch weiter zunahm. **Höhere Erreichbarkeitswerte sind stärker um Haltestellen mit größerer Fahrtzahl konzentriert (rote Punkte).**

## 4. Technische Details

### Berechnung
Der Erreichbarkeitswert jeder sechseckigen Zelle innerhalb einer Heatmap wird mit Hilfe von gravity-basierenden Maßnahmen berechnet und kann wie folgt operationalisiert werden:

*Erreichbarkeitsformel:*

<MathJax.Provider>
  <div style={{ marginTop: '20px', fontSize: '24px'  }}>
    <MathJax.Node formula={"A_i=\\sum_j O_jf(t_{i,j})"} />
  </div>
</MathJax.Provider>

wobei die Erreichbarkeit **A** des Ausgangspunkts **i** die Summe aller am Zielort **j** verfügbaren Möglichkeiten **O** ist, gewichtet mit einer Funktion der Reisezeit **tij** zwischen **i** und **j**. Die Funktion **f(tij)** ist die Impedanzfunktion, die `Gaussfunktion`, `lineare Funktion`, `Exponentialfunktion`, oder `Powerfunktion`. sein kann. Der Parameter **β** für die *Sensitivität* und das *Zielpotenzialfeld* werden verwendet, um den Erreichbarkeitswert einzustellen.

#### GOAT verwendet die folgenden Formeln für seine Widerstandsfunktionen:

*Modifizierter Gauß, (Kwan,1998):*

<MathJax.Provider>
  <div style={{ marginTop: '20px', fontSize: '24px'  }}>
    <MathJax.Node formula={"f(t_{i,j})=\\exp^{(-t_{i,j}^2/\\beta)}"} />
  </div>
</MathJax.Provider>


*Lineare kumulative Chancen, (Kwan,1998):*

<div>
<MathJax.Provider>
  <div style={{ marginTop: '20px', fontSize: '24px' }}>
    <MathJax.Node formula={`f(t_{ij}) = \\begin{cases}
      \\left(1 - \\frac{t_{ij}}{\\bar{t}} \\right) & \\text{for } t_{ij} \\leq \\bar{t} \\\\
      0 & \\text{sonst}
    \\end{cases}`} />
  </div>
</MathJax.Provider>
</div>

*Negative Exponentialfunktion, (Kwan,1998):*

<div>
<MathJax.Provider>
  <div style={{ marginTop: '20px', fontSize: '24px'  }}>
    <MathJax.Node formula={"f(t_{i,j})=\\exp^{(-\\beta t_{i,j})}"} />
  </div>
</MathJax.Provider>
</div>


*Inverse Power, (Kwan,1998) ('Powerfunktion' im GOAT):*

<div>
<MathJax.Provider>
  <div style={{ marginTop: '20px', fontSize: '24px' }}>
    <MathJax.Node formula={`f(t_{ij}) = \\begin{cases}
      \\ 1 & \\text{for } t_{ij} \\leq 1 \\\\
      t_{i,j}^{-\\beta} & \\text{sonst}
    \\end{cases}`} />
  </div>
</MathJax.Provider>
</div>

Die Reisezeit wird in Minuten gemessen. Bei einer maximalen Reisezeit von 30 Minuten gelten Ziele, die weiter als 30 Minuten entfernt sind, als nicht erreichbar und werden daher bei der Berechnung der Erreichbarkeit nicht berücksichtigt.
Der Parameter *Sensitivität* bestimmt, wie sich die Erreichbarkeit mit zunehmender Reisezeit verändert. Da der Parameter *Sensitivität* für die Messung der Erreichbarkeit entscheidend ist, können Sie ihn in GOAT anpassen. Die folgenden Diagramme zeigt, wie die Bereitschaft, zu Fuß zu gehen, mit zunehmender Reisezeit auf der Grundlage der gewählten Impedanzfunktion und des Sensitivität (β) abnimmt.

import ImpedanceFunction from '@site/src/components/ImpedanceFunction';

<div style={{ display: 'block', textAlign: 'center'}}>
  <div style={{ maxHeight: "auto", maxWidth: "auto"}}>
    <ImpedanceFunction />
   </div> 
</div>

In ähnlicher Weise kann auch das *Zielpotenzialfeld* verändert werden. So kann z.B. einem POI-Typ (z.B. Verbrauchermärkte) ein höherer Erreichbarkeitseffekt zugeordnet werden als anderen POI-Typen (z.B. Discounter). Im [Gelegenheit](#gelegenheit) Abschnitt, bei **Schritt 7**, decken wir das *Zielpotenzial* im Detail ab.


:::tip

Für ein Berechnungsbeispiel siehe unser Tutorial-Video.

:::

### Klassifizierung
Zur Klassifizierung der Erreichbarkeitsstufen, die für jede Rasterzelle berechnet wurden (für die farbige Visualisierung), wird **standardmäßig** eine Klassifizierung basierend auf **8 Quantil-Gruppen** verwendet. Das bedeutet, dass jede Farbe 12,5 % der Gitterzellen abdeckt. Der Bereich außerhalb der berechneten Ebene hat keinen Zugriff innerhalb der definierten Reisezeit.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
<img src={require('/img/toolbox/accessibility_indicators/heatmaps/gravity_based/gravity_default_classification_de.png').default} alt="gravity-default-classification" style={{ maxHeight: "250px", maxWidth: "auto"}}/>
</div>

Es können jedoch auch verschiedene andere Klassifizierungsmethoden verwendet werden. Weitere Informationen finden Sie im Abschnitt **[Datenklassifizierungsmethoden](../../map/layer_style/attribute_based_styling#datenklassifizierungsmethoden)** auf der Seite *attributbasiertes Styling*.

### Visualisierung 

Heatmaps in GOAT nutzen die **[Uber H3 auf Gitter basierende](../further_reading/glossary#h3-grid)** Lösung für effiziente Berechnungen und leicht verständliche Visualisierungen. Hinter den Kulissen wird eine vorberechnete Reisezeitmatrix für jeden *Routing-Typ* mit dieser Lösung abgefragt und in Echtzeit weiterverarbeitet, um die Erreichbarkeit zu berechnen und eine endgültige Heatmap zu erstellen.

Die Auflösung und die Abmessungen des verwendeten sechseckigen Gitters hängen von dem gewählten *Routing-Typ* ab:

<Tabs>

<TabItem value="walk" label="Zu Fuß" default className="tabItemBox">

#### Zu Fuß
- Auflösung: 10
- Durchschnittliche Sechseckfläche: 11285.6 m²
- Durchschnittliche Kantenlänge des Sechsecks: 65,9 m

</TabItem>
  
<TabItem value="bicycle" label="Fahrrad" className="tabItemBox">

#### Fahrrad
- Auflösung: 9
- Durchschnittliche Sechseckfläche: 78999.4 m²
- Durchschnittliche Kantenlänge des Sechsecks: 174,4 m

</TabItem>

<TabItem value="pedelec" label="Pedelec" className="tabItemBox">

#### Pedelec
- Auflösung: 9
- Durchschnittliche Sechseckfläche: 78999.4 m²
- Durchschnittliche Kantenlänge des Sechsecks: 174,4 m

</TabItem>

<TabItem value="car" label="Auto" className="tabItemBox">

#### Auto
- Auflösung: 8
- Durchschnittliche Sechseckfläche: 552995.7 m²
- Durchschnittliche Kantenlänge des Sechsecks: 461,4 m

</TabItem>

</Tabs>

:::tip Tipp

Für weitere Einblicke in den Routing-Algorithmus, besuchen Sie [Routing](../../category/routing). Außerdem können Sie diese [Publikation](https://doi.org/10.1016/j.jtrangeo.2021.103080) lesen.
:::


## 5. Referenzen

Kwan, Mei-Po. 1998. “Space-Time and Integral Measures of Individual Accessibility: A Comparative Analysis Using a Point-Based Framework.” Geographical Analysis 30 (3): 191–216. [https://doi.org/10.1111/j.1538-4632.1998.tb00396.x](https://doi.org/10.1111/j.1538-4632.1998.tb00396.x).

Vale, D.S., and M. Pereira. 2017. “The Influence of the Impedance Function on Gravity-Based Pedestrian Accessibility Measures: A Comparative Analysis.” Environment and Planning B: Urban Analytics and City Science 44 (4): 740–63.  [https://doi.org/10.1177%2F0265813516641685](https://doi.org/10.1177%2F0265813516641685).

Higgins, Christopher D. 2019. “Accessibility Toolbox for R and ArcGIS.” Transport Findings, May.  [https://doi.org/10.32866/8416](https://doi.org/10.32866/8416).
