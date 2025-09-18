---
sidebar_position: 4
---

import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';
import thematicIcon from "/img/toolbox/data_management/join/toolbox.webp";
import MathJax from 'react-mathjax';

# Heatmap - Gravity
Eine farblich gekennzeichnete Karte zur Visualisierung der Erreichbarkeit von Punkten (wie z.B. [POI](../../further_reading/glossary#points-of-interest-poi "What is a POI?")) aus der Umgebung.

<iframe width="100%" height="500" src="https://www.youtube.com/embed/jOV5dSk64rM?si=s7PZIatUHvnLsKA0" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>

## 1. Erklärung

Die Heatmap wird als farblich gekennzeichnetes sechseckiges Raster dargestellt und berücksichtigt reale Verkehrs- und Straßennetze, um die Erreichbarkeit zu berechnen. Nach Angabe eines *Verkehrsmittels* (zu Fuß, mit dem Fahrrad usw.), eines *Gelegenheits-Layers* und eines *Reisezeitlimits* zeigt das Ergebnis ein farblich gekennzeichnetes sechseckiges Raster für alle unter diesen Bedingungen erreichbaren Gebiete an. Die Farbskala bezieht sich auf die lokale Erreichbarkeit.

:::info INFO

Ein `Gelegenheits-Layer` enthält [geografische Punkte](../../data/data_types "Was sind geografische Punkte?"). Wählen Sie einen oder mehrere solcher Layer mit Ihren Zielpunkten (Opportunities) als Input für die Heatmap.

:::

Einzigartig an der Gravity Heatmap sind die anpassbaren Eigenschaften wie *Sensitivität*, *Widerstandsfunktion* und das *Zielpotenzialfeld*, die Ihnen eine genaue Kontrolle über die verwendete Methode und die Metadaten geben, die bei der Berechnung des Erreichbarkeitswertes für ein Gebiet berücksichtigt werden. Beeinflusst durch diese Eigenschaften kann die Erreichbarkeit eines Punktes komplexes menschliches Verhalten in der realen Welt modellieren und ist ein leistungsfähiges Maß für die Verkehrs- und Erreichbarkeitsplanung.

:::tip Profi-Tipp

Kurz gesagt, sind Erreichbarkeits-Heatmaps eine Visualisierung, die die *Erreichbarkeit* von verschiedenen, nicht spezifizierten Ausgangspunkten zu einem oder mehreren spezifizierten Zielen darstellt. Dies steht im Gegensatz zu Einzugsgebieten, die den *Ausgang* von einem oder mehreren bestimmten Quellen zu verschiedenen, nicht spezifizierten Zielen darstellen.

:::

![Gravity-based Heatmap in GOAT](/img/toolbox/accessibility_indicators/heatmaps/gravity_based/heatmap_gravity_based.webp "Gravity-based Heatmap in GOAT")

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

 - Wie ist die Erreichbarkeit in verschiedenen Stadtteilen im Vergleich, wenn man die qualitativen Aspekte der Einrichtungen berücksichtigt (z. B. Häufigkeit der Bushaltestellen, Größe der Supermärkte, Kapazität der Schulen usw.)?

 - Wie sieht die Erreichbarkeit von Bahnhöfen des öffentlichen Verkehrs aus, wenn sich die Fahrtzeiten zu diesen Bahnhöfen nicht linear auf ihre Erreichbarkeit auswirken?



## 3. Wie ist der Indikator zu verwenden?

<div class="step">
  <div class="step-number">1</div>
  <div class="content">Klicken Sie auf <code>Werkzeuge</code> <img src={thematicIcon} alt="toolbox" style={{width: "25px"}}/>. </div>
</div>

<div class="step">
  <div class="step-number">2</div>
  <div class="content">Unter <code>Erreichbarkeitsindikatoren</code> wählen Sie <code>Heatmap Gravity</code>.</div>
</div>

### Verkehrsmittel

<div class="step">
  <div class="step-number">3</div>
  <div class="content">Wählen Sie das <code>Verkehrsmittel</code> welches Sie für die Heatmap benutzen möchten.</div>
</div>

<Tabs>

<TabItem value="zu Fuß" label="zu Fuß" default className="tabItemBox">

#### Zu Fuß

Berücksichtigt alle zu Fuß begehbaren Wege. Für Heatmaps wird eine Gehgeschwindigkeit von 5 km/h angenommen.

:::tip Tipp

Weitere Einblicke in den Routing-Algorithmus erhalten Sie unter [Verkehrsmittel/zu Fuß](../../routing/walking).

:::

</TabItem>
  
<TabItem value="Fahrrad" label="Fahrrad" className="tabItemBox">

#### Fahrrad

Berücksichtigt alle mit dem Fahrrad befahrbaren Wege. Dieser Routing-Modus berücksichtigt bei der Berechnung der Erreichbarkeit die Oberfläche, die Glätte und die Steigung der Straßen. Für Heatmaps wird eine Fahrradgeschwindigkeit von 15 km/h angenommen.

:::tip Tipp

Weitere Einblicke in den Routing-Algorithmus erhalten Sie unter [Verkehrsmittel/Fahrrad](../../routing/bicycle). Darüber hinaus können Sie diese [Publikation](https://doi.org/10.1016/j.jtrangeo.2021.103080) lesen.

:::

</TabItem>

<TabItem value="Pedelec" label="Pedelec" className="tabItemBox">

#### Pedelec

Berücksichtigt alle mit dem Pedelec befahrbaren Wege. Dieser Routing-Modus berücksichtigt bei der Berechnung der Erreichbarkeit die Oberfläche und Glätte der Straßen. Für Heatmaps wird eine Pedelec-Geschwindigkeit von 23 km/h angenommen.

:::tip Tipp

Weitere Einblicke in den Routing-Algorithmus erhalten Sie unter [Verkehrsmittel/Fahrrad](../../routing/fahrrad). Darüber hinaus können Sie diese [Publikation](https://doi.org/10.1016/j.jtrangeo.2021.103080) lesen.

:::

</TabItem>

<TabItem value="Auto" label="Auto" className="tabItemBox">

#### Auto

Berücksichtigt alle mit dem Auto befahrbaren Wege. Dieser Routing-Modus berücksichtigt bei der Berechnung der Erreichbarkeit Geschwindigkeitsbegrenzungen und Einbahnstraßenbeschränkungen.

:::tip Tipp

Weitere Einblicke in den Routing-Algorithmus erhalten Sie unter [Verkehrsmittel/Auto](../../routing/car).

:::

</TabItem>

</Tabs>

### Konfiguration

<div class="step">
  <div class="step-number">4</div>
  <div class="content">Wählen Sie die <code>Widerstandsfunktion</code> welche Sie für die Heatmap anwenden möchten.</div>
</div>

<Tabs>

<TabItem value="gaussian" label="Gaussfunktion" default className="tabItemBox">

#### Gaussfunktion

Diese Funktion berechnet die Erreichbarkeiten auf der Grundlage einer Gaußschen Kurve, die durch die von Ihnen definierten Parameter `Sensitivität` und `Zielpotentialfeld` beeinflusst wird. Ein ausführlicheres Verständnis finden Sie im Abschnitt [Technische Details](./gravity#4-technische-details).

:::tip Pro Tipp

Wie Studien gezeigt haben, ist die Beziehung zwischen Reisezeit und Erreichbarkeit oft nicht linear. Das bedeutet, dass Menschen bereit sein können, eine kurze Strecke zurückzulegen, um eine Einrichtung zu erreichen, aber mit zunehmender Entfernung nimmt ihre Bereitschaft, diese Strecke zurückzulegen, schnell ab (oft überproportional).

Mit Hilfe der von Ihnen definierten *Sensitivität* ermöglicht die Gauß-Funktion eine genauere Modellierung dieses Aspekts des Verhaltens in der realen Welt.

:::

</TabItem>
  
<TabItem value="linear" label="Lineare Funktion" default className="tabItemBox">

#### Lineare Funktion

Diese Funktion stellt eine direkte Korrelation zwischen Reisezeit und Erreichbarkeit her, die durch das von Ihnen angegebene `Zielpotentialfeld` moduliert wird. Ein ausführlicheres Verständnis finden Sie im Abschnitt [Technische Details](./gravity#4-technische-details).

:::info Tipp 
Diese Funktion befindet sich derzeit in der Entwicklung. 🧑🏻‍💻
:::

</TabItem>

<TabItem value="exponential" label="Exponentialfunktion" default className="tabItemBox">

#### Exponentialfunktion

Diese Funktion berechnet die Erreichbarkeiten auf der Grundlage einer Exponentialkurve, die von der von Ihnen definierten `Sensitivität` und dem `Zielpotentialfeld`  beeinflusst wird. Ein ausführlicheres Verständnis finden Sie im Abschnitt [Technische Details](./gravity#4-technische-details).

:::info Tipp 
Diese Funktion befindet sich derzeit in der Entwicklung. 🧑🏻‍💻
:::
</TabItem>

<TabItem value="power" label="Powerfunktion" default className="tabItemBox">

#### Powerfunktion

Diese Funktion berechnet die Erreichbarkeiten auf der Grundlage einer Leistungskurve, die durch die von Ihnen definierte `Sensitivität` und das `Zielpotentialfeld` beeinflusst wird. Ein ausführlicheres Verständnis finden Sie im Abschnitt [Technische Details](./gravity#4-technische-details).

:::info Tipp 
Diese Funktion befindet sich derzeit in der Entwicklung. 🧑🏻‍💻
:::
</TabItem>

</Tabs>

### Gelegenheiten

Gelegenheiten sind im Wesentlichen punktbasierte Daten (wie [POI](../../further_reading/glossary#point-of-interest-poi "Was ist ein POI?")), für die Sie eine Heatmap berechnen möchten. Dies sind die „Destinationen“ (z. B. Bahnhöfe, Schulen, andere Einrichtungen oder Ihre eigenen punktbasierten Daten), während die umliegenden Gebiete „Quellen“ sind, für die ein Erreichbarkeitswert berechnet und visualisiert wird.

Zusätzlich können Sie weitere Gelegenheiten über die Schaltfläche `+ Gelegenheit hinzufügen`am unteren Rand der Leiste erstellen. Alle Gelegenheits-Layer werden kombiniert, um eine einheitliche Heatmap zu erstellen.

<div class="step">
  <div class="step-number">5</div>
  <div class="content">Wählen Sie Ihren <code>Gelegenheitslayer</code> aus dem Dropdown-Menü aus. Dies kann ein zuvor erstellter Layer sein, der punktbasierte Daten enthält.</div>
</div>

<div class="step">
  <div class="step-number">6</div>
  <div class="content">Wählen Sie eine <code>Reisezeitbegrenzung</code> für Ihre Heatmap aus. Dies wird im Kontext Ihres zuvor ausgewählten <i>Verkehrsmittel</i> verwendet.</div>
</div>

:::tip Tipp

Benötigen Sie Hilfe bei der Auswahl einer geeigneten Reisezeit für verschiedene Einrichtungen? Das [„Standort-Werkzeug“](https://www.chemnitz.de/chemnitz/media/unsere-stadt/verkehr/verkehrsplanung/vep2040_standortwerkzeug.pdf) der Stadt Chemnitz kann Ihnen dabei behilflich sein.

:::

<div class="step">
  <div class="step-number">7</div>
  <div class="content">Falls erforderlich, wählen Sie ein <code>Zielpotenzialfeld</code> aus. Dies muss ein numerisches Feld aus Ihrem <i>Gelegenheitslayer</i> sein, das als Koeffizient von der Erreichbarkeitsfunktion verwendet wird.</div>
</div>

:::tip Pro-Tipp

Das *Zielpotenzialfeld* ist eine nützliche Methode, um bestimmte Möglichkeiten gegenüber anderen zu bevorzugen. Wenn es zum Beispiel zwei Supermärkte gibt und einer näher liegt als der andere, würde er aufgrund seiner Nähe in der Regel eine höhere Erreichbarkeitsbewertung erhalten. Wenn der weiter entfernte Supermarkt jedoch größer ist, sollten Sie ihm eine höhere Priorität einräumen. Mit *Zielpotenzialfeld* können Sie eine zusätzliche Eigenschaft (z. B. die Größe von Supermärkten) verwenden, um Gelegenheiten ein "Potenzial" zuzuweisen und bei der Berechnung der Erreichbarkeit qualitative Informationen zu verwenden.

:::

<div class="step">
  <div class="step-number">8</div>
  <div class="content">Geben Sie einen Wert für die <code>Sensitivität</code> an. Dieser muss numerisch sein und wird von der Heatmap-Funktion verwendet, um zu bestimmen, wie sich die Erreichbarkeit mit zunehmender Reisezeit ändert.</div>
</div>

<div class="step">
  <div class="step-number">9</div>
  <div class="content">Klicken Sie auf <code>Ausführen</code>, um die Berechnung der Heatmap zu starten.</div>
</div>

:::tip Tipp

Je nach Ihrer Konfiguration kann die Berechnung einige Minuten dauern. Die [Statusleiste](../../workspace/home#statusleiste) zeigt den aktuellen Fortschritt an.

:::

### Ergebnisse

<div class="step">
  <div class="step-number">10</div>
  <div class="content">Sobald die Berechnung abgeschlossen ist, wird ein Ergebnislayer zur Karte hinzugefügt. Dieser Layer namens <i>Heatmap Gravity</i> enthält Ihre farblich gekennzeichnete Heatmap.
  <p></p>
  Durch Klicken auf eine der sechseckigen Zellen der Heatmap wird der berechnete Erreichbarkeitswert für diese Zelle angezeigt.</div>
</div>


![Ergebnis der Gravity Heatmap-Berechnung in GOAT](/img/toolbox/accessibility_indicators/heatmaps/gravity_based/heatmap_gravity_result.png "Ergebnis der Gravity Heatmap-Berechnung in GOAT")


:::tip Tipp

Möchten Sie Ihre Heatmaps bearbeiten und schöne Karten erstellen? Sie können dies unter [Layer Design](../../map/layer_style/styling).

:::

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

<ImpedanceFunction />

In ähnlicher Weise kann auch das *Zielpotenzialfeld* verändert werden. So kann z.B. einem POI-Typ (z.B. Verbrauchermärkte) ein höherer Erreichbarkeitseffekt zugeordnet werden als anderen POI-Typen (z.B. Discounter). Die folgenden Bilder zeigen den Einfluss des Parameters *Zielpotenzialfeld* auf die Erreichbarkeit:

:::info demnächst verfügbar

Beispiele für diese Funktionalität werden bald online sein. 🧑🏻‍💻

:::

### Klassifizierung
Zur Klassifizierung der Erreichbarkeitsstufen, die für jede Rasterzelle berechnet wurden (für die farbige Visualisierung), wird standardmäßig eine Klassifizierung auf der Grundlage von Quantilen verwendet. Es können jedoch auch verschiedene andere Klassifizierungsmethoden verwendet werden. Weitere Informationen finden Sie im Abschnitt **[Datenklassifizierungsmethoden](../../map/layer_style/attribute_based_styling#datenklassifizierungsmethoden)** auf der Seite *attributbasiertes Styling*.

### Visualisierung

Heatmaps in GOAT nutzen die **[Uber H3 auf Gitter basierende](../../further_reading/glossary#h3-grid)** Lösung für effiziente Berechnungen und leicht verständliche Visualisierungen. Hinter den Kulissen wird eine vorberechnete Reisezeitmatrix für jedes *Verkehrsmittel* mit dieser Lösung abgefragt und in Echtzeit weiterverarbeitet, um die Erreichbarkeit zu berechnen und eine endgültige Heatmap zu erstellen.

Die Auflösung und die Abmessungen des verwendeten sechseckigen Gitters hängen von dem gewählten *Verkehrsmittel* ab:

#### Zu Fuß
- Auflösung: 10
- Durchschnittliche Sechseckfläche: 11285.6 m²
- Durchschnittliche Kantenlänge des Sechsecks: 65,9 m

#### Fahrrad
- Auflösung: 9
- Durchschnittliche Sechseckfläche: 78999.4 m²
- Durchschnittliche Kantenlänge des Sechsecks: 174,4 m

#### Pedelec
- Auflösung: 9
- Durchschnittliche Sechseckfläche: 78999.4 m²
- Durchschnittliche Kantenlänge des Sechsecks: 174,4 m

#### Auto
- Auflösung: 8
- Durchschnittliche Sechseckfläche: 552995.7 m²
- Durchschnittliche Kantenlänge des Sechsecks: 461,4 m

### Beispiel einer Berechnung
#### Berechnung der Reisezeiten
Das folgende Beispiel veranschaulicht, wie die Heatmap der lokalen Erreichbarkeit berechnet wird. Für jede Rasterzelle werden die Fahrtzeiten zum jeweiligen Ziel im Straßennetz berechnet.

Für das hier dargestellte Sechseck ergibt die Berechnung je nach Sensitivitätsparameter folgende Ergebnisse:

##### Einheitlicher Empfindlichkeitsparameter:
:::info demnächst verfügbar

Beispiele für diese Funktionalität werden bald online sein. 🧑🏻‍💻

:::

##### Variierender Empfindlichkeitsparameter für Hypermarkt:
:::info demnächst verfügbar

Beispiele für diese Funktionalität werden bald online sein. 🧑🏻‍💻

:::

In GOAT angewandt, ergeben sich folgende Unterschiede:

#### Berechnung mit einheitlichem Empfindlichkeitsparameter
Im ersten Beispiel wird die Erreichbarkeit von Lebensmittelgeschäften in 15 min mit einem einheitlichen Empfindlichkeitsparameter (β=300.000) für alle Geschäfte berechnet. Das Ergebnis sieht wie folgt aus:

:::info demnächst verfügbar

Beispiele für diese Funktionalität werden bald online sein. 🧑🏻‍💻

:::

#### Berechnung mit verschiedenen Empfindlichkeitsparametern
Im zweiten Beispiel wird die Erreichbarkeit von Lebensmittelgeschäften in 15 min mit unterschiedlichen Sensitivitätsparametern (β=300.000 und β=400.000) durchgeführt. Das bedeutet, dass der Sensitivitätsparameter von den verschiedenen Lebensmittelladentypen abhängt. Für dieses Beispiel haben wir β=400.000 für Hypermärkte und β=300.000 für Discounter und Supermärkte verwendet. Daraus ergibt sich das folgende Ergebnis:

:::info demnächst verfügbar

Beispiele für diese Funktionalität werden bald online sein. 🧑🏻‍💻

:::

Wenn Sie die beiden Ergebnisse vergleichen, bekommen Sie einen Eindruck davon, wie sich die *Sensitivität* auf die Erreichbarkeit auswirkt.

## 5. Referenzen

Kwan, Mei-Po. 1998. “Space-Time and Integral Measures of Individual Accessibility: A Comparative Analysis Using a Point-Based Framework.” Geographical Analysis 30 (3): 191–216. [https://doi.org/10.1111/j.1538-4632.1998.tb00396.x](https://doi.org/10.1111/j.1538-4632.1998.tb00396.x).

Vale, D.S., and M. Pereira. 2017. “The Influence of the Impedance Function on Gravity-Based Pedestrian Accessibility Measures: A Comparative Analysis.” Environment and Planning B: Urban Analytics and City Science 44 (4): 740–63.  [https://doi.org/10.1177%2F0265813516641685](https://doi.org/10.1177%2F0265813516641685).

Higgins, Christopher D. 2019. “Accessibility Toolbox for R and ArcGIS.” Transport Findings, May.  [https://doi.org/10.32866/8416](https://doi.org/10.32866/8416).
