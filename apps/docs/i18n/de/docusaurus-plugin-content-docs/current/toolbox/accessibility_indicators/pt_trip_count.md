---
sidebar_position: 6
---
import thematicIcon from "/img/toolbox/data_management/join/toolbox.webp";

# Abfahrten ÖPNV

Dieser Indikator zeigt die **durchschnittliche Anzahl der Abfahrten öffentlicher Verkehrsmittel** pro Stunde für jede Haltestelle des ÖVs an.

<iframe width="100%" height="500" src="https://www.youtube.com/embed/bLKcxAqSNjA?si=7YetwUdGHMRnmdHE" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>

## 1. Erklärung

Das Werkzeug "Abfahrten ÖPNV" zeigt die *durchschnittliche Anzahl der Abfahrten öffentlicher Verkehrsmittel pro Stunde** für ein ausgewähltes **Zeitfenster** für jede Haltestelle des öffentlichen Verkehrs auf einem Punkt-Layer an. Die Ergebnisse können entweder als Summe aller Verkehrsmittel oder durch Fokussierung auf einen bestimmtes davon (z.B. Bus, Straßenbahn, U-Bahn, Bahn) visualisiert werden.

Dieser Indikator dient als Grundlage für die [ÖV-Güteklassen](./oev_gueteklassen.md), kann aber auch eigenständig als einfache Maßnahme für das Angebot an öffentlichen Verkehrsmitteln auf **Haltestellenebene** verwendet werden. Er gibt eine Zusammenfassung der Abfahrten einer Haltestelle während eines bestimmten Zeitfensters und Tages und bietet einen wertvollen Überblick über das öffentliche Verkehrsangebot in einer Stadt. Daher wird der Indikator oft in **Schwachstellenanalysen von lokalen Verkehrsplänen** verwendet (siehe unter anderem [Richtlinie für die Nahverkehrsplanung in Bayern](https://www.demografie-leitfaden-bayern.de/index.html)).

![Public Transport Trip Count](/img/toolbox/accessibility_indicators/trip_count/sample.png "Public Transport Trip Count")

import MapViewer from '@site/src/components/MapViewer';

:::info
Abfahrten ÖPNV ist nur in Gebieten verfügbar, in denen das Verkehrsnetz in GOAT integriert ist.

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
        { label: "Abdeckung für die Berechnung der ÖPNV-Abfahrten", color: "#ffffff" }
      ]}
  />

</div>

Falls Sie Analysen außerhalb dieses Geofences durchführen müssen, kontaktieren Sie bitte den [Support](https://plan4better.de/de/contact/ "Contact Support") und wir werden prüfen, was möglich ist.
:::

## 2. Anwendungsbeispiele

- Welche Stationen in der Stadt dienen als Hauptknotenpunkte?
- Welche Stationen haben im Vergleich zu anderen niedrige Serviceraten?
- Wie variiert die Qualität des öffentlichen Verkehrs zu unterschiedlichen Zeiten der Woche oder des Tages?

## 3. Wie benutzt man den Indikator?

<div class="step">
  <div class="step-number">1</div>
  <div class="content">Klicken Sie auf <code>Werkzeuge</code> <img src={thematicIcon} alt="toolbox" style={{width: "25px"}}/>.</div>
</div>

<div class="step">
  <div class="step-number">2</div>
  <div class="content">Unter <code>Erreichbarkeitsindikatoren</code> wähen Sie <code>Abfahrten ÖPNV</code>. Dies öffnet das Einstellungsmenü.</div>
</div>

![Menüübersicht für den Public Transport Trip Count](/img/toolbox/accessibility_indicators/trip_count/overview.png "Menüübersicht für den Public Transport Trip Count")

### Berechnungszeit

<div class="step">
  <div class="step-number">3</div>
  <div class="content">Wählen Sie aus, für welchen <code>Tag</code>, <code>Startzeit</code> und <code>Endzeit</code> Sie die Abfahrten ÖPNV berechnen möchten.</div>
</div>

### Referenzlayer

<div class="step">
  <div class="step-number">4</div>
  <div class="content">Wählen Sie den <code>Referenzlayer</code>, der das Gebiet enthält, für das Sie den Indikator berechnen möchten. Dies kann jeder Polygon-Feature-Layer sein.</div>
</div>

<div class="step">
  <div class="step-number">5</div>
  <div class="content">Klicken Sie auf <code>Ausführen</code>. Dies startet die Berechnung des Abfahrten ÖPNV für das ausgewählte Gebiet und Zeitintervall.</div>
</div>

:::tip Tipp

Je nach Größe des ausgewählten Gebiets kann die Berechnung einige Minuten dauern. Die [Statusleiste](../../workspace/home#status-bar) zeigt den aktuellen Fortschritt an.

:::

### Ergebnisse

<div class="step">
  <div class="step-number">6</div>
  <div class="content">Sobald der Berechnungsprozess abgeschlossen ist, wird der resultierende Layer mit dem Namen <b>"Trip Count Station"</b> zur Karte hinzugefügt.</div>
</div>

![Menüübersicht für den Public Transport Trip Count](/img/toolbox/accessibility_indicators/trip_count/result.png "Menüübersicht für den Public Transport Trip Count")

<div class="step">
  <div class="step-number">7</div>
  <div class="content">Wenn Sie auf einen Punkt in der Karte klicken, können Sie den <b>Haltestellennamen</b>, die <b>Gesamtanzahl der Abfahrten</b> und die <b>Abfahrten pro Verkehrsmittel</b> sehen.</div>
</div>

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>

  <img src={require('/img/toolbox/accessibility_indicators/trip_count/details.png').default} alt="Weitere Details zum Trip Count" style={{ maxHeight: "300px", maxWidth: "300px", objectFit: "cover"}}/>

</div>

:::tip Tipp

Falls Sie an einem bestimmten Verkehrsmittel interessiert sind, z.B. nur Busse, können Sie das [attributbasierte Styling](../../map/layer_style/attribute_based_styling.md) verwenden, um die Punktfarbe basierend auf der gewünschten Spalte anzupassen.

:::

## 4. Technische Details

Ähnlich den Public Transport Quality Classes <i>(Deutsch: ÖV-Güteklassen)</i>, wird dieser Indikator basierend auf **GTFS-Daten** berechnet (siehe [Eingebaute Datensätze](../../data/data_basis)). Basierend auf dem ausgewählten Tag und Zeitfenster wird die durchschnittliche Anzahl der Abfahrten pro Stunde (unabhängig von der Richtung) berechnet.

## 5. Referenzen

Shkurti, Majk (2022). [Spatio-temporal public transport accessibility analysis and benchmarking in an interactive WebGIS](https://www.researchgate.net/publication/365790691_Spatio-temporal_public_transport_accessibility_analysis_and_benchmarking_in_an_interactive_WebGIS)
