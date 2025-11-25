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
<iframe width="674" height="378" src="https://www.youtube.com/embed/azIe5etz5sM?si=MIHjuHZNlR3D6f6T&amp;start=46" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>
</div>

## 1. Erklärung

Die Heatmap zeigt ein farbkodiertes sechseckiges Raster, das **die durchschnittlichen Reisezeiten zu Zielen (Gelegenheiten) anhand realer Verkehrsnetze darstellt.** Sie können den **Routing-Typ**, den **Gelegenheits-Layer**, die **Anzahl der Ziele** und das **Reisezeitlimit** spezifizieren, um die Visualisierung zu erstellen.

Der **Gelegenheits-Layer enthält punktbasierte Zieldaten** (POIs, Haltestellen, Schulen, Einrichtungen oder benutzerdefinierte Daten), **für die Sie die Erreichbarkeit analysieren möchten**. Sie können mehrere Gelegenheits-Layer verwenden, die zu einer einheitlichen Heatmap kombiniert werden.

Die **Anzahl der Ziele setzt die Berechnung der durchschnittlichen Reisezeit auf nur die *n* nächstgelegenen Gelegenheiten**. Dies schafft eine gezieltere Erreichbarkeitsanalyse.

**Hauptunterschied:** Heatmaps zeigen den *Zugang* von vielen Ausgangspunkten zu spezifischen Zielen, während Einzugsgebiete die *Reichweite* von spezifischen Ausgangspunkten zu vielen Zielen zeigen.

import MapViewer from '@site/src/components/MapViewer'; 

:::info 

Heatmaps sind in bestimmten Regionen verfügbar. Beim Auswählen eines `Verkehrsmittels` wird auf der Karte ein **Geofence** angezeigt, um die unterstützten Regionen hervorzuheben.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', width: '100%', maxWidth: '500px', margin: '0 auto' }}>
  <div style={{ width: '100%', maxWidth: '400px' }}>
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
        style={{ width: '100%', maxWidth: '400px' }}
    />
  </div>
</div> 

Wenn Sie Analysen außerhalb dieses Geofence durchführen möchten, kontaktieren Sie uns bitte [hier](https://plan4better.de/de/contact/ "Kontaktieren Sie uns").

:::

## 2. Anwendungsbeispiele

 - Haben Bewohner in bestimmten Gebieten längere durchschnittliche Reisezeiten zu Einrichtungen als andere?

 - Wie variiert die durchschnittliche Reisezeit zu Einrichtungen zwischen verschiedenen Verkehrsmitteln?

 - Wie variiert die durchschnittliche Reisezeit zwischen verschiedenen Arten von Einrichtungen?
 
 - Wenn Standards verlangen, dass eine Mindestanzahl von Einrichtungen innerhalb einer bestimmten Reisezeit zugänglich sein muss, welche Gebiete erfüllen diese Standards?

## 3. Wie verwendet man den Indikator?

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

<TabItem value="walk" label="Walk" default className="tabItemBox">

**Berücksichtigt alle Wege, die zu Fuß zugänglich sind.** Für Heatmaps wird eine Gehgeschwindigkeit von 5 km/h angenommen.

</TabItem>
  
<TabItem value="cycling" label="Bicycle" className="tabItemBox">

**Berücksichtigt alle Wege, die mit dem Fahrrad zugänglich sind**. Dieser Routing-Modus berücksichtigt die Oberfläche, Glätte und Steigung der Straßen bei der Berechnung der Erreichbarkeit. Für Heatmaps wird eine Fahrradgeschwindigkeit von 15 km/h angenommen.

</TabItem>

<TabItem value="pedelec" label="Pedelec" className="tabItemBox">

**Berücksichtigt alle Wege, die mit dem Pedelec zugänglich sind**. Dieser Routing-Modus berücksichtigt die Oberfläche und Glätte der Straßen bei der Berechnung der Erreichbarkeit. Im Gegensatz zu normalen Fahrrädern haben Steigungen bei Pedelecs eine geringere Behinderung. Für Heatmaps wird eine Pedelec-Geschwindigkeit von 23 km/h angenommen.

</TabItem>

<TabItem value="car" label="Car" className="tabItemBox">

**Berücksichtigt alle Wege, die mit dem Auto zugänglich sind**. Dieser Routing-Modus berücksichtigt Geschwindigkeitsbegrenzungen und Einbahnstraßenbeschränkungen bei der Berechnung der Erreichbarkeit.

</TabItem>

</Tabs>

### Gelegenheiten

<div class="step">
  <div class="step-number">4</div>
  <div class="content">Wählen Sie Ihre <code>Gelegenheitsdaten</code> aus dem Dropdown-Menü aus. Dies kann ein zuvor ersteller Layer sein, die punktbasierte Daten enthält.</div>
</div>

<div class="step">
  <div class="step-number">5</div>
  <div class="content">Wählen Sie ein <code>Reisezeitlimit</code> für Ihre Heatmap. Dies wird im Zusammenhang mit Ihrem zuvor ausgewählten <i>Verkehrsmittel</i> verwendet.</div>
</div>

:::tip Hint

Brauchen Sie Hilfe bei der Wahl eines geeigneten Reisezeitlimits für verschiedene gängige Einrichtungen? Das ["Standort-Werkzeug"](https://www.chemnitz.de/chemnitz/media/unsere-stadt/verkehr/verkehrsplanung/vep2040_standortwerkzeug.pdf) der Stadt Chemnitz kann hilfreiche Leitlinien bieten.

:::

<div class="step">
  <div class="step-number">6</div>
  <div class="content">Geben Sie die <code>Anzahl der Ziele</code> an, die beim Berechnen der durchschnittlichen Reisezeit berücksichtigt werden sollen.</div>
</div>

<div class="step">
  <div class="step-number">7</div>
  <div class="content">Klicken Sie auf <code>Ausführen</code>, um die Berechnung der Heatmap zu beginnen.</div>
</div>

### Ergebnisse

Sobald die Berechnung abgeschlossen ist, wird ein Ergebnislayer zur Karte hinzugefügt. **Durch Klicken auf eine der sechseckigen Zellen der Heatmap wird der berechnete Durchschnittswert der Reisezeit für diese Zelle angezeigt**.


<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/toolbox/accessibility_indicators/heatmaps/closest_average_based/clst-avg-calculation.gif').default} alt="Heatmap Durchschnitt Reisezeit Berechnung" style={{width: "auto", height: "400px", objectFit: "cover"}}/>
</div>

## 5. Technische Details

### Berechnung

**Nachdem alle Gelegenheits-Layer kombiniert wurden** (z.B. Schulen, Geschäfte oder Parks), erstellt das Tool **ein Gitter aus sechseckigen Zellen um das Gebiet**. **Es werden nur Zellen einbezogen, in denen mindestens eine Gelegenheit basierend auf dem gewählten** **Verkehrsmittel** (z.B. zu Fuß, Fahrrad) und **Reisezeitlimit** (z.B. 15 Minuten) erreichbar ist.

Dann wird für jede Zelle die durchschnittliche Reisezeit zu den **nächsten n Zielen** (wie in den Einstellungen festgelegt) berechnet.

Die Formel für die durchschnittliche Reisezeit lautet:

<MathJax.Provider>
  <div style={{ marginTop: '20px', fontSize: '24px' }}>
    <MathJax.Node formula={"\\overline{t}_i = \\frac{\\sum_{j=1}^{n} t_{ij}}{n}"} />
  </div>
</MathJax.Provider>

Für jede Zelle (**i**) summiert das Tool die Reisezeiten (**tij**) zu allen erreichbaren Gelegenheiten (**j**), bis zu **n** davon, und teilt durch **n**, um die durchschnittliche Reisezeit zu erhalten.

### Klassifizierung
In order to classify the accessibility levels that were computed for each grid cell, a classification based on quantiles is used by default. However, various other classification methods may be used instead. Read more in the **[Datenklassifizierungsmethoden](../../map/layer_style/attribute_based_styling#datenklassifizierungsmethoden)** section of the *Attributbasiertes Styling* page.

### Visualisierung

Heatmaps in GOAT nutzen die **[Uber H3 Gitter-basierte](../../further_reading/glossary#h3-gitter)** Lösung für effiziente Berechnungen und eine leicht verständliche Visualisierung. Hinter den Kulissen nutzt eine vorberechnete Reisezeitmatrix für jedes *Verkehrsmittel* diese Lösung und wird in Echtzeit abgefragt und weiterverarbeitet, um die Erreichbarkeit zu berechnen und eine endgültige Heatmap zu erstellen.

Die Auflösung und die Dimensionen des verwendeten sechseckigen Gitters hängen vom gewählten *Verkehrsmittel* ab:

<div style={{ marginLeft: '20px' }}>

<Tabs>

<TabItem value="walk" label="Zu Fuß" default className="tabItemBox">

<li parentName="ul">{`Auflösung: 10`}</li>
<li parentName="ul">{`Durchschnittliche Sechseckfläche: 11285.6 m²`}</li>
<li parentName="ul">{`Durchschnittliche Kantenlänge des Sechsecks: 65,9 m`}</li>
</TabItem>
  
<TabItem value="cycling" label="Fahrrad" className="tabItemBox">

<li parentName="ul">{`Auflösung: 9`}</li>
<li parentName="ul">{`Durchschnittliche Sechseckfläche: 78999.4 m²`}</li>
<li parentName="ul">{`Durchschnittliche Kantenlänge des Sechsecks: 174,4 m`}</li>
</TabItem>

<TabItem value="pedelec" label="Pedelec" className="tabItemBox">

<li parentName="ul">{`Auflösung: 9`}</li>
<li parentName="ul">{`Durchschnittliche Sechseckfläche: 78999.4 m²`}</li>
<li parentName="ul">{`Durchschnittliche Kantenlänge des Sechsecks: 174,4 m`}</li> 
</TabItem>

<TabItem value="car" label="Auto" className="tabItemBox">

<li parentName="ul">{`Auflösung: 8`}</li>
<li parentName="ul">{`Durchschnittliche Sechseckfläche: 552995.7 m²`}</li>
<li parentName="ul">{`Durchschnittliche Kantenlänge des Sechsecks: 461,4 m`}</li>

</TabItem>

</Tabs>
</div>

:::tip Tipp

Für weitere Einblicke in den Routing-Algorithmus besuchen Sie [Routing](../../category/routing). Außerdem können Sie diese [Publikation](https://doi.org/10.1016/j.jtrangeo.2021.103080) einsehen.

:::

### Beispiel für die Berechnung

Die folgenden Beispiele illustrieren die Berechnung einer Heatmap Durchschnitt Reisezeit für die gleichen Gelegenheiten, mit einem variierenden Wert für die `Anzahl der Ziele`.

<div style={{ display: 'flex', justifyContent: 'center' }}>
<img src={require('/img/toolbox/accessibility_indicators/heatmaps/closest_average_based/cls-avg-destinations.png').default} alt="Heatmap Durchschnitt Reisezeit für verschiedene Ziele" style={{ maxHeight: "auto", maxWidth: "80%"}}/>
</div>

<p></p>

Im ersten Beispiel wird die durchschnittliche Reisezeit nur für das nächstgelegene Ziel berechnet, während im zweiten Beispiel die 5 nächstgelegenen Ziele berücksichtigt werden.
