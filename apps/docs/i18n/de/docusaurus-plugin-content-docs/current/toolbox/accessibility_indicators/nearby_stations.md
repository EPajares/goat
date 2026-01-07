---
sidebar_position: 7
---
import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';


# Nahgelegene ÖV-Haltestellen 

Der ÖV Nahegelegene Stationen Indikator wird verwendet, um **öffentliche Verkehrshaltestellen zu finden, die zu Fuß oder mit dem Fahrrad innerhalb einer bestimmten Zeit erreichbar sind.**

<div style={{ display: 'flex', justifyContent: 'center' }}>
<iframe width="674" height="378" src="https://www.youtube.com/embed/ksLVUU2zMTU?si=4cvwdFIL188ZuwCB&amp;start=46" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>
</div>

## 1. Erklärung

Das Tool identifiziert **öffentliche Verkehrsstationen, die von Startpunkten innerhalb bestimmter Reiseparameter erreichbar sind.** Es verwendet Startpunkte, Stationszugangsart (zu Fuß, Fahrrad oder Pedelec), Reisezeitlimit und öffentliche Verkehrsmittel als Eingaben. Mit realen Straßen- und Verkehrsnetzen **berechnet es, welche Stationen erreichbar sind und liefert detaillierte Serviceinformationen für jede.**

Für jede erreichbare Station zeigt die Analyse **verfügbare Verkehrsmittel**, **Servicefrequenzen**, **Abfahrtspläne** und **Zugangszeiten**. Diese umfassende Sicht hilft bei der Bewertung der Verkehrsanbindung und unterstützt Planungsentscheidungen.

import MapViewer from '@site/src/components/MapViewer';

:::info 
Die Berechnung der nahegelegenen Haltestellen ist nur für Gebiete verfügbar, in denen das öffentliche Verkehrsnetz in GOAT integriert ist.

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
        { label: "Abdeckung für die Berechnung der nächstgelegenen ÖV-Haltestellen", color: "#ffffff" }
      ]}
  />
</div> 

Falls Sie eine Analyse außerhalb dieses Geofence durchführen müssen, wenden Sie sich bitte an den [Support](https://plan4better.de/de/contact/ "Support") und wir werden prüfen, was möglich ist.
:::


## 2. Anwendungsbeispiele

- Welche öffentlichen Verkehrshaltestellen befinden sich in der Nähe und bieten eine bequeme Erreichbarkeit zu wichtigen Sehenswürdigkeiten und Wahrzeichen für Touristen, die eine neue Stadt erkunden?
- Bei der täglichen Pendelstrecke zur Arbeit, welche nahegelegenen öffentlichen Verkehrshaltestellen bieten optimale Routen und Fahrpläne für eine nahtlose Reise?
- Welche nahegelegenen öffentlichen Verkehrshaltestellen bieten eine bequeme Erreichbarkeit zu Einkaufszentren?


## 3. Wie verwendet man den Indikator?

<div class="step">
  <div class="step-number">1</div>
  <div class="content">Klicken Sie auf <code>Werkzeuge</code> <img src={require('/img/icons/toolbox.png').default} alt="Options" style={{ maxHeight: "20px", maxWidth: "20px", objectFit: "cover"}}/>. </div>
</div>

<div class="step">
  <div class="step-number">2</div>
  <div class="content">Unter <code>Erreichbarkeitsindikatoren</code> wählen Sie <code>Nahgelegene ÖV-Haltestellen</code>.</div>
</div>



### Zugang zu Stationen

<div class="step">
  <div class="step-number">3</div>
  <div class="content">Wählen Sie den <code>Zugang zu Stationen</code> (<i>zu Fuß, mit dem Fahrrad oder Pedelec</i>), der für den Weg zur nächstgelegenen Station verwendet werden soll.</div>
</div>

<div class="step">
  <div class="step-number">4</div>
  <div class="content">Legen Sie die Konfigurationen für die Haltestellen-Erreichbarkeit fest, indem Sie <code>Reisezeitlimit in (Minuten)</code> und <code>Reisegeschwindigkeit in (km/h)</code> bestimmen.</div>
</div>

### Haltestellen Konfiguration 

<div class="step">
  <div class="step-number">5</div>
  <div class="content">Wählen Sie aus, welche <code>Verkehrsmittel ÖV</code> für die nahegelegenen Haltestellen berücksichtigt werden sollen.</div>
</div>

<div class="step">
  <div class="step-number">6</div>
  <div class="content">Wählen Sie aus, für welchen <code>Tag</code>, <code>Startzeit</code> und <code>Endzeit</code> Sie die öffentlichen Verkehrsanbindungen sehen möchten.</div>
</div>



### Startpunkte

<div class="step">
  <div class="step-number">7</div>
  <div class="content">Wählen Sie die <code>Art der Startpunkte</code> aus, um zu definieren, wie Sie den bzw. die Startpunkt(e) für die Reise(n) festlegen möchten. Sie können entweder <b>Klicke auf die Karte</b> oder <b>Wähle vom Layer</b> auswählen.</div>
</div>

<Tabs>
  <TabItem value="Klicke auf die Karte" label="Klicke auf die Karte" default className="tabItemBox">
 
  Klicken Sie auf <code>Klicke auf die Karte</code>. Wählen Sie den/die Startpunkt(e) aus, indem Sie auf die jeweiligen Position(en) in der Karte klicken. Sie können beliebig viele Startpunkte hinzufügen.

  </TabItem>

  <TabItem value="Wähle vom Layer" label="Wähle vom Layer" className="tabItemBox">
  
  Klicken Sie auf <code>Wähle vom Layer</code>. Wählen Sie den <code>Punktlayer</code> aus, der die Startpunkte enthält, die Sie verwenden möchten.
  
  </TabItem>
</Tabs>

<div class="step">
  <div class="step-number">8</div>
  <div class="content">Klicken Sie auf <code>Ausführen</code>. Dadurch wird die Erfassung der nahegelegenen Haltestellen von den ausgewählten Startpunkt(en) gestartet.</div>
</div>

:::tip Tipp

Je nach Anzahl der ausgewählten Startpunkte kann die Berechnung einige Minuten dauern. Die [Statusleiste](../../workspace/home#status-bar) zeigt den aktuellen Fortschritt an.

:::

### Ergebnisse

Sobald die Berechnung abgeschlossen ist, werden die resultierenden Layer zur Karte hinzugefügt:

- **"Nahegelegene Stationen"** Layer zeigt erreichbare öffentliche Verkehrshaltestellen
- **"Startpunkte - Nahegelegene Stationen"** Layer mit Analyseausgangspunkten

Klicken Sie auf Stationen, um Details anzuzeigen, einschließlich **Haltestellenname**, **Zugangszeit** und **Servicefrequenz**.

<img src={require('/img/toolbox/accessibility_indicators/nearby_stations/nearby_stations_calculation.gif').default} alt="Result of Public Transport Nearby Stations" style={{ maxHeight: "auto", maxWidth: "80%"}}/>



:::tip Tipp
Möchten Sie Ihre Ergebnisse bearbeiten und ansprechende Karten erstellen? Dies können Sie unter [Layer Design](../../map/layer_style/style/styling).
:::

## 4. Technische Details

Ähnlich wie die Public Transport Quality Classes (ÖV-Güteklassen) wird dieser Indikator auf Basis von **GTFS-Daten** berechnet (siehe [Eingebaute Datensätze](../../data/builtin_datasets)). Basierend auf den ausgewählten Verkehrsmitteln, dem Tag und dem Zeitfenster werden die nahegelegenen ÖV-Haltestellen ermittelt.
