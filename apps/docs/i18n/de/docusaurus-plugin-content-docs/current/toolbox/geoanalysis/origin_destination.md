---
sidebar_position: 4
---

import thematicIcon from "/img/toolbox/data_management/join/toolbox.webp";

# Quell-Ziel-Beziehungen

Die **Quell-Ziel-Beziehungen**-Analyse wird in verschiedenen Bereichen wie Verkehrsplanung und Stadtplanung verwendet, um **Bewegungen oder Flüsse zwischen verschiedenen Orten** zu untersuchen.

<iframe width="100%" height="500" src="https://www.youtube.com/embed/v5zCF0_9W2I?si=Wq3gCDZuNtXykKHY" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>

## 1. Erklärung

Das Quell-Ziel-Beziehungen (OD)-Werkzeug eignet sich zur Untersuchung von **Bewegungsmustern zwischen Standorten**, wie z.B. Pendlerströmen, und bietet Einblicke in räumliche Interaktionen. Dieser analytische Prozess visualisiert die Beziehungen zwischen **Ausgangspunkten (Quellen)** und **Endpunkten (Zielen)**, indem sie **mit einer geraden Linie verbunden** werden. Solche Analysen helfen zu verstehen, wie und warum Bewegungen in verschiedenen Kontexten stattfinden, und unterstützen die Bewertung und Planung von Verkehrsnetzen und städtischen Infrastrukturen. Es unterstützt datenbasierte Entscheidungen, indem **Muster und Trends in räumlichen Interaktionen** hervorgehoben werden, was zur Verbesserung der Effizienz und Nachhaltigkeit von Verkehrssystemen und Stadtstrukturen beiträgt.

Das untenstehende Beispiel zeigt eine *Eingabetabelle (Matrix)* und die resultierenden *Quell-Ziel-Linien* basierend auf den *Postleitzahlgebieten (Geometrien)*.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
  <img src={require('/img/toolbox/geoanalysis/origin_destination/od_example.png').default} alt="Origin Destination Tool in GOAT" style={{ maxHeight: "700px", maxWidth: "700px", objectFit: "cover"}}/>
</div> 


## 2. Anwendungsbeispiele

- Visualisierung der Pendlerströme zwischen Wohngebieten (Quellen) und Arbeitsplätzen (Zielen).
- Bewertung der Passagierströme im öffentlichen Nahverkehr zwischen verschiedenen Haltestellen.
- Analyse des Personenflusses von Wohngebieten (Quellen) zu Einkaufsorten (Zielen).

## 3. Wie benutzt man das Werkzeug?

<div class="step">
  <div class="step-number">1</div>
  <div class="content">Klicken Sie auf <code>Werkzeuge</code> <img src={thematicIcon} alt="toolbox" style={{width: "25px"}}/>. </div>
</div>

<div class="step">
  <div class="step-number">2</div>
  <div class="content">Drücken Sie anschließend im Menü<code>Geoanalyse</code> auf <code>Quell-Ziel-Beziehungen</code>.</div>
</div>

<img src={require('/img/toolbox/geoanalysis/origin_destination/overview.png').default} alt="Origin Destination Tool Overview" style={{ maxHeight: "auto", maxWidth: "auto", objectFit: "cover"}}/>

### Layer

<div class="step">
  <div class="step-number">3</div>
  <div class="content">Wählen Sie Ihren <code>Geometrien-Layer</code> (dies sollte ein Feature-Layer sein, der die Geometrien der Quellen und Ziele und ein Attribut enthält, das als Identifikator verwendet werden kann, um die Quell-Ziel-Beziehungen mit den Geometrien abzugleichen) und das Feld <code>Eindeutige ID</code>.</div>
</div>

### Matrix

<div class="step">
  <div class="step-number">4</div>
  <div class="content">Wählen Sie die <code>Matrix-Tabelle</code> (die Tabelle mit der Quell-Ziel-Matrix) und das <code>Feld Quelle</code>.</div>
</div>

<div class="step">
  <div class="step-number">5</div>
  <div class="content">Wählen Sie ein <code>Felder Ziel</code> (das Feld, das die Ziele in der Quell-Ziel-Matrix enthält).</div>
</div>

<div class="step">
  <div class="step-number">6</div>
  <div class="content">Anschließend bestimmen Sie das <code>Feld Gewichtung</code> (das Feld, das die Gewichte in der Quell-Ziel-Matrix enthält).</div>
</div>

<div class="step">
  <div class="step-number">7</div>
  <div class="content">Drücken Sie nun auf <code>Ausführen</code>.</div>
</div>

:::tip Tipp

Abhängig von der Komplexität der Quell-Ziel-Matrix kann die Berechnung einige Minuten dauern. Die [Statusleiste](../../workspace/home#status-bar) zeigt den aktuellen Fortschritt an.

:::

### Ergebnisse 

<div class="step">
  <div class="step-number">8</div>
  <div class="content">Sobald der Berechnungsprozess abgeschlossen ist, werden die resultierenden Layer zur Karte hinzugefügt. Die Ergebnisse bestehen aus einem Layer namens <b>"O-D-Relation"</b>, der die Linien zwischen den Quellen und Zielen zeigt, und einem Layer namens <b>"O-D-Punkt"</b>, der alle Quell- und Zielpunkte bereitstellt (für Polygone werden die Zentroiden verwendet).<p></p>
  Wenn Sie auf ein "O-D-Relation"-Element auf der Karte klicken, können Sie die Attributdetails anzeigen, wie z.B. die <b>Quelle</b>, das <b>Ziel</b> und die <b>Gewichtung</b> dieser Beziehung.</div>
</div>

<img src={require('/img/toolbox/geoanalysis/origin_destination/result.png').default} alt="Origin Destination Result in GOAT" style={{ maxHeight: "auto", maxWidth: "auto", objectFit: "cover"}}/>

:::tip TIPP
Möchten Sie Ihre Ergebnisslayer bearbeiten und ansprechende Karten erstellen? Dies können Sie unter [Layer Design](../../map/layer_style/styling).
:::