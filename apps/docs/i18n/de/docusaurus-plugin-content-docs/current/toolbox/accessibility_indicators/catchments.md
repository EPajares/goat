---
sidebar_position: 1
---

import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';
import thematicIcon from "/img/toolbox/data_management/join/toolbox.webp";


# Einzugsgebiet

**Einzugsgebiete** zeigen, wie weit Menschen innerhalb einer bestimmten Reisezeit oder Entfernung mit einem oder mehreren Verkehrsmitteln reisen können.

<iframe width="100%" height="500" src="https://www.youtube.com/embed/9ma4f0qpq-8?si=TJwFeviuxpEsFy_T" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>

## 1. Erklärung

Ausgehend von den angegebenen Startpunkten, der maximalen Reisezeit oder Entfernung und den Verkehrsmitteln visualisieren **Einzugsgebiete** das Ausmaß der Erreichbarkeit. Dies wird anhand von **realen Daten** berechnet und liefert nützliche Einblicke in die Qualität, Dichte und Reichweite des Verkehrsnetzes einer Region.

Darüber hinaus kann das Einzugsgebiet mit räumlichen Datensätzen wie Bevölkerungs- und POI-Daten überlagert werden. Dies ermöglicht beispielsweise die Bewertung, wie viele POIs von einem bestimmten Standort aus erreichbar sind und damit festzustellen, welcher Anteil der Einwohner eine gute Erreichbarkeit zu wichtigen Annehmlichkeiten innerhalb einer bestimmten Reisezeit hat.

![Catchment Area in GOAT](/img/toolbox/accessibility_indicators/catchments/catchment_sample.png "Catchment Area in GOAT")
  

:::tip Tipp
Sie kennen diese Funktion möglicherweise aus unseren früheren Softwareversionen unter den Begriffen Single-Isochrone und Multi-Isochrone. Mit der Veröffentlichung von GOAT Version 2.0 haben wir diese beiden Indikatoren im gleichen Ablauf zusammengeführt und mit weiteren Berechnungsoptionen angereichert.
:::

import MapViewer from '@site/src/components/MapViewer';

:::info
Die Berechnung von Einzugsgebieten ist in bestimmten Regionen möglich.

Nach Auswahl eines <code>Routentyps</code> zeigt GOAT eine Kartenüberlagerung an, die dies anzeigt.  
Für <code>Fußweg</code>, <code>Fahrrad</code>, <code>Pedelec</code> und <code>Auto</code> werden über 30 europäische Länder unterstützt, während Einzugsgebiete für <code>Öffentlichen Verkehr</code> für Deutschland berechnet werden können.

<div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '20px', flexWrap: "wrap" }}>
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
  <div class="content">Klicken Sie auf <code>Werkzeuge</code> <img src={thematicIcon} alt="toolbox" style={{width: "25px"}}/>. </div>
</div>

<div class="step">
  <div class="step-number">2</div>
  <div class="content">Unter dem <code>Erreichbarkeitsindikatoren</code> Menü, wählen Sie<code>Einzugsgebiet</code>.</div>
</div>

### Routing


<div class="step">
  <div class="step-number">3</div>
  <div class="content">Wählen Sie das <code>Verkehrsmittel</code> für das Sie ein Einzugsgebiet berechnen möchten</div>
</div>


### Konfiguration

<Tabs>
  <TabItem value="zu Fuß" label="zu Fuß" default className="tabItemBox">

#### zu Fuß

Berücksichtigt alle zu Fuß erreichbaren Wege.

:::tip Tipp

Für weitere Einblicke in den Routing-Algorithmus besuchen Sie  [Verkehrsmittel/Zu Fuß](../../routing/walking).

:::

<div class="step">
  <div class="step-number">4</div>
  <div class="content">Wählen Sie, ob Sie das Einzugsgebiet basierend auf <b>Zeit</b> oder <b>Entfernung </b>berechnen möchten.</div>
</div>



<Tabs>
  <TabItem value="Zeit" label="Zeit" default className="tabItemBox">

#### Zeit

<div class="step">
  <div class="step-number">5</div>
  <div class="content">Legen Sie die Konfigurationen für<code>Reisezeitlimit</code>, <code>Reisegeschwindigkeit</code>, und <code> Anzahl der Schritte </code>fest.</div>
</div>

<img src={require('/img/toolbox/accessibility_indicators/catchments/walk_config_time.png').default} alt="Konfigurationen für Reisezeit zu Fuß" style={{ maxHeight: "300px", maxWidth: "300px"}}/>

:::tip Tipp

Für die Definition, welche Reisezeitlimits für welche Annehmlichkeit geeignet sind, bietet das ["Standort-Werkzeug"](https://www.chemnitz.de/chemnitz/media/unsere-stadt/verkehr/verkehrsplanung/vep2040_standortwerkzeug.pdf) der Stadt Chemnitz hilfreiche Orientierung.

:::

#### Erweiterte Konfigurationen

Standardmäßig werden die Einzugsgebiete in Polygonform berechnet. Falls Sie dies anpassen möchten, finden Sie weitere Optionen in den erweiterten Konfigurationen.

<div class="step">
  <div class="step-number">6</div>
  <div class="content">Klicken Sie auf <b>Erweiterte Einstellungen</b> <img src={require('/img/map/styling/options_icon.png').default} alt="Options Icon" style={{ maxHeight: "25px", maxWidth: "25px", objectFit: "cover"}}/>. Hier können Sie die <code> Form des Einzugsgebiets</code>wählen. Die Auswahlmöglichkeiten sind <b> Polygon</b>, <b>Netzwerk</b> und <b>Sechseckiges Gitter</b>.</div>
</div>

  </TabItem>
  <TabItem value="Entfernung" label="Entfernung" default className="tabItemBox">

#### ENtfernung

<div class="step">
  <div class="step-number">5</div>
  <div class="content">Legen Sie die Konfigurationen für <code>Reiseentfernung</code> und <code>Anzahl der Schritte</code> fest.</div>
</div>

<img src={require('/img/toolbox/accessibility_indicators/catchments/walk_config_distance.png').default} alt="Konfigurationen für Reiseentfernung zu Fuß" style={{ maxHeight: "300px", maxWidth: "300px"}}/>

:::tip Tipp

Für die Definition, welche Reiseentfernungen für welche Annehmlichkeit geeignet sind, bietet das ["Standort-Werkzeug"](https://www.chemnitz.de/chemnitz/media/unsere-stadt/verkehr/verkehrsplanung/vep2040_standortwerkzeug.pdf) der Stadt Chemnitz hilfreiche Orientierung.

:::


#### Erweiterte Konfigurationen

Standardmäßig werden die Einzugsgebiete in Polygonform berechnet. Falls Sie dies anpassen möchten, finden Sie weitere Optionen in den erweiterten Konfigurationen.

<div class="step">
  <div class="step-number">6</div>
  <div class="content">Klicken Sie auf <b>Erweiterte Einstellungen</b> <img src={require('/img/map/styling/options_icon.png').default} alt="Options Icon" style={{ maxHeight: "25px", maxWidth: "25px", objectFit: "cover"}}/>. Hier können Sie die <code> Form des Einzugsgebiets</code>auswählen. Die Möglichkeiten sind <b> Polygon</b>, <b>Netzwerk</b> und <b>Sechseckiges Gitter</b>.</div>
</div>

  </TabItem>

</Tabs>

  </TabItem>
  <TabItem value="Fahrrad" label="Fahrrad/Pedelec" className="tabItemBox">

    
#### Fahrrad/Pedelec

Berücksichtigt alle mit dem Fahrrad erreichbaren Wege. Dieser Routentyp berücksichtigt die Oberfläche, Glätte und Steigung der Straßen bei der Berechnung der Erreichbarkeit. Für Pedelec werden Steigungen mit einer geringeren Impedanz als für Standardfahrräder berücksichtigt.

:::tip Tipp

Für weitere Einblicke in den Routing-Algorithmus besuchen Sie [Verkehrsmittel/Fahrrad](../../routing/bicycle). Zusätzlich können Sie diese [Richtlinie](https://doi.org/10.1016/j.jtrangeo.2021.103080) verwenden.

:::

<div class="step">
  <div class="step-number">4</div>
  <div class="content">Wählen Sie, ob Sie das Einzugsgebiet basierend auf <b>Zeit</b> or <b>Entfernung </b>berechnen möchten.</div>
</div>

<Tabs>
  <TabItem value="Zeit" label="Zeit" default className="tabItemBox">

#### Zeit

<div class="step">
  <div class="step-number">5</div>
  <div class="content">Legen Sie die Konfigurationen für<code>Reisezeitlimit</code>, <code>Reisegeschwindigkeit</code>, und <code> Anzahl der Schritte</code> fest.</div>
</div>

<img src={require('/img/toolbox/accessibility_indicators/catchments/walk_config_time.png').default} alt="Konfigurationen für Reisezeit mit dem Fahrrad" style={{ maxHeight: "300px", maxWidth: "300px"}}/>

:::tip Tipp

Für die Definition, welche Reisezeitlimits für welche Annehmlichkeit geeignet sind, bietet das ["Standort-Werkzeug"](https://www.chemnitz.de/chemnitz/media/unsere-stadt/verkehr/verkehrsplanung/vep2040_standortwerkzeug.pdf) der Stadt Chemnitz hilfreiche Orientierung.

:::


#### Erweiterte Konfigurationen

Standardmäßig werden die Einzugsgebiete in Polygonform berechnet. Falls Sie dies anpassen möchten, finden Sie weitere Optionen in den erweiterten Konfigurationen.

<div class="step">
  <div class="step-number">6</div>
  <div class="content">Klicken Sie auf <b>Erweiterte Einstellungen</b> <img src={require('/img/map/styling/options_icon.png').default} alt="Options Icon" style={{ maxHeight: "25px", maxWidth: "25px", objectFit: "cover"}}/>. Hier können Sie die<code> Form des Einzugsgebiets</code>festlegen. Die Auswahlmöglichkeiten sind <b> Polygon</b>, <b>Netzwerk</b> und <b>Sechseckiges Gitter</b>.</div>
</div>

  </TabItem>
  <TabItem value="Entfernung" label="Entfernung" default className="tabItemBox">

#### Entfernung

<div class="step">
  <div class="step-number">5</div>
  <div class="content">Legen Sie die Konfigurationen für<code>Reiseentfernung</code> and <code> Anzahl der Schritte</code>fest.</div>
</div>

<img src={require('/img/toolbox/accessibility_indicators/catchments/walk_config_distance.png').default} alt="walking-distance configurations" style={{ maxHeight: "300px", maxWidth: "300px"}}/>

:::tip Tipp

Für die Definition, welche Reiseentfernungen für welche Annehmlichkeit geeignet sind, bietet das  ["Standort-Werkzeug"](https://www.chemnitz.de/chemnitz/media/unsere-stadt/verkehr/verkehrsplanung/vep2040_standortwerkzeug.pdf) der Stadt Chemnitz hilfreiche Orientierung.

:::


#### Erweiterte Konfigurationen

Standardmäßig werden die Einzugsgebiete in Polygonform berechnet. Falls Sie dies anpassen möchten, finden Sie weitere Optionen in den erweiterten Konfigurationen.

<div class="step">
  <div class="step-number">6</div>
  <div class="content">Klicken Sie auf<b>Erweiterte Einstellungen</b> <img src={require('/img/map/styling/options_icon.png').default} alt="Options Icon" style={{ maxHeight: "25px", maxWidth: "25px", objectFit: "cover"}}/>. Hier können Sie die <code>Form des Einzugsgebiets</code>festlegen. Die Auswahlmöglichkeien sind <b> Polygon</b>, <b>Netzwerk</b> und <b>Sechseckiges Gitter</b>.</div>
</div>

  </TabItem>

</Tabs>


  </TabItem>

  <TabItem value="Auto" label="Auto" className="tabItemBox">

#### Auto

Berücksichtigt alle mit dem Auto erreichbaren Wege.

:::tip Tipp

Für weitere Einblicke in den Routing-Algorithmus besuchen Sie [Verkehrsmittel/Auto](../../routing/car).

:::

<div class="step">
  <div class="step-number">4</div>
  <div class="content">Wählen Sie, ob Sie das Einzugsgebiet basierend auf <b>Zeit</b> oder <b>Entfernung</b> berechnen möchten.</div>
</div>

<Tabs>
  <TabItem value="Zeit" label="Zeit" default className="tabItemBox">

#### Zeit

<div class="step">
  <div class="step-number">5</div>
  <div class="content">Legen Sie die Konfigurationen für<code>Reisegeschwindigkeit</code> und <code> Anzahl der Schritte</code>fest.</div>
</div>

<img src={require('/img/toolbox/accessibility_indicators/catchments/walk_config_time.png').default} alt="Konfigurationen für Reisezeit mit dem Auto" style={{ maxHeight: "300px", maxWidth: "300px"}}/>


#### Erweiterte Konfigurationen

Standardmäßig werden die Einzugsgebiete in Polygonform berechnet. Falls Sie dies anpassen möchten, finden Sie weitere Optionen in den erweiterten Konfigurationen. 

<div class="step">
  <div class="step-number">6</div>
  <div class="content">Klicken Sie auf <b>Erweiterte Einstellungen</b> <img src={require('/img/map/styling/options_icon.png').default} alt="Options Icon" style={{ maxHeight: "25px", maxWidth: "25px", objectFit: "cover"}}/>. Hier können Sie die<code> Form des Einzugsgebiets</code>bestimmen. Die Auswahlmöglichkeiten sind <b>Polygon</b>, <b>Netzwerk</b> und <b>Sechseckiges Gitter</b>.</div>
</div>

  </TabItem>
  <TabItem value="Entfernung" label="Entfernung" default className="tabItemBox">

#### Entfernung

<div class="step">
  <div class="step-number">5</div>
  <div class="content">Legen Sie die Konfigurationen für<code>Reiseentfernung</code> und <code> Anzahl der Schritte</code>fest.</div>
</div>

<img src={require('/img/toolbox/accessibility_indicators/catchments/walk_config_distance.png').default} alt="Konfigurationen für Reiseentfernung mit dem Auto" style={{ maxHeight: "300px", maxWidth: "300px"}}/>

#### Erweiterte Konfigurationen

Standardmäßig werden die Einzugsgebiete in Polygonform berechnet. Falls Sie dies anpassen möchten, finden Sie weitere Optionen in den erweiterten Konfigurationen. 

<div class="step">
  <div class="step-number">6</div>
  <div class="content">Klicken Sie auf <b>Erweiterte Einstellungen</b> <img src={require('/img/map/styling/options_icon.png').default} alt="Options Icon" style={{ maxHeight: "25px", maxWidth: "25px", objectFit: "cover"}}/>. Hier können Sie die<code> Form des Einzugsgebiets</code>bestimmen. Die Auswahlmöglichkeiten sind <b>Polygon</b>, <b>Netzwerk</b> und <b>Sechseckiges Gitter</b>.</div>
</div>

  </TabItem>
</Tabs>

  </TabItem>
  <TabItem value="ÖV" label="ÖV" className="tabItemBox">

#### ÖV

Berücksichtigt alle mit dem öffentlichen Verkehr erreichbaren Wege. Dieser Routing-Modus berücksichtigt intermodale Transfers einschließlich des Zugangs zu und von Bahnhöfen.


:::tip Tipp

Für weitere Einblicke in den Routing-Algorithmus besuchen Sie [Verkehrsmittel/ÖV](../../routing/public_transport).

:::

<div class="step">
  <div class="step-number">4</div>
  <div class="content">Wählen Sie die <code>Verkehrsmittel ÖV</code> die Sie analysieren möchten(<i>Bus, Tram, Bahn, U-Bahn, Fähre, Seilbahn, Gondelbahn</i> und/oder <i>Standseilbahn</i>).</div>
</div>

<div>
  <img src={require('/img/toolbox/accessibility_indicators/catchments/pt_type.png').default} alt="Verkehrsmittel ÖV in GOAT" style={{ maxHeight: "400px", maxWidth: "400px", objectFit: "cover"}}/>
</div>

<br />

<div class="step">
  <div class="step-number">5</div>
  <div class="content">
    <code>Reisezeitlimit</code> – die maximal zulässige Dauer der Wege, die in der Analyse berücksichtigt werden  
    <br />
    <code>Anzahl der Intervalle</code> – bestimmt die Auflösung der resultierenden Isochrone für das Einzugsgebiet  
    <br />
    <code>Tag</code> – der Wochentag, an dem die Analyse durchgeführt wird: <i>Werktag, Samstag</i> oder <i>Sonntag</i>  
    <br />
    <code>Startzeit</code> und <code>Endzeit</code> – es werden die schnellstmöglichen Wege innerhalb dieses Zeitfensters berücksichtigt  
    <br />
    <p>
      Mehr Informationen zu Routing-Optionen finden Sie {" "}
      <a href="../../routing/public_transport#routing-options">hier</a>.
    </p>
  </div>
</div>

<img src={require('/img/toolbox/accessibility_indicators/catchments/pt_config.png').default} alt="ÖPNV-Konfigurationen" style={{ maxHeight: "400px", maxWidth: "400px"}}/>

:::tip Tipp

Das ["Standort-Werkzeug"](https://www.chemnitz.de/chemnitz/media/unsere-stadt/verkehr/verkehrsplanung/vep2040_standortwerkzeug.pdf) der Stadt Chemnitz bietet hilfreiche Anhaltspunkte zur Wahl geeigneter Reisezeitgrenzen für die Bewertung der Erreichbarkeit verschiedener Einrichtungen.

:::


#### Erweiterte Konfigurationen

Standardmäßig werden die Einzugsgebiete in Polygonform berechnet. Falls Sie dies anpassen möchten, finden Sie weitere Optionen in den erweiterten Konfigurationen.

<div class="step">
  <div class="step-number">6</div>
  <div class="content">Klicken Sie auf <b>Erweiterte Einstellungen</b> <img src={require('/img/map/styling/options_icon.png').default} alt="Options Icon" style={{ maxHeight: "25px", maxWidth: "25px", objectFit: "cover"}}/>. Hier können Sie die <code> Form des Einzugsgebiets</code>bestimmen. Die Auswahlmöglichkeite sind <b>Polygon</b>, <b>Netzwerk</b> and <b>Sechseckiges Gitter</b>.</div>
</div>

  </TabItem>
</Tabs>


<Tabs>
  <TabItem value="Polygon" label="Polygon" default className="tabItemBox">

 #### Polygon
- Es ist die *geometrische Darstellung* der Einzugsgebiete.
- Bietet eine leicht verständliche Visualisierung des Einzugsgebiets.
- Für jeden <code>Schritt</code> wird ein Polygon erzeugt.

<img src={require('/img/toolbox/accessibility_indicators/catchments/pt_polygon.png').default} alt="Einzugsgebiet (Polygon) ÖV in GOAT" style={{ maxHeight: "300px", maxWidth: "300px"}}/>

:::tip Tipp

Wenn Sie **Polygon-Differenz** aktivieren, wird für jeden Schritt nur das "inkrementelle" (oder differenzielle) Polygon erstellt. Wenn Sie **Polygon-Differenz** deaktivieren, wird für jeden Schritt ein "vollständiges" Polygon erstellt (einschließlich der Bereiche, die von allen vorherigen Schritten abgedeckt wurden).

<img src={require('/img/toolbox/accessibility_indicators/catchments/polygon_difference.png').default} alt="ÖV Konfigurationen" style={{ maxHeight: "400px", maxWidth: "400px"}}/>

:::

  </TabItem>
  <TabItem value="Netzwerk" label="Netzwerk" className="tabItemBox">

 #### Netzwerk
- Es ist eine *Darstellung auf Straßenebene* der Einzugsgebiete.
- Ermöglicht eine einfache Korrelation zu tatsächlichen Straßen und deren Erreichbarkeit innerhalb des Einzugsgebiets.
- Bietet feinere Details im Vergleich zu den anderen Einzugsgebietstypen.

<img src={require('/img/toolbox/accessibility_indicators/catchments/pt_network.png').default} alt="Einzugsgebiet (Network) ÖV in GOAT" style={{ maxHeight: "300px", maxWidth: "300px"}}/>

  </TabItem>
  <TabItem value="Sechseckiges Gitter" label="Sechseckiges Gitter" className="tabItemBox">

#### Sechseckiges Gitter
- Es ist eine *gitterzellenbasierte Darstellung* der Einzugsgebiete.
- Erscheint ähnlich wie eine „Heatmap“-Visualisierung, unterscheidet sich jedoch konzeptionell und rechnerisch (dies stellt das Abfließen von einem bestimmten Ursprung zu verschiedenen anderen Standorten dar, während Heatmaps den Zugang von verschiedenen Standorten zu einem bestimmten Ziel darstellen).

<img src={require('/img/toolbox/accessibility_indicators/catchments/pt_grid.png').default} alt="Einzugsgebiet(Gitter) ÖV in GOAT" style={{ maxHeight: "300px", maxWidth: "300px"}}/>

  </TabItem>
</Tabs>

### Ausgangspunkte

<div class="step">
  <div class="step-number">7</div>
  <div class="content">Wählen Sie die <code>Art der Startpunkte</code> aus, um zu definieren, wie Sie den/die Startpunkt(e) für die Einzugsgebiete festlegen möchten. Sie können entweder <b>Klicke auf Karte</b> oder <b>Wähle vom Layer</b> auswählen.</div>
</div>

<Tabs>
  <TabItem value="Klicke auf Karte" label="Klicke auf Karte" default className="tabItemBox">

 #### Klicke auf Karte

<div class="step">
  <div class="step-number">8</div>
  <div class="content">Wählen Sie <code>Klicke auf Karte</code>. Wählen Sie den/die Startpunkt(e), indem Sie auf die jeweiligen Position(en) in der Karte klicken. Sie können <b>so viele Startpunkte</b> hinzufügen, wie Sie möchten.</div>
</div>


  </TabItem>
  <TabItem value="Wähle vom Layer" label="Wähle vom Layer" className="tabItemBox">

 #### Wähle vom Layer

 <div class="step">
  <div class="step-number">8</div>
  <div class="content">Klicken Sie auf <code>Wähle vom Layer</code>. Wählen Sie den <code>Punktlayer</code>, der die Startpunkte enthält, die Sie verwenden möchten.</div>
</div>


  </TabItem>
</Tabs>


<div class="step">
  <div class="step-number">9</div>
  <div class="content">Klicken Sie auf <code>Ausführen</code>. Dies startet die Berechnung der <b>Einzugsgebiete</b> von den ausgewählten Startpunkten.</div>
</div>

:::tip Tipp

Je nach gewählten Einstellungen kann die Berechnung einige Minuten dauern. Die [Statusleiste](../../workspace/home#statusleiste) zeigt den aktuellen Fortschritt an.

:::

### Ergebnisse

<div class="step">
  <div class="step-number">10</div>
  <div class="content">Sobald der Berechnungsprozess abgeschlossen ist, werden die resultierenden Layer zur Karte hinzugefügt. Der Layer namens <b>"Einzugsgebiet"</b> enthält die berechneten Einzugsgebiete. Wenn die Startpunkte durch Klicken auf die Karte erstellt wurden, werden sie ebenfalls in einem Layer namens <b>"Startpunkte"</b> gespeichert.
  <p></p>
  Wenn Sie auf ein Einzugsgebietspolygon auf der Karte klicken, sehen Sie weitere Details in seiner Attributtabelle. Das Attribut <b>travel_cost</b> zeigt die Reisekosten in Form von Entfernung oder Zeit, je nachdem, welche Einheit Sie für die Berechnung gewählt haben. Wenn Sie die Reisezeit gewählt haben, zeigt der travel_cost die <b>Zeit in Minuten</b> an. Wenn Sie die Entfernung gewählt haben, zeigt der travel_cost die <b>Entfernung in Metern</b> an.</div>
</div>

![Catchment Area Calculation Result in GOAT](/img/toolbox/accessibility_indicators/catchments/catchment_result.png "Catchment Area Calculation Result in GOAT")

:::tip Tipp
Möchten Sie Ihre Einzugsgebiete stilisieren und schöne Karten erstellen? Siehe [Styling](../../map/layer_style/styling).
:::

## 4. Technische Details

Einzugsgebiete sind **Isolinien**, die alle Punkte verbinden, die von einem oder mehreren Startpunkten innerhalb eines bestimmten Zeitfensters (genannt *Isochronen*) oder einer bestimmten Entfernung (genannt *Isodistanz*) erreicht werden können. Je nach gewähltem Verkehrsmittel werden die entsprechenden Verkehrsnetze für das [Verkehrsmittel](/docs/routing/walking) verwendet.

Die Einzugsgebiete werden dynamisch im Frontend auf der Basis eines Reisezeit-/Entfernungsgitters erstellt. Daher können Einzugsgebiete schnell und für verschiedene Intervalle in Echtzeit erstellt werden.

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
