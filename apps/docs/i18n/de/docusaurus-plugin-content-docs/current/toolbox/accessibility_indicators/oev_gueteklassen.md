---
sidebar_position: 5
---
import thematicIcon from "/img/toolbox/data_management/join/toolbox.webp";

# ÖV-Güteklassen


Die ÖV-Güteklassen zeigen die **Attraktivität von öffentlichen Verkehrsmitteln** in einem ausgewählten Gebiet.

<iframe width="100%" height="500" src="https://www.youtube.com/embed/iWwGyGOUokQ?si=YVvq0o0NRi6724m7" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>

## 1. Erklärung

ÖV-Güteklassen, auch bekannt als **Qualitätsklassen öffentlicher Verkehrsmittel**, sind ein Klassifizierungssystem zur Bewertung und Kategorisierung der **Qualität** von öffentlichen Verkehrsmitteln in einem bestimmten Gebiet. Das Konzept wird verwendet, um öffentliche Verkehrsdienste zu planen und zu bewerten, damit sie bestimmten Standards entsprechen und die Bedürfnisse der Bevölkerung erfüllen. Die **Güteklassen** reichen dabei von **<span style={{color: "#199741"}}>A</span>** (sehr gutes Angebot) bis **<span style={{color: "#E4696A"}}>F</span>** (sehr schlechtes Angebot).

![ÖV-Güteklassen in GOAT](/img/toolbox/accessibility_indicators/gueteklassen/example.png "ÖV-Güteklassen in GOAT")

import MapViewer from '@site/src/components/MapViewer';

:::info
Die Berechnung der ÖV-Güteklassen ist nur für Gebiete verfügbar, in denen das Verkehrsnetz in GOAT integriert ist.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
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
        { label: "Abdeckung für ÖV-Güteklassen", color: "#ffffff" }
      ]}
  />
</div>

Falls Sie eine Analyse außerhalb dieses Geofence durchführen müssen, kontaktieren Sie bitte den [Support](https://plan4better.de/de/contact/ "Support kontaktieren") und wir prüfen, was möglich ist.
:::

## 2. Anwendungsbeispiele

- Wie gut ist das Angebot an öffentlichen Verkehrsmitteln in verschiedenen Teilen der Stadt?
- Wie viele Menschen sind unterversorgt mit öffentlichen Verkehrsmitteln? Wo besteht Bedarf an weiteren Angeboten?
- Wie unterscheidet sich die Qualität der öffentlichen Verkehrsmittel zu verschiedenen Zeiten der Woche und des Tages?

## 3. Verwendung des Indikators

<div class="step">
  <div class="step-number">1</div>
  <div class="content">Gehen Sie auf <code>Werkzeuge</code> <img src={thematicIcon} alt="toolbox" style={{width: "25px"}}/>. </div>
</div>

<div class="step">
  <div class="step-number">2</div>
  <div class="content">Klicken Sie im Menü <code>Erreichbarkeitsindikatoren</code> auf <code>ÖV-Güteklassen</code>. Dadurch wird das Einstellungsmenü geöffnet.</div>
</div>

![Menüübersicht für ÖV-Güteklassen](/img/toolbox/accessibility_indicators/gueteklassen/overview_new.png "Menüübersicht für ÖV-Güteklassen")

### Berechnungszeit

<div class="step">
  <div class="step-number">3</div>
  <div class="content">Definieren Sie den <code>Tag</code>, die <code>Startzeit</code> und die <code>Endzeit</code>, für die Sie die Analyse durchführen möchten.</div>
</div>

### Referenzlayer

<div class="step">
  <div class="step-number">4</div>
  <div class="content">Wählen Sie den <code>Referenzlayer</code> aus, für den Sie den Indikator berechnen möchten. Dies kann jeder Polygon-Feature-Layer sein.</div>
</div>

### Einstellungen

<div class="step">
  <div class="step-number">5</div>
  <div class="content">Wählen Sie den <code>Einzugsgebietstyp</code> aus, für den Sie den Indikator berechnen möchten. Dieser kann auf einem <code>Puffer</code> oder auf dem <code>Netzwerk</code> basieren. </div>
</div>

:::info

**Pufferzonen** stellen Bereiche rund um öffentliche Verkehrsstationen dar, gemessen „in Luftlinie“, während **Netzwerk-Einzugsgebiete** dieselben Entfernungen entlang realer Straßen und Wege berücksichtigen.

:::

![Auswahl des Referenzgebiets](/img/toolbox/accessibility_indicators/gueteklassen/reference_area_new.png "Auswahl des Referenzgebiets")

<div class="step">
  <div class="step-number">6</div>
  <div class="content">Klicken Sie auf <code>Ausführen</code>. Dies startet die Berechnung der ÖV-Güteklassen für das ausgewählte Gebiet.</div>
</div>

:::tip Tipp
Je nach Größe des ausgewählten Gebiets kann die Berechnung einige Minuten dauern. Die [Statusleiste](../../workspace/home#status-bar) zeigt den aktuellen Fortschritt an.
:::

### Ergebnisse

<div class="step">
  <div class="step-number">7</div>
  <div class="content">Sobald der Berechnungsprozess abgeschlossen ist, werden die resultierenden Layer zur Karte hinzugefügt. Die Ergebnisse bestehen aus einem Layer namens <b>"ÖV-Güteklassen"</b>, die die ÖV-Güteklassen zeigt, und einer Layer namens <b>"ÖV-Güteklassen Stationen"</b>, die alle Stationen enthält, die für die Berechnung dieses Indikators verwendet wurden. Die in Grau dargestellten Stationen haben eine zu geringe Servicefrequenz und tragen daher nicht zu einer ÖV-Güteklasse bei.
  <p></p>
  Wenn Sie auf ein "ÖV-Güteklassen"-Symbol auf der Karte klicken, sehen Sie weitere Details wie dessen pt_class und pt_class_number, die die <a href="#calculation">Qualität des öffentlichen Verkehrs</a> angeben.</div>
</div>

![Ergebnis - ÖV-Güteklassen](/img/toolbox/accessibility_indicators/gueteklassen/result.png "Ergebnis - ÖV-Güteklassen")
![Ergebnis - ÖV-Güteklassen](/img/toolbox/accessibility_indicators/gueteklassen/results_isochrone.png "Ergebnis - ÖV-Güteklassen")


## 4. Technische Details

### Wissenschaftlicher Hintergrund

Die Qualität und Häufigkeit von Verkehrsangeboten ist ein **entscheidender** Indikator in der öffentlichen Verkehrspolitik und Raumplanung. Er kann verwendet werden, um Defizite im Verkehrsangebot aufzuzeigen und gut versorgte Standorte als attraktive Entwicklungsgebiete zu identifizieren. Der Ansatz der ÖV-Güteklassen ist **methodisch überlegen** gegenüber den üblichen Einzugsgebieten. 2011 begann das [Schweizer Bundesamt für Raumentwicklung (ARE)](https://www.are.admin.ch/are/de/home.html) mit der Nutzung des Indikators ÖV-Güteklassen, um die **Attraktivität des öffentlichen Verkehrs** in die Bewertung der Entwicklungsqualität einzubeziehen; seitdem werden diese als wichtiges Instrument in formellen Planungsprozessen in der Schweiz betrachtet. Zudem diente das Schweizer Modell als Inspiration für die Anwendung in Österreich (z.B. Vorarlberg) und findet erste Anwendungen in Deutschland (z.B. durch [KCW](https://www.plan4better.de/de/references/calculation-of-public-transport-quality-classes-in-germany) und [Agora Verkehrswende](https://www.plan4better.de/de/references/accessibility-analyses-for-the-mobility-guarantee-and-public-transport-atlas-projects)).

Die Institutionalisierung des Indikators im deutschsprachigen Raum sowie die nachvollziehbare und zugleich differenzierte Berechnungsmethodik sind wichtige Vorteile der ÖV-Güteklassen.

### Berechnung

In der Schweizer Version des Indikators wird die Berechnung der Güteklassen üblicherweise für Abfahrten an Werktagen zwischen 6 Uhr und 20 Uhr durchgeführt. Für die Nutzung in GOAT wurde der **Berechnungszeitraum** flexibler gestaltet, sodass der Indikator **für jeden Wochentag und jede Tageszeit** berechnet werden kann. Zudem wurde der Indikator an die Bedingungen in Deutschland angepasst.

Die Berechnungen basieren auf **GTFS-Daten** (siehe [Eingebaute Datensätze](../../data/data_basis)). Zunächst wird die Anzahl der Abfahrten pro Verkehrsmittel (Zug, U-Bahn, Straßenbahn und Bus) für jede Station dynamisch berechnet. Die Summe der Abfahrten wird durch zwei geteilt, um die Frequenz zu berechnen und die Hin- und Rückrichtungen zu eliminieren. Im nächsten Schritt wird die **durchschnittliche Frequenz** für das ausgewählte Zeitfenster berechnet. Das höherwertige Angebot wird als **Art der Haltestelle** ausgewählt, falls mehrere Verkehrsmittel die Haltestelle bedienen. Zum Beispiel ist bei Bussen und Zügen der Zug der höherwertige Service. Mithilfe der unten stehenden Tabelle sowie der Art der Haltestelle und der Frequenz kann nun die Haltestellenkategorie bestimmt werden.

![Klassifikation der Verkehrshaltestellen](/img/toolbox/accessibility_indicators/gueteklassen/classification_stations_de.webp "Klassifikation der Verkehrshaltestellen")

Anschließend werden **Puffer** oder **Netzwerk-Einzugsgebiete** der angegebenen Größe für die entsprechenden Haltestellenkategorien berechnet. Dadurch entstehen mehrere Puffer/Isochronen, die zusammengeführt werden. Bei überlappenden Puffern/Isochronen wird die höherwertige Klasse verwendet.

![Bestimmung der ÖV-Güteklassen](/img/toolbox/accessibility_indicators/gueteklassen/determination_oev_gueteklasse_de.webp "Bestimmung der ÖV-Güteklassen")

<div></div>

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/toolbox/accessibility_indicators/gueteklassen/oev_figure_de.png').default} alt="ÖV-Güteklassen calculation figure" style={{ maxHeight: "600px", maxWidth: "600px", alignItems:'center'}}/>
</div> 

<div></div>

*Übersichtsabbildung zur Veranschaulichung der Berechnung der ÖV-Güteklassen*

### Visualisierung

Die erstellten Puffer/Netzwerk-Einzugsgebiete werden um die Haltestellen in den entsprechenden Farben visualisiert, um die **Güteklasse** (<span style={{color: "#199741"}}>A</span>-<span style={{color: "#E4696A"}}>F</span>) hervorzuheben.

![Visualisierung der ÖV-Güteklassen](/img/toolbox/accessibility_indicators/gueteklassen/visualization.png "Visualisierung der ÖV-Güteklassen")
![Visualisierung der ÖV-Güteklassen](/img/toolbox/accessibility_indicators/gueteklassen/visualization_network.png "Visualisierung der ÖV-Güteklassen")

## 5. Weitere Lektüre

Beispielprojekte, in denen ÖV-Güteklassen verwendet wurden:
- [Deutschlandweite Bewertung der ÖV-Erschließung mittels ÖV-Güteklassen Whitepaper](https://www.plan4better.de/de/whitepapers/ov-erschliessung)
- [Erreichbarkeitsanalysen für die Projekte "Mobilitätsgarantie" und "ÖPNV-Atlas"](https://www.plan4better.de/de/references/accessibility-analyses-for-the-mobility-guarantee-and-public-transport-atlas-projects)
- [Berechnung der ÖV-Güteklassen in Österreich](https://www.plan4better.de/de/references/guteklassen-osterreich)
- [Berechnung der ÖV-Güteklassen in Deutschland](https://www.plan4better.de/de/references/calculation-of-public-transport-quality-classes-in-germany)

## 6. Referenzen

Bundesamt für Raumentwicklung ARE, 2022. [ÖV-Güteklassen Berechnungsmethodik ARE (Grundlagenbericht)](https://www.are.admin.ch/are/de/home/medien-und-publikationen/publikationen/verkehr/ov-guteklassen-berechnungsmethodik-are.html "Open Reference").

Hiess, H., 2017. [Entwicklung eines Umsetzungskonzeptes für österreichweite ÖV-Güteklassen](https://www.oerok.gv.at/fileadmin/user_upload/Bilder/2.Reiter-Raum_u._Region/1.OEREK/OEREK_2011/PS_RO_Verkehr/OeV-G%C3%BCteklassen_Bericht_Final_2017-04-12.pdf "Open Reference").

metron, 2017. [Bedienungsqualität und Erschließungsgüte im Öffentlichen Verkehr](https://vorarlberg.at/documents/302033/472144/1-+Schlussbericht.pdf/81c5f0d7-a0f0-54c7-e951-462cd5cf2831?t=1616147848364 "Open Reference").

Shkurti, Majk, 2022. "Spatio-temporal public transport accessibility analysis and benchmarking in an interactive WebGIS". url: https://www.researchgate.net/publication/365790691_Spatio-temporal_public_transport_accessibility_analysis_and_benchmarking_in_an_interactive_WebGIS

