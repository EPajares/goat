---
sidebar_position: 3
---

import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';
import thematicIcon from "/img/toolbox/data_management/join/toolbox.webp";
import MathJax from 'react-mathjax';

# Heatmap - Durchschnitt Reisezeit

Der Heatmap - Durchschnitt Reisezeit Indikator **erstellt eine farbkodierte Karte zur Visualisierung der durchschnittlichen Reisezeit zu Punkten, wie POIs, aus umliegenden Gebieten.**

<div style={{ display: 'flex', justifyContent: 'center' }}>
<iframe width="674" height="378" src="https://www.youtube.com/embed/-nBXd-LAqZA?si=Ijls6J_GlJB8dav4" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>
</div>

## 1. Erklärung

Die Heatmap zeigt ein farbkodiertes sechseckiges Raster, das **die durchschnittlichen Reisezeiten zu Zielen (Gelegenheiten) anhand realer Verkehrsnetze darstellt.** Sie können den **Routing-Typ**, den **Gelegenheits-Layer**, die **Anzahl der Ziele** und das **Reisezeitlimit** spezifizieren, um die Visualisierung zu erstellen.

Der **Gelegenheits-Layer** enthält punktbasierte Zieldaten (POIs, Haltestellen, Schulen, Einrichtungen oder benutzerdefinierte Daten), für die Sie die Erreichbarkeit analysieren möchten. Sie können mehrere Gelegenheits-Layer verwenden, die zu einer einheitlichen Heatmap kombiniert werden.

Die **Anzahl der Ziele** setzt die Berechnung der durchschnittlichen Reisezeit auf nur die *n* nächstgelegenen Gelegenheiten. Dies schafft eine gezieltere Erreichbarkeitsanalyse.

**Hauptunterschied:** Heatmaps zeigen den *Zugang* von vielen Ausgangspunkten zu spezifischen Zielen, während Einzugsgebiete die *Reichweite* von spezifischen Ausgangspunkten zu vielen Zielen zeigen.

import MapViewer from '@site/src/components/MapViewer'; 

:::info 

Heatmaps sind in bestimmten Regionen verfügbar. Beim Auswählen eines `Verkehrsmittels` wird auf der Karte ein **Geofence** angezeigt, um die unterstützten Regionen hervorzuheben.

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
        { label: "Heatmap-Abdeckung der Durchschnittsreisezeit", color: "#ffffff" }
      ]}
  />

</div> 

Wenn Sie Analysen außerhalb dieses Geofence durchführen möchten, kontaktieren Sie uns bitte [hier](https://plan4better.de/de/contact/ "Kontaktieren Sie uns").

:::

## 2. Video-Tutorial

<div style={{width:'100%',height:'0px',position:'relative',paddingBottom:'56.250%'}}>
  <iframe src="https://streamable.com/e/3ajz1b?autoplay=1&nocontrols=1" frameborder="0" width="674" height="378" allowfullscreen allow="autoplay" style={{width:'100%',height:'100%',position:'absolute',left:'0px',top:'0px',overflow:'hidden'}}></iframe>
</div>

## 3. Anwendungsbeispiele

- **Gleichmäßige Verteilung der Erreichbarkeit**: Haben Bewohner in bestimmten Gebieten längere durchschnittliche Reisezeiten zu Einrichtungen als andere?
- **Nachbarschaftliche Unterschiede**: Gibt es einen signifikanten Unterschied in den durchschnittlichen Reisezeiten zu Einrichtungen zwischen verschiedenen Vierteln?
- **Verkehrsmittelbewertung**: Wie variieren die durchschnittlichen Reisezeiten zu Einrichtungen je nach Verkehrsmittel?
- **Einrichtungsarten-Vergleich**: Wie variieren die durchschnittlichen Reisezeiten zu verschiedenen Arten von Einrichtungen?
- **Infrastruktur-Optimierung**: Gibt es Gebiete mit hohen durchschnittlichen Reisezeiten zu Einrichtungen, die von einer verbesserten Verkehrsinfrastruktur profitieren könnten?
- **Standards-Compliance**: Wenn Standards verlangen, dass eine Mindestanzahl von Einrichtungen innerhalb einer bestimmten Reisezeit zugänglich sein muss, welche Gebiete erfüllen diese Standards?

## 4. Wie verwendet man den Indikator?

<div class="step">
  <div class="step-number">1</div>
  <div class="content">Klicken Sie auf <code>Werkzeuge</code> <img src={thematicIcon} alt="toolbox" style={{width: "25px"}}/>.</div>
</div>

<div class="step">
  <div class="step-number">2</div>
  <div class="content">Unter <code>Erreichbarkeitsindikatoren</code> klicken Sie auf <code>Heatmap Durchschnitt Reisezeit</code>.</div>
</div>

### Verkehrsmittel

<div class="step">
  <div class="step-number">3</div>
  <div class="content">Wählen Sie ein <code>Verkehrsmittel</code> welches Sie für die Heatmap anwenden möchten.</div>
</div>

<Tabs>

<TabItem value="zu Fuß" label="Zu Fuß" default className="tabItemBox">

##### Zu Fuß

Berücksichtigt alle Wege, die zu Fuß zugänglich sind. Für Heatmaps wird eine Gehgeschwindigkeit von 5 km/h angenommen.

:::tip Tipp

Für weitere Einblicke in den Routing-Algorithmus, besuchen Sie [Verkehrsmittel/Zu Fuß](../../routing/walking).

:::

</TabItem>
  
<TabItem value="Fahrrad" label="Fahrrad" className="tabItemBox">

##### Fahrrad

Berücksichtigt alle Wege, die mit dem Fahrrad zugänglich sind. Dieser Routing-Modus berücksichtigt die Oberfläche, Glätte und Steigung der Straßen bei der Berechnung der Erreichbarkeit. Für Heatmaps wird eine Fahrradgeschwindigkeit von 15 km/h angenommen.

:::tip Tipp

Für weitere Einblicke in den Routing-Algorithmus, besuchen Sie [Verkehrsmittel/Fahrrad](../../routing/bicycle). Außerdem können Sie diese [Publikation](https://doi.org/10.1016/j.jtrangeo.2021.103080) lesen.

:::

</TabItem>

<TabItem value="pedelec" label="Pedelec" className="tabItemBox">

##### Pedelec

Berücksichtigt alle Wege, die mit dem Pedelec zugänglich sind. Dieser Routing-Modus berücksichtigt die Oberfläche und Glätte der Straßen bei der Berechnung der Erreichbarkeit. Für Heatmaps wird eine Pedelec-Geschwindigkeit von 23 km/h angenommen.

:::tip Tipp

Für weitere Einblicke in den Routing-Algorithmus, besuchen Sie [Verkehrsmittel/Fahrrad](../../routing/bicycle). Außerdem können Sie diese [Publikation](https://doi.org/10.1016/j.jtrangeo.2021.103080) lesen.

:::

</TabItem>

<TabItem value="Auto" label="Auto" className="tabItemBox">

##### Auto

Berücksichtigt alle Wege, die mit dem Auto zugänglich sind. Dieser Routing-Modus berücksichtigt Geschwindigkeitsbegrenzungen und Einbahnstraßenbeschränkungen bei der Berechnung der Erreichbarkeit.

:::tip Tipp

Für weitere Einblicke in den Routing-Algorithmus, besuchen Sie [Verkehrsmittel/Auto](../../routing/car).

:::

</TabItem>

</Tabs>

### Gelegenheiten

Gelegenheiten sind im Wesentlichen punktbasierte Daten (wie [POI](../../further_reading/glossary#point-of-interest-poi "Was ist ein POI?")), für die Sie eine Heatmap berechnen möchten. Dies sind die "Ziele" (wie Transitstationen, Schulen, andere Einrichtungen oder Ihre eigenen benutzerdefinierten punktbasierten Daten), während umliegende Gebiete "Quellen" sind, für die ein Erreichbarkeitswert berechnet und visualisiert wird.

Zusätzlich können Sie über die Schaltfläche `+ Gelegenheit hinzufügen` am unteren Rand des Drawers weitere Opportunities erstellen. Alle Gelegenheits-Layer werden kombiniert, um eine einheitliche Heatmap zu erzeugen.

<div class="step">
  <div class="step-number">4</div>
  <div class="content">Wählen Sie Ihre <code>Gelegenheitsdaten</code> aus dem Dropdown-Menü aus. Dies kann ein zuvor ersteller Layer sein, die punktbasierte Daten enthält.</div>
</div>

<div class="step">
  <div class="step-number">5</div>
  <div class="content">Wählen Sie ein <code>Reisezeitlimit</code> für Ihre Heatmap. Dies wird im Zusammenhang mit Ihrem zuvor ausgewählten <i>Verkehrsmittel</i> verwendet.</div>
</div>

:::tip Tipp

Brauchen Sie Hilfe bei der Wahl eines geeigneten Reisezeitlimits für verschiedene gängige Einrichtungen? Das ["Standort-Werkzeug"](https://www.chemnitz.de/chemnitz/media/unsere-stadt/verkehr/verkehrsplanung/vep2040_standortwerkzeug.pdf) der Stadt Chemnitz kann hilfreiche Leitlinien bieten.

:::

<div class="step">
  <div class="step-number">6</div>
  <div class="content">Geben Sie die <code>Anzahl der Ziele</code> an, die beim Berechnen der durchschnittlichen Reisezeit berücksichtigt werden sollen.</div>
</div>

:::tip Tipp

Da der Parameter *Anzahl der Ziele* einmal pro Gelegenheits-Layer angegeben wird, haben Sie die Flexibilität, für jeden Gelegenheits-Layer unterschiedliche Werte anzugeben. Dies kann nützlich sein, wenn verschiedene Arten von Einrichtungen unterschiedliche Erreichbarkeitsstandards haben.

:::

<div class="step">
  <div class="step-number">7</div>
  <div class="content">Klicken Sie auf <code>Ausführen</code>, um die Berechnung der Heatmap zu beginnen.</div>
</div>

:::tip Tipp

Je nach Konfiguration kann die Berechnung einige Minuten dauern. Die [Statusleiste](../../workspace/home#statusleiste) zeigt den aktuellen Fortschritt an.

:::

### Ergebnisse

<div class="step">
  <div class="step-number">8</div>
  <div class="content">Sobald die Berechnung abgeschlossen ist, wird ein Ergebnislayer zur Karte hinzugefügt. Dieser Layer mit dem Namen <i>Heatmap Durchschnitt Reisezeit</i> wird Ihre farblich gekennzeichnete Heatmap enthalten.
  <p></p>
  Durch Klicken auf eine der sechseckigen Zellen der Heatmap wird der berechnete Durchschnittswert der Reisezeit für diese Zelle angezeigt.</div>
</div>

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/toolbox/accessibility_indicators/heatmaps/closest_average_based/clst-avg-calculation.gif').default} alt="Heatmap Durchschnitt Reisezeit Berechnung" style={{width: "auto", height: "400px", objectFit: "cover"}}/>
</div>

:::tip Tipp

Möchten Sie Ihre Heatmaps gestalten und ansprechende Karten erstellen? Infos hierzu finden Sie unter [Layer Design](../../map/layer_style/styling).

:::

## 5. Technische Details

### Berechnung

Sobald alle eingegebenen Gelegenheits-Layer kombiniert sind, wird ein Gitter aus umliegenden sechseckigen Zellen identifiziert. Dies geschieht durch die Berücksichtigung von Zellen, in denen mindestens eine Gelegenheit erreichbar ist, unter Berücksichtigung des spezifizierten `Verkehrsmittels` und `Reisezeitlimits`. Anschließend wird die durchschnittliche Reisezeit für jede Zelle innerhalb dieses Gitters berechnet, wobei die nächstgelegenen *n* Gelegenheiten, wie in dem Gelegenheits-Layer angegeben, berücksichtigt werden.

Formel für die durchschnittliche Fahrtzeit:

<MathJax.Provider>
  <div style={{ marginTop: '20px', fontSize: '24px' }}>
    <MathJax.Node formula={"\\overline{t}_i = \\frac{\\sum_{j=1}^{n} t_{ij}}{n}"} />
  </div>
</MathJax.Provider>

wobei die durchschnittliche Reisezeit für Zelle **i** die Summe von bis zu **n** Reisezeiten von Zelle **i** zu Möglichkeit **j** (**tij**) geteilt durch die Anzahl der Möglichkeiten **n** ist, die kleiner sein muss als der angegebene Parameter 'Anzahl der Ziele'.

### Klassifizierung
Zur Klassifizierung der Erreichbarkeitsstufen, die für jede Rasterzelle berechnet wurden (für die farbige Visualisierung), wird standardmäßig eine Klassifizierung auf Basis von Quantilen verwendet. Es können jedoch auch verschiedene andere Klassifizierungsmethoden verwendet werden. Weitere Informationen finden Sie im Abschnitt **[Datenklassifizierungsmethoden](../../map/layer_style/attribute_based_styling#datenklassifizierungsmethoden)** auf der Seite *attributbasiertes Styling*.

### Visualisierung 

Heatmaps in GOAT nutzen die **[Uber H3 auf Gitter basierende](../../further_reading/glossary#h3-gitter)** Lösung für effiziente Berechnungen und leicht verständliche Visualisierung. Hinter den Kulissen nutzt eine vorberechnete Reisezeitmatrix für jedes *Verkehrsmittel* diese Lösung und wird in Echtzeit abgefragt und weiterverarbeitet, um die Erreichbarkeit zu berechnen und eine endgültige Heatmap zu erstellen.

Die Auflösung und die Abmessungen des verwendeten sechseckigen Gitters hängen vom gewählten *Verkehrsmittel* ab:

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

### Berechnungsbeispiel

Die folgenden Beispiele veranschaulichen die Berechnung einer auf dem nächstgelegenen Durchschnitt basierenden Heatmap für dieselben Opportunities mit einem variierenden Wert für die „Anzahl der Ziele“.

![Closest Average Heatmaps for different destinations](/img/toolbox/accessibility_indicators/heatmaps/closest_average_based/cls-avg-destinations.png "Closest Average Heatmaps for different destinations")

Im ersten Beispiel wird die durchschnittliche Reisezeit nur für das nächstgelegene Ziel berechnet, während im zweiten Beispiel die 5 nächstgelegenen Ziele berücksichtigt werden.
