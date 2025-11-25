---
sidebar_position: 5
---
import thematicIcon from "/img/toolbox/data_management/join/toolbox.webp";

# ÖV-Güteklassen

Der ÖV-Güteklassen Indikator **klassifiziert die Qualität der öffentlichen Verkehrsdienste in einem bestimmten Gebiet** und hilft Planern und Interessengruppen dabei, gut versorgte und unterversorgte Standorte schnell zu identifizieren.

<div style={{ display: 'flex', justifyContent: 'center' }}>
<iframe width="674" height="378" src="https://www.youtube.com/embed/hX0Lau9-slg?si=jBL2tJB2QLp83qAZ&amp;start=46" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>
</div>

## 1. Erklärung

ÖV-Güteklassen (Qualitätsklassen öffentlicher Verkehrsmittel) bieten eine standardisierte Methode zur **Bewertung und Visualisierung der Attraktivität öffentlicher Verkehrsdienste**. Die Klassen reichen von **A** (sehr gut) bis **F** (sehr schlecht) und basieren auf der Servicefrequenz, dem Stationstyp und der räumlichen Abdeckung.

Der ÖV-Güteklassen-Indikator ist entscheidend und kann verwendet werden, um Defizite im öffentlichen Verkehrsangebot hervorzuheben und gut versorgte Standorte als attraktive Entwicklungsgebiete zu identifizieren.

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

## 3. Wie wird der Indikator verwendet?

<div class="step">
  <div class="step-number">1</div>
  <div class="content">Klicken Sie auf <code>Werkzeugleiste</code> <img src={thematicIcon} alt="toolbox" style={{width: "25px"}}/>. </div>
</div>

<div class="step">
  <div class="step-number">2</div>
  <div class="content">Unter <code>Erreichbarkeitsindikatoren</code> wählen Sie <code>ÖV-Güteklassen</code>, um das Einstellungsmenü zu öffnen.</div>
</div>

### Berechnungszeit

<div class="step">
  <div class="step-number">3</div>
  <div class="content">Setzen Sie <code>Tag</code>, <code>Startzeit</code> und <code>Endzeit</code> für Ihre Analyse.</div>
</div>

### Referenz-Layer

<div class="step">
  <div class="step-number">4</div>
  <div class="content">Wählen Sie den <code>Referenz-Layer</code> (Polygon-Feature-Layer) für das Gebiet aus, das Sie analysieren möchten.</div>
</div>

### Einstellungen

<div class="step">
  <div class="step-number">5</div>
  <div class="content">Wählen Sie den <code>Einzugsgebietstyp</code>: <b>Puffer</b> oder <b>Netzwerk</b>.</div>
</div>

:::info

**Pufferzonen** stellen Bereiche rund um öffentliche Verkehrsstationen dar, gemessen „in Luftlinie“, während **Netzwerk-Einzugsgebiete** dieselben Entfernungen entlang realer Straßen und Wege berücksichtigen.

:::

<div class="step">
  <div class="step-number">6</div>
  <div class="content">Klicken Sie auf <code>Ausführen</code>, um die Berechnung zu starten.</div>
</div>

### Ergebnisse

Nach der Berechnung werden zwei Layer zur Karte hinzugefügt:
- **ÖV-Güteklassen**: Zeigt die Qualitätsklasse für jedes Gebiet.
- **ÖV-Güteklassen Stationen**: Zeigt alle Stationen, die in der Berechnung verwendet wurden (graue Punkte = zu niedrige Frequenz, tragen zu keiner ÖV-Qualitätsklasse bei).

Wenn Sie auf ein ÖV-Güteklassen-Ergebnis klicken, sehen Sie weitere Details wie **ÖV-Klasse** und **ÖV-Klassennummer**. Beide zeigen dieselbe Qualität des öffentlichen Verkehrs in diesem Gebiet an (siehe [Berechnung](#berechnung) für weitere Details).

Wenn Sie auf eine beliebige Station klicken, können Sie Details wie den **Haltestellennamen**, die **durchschnittliche Frequenz** und die **Stationskategorie** sehen.

<img src={require('/img/toolbox/accessibility_indicators/gueteklassen/gueteklassen_calculation.gif').default} alt="Berechnung - ÖV-Güteklassen" style={{ maxHeight: "auto", maxWidth: "80%"}}/>

## 4. Technische Details

### Wissenschaftlicher Hintergrund

Die Qualität und Häufigkeit von Verkehrsangeboten ist ein **entscheidender** Indikator in der öffentlichen Verkehrspolitik und Raumplanung. Er kann verwendet werden, um Defizite im Verkehrsangebot aufzuzeigen und gut versorgte Standorte als attraktive Entwicklungsgebiete zu identifizieren. Der Ansatz der ÖV-Güteklassen ist **methodisch überlegen** gegenüber den üblichen Einzugsgebieten. 2011 begann das [Schweizer Bundesamt für Raumentwicklung (ARE)](https://www.are.admin.ch/are/de/home.html) mit der Nutzung des Indikators ÖV-Güteklassen, um die **Attraktivität des öffentlichen Verkehrs** in die Bewertung der Entwicklungsqualität einzubeziehen; seitdem werden diese als wichtiges Instrument in formellen Planungsprozessen in der Schweiz betrachtet. Zudem diente das Schweizer Modell als Inspiration für die Anwendung in Österreich (z.B. Vorarlberg) und findet erste Anwendungen in Deutschland (z.B. durch [KCW](https://www.plan4better.de/de/references/calculation-of-public-transport-quality-classes-in-germany) und [Agora Verkehrswende](https://www.plan4better.de/de/references/accessibility-analyses-for-the-mobility-guarantee-and-public-transport-atlas-projects)).

Die Institutionalisierung des Indikators im deutschsprachigen Raum sowie die nachvollziehbare und zugleich differenzierte Berechnungsmethodik sind wichtige Vorteile der ÖV-Güteklassen.

### Berechnung

In der Schweizer Version des Indikators wird die Berechnung der Güteklassen üblicherweise für Abfahrten an Werktagen zwischen 6 Uhr und 20 Uhr durchgeführt. Für die Nutzung in GOAT wurde der **Berechnungszeitraum** flexibler gestaltet, sodass der Indikator **für jeden Wochentag und jede Tageszeit** berechnet werden kann.

Die Berechnungen werden basierend auf **GTFS-Daten** durchgeführt (siehe [Eingebaute Datensätze](../../data/data_basis)):
Zunächst wird die Anzahl der Abfahrten pro öffentlichem Verkehrsmittel (Zug, U-Bahn, Straßenbahn und Bus) für jede Station dynamisch berechnet. Die Summe der Abfahrten wird durch zwei geteilt, um die Frequenz zu berechnen und die Hin- und Rückrichtungen zu eliminieren. Im nächsten Schritt wird die **durchschnittliche Frequenz** für das ausgewählte Zeitintervall berechnet. Das höherwertige Verkehrsmittel wird als **Stationstyp** ausgewählt, falls mehrere Verkehrsmittel die Station bedienen. Zum Beispiel ist bei Bus und Zug der Zug das höherwertige Verkehrsmittel. Mit Hilfe der unten stehenden Tabelle sowie dem Stationstyp und der Frequenz kann nun die Stationskategorie bestimmt werden.

### Berechnungsschritte

1. **Abfahrten pro Station**: Berechnung der Anzahl der Abfahrten pro Verkehrsmittel (Zug, U-Bahn, Straßenbahn, Bus) für jede Station mit **GTFS-Daten** (siehe [Eingebaute Datensätze](../../data/data_basis)).
2. **Frequenz**: Die Summe der Abfahrten wird durch zwei geteilt, um die Hin- und Rückrichtungen zu eliminieren.
3. **Stationstyp**: Für jede Station wird das höchstrangige Verkehrsmittel bestimmt (z.B. wenn sowohl Bus als auch Zug verfügbar sind, wird die Station als Bahnstation klassifiziert).
4. **Kategorienzuweisung**: Verwendung des Stationstyps und der Frequenz zur Bestimmung der Kategorie (siehe Tabelle unten).
5. **Einzugsgebiete**: Erstellung von Pufferzonen oder Netzwerk-Isochronen für jede Stationskategorie.
6. **Zusammenführung der Gebiete**: Überlappende Gebiete werden zusammengeführt, wobei die höhere Qualitätsklasse Vorrang hat.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  
  <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'flex-start', gap: '20px', flexWrap: 'wrap', marginBottom: '20px' }}>
    <img src={require('/img/toolbox/accessibility_indicators/gueteklassen/classification_stations_de.webp').default} alt="Klassifikation der Verkehrshaltestellen" style={{ maxHeight: "auto", maxWidth: "45%", objectFit: "cover"}}/>
    <img src={require('/img/toolbox/accessibility_indicators/gueteklassen/determination_oev_gueteklasse_de.webp').default} alt="Bestimmung der ÖV-Güteklassen" style={{ maxHeight: "auto", maxWidth: "45%", objectFit: "cover"}}/>
  </div>

  <img src={require('/img/toolbox/accessibility_indicators/gueteklassen/oev_figure_de.png').default} alt="ÖV-Güteklassen Berechnung" style={{ maxHeight: "auto", maxWidth: "30%", objectFit: "cover"}}/>
</div>

<div></div>

### Visualisierung

Die erstellten Puffer/Netzwerk-Einzugsgebiete werden um die Haltestellen in den entsprechenden Farben visualisiert, um die **Güteklasse** (<span style={{color: "#199741"}}>A</span>-<span style={{color: "#E4696A"}}>F</span>) hervorzuheben.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/toolbox/accessibility_indicators/gueteklassen/visualization.png').default} alt="Visualisierung der ÖV-Güteklassen" style={{ maxHeight: "400px", maxWidth: "100%", objectFit: "cover"}}/>
</div>

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

