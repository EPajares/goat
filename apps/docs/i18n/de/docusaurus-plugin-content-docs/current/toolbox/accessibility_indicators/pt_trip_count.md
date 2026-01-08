---
sidebar_position: 6
---


# Abfahrten ÖPNV

Dieser Indikator zeigt die **durchschnittliche Anzahl der Abfahrten öffentlicher Verkehrsmittel** pro Stunde für jede Haltestelle des öffentlichen Verkehrs an.

<div style={{ display: 'flex', justifyContent: 'center' }}>
<iframe  width="674" height="378" src="https://www.youtube.com/embed/psnuUksG7W4?si=dhLw5Gp0ThYHFd5l&amp;start=46" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>
</div>

## 1. Erklärung

Die ÖPNV-Abfahrten zeigen die **durchschnittliche Anzahl der Abfahrten pro Stunde für ein ausgewähltes Zeitintervall an jeder Haltestelle des öffentlichen Verkehrs**. Sie können die Summe für alle Verkehrsmittel anzeigen oder sich auf ein bestimmtes Verkehrsmittel konzentrieren (z.B. Bus, Straßenbahn, U-Bahn, Bahn).

Dieser Indikator ist die Grundlage für die [ÖV-Güteklassen](./oev_gueteklassen.md) und ist nützlich für **Schwachstellenanalysen von lokalen Verkehrsplänen** (siehe unter anderem [Richtlinie für die Nahverkehrsplanung in Bayern](https://www.demografie-leitfaden-bayern.de/index.html)).

import MapViewer from '@site/src/components/MapViewer';

:::info 
Die ÖPNV-Abfahrten sind nur in Gebieten verfügbar, in denen das Verkehrsnetz in GOAT integriert ist.

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
  <div class="content">Klicken Sie auf <code>Werkzeuge</code> <img src={require('/img/icons/toolbox.png').default} alt="Options" style={{ maxHeight: "20px", maxWidth: "20px", objectFit: "cover"}}/>.</div>
</div>

<div class="step">
  <div class="step-number">2</div>
  <div class="content">Unter <code>Erreichbarkeitsindikatoren</code> wählen Sie <code>Abfahrten ÖPNV</code>, um das Einstellungsmenü zu öffnen.</div>
</div>

### Berechnungszeit

<div class="step">
  <div class="step-number">3</div>
  <div class="content">Wählen Sie <code>Tag</code>, <code>Startzeit</code> und <code>Endzeit</code> für Ihre Analyse.</div>
</div>

### Referenz-Layer

<div class="step">
  <div class="step-number">4</div>
  <div class="content">Wählen Sie den <code>Referenz-Layer</code> (Polygon-Feature-Layer) für das Gebiet aus, das Sie analysieren möchten.</div>
</div>

<div class="step">
  <div class="step-number">5</div>
  <div class="content">Klicken Sie auf <code>Ausführen</code>, um die Berechnung zu starten.</div>
</div>

### Ergebnisse

Nach Abschluss der Berechnung wird ein neuer Layer namens <b>"Trip Count Station"</b> zur Karte hinzugefügt.

Klicken Sie auf Stationen, um Details anzuzeigen, einschließlich **Stationsname**, **Gesamtanzahl der Abfahrten** und **Abfahrten pro Verkehrsmittel**.

<img src={require('/img/toolbox/accessibility_indicators/trip_count/trip_count_calculation.gif').default} alt="Menu Overview for Public Transport Trip Count" style={{ maxHeight: "auto", maxWidth: "80%"}}/>

:::tip Tipp

Falls Sie an einem bestimmten Verkehrsmittel interessiert sind, z.B. nur Busse, können Sie das [attributbasierte Styling](../../map/layer_style/style/attribute_based_styling) verwenden, um die Punktfarbe basierend auf der gewünschten Spalte anzupassen.

:::

## 4. Technische Details

Ähnlich den Public Transport Quality Classes <i>(Deutsch: ÖV-Güteklassen)</i>, wird dieser Indikator basierend auf **GTFS-Daten** berechnet (siehe [Eingebaute Datensätze](../../data/builtin_datasets)). Basierend auf dem ausgewählten Tag und Zeitfenster wird die durchschnittliche Anzahl der Abfahrten pro Stunde (unabhängig von der Richtung) berechnet.

## 5. Referenzen

Shkurti, Majk (2022). [Spatio-temporal public transport accessibility analysis and benchmarking in an interactive WebGIS](https://www.researchgate.net/publication/365790691_Spatio-temporal_public_transport_accessibility_analysis_and_benchmarking_in_an_interactive_WebGIS)
