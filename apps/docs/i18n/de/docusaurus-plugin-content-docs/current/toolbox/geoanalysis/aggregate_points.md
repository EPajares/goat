---
sidebar_position: 1
---
import thematicIcon from "/img/toolbox/data_management/join/toolbox.webp";
import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';

# Punkte Aggregieren

Das Werkzeug "Punkte Aggregieren" **führt statistische Analysen von Punkten durch, z.B. Anzahl, Summe, Minimum oder Maximum, und aggregiert die Informationen auf Polygonen.**

<iframe width="674" height="378" src="https://www.youtube.com/embed/_ybPf_fuMLA?si=mX1-uugIA5LiCKss" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>

## 1. Erklärung

Das Werkzeug "Punkte Aggregieren" kann verwendet werden, um **die Eigenschaften von Punkten innerhalb eines bestimmten Gebiets zu analysieren**. Es aggregiert die Informationen der Punkte und ermöglicht dadurch die Berechnung der Punktanzahl, die Summe von Punktattributen oder die Ableitung z.B. des Maximalwerts eines bestimmten Punktattributs innerhalb eines Polygons. Als Polygon-Layer kann entweder ein Feature-Layer (z.B. Stadtbezirke) oder ein Hexagonal-Gitter verwendet werden.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>

  <img src={require('/img/toolbox/geoanalysis/aggregate_points/point_aggregation.png').default} alt="Punkt-Aggregation" style={{ maxHeight: "600px", maxWidth: "600px", objectFit: "cover"}}/>

</div> 


## 2. Beispiel-Anwendungsfälle

- Aggregation der Bevölkerungszahlen auf einem Hexagon-Gitter.
- Ableitung der Summe von Verkehrsunfällen innerhalb eines Stadtbezirks.
- Visualisierung der durchschnittlichen Anzahl verfügbarer Carsharing-Fahrzeuge pro Station auf Bezirksebene.

## 3. Wie wird das Werkzeug verwendet?

<div class="step">
  <div class="step-number">1</div>
  <div class="content">Klicken Sie auf <code>Werkzeugleiste</code> <img src={thematicIcon} alt="toolbox" style={{width: "25px"}}/>. </div>
</div>

<div class="step">
  <div class="step-number">2</div>
  <div class="content">Klicken Sie im Menü <code>Geoanalyse</code> auf <code>Punkte Aggregieren</code>.</div>
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
  <div class="content">Wählen Sie die <code>Statistische Methode</code> und das Feld, das Sie für die <code>Feld-Statistiken</code> verwenden möchten (das Feld im Quell-Layer, das zur Gruppierung der aggregierten Punkte für Statistiken verwendet wird).</div>
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
  <div class="content">Klicken Sie auf <code>Ausführen</code>.</div>
</div>

### Ergebnisse

Sobald der Berechnungsprozess abgeschlossen ist, wird der resultierende Layer **"Aggregation Punkt"** zur Karte hinzugefügt. Dieser Layer besteht aus den Informationen des Quell-Layers und einer **zusätzlichen Spalte**, die die Ergebnisse der **statistischen Operation** zeigt. Sie können die Tabelle sehen, indem Sie auf das Polygon auf der Karte klicken.

<img src={require('/img/toolbox/geoanalysis/aggregate_points/aggregate_points_result.png').default} alt="Punkt-Aggregation Ergebnis in GOAT" style={{ maxHeight: "auto", maxWidth: "auto"}}/>


:::tip Tipp
Möchten Sie Ihren Ergebnis-Layer stylen und schön aussehende Karten erstellen? Siehe [Styling](../../map/layer_style/styling).
:::