---
sidebar_position: 1
---

import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';
import thematicIcon from "/img/toolbox/data_management/join/toolbox.webp";


# Einzugsgebiet

Einzugsgebiete zeigen **wie weit Menschen innerhalb einer bestimmten Reisezeit oder Entfernung, mit einem oder mehreren Verkehrsmitteln reisen können.**

<div style={{ display: 'flex', justifyContent: 'center' }}>
<iframe width="674" height="378" src="https://www.youtube.com/embed/GA_6PbhAA6k?si=4mA2OdTPGCl7iVRi&amp;start=46" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>
</div>

## 1. Erklärung

Basierend auf festgelegten Startpunkten, maximaler Reisezeit oder Entfernung und Verkehrsmitteln **visualisieren Einzugsgebiete das Ausmaß der Erreichbarkeit anhand realer Daten.** Dies bietet Einblicke in die Qualität, Dichte und Reichweite des Verkehrsnetzes.

Das Einzugsgebiet kann mit räumlichen Datensätzen wie Bevölkerungsdaten überlagert werden, um erreichbare Einrichtungen zu bewerten und die Zugänglichkeitsabdeckung für die Bewohner zu identifizieren.
  

:::tip Tipp
Sie kennen diese Funktion möglicherweise aus unseren früheren Softwareversionen unter den Begriffen Single-Isochrone und Multi-Isochrone. Mit der Veröffentlichung von GOAT Version 2.0 haben wir diese beiden Indikatoren im gleichen Ablauf zusammengeführt und mit weiteren Berechnungsoptionen angereichert.
:::

import MapViewer from '@site/src/components/MapViewer';

:::info
Die Berechnung von Einzugsgebieten ist in bestimmten Regionen möglich.

Nach Auswahl eines <code>Routentyps</code> zeigt GOAT eine Kartenüberlagerung an, die dies anzeigt.  
Für <code>zu Fuß</code>, <code>Fahrrad</code>, <code>Pedelec</code> und <code>Auto</code> werden über 30 europäische Länder unterstützt, während Einzugsgebiete für <code>ÖV</code> für Deutschland berechnet werden können.

<div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '20px', flexWrap: "nowrap", maxWidth: '100%', padding: '0 20px' }}>
  <div style={{ flex: '1', maxWidth: 'none', minWidth: '0' }}>
    <MapViewer
        geojsonUrls={[
          "https://assets.plan4better.de/other/geofence/geofence_street.geojson"
        ]}
        styleOptions={{
          fillColor: "#808080",
          outlineColor: "#808080",
          fillOpacity: 0.8
        }}
        legendItems={[
          { label: "Abdeckung für Fußwege, Fahrrad, Pedelec und Auto", color: "#ffffff" }
        ]}
    />
  </div>
  <div style={{ flex: '1', maxWidth: 'none', minWidth: '0' }}>
    <MapViewer
        geojsonUrls={[
          "https://assets.plan4better.de/other/geofence/geofence_gtfs.geojson"
        ]}
        styleOptions={{
          fillColor: "#808080",
          outlineColor: "#808080",
          fillOpacity: 0.8
        }}
        legendItems={[
          { label: "Abdeckung für den öffentlichen Nahverkehr", color: "#ffffff" }
        ]}
    />
  </div>
</div>

<br />

Wenn Sie Analysen außerhalb dieser Regionen durchführen möchten, [kontaktieren Sie uns gerne](https://plan4better.de/en/contact/ "contact us") – wir besprechen mit Ihnen gerne weitere Möglichkeiten.
:::

## 2. Anwendungsbeispiele

- Welche Annehmlichkeiten sind von einem bestimmten Punkt aus in einem 15-minütigen Fußweg erreichbar?
- Wie viele Einwohner erreichen einen Supermarkt innerhalb von 10 Minuten mit dem Fahrrad?
- Welcher Anteil der Bevölkerung hat einen Hausarzt innerhalb von 500m Entfernung?
- Wie groß ist das Einzugsgebiet eines Arbeitsplatzes mit dem Auto im vergleich zu öffentlichen Verkehrsmitteln? Wie viele Mitarbeiter leben in diesen Einzugsgebieten?
- Wie gut sind Kindergärten derzeit über die Stadt verteilt? In welchen Bezirken gibt es Defizite in der Erreichbarkeit?


## 3. Wie benutzt man den Indikator?

<div class="step">
  <div class="step-number">1</div>
  <div class="content">Klicken Sie auf <code>Werkzeuge</code> <img src={thematicIcon} alt="toolbox" style={{width: "25px"}}/>.</div>
</div>

<div class="step">
  <div class="step-number">2</div>
  <div class="content">Unter <code>Erreichbarkeitsindikatoren</code>, klicken Sie auf <code>Einzugsgebiet</code>.</div>
</div>

### Routing


<div class="step">
  <div class="step-number">3</div>
  <div class="content">Wählen Sie den <code>Routing-Typ</code> für Ihre Einzugsgebietsberechnung.</div>
</div>


### Konfiguration

<Tabs>
  <TabItem value="walk" label="zu Fuß" default className="tabItemBox">

**Berücksichtigt alle zu Fuß zugänglichen Wege.**

  <div class="step">
    <div class="step-number">4</div>
    <div class="content">Wählen Sie, ob Sie das Einzugsgebiet basierend auf **Zeit** oder **Entfernung** berechnen möchten.</div>
  </div>

  <Tabs>
  <TabItem value="time" label="Zeit" default className="tabItemBox">

  #### Zeit

  <div class="step">
    <div class="step-number">5</div>
    <div class="content">Konfigurieren Sie <code>Reisezeitlimit</code>, <code>Reisegeschwindigkeit</code> und <code>Anzahl der Schritte</code>.</div>
  </div>

  <img src={require('/img/toolbox/accessibility_indicators/catchments/walk_config_time.png').default} alt="walking-time configurations" style={{ maxHeight: "300px", maxWidth: "300px"}}/>

:::tip Hint

Für geeignete Reisezeitgrenzen je Annehmlichkeitstyp siehe das [Location Tool](https://www.chemnitz.de/chemnitz/media/unsere-stadt/verkehr/verkehrsplanung/vep2040_standortwerkzeug.pdf) der Stadt Chemnitz.

:::
  </TabItem>
  
  <TabItem value="distance" label="Entfernung" default className="tabItemBox">

  #### Entfernung

  <div class="step">
    <div class="step-number">5</div>
    <div class="content">Konfigurieren Sie <code>Reiseentfernung</code> und <code>Anzahl der Schritte</code>.</div>
  </div>

  <img src={require('/img/toolbox/accessibility_indicators/catchments/walk_config_distance.png').default} alt="walking-distance configurations" style={{ maxHeight: "300px", maxWidth: "300px"}}/>
  
  </TabItem>
  </Tabs>

</TabItem>

<TabItem value="cycling" label="Fahrrad/Pedelec" className="tabItemBox">

**Berücksichtigt alle mit dem Fahrrad zugänglichen Wege.** Dieser Routing-Modus berücksichtigt Oberfläche, Glätte und Steigung bei der Berechnung der Erreichbarkeit. Bei Pedelecs haben Steigungen eine geringere Behinderung als bei normalen Fahrrädern.

<div class="step">
  <div class="step-number">4</div>
  <div class="content">Wählen Sie, ob Sie das Einzugsgebiet basierend auf **Zeit** oder **Entfernung** berechnen möchten.</div>
</div>

  <Tabs>
  <TabItem value="time" label="Zeit" default className="tabItemBox">

  #### Zeit

  <div class="step">
    <div class="step-number">5</div>
    <div class="content">Konfigurieren Sie <code>Reisezeitlimit</code>, <code>Reisegeschwindigkeit</code>, und <code>Anzahl der Schritte</code>.</div>
  </div>

  <img src={require('/img/toolbox/accessibility_indicators/catchments/walk_config_time.png').default} alt="walking-time configurations" style={{ maxHeight: "300px", maxWidth: "300px"}}/>

:::tip Hint

Für geeignete Reisezeitgrenzen je Annehmlichkeitstyp siehe das [Location Tool](https://www.chemnitz.de/chemnitz/media/unsere-stadt/verkehr/verkehrsplanung/vep2040_standortwerkzeug.pdf) der Stadt Chemnitz.

:::
  </TabItem>
  
  <TabItem value="distance" label="Entfernung" default className="tabItemBox">

  #### Entfernung

  <div class="step">
    <div class="step-number">5</div>
    <div class="content">Konfigurieren Sie <code>Reiseentfernung</code> und <code>Anzahl der Schritte</code>.</div>
  </div>

  <img src={require('/img/toolbox/accessibility_indicators/catchments/walk_config_distance.png').default} alt="walking-distance configurations" style={{ maxHeight: "300px", maxWidth: "300px"}}/>
  
  </TabItem>
  </Tabs>

</TabItem>

<TabItem value="car" label="Auto" className="tabItemBox">

**Berücksichtigt alle mit dem Auto zugänglichen Wege.** Dieser Routing-Modus berücksichtigt Geschwindigkeitsbegrenzungen und Einbahnstraßenbeschränkungen bei der Berechnung der Erreichbarkeit.

<div class="step">
  <div class="step-number">4</div>
  <div class="content">Wählen Sie, ob Sie das Einzugsgebiet basierend auf **Zeit** oder **Entfernung** berechnen möchten.</div>
</div>

  <Tabs>
  <TabItem value="time" label="Zeit" default className="tabItemBox">

  #### Zeit

  <div class="step">
    <div class="step-number">5</div>
    <div class="content">Konfigurieren Sie <code>Reisezeitlimit</code> und <code>Anzahl der Schritte</code>.</div>
  </div>

  <img src={require('/img/toolbox/accessibility_indicators/catchments/walk_config_time.png').default} alt="travel-time configurations" style={{ maxHeight: "300px", maxWidth: "300px"}}/>

:::tip Hint

Für geeignete Reisezeitgrenzen je Annehmlichkeitstyp siehe das [Location Tool](https://www.chemnitz.de/chemnitz/media/unsere-stadt/verkehr/verkehrsplanung/vep2040_standortwerkzeug.pdf) der Stadt Chemnitz.

:::
  </TabItem>
  
  <TabItem value="distance" label="Entfernung" default className="tabItemBox">

  #### Entfernung

  <div class="step">
    <div class="step-number">5</div>
    <div class="content">Konfigurieren Sie <code>Reiseentfernung</code> und <code>Anzahl der Schritte</code>.</div>
  </div>

  <img src={require('/img/toolbox/accessibility_indicators/catchments/walk_config_distance.png').default} alt="travel-distance configurations" style={{ maxHeight: "300px", maxWidth: "300px"}}/>
  
  </TabItem>
  </Tabs>

</TabItem>
  <TabItem value="public transport" label="Public Transport (PT)" className="tabItemBox">

**Berücksichtigt alle mit öffentlichen Verkehrsmitteln erreichbaren Orte, einschließlich intermodaler Transfers und Stationszugang.**

<div class="step">
  <div class="step-number">4</div>
  <div class="content">Wählen Sie die zu analysierenden <code>Öffentlichen Verkehrsmittel</code>: <code>Bus</code>, <code>Straßenbahn</code>, <code>Bahn</code>, <code>U-Bahn</code>, <code>Fähre</code>, <code>Seilbahn</code>, <code>Gondel</code> und/oder <code>Standseilbahn</code>.</div>
</div>

<div>
  <img src={require('/img/toolbox/accessibility_indicators/catchments/pt_type.png').default} alt="Public Transport Modes in GOAT" style={{ maxHeight: "400px", maxWidth: "400px", objectFit: "cover"}}/>
</div>

<br />

<div class="step">
  <div class="step-number">5</div>
  <div class="content"> 
  <p>
  Konfigurieren Sie die folgenden Parameter: <code>Reisezeitlimit</code>, <code>Anzahl der Schritte</code>, <code>Tag</code>, und <code>Startzeit</code> und <code>Endzeit</code>.
    </p>
  </div>
</div>

<img src={require('/img/toolbox/accessibility_indicators/catchments/pt_config.png').default} alt="Public Transport Configurations" style={{ maxHeight: "400px", maxWidth: "400px"}}/>

:::tip Hint

Für geeignete Reisezeitgrenzen je Annehmlichkeitstyp siehe das [Location Tool](https://www.chemnitz.de/chemnitz/media/unsere-stadt/verkehr/verkehrsplanung/vep2040_standortwerkzeug.pdf) der Stadt Chemnitz.

:::


  </TabItem>

</Tabs>


### Erweiterte Einstellungen

  Standardmäßig werden Einzugsgebiete als Polygone berechnet. Um dies anzupassen, verwenden Sie die erweiterten Einstellungen.

  <div class="step">
    <div class="step-number">6</div>
    <div class="content">Klicken Sie auf <code>Erweiterte Konfiguration</code> <img src={require('/img/map/styling/options_icon.png').default} alt="Options Icon" style={{ maxHeight: "25px", maxWidth: "25px", objectFit: "cover"}}/>. Hier können Sie die <code>Einzugsgebietsform</code> auswählen. Sie können zwischen <b>Polygon</b>, <b>Netzwerk</b> und <b>Rechteckiges Gitter</b> wählen.</div>
  </div>

<Tabs>
  <TabItem value="Polygon" label="Polygon" default className="tabItemBox">

- Es ist die **geometrische Darstellung** der Einzugsgebiete.
- **Leicht verständliche** Visualisierung
- **Ein Polygon pro Schritt**

<img src={require('/img/toolbox/accessibility_indicators/catchments/pt_polygon.png').default} alt="Einzugsgebiet (Polygon) ÖV in GOAT" style={{ maxHeight: "300px", maxWidth: "300px"}}/>

Sie können <code>Polygon-Differenz</code> **aktivieren**, wodurch "inkrementelle" Polygone für jeden Schritt erstellt werden. Andererseits erstellt **deaktiviert** "vollständige" Polygone einschließlich aller vorherigen Schritte.

  </TabItem>
  <TabItem value="Network" label="Network" className="tabItemBox">

- Es ist eine **Darstellung auf Straßenebene** der Einzugsgebiete.
- Ermöglicht **einfache Korrelation zu tatsächlichen Straßen** und deren Erreichbarkeit innerhalb des Einzugsgebiets.
- **Feinere Details** im Vergleich zu den anderen Einzugsgebietstypen.

<img src={require('/img/toolbox/accessibility_indicators/catchments/pt_network.png').default} alt="Einzugsgebiet (Network) ÖV in GOAT" style={{ maxHeight: "300px", maxWidth: "300px"}}/>

  </TabItem>
  <TabItem value="Rectangular Grid" label="Rectangular Grid" className="tabItemBox">

- Es ist eine **gitterzellenbasierte Darstellung** der Einzugsgebiete.
- Erscheint ähnlich wie eine „Heatmap“-Visualisierung, unterscheidet sich jedoch konzeptionell und rechnerisch (dies stellt das Abfließen von einem bestimmten Ursprung zu verschiedenen anderen Standorten dar, während Heatmaps den Zugang von verschiedenen Standorten zu einem bestimmten Ziel darstellen).

<img src={require('/img/toolbox/accessibility_indicators/catchments/pt_grid.png').default} alt="Einzugsgebiet(Gitter) ÖV in GOAT" style={{ maxHeight: "300px", maxWidth: "300px"}}/>

  </TabItem>
</Tabs>

### Starting Points

<div class="step">
  <div class="step-number">7</div>
  <div class="content">Wählen Sie die <code>Startpunkt-Methode</code>: <code>Auf Karte auswählen</code> oder <code>Aus Layer auswählen</code>.</div>
</div>

<Tabs>
  <TabItem value="Select on Map" label="Select on Map" default className="tabItemBox">

<div class="step">
  <div class="step-number">8</div>
  <div class="content">Wählen Sie <code>Auf Karte auswählen</code>. Klicken Sie auf die Karte, um Startpunkte auszuwählen. Sie können mehrere Startpunkte hinzufügen.</div>
</div>


  </TabItem>
  <TabItem value="Select From Layer" label="Select From Layer" className="tabItemBox">


 <div class="step">
  <div class="step-number">8</div>
  <div class="content">Klicken Sie auf <code>Aus Layer auswählen</code>. Wählen Sie den <code>Punkt-Layer</code>, der Ihre gewünschten Startpunkte enthält.</div>
</div>


  </TabItem>
</Tabs>


<div class="step">
  <div class="step-number">9</div>
  <div class="content">Klicken Sie auf <code>Ausführen</code>. Dies startet die Einzugsgebietsberechnung von den ausgewählten Startpunkten.</div>
</div>

:::tip Hint

Die Berechnungszeit variiert je nach Einstellungen. Überprüfen Sie die [status bar](../../workspace/home#status-bar) für den Fortschritt.

:::

### Results

Nach Abschluss der Berechnung werden die resultierenden Layer zur Karte hinzugefügt. Der **"Einzugsgebiet"** Layer enthält die berechneten Einzugsgebiete. Falls Startpunkte durch Klicken auf die Karte erstellt wurden, werden sie im **"Startpunkte"** Layer gespeichert.

Klicken Sie auf ein Einzugsgebietspolygon, um Details anzuzeigen. Das **travel_cost** Attribut zeigt Reiseentfernung oder -zeit basierend auf Ihrer Berechnungseinheit: **Zeit in Minuten** oder **Entfernung in Metern**.

<div style={{ display: 'flex', justifyContent: 'center' }}>
  <img src={require('/img/toolbox/accessibility_indicators/catchments/catchment_calculation.gif').default} alt="Einzugsgebietsberechnung Ergebnis in GOAT" style={{ maxHeight: "auto", maxWidth: "80%"}}/>
</div>

:::tip Tipp
Möchten Sie Ihre Einzugsgebiete stilisieren und schöne Karten erstellen? Siehe [Styling](../../map/layer_style/styling).
:::

## 4. Technische Details

**Einzugsgebiete sind Isolinien, die Punkte verbinden, die von Startpunkt(en) innerhalb eines Zeitintervalls (*Isochronen*) oder einer Entfernung (*Isodistanz*) erreichbar sind**. Die Berechnung verwendet die entsprechenden Verkehrsnetze für das Routing basierend auf dem gewählten Verkehrsmittel.

Einzugsgebiete werden dynamisch im Frontend aus einem Reisezeit-/Entfernungsgitter erstellt, was eine schnelle Erstellung mit verschiedenen Intervallen bei Bedarf ermöglicht.

:::tip Hinweis

Für weitere Einblicke in den Routing-Algorithmus besuchen Sie [Routing](../../category/routing).

:::

### Wissenschaftlicher Hintergrund

Aus wissenschaftlicher Sicht sind Einzugsgebiete _konturbasierte Maßnahmen_ (auch bekannt als _kumulative Gelegenheiten_). Sie werden wegen ihrer **leicht interpretierbaren Ergebnisse** geschätzt ([Geurs und van Eck 2001](#6-referenzen); [Albacete 2016](#6-referenzen)), haben jedoch den Nachteil, dass sie innerhalb des **Cut-off-Bereichs** nicht zwischen verschiedenen Reisezeiten unterscheiden ([Bertolini, le Clercq, und Kapoen 2005](#6-referenzen)), wie es bei [Heatmaps](../accessibility_indicators/closest_average.md) der Fall ist.

### Visualisierung

Die Form der Einzugsgebiete wird aus dem Routing-Gitter unter Verwendung des [Marching-Square-Konturlinien-Algorithmus](https://de.wikipedia.org/wiki/Marching_Squares "Wikipedia: Marching Squares") abgeleitet, einem Computergraphik-Algorithmus, der zweidimensionale Konturlinien aus einem rechteckigen Wertearray erzeugen kann ([de Queiroz Neto et al. 2016](#6-referenzen)). Dieser Algorithmus transformiert das Gitter von einem 2D-Array in eine Form, um es zu visualisieren oder zu analysieren. Eine Illustration der 2D-Bildverarbeitung ist in der Abbildung dargestellt.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/toolbox/accessibility_indicators/catchments/wiki.png').default} width="1000px" alt="marching square" style={{ width: "1000px", height: "400px", maxHeight: "400px", maxWidth: "400px", objectFit: "contain"}}/>
</div> 

## 5. Weiterführende Literatur

Weitere Einblicke in die Einzugsgebietsberechnung und deren wissenschaftlichen Hintergrund finden Sie in dieser [Publikation](https://doi.org/10.1016/j.jtrangeo.2021.103080).

## 6. Referenzen

Albacete, Xavier. 2016. “Evaluation and Improvements of Contour-Based Accessibility Measures.” url: https://dspace.uef.fi/bitstream/handle/123456789/16857/urn_isbn_978-952-61-2103-1.pdf?sequence=1&isAllowed=y 

Bertolini, Luca, F. le Clercq, and L. Kapoen. 2005. “Sustainable Accessibility: A Conceptual Framework to Integrate Transport and Land Use Plan-Making. Two Test-Applications in the Netherlands and a Reflection on the Way Forward.” Transport Policy 12 (3): 207–20. https://doi.org/10.1016/j.tranpol.2005.01.006.

J. F. de Queiroz Neto, E. M. d. Santos, and C. A. Vidal. “MSKDE - Using
Marching Squares to Quickly Make High Quality Crime Hotspot Maps”. en.
In: 2016 29th SIBGRAPI Conference on Graphics, Patterns and Images (SIBGRAPI).
Sao Paulo, Brazil: IEEE, Oct. 2016, pp. 305–312. isbn: 978-1-5090-3568-7. doi:
10.1109/SIBGRAPI.2016.049. url: https://ieeexplore.ieee.org/document/7813048

https://fr.wikipedia.org/wiki/Marching_squares#/media/Fichier:Marching_Squares_Isoline.svg

Majk Shkurti, "Spatio-temporal public transport accessibility analysis and benchmarking in an interactive WebGIS", Sep 2022. url: https://www.researchgate.net/publication/365790691_Spatio-temporal_public_transport_accessibility_analysis_and_benchmarking_in_an_interactive_WebGIS 

Matthew Wigginton Conway, Andrew Byrd, Marco Van Der Linden. "Evidence-Based Transit and Land Use Sketch Planning Using Interactive Accessibility Methods on Combined Schedule and Headway-Based Networks", 2017. url: https://journals.sagepub.com/doi/10.3141/2653-06

Geurs, Karst T., and Ritsema van Eck. 2001. “Accessibility Measures: Review and Applications.” RIVM Report 408505 006. url: https://rivm.openrepository.com/handle/10029/259808
