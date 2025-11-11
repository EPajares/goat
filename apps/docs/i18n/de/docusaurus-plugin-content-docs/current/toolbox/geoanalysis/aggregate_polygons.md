---
sidebar_position: 3
---

import thematicIcon from "/img/toolbox/data_management/join/toolbox.webp";
import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';


# Polygone Aggregieren

Das Werkzeug "Polygone Aggregieren" **führt statistische Analysen von Polygonen durch, z.B. Anzahl, Summe, Minimum oder Maximum, und aggregiert die Informationen auf Polygonen.**

## 1. Erklärung

Das Werkzeug "Polygone Aggregieren" kann verwendet werden, um **die Eigenschaften von Polygonen innerhalb eines bestimmten Gebiets zu analysieren**. Es aggregiert die Informationen der Polygone und ermöglicht die Berechnung der Polygonanzahl, die Summe von Polygonattributen oder die Ableitung z.B. des Maximalwerts eines bestimmten Polygonattributs innerhalb eines Aggregationsbereichs.

Das folgende Beispiel zeigt, dass die Geometrie des *Quell-Layers* unverändert bleibt, während seine Attribute durch die Aggregation von Informationen aus dem *Aggregationsbereich* angereichert werden.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
  <img src={require('/img/toolbox/geoanalysis/aggregate_polygons/polygon_aggregation.png').default} alt="Polygon-Aggregation" style={{ maxHeight: "400px", maxWidth: "400px", objectFit: "cover"}}/>
</div> 


## 2. Beispiel-Anwendungsfälle

- Visualisierung der Anzahl Parks pro Stadtbezirk.
- Berechnung der durchschnittlichen Gebäudegröße in einem Gebiet.
- Aggregation von Bevölkerungszahlen auf einem Hexagonal-Gitter und Berechnung von Bevölkerungsdichten.

## 3. Wie wird das Werkzeug verwendet?

<div class="step">
  <div class="step-number">1</div>
  <div class="content">Klicken Sie auf <code>Werkzeugleiste</code> <img src={thematicIcon} alt="toolbox" style={{width: "25px"}}/>. </div>
</div>

<div class="step">
  <div class="step-number">2</div>
  <div class="content">Klicken Sie im Menü <code>Geoanalyse</code> auf <code>Polygone Aggregieren</code>.</div>
</div>

### Zu aggregierender Layer

<div class="step">
  <div class="step-number">3</div>
  <div class="content">Wählen Sie Ihren <code>Quell-Layer</code>, der die Daten enthält, die Sie aggregieren möchten.</div>
</div>

### Zusammenfassungsbereiche

<div class="step">
  <div class="step-number">4</div>
  <div class="content">Wählen Sie den <code>Bereichstyp</code>, auf dem Sie den Quell-Layer aggregieren möchten. Sie können zwischen <b>Polygon</b> oder <b>H3-Gitter</b> wählen.</div>
</div>

<Tabs>
  <TabItem value="Polygon" label="Polygon" default className="tabItemBox">

 #### Polygon

<div class="step">
  <div class="step-number">5</div>
  <div class="content">Wählen Sie den <code>Bereichs-Layer</code>, der die Polygone enthält, auf denen Sie Ihre Punktdaten aggregieren möchten.</div>
</div>


  </TabItem>
  <TabItem value="H3 Grid" label="H3-Gitter" className="tabItemBox">

 #### H3-Gitter

 <div class="step">
  <div class="step-number">5</div>
  <div class="content">Wählen Sie die <code>H3-Gitter-Auflösung</code>. Sie können Auflösungen zwischen <b>3</b> (durchschnittliche Kantenlänge von 69km) und <b>10</b> (durchschnittliche Kantenlänge von 70m) wählen.</div>
</div>

:::tip HINWEIS

Um mehr über das H3-Gitter zu erfahren, können Sie das [Glossar](../../further_reading/glossary#H3-grid) besuchen.

:::

  </TabItem>
</Tabs>

### Statistiken

<div class="step">
  <div class="step-number">6</div>
  <div class="content">Wählen Sie die <code>Statistische Methode</code> und <code>Feld-Statistiken</code> (das Feld im Quell-Layer, das zur Gruppierung der Aggregation verwendet wird).</div>
</div>

Die verfügbaren **Statistische Methoden** sind in der folgenden Tabelle aufgeführt. Die verfügbaren Methoden hängen vom Datentyp des gewählten Attributs ab:

| Methode | Typ | Beschreibung |
| -------|------| ------------|
| Anzahl  | `string`,`number`    | Zählt die Anzahl der Nicht-Null-Werte in der ausgewählten Spalte|
| Summe    | `number`   | Berechnet die Summe aller Zahlen in der ausgewählten Spalte|
| Mittelwert   | `number`   | Berechnet den Durchschnittswert (Mittelwert) aller numerischen Werte in der ausgewählten Spalte|
| Median | `number`   | Liefert den mittleren Wert in der sortierten Liste der numerischen Werte der ausgewählten Spalte|
| Min    | `number`   | Liefert den Mindestwert der ausgewählten Spalte|
| Max    | `number`   | Liefert den Höchstwert der ausgewählten Spalte|


<div class="step">
  <div class="step-number">7</div>
  <div class="content">Falls gewünscht, können Sie die <code>Gewichtung nach Schnittflächenanteil</code> aktivieren, indem Sie auf die <code>Optionen-Schaltfläche</code> <img src={require('/img/map/styling/options_icon.png').default} alt="Options Icon" style={{ maxHeight: "25px", maxWidth: "25px", objectFit: "cover"}}/> klicken. Dadurch werden aggregierte Werte nach dem Anteil der Schnittfläche zwischen dem <i>Quell-Layer</i> und dem <i>Aggregations-Layer</i> gewichtet.</div>
</div>

<div class="step">
  <div class="step-number">8</div>
  <div class="content">Klicken Sie auf <code>Ausführen</code>.</div>
</div>

### Ergebnisse
Sobald der Berechnungsprozess abgeschlossen ist, wird der resultierende Layer <b>Aggregation Polygon</b> zur Karte hinzugefügt. Der Ergebnis-Layer besteht aus den Informationen des Quell-Layers und einer <b>zusätzlichen Spalte</b>, die die Ergebnisse der <b>statistischen Operation</b> zeigt. Sie können die Tabelle sehen, indem Sie auf das Polygon auf der Karte klicken.

<img src={require('/img/toolbox/geoanalysis/aggregate_polygons/aggregate_polygons_result.png').default} alt="Polygon-Aggregation Ergebnis in GOAT" style={{ maxHeight: "auto", maxWidth: "auto"}}/>

:::tip Tipp
Möchten Sie Ihren Ergebnis-Layer stylen und schön aussehende Karten erstellen? Siehe [Styling](../../map/layer_style/styling).
:::