---
sidebar_position: 4
---



# Quelle-Ziel

Das Werkzeug "Quelle-Ziel" ermöglicht es Ihnen, **Bewegungsströme zwischen verschiedenen Standorten zu visualisieren, indem Linien erstellt werden, die Quellen mit Zielen verbinden**. Perfekt für die Analyse von Pendlermustern, Verkehrsströmen und räumlichen Interaktionen.

<iframe width="674" height="378" src="https://www.youtube.com/embed/VmHe1NfApRw?si=xzUGIkh2IHn6DTTl" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>


## 1. Erklärung

Das Quelle-Ziel-Werkzeug erstellt **gerade Linien, die Startpunkte (Quellen) mit Endpunkten (Zielen) verbinden**, basierend auf Ihren Daten. Es nimmt eine Matrixtabelle mit Flussdaten und einen Geometrie-Layer mit Standorten und **visualisiert die Verbindungen und ihre Gewichtungen** als Linien auf der Karte.

Das folgende Beispiel zeigt eine *Eingabetabelle (Matrix-Layer)* und die resultierenden *Quelle-Ziel-Linien* basierend auf den *Postleitzahlengebieten (Geometrie-Layer)*.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
  <img src={require('/img/toolbox/geoanalysis/origin_destination/od_example.png').default} alt="Quelle-Ziel Werkzeug in GOAT" style={{ maxHeight: "auto", maxWidth: "500px", objectFit: "cover"}}/>
</div> 


## 2. Beispiel-Anwendungsfälle

- Visualisierung der Bewegungsströme zwischen Wohngebieten (Quellen) und Arbeitsplätzen (Zielen).
- Analyse der Fahrgastströme zwischen verschiedenen ÖV-Haltestellen oder Bahnhöfen.
- Untersuchung der Einkaufsströme von Wohngebieten zu Einkaufsstandorten.


## 3. Wie wird das Werkzeug verwendet?

<div class="step">
  <div class="step-number">1</div>
  <div class="content">Klicken Sie auf <code>Werkzeuge</code> <img src={require('/img/icons/toolbox.png').default} alt="Options" style={{ maxHeight: "20px", maxWidth: "20px", objectFit: "cover"}}/></div>
</div>

<div class="step">
  <div class="step-number">2</div>
  <div class="content">Klicken Sie im Menü <code>Geoanalyse</code> auf <code>Quelle-Ziel</code>.</div>
</div>

### Layer

<div class="step">
  <div class="step-number">3</div>
  <div class="content">Wählen Sie Ihren <code>Geometrie-Layer</code>. Dies sollte ein <b>Feature-Layer sein, der die Geometrien der Quellen und Ziele enthält und ein Attribut, das als Identifikator verwendet werden kann</b>, um die QZ-Verbindungen mit den Geometrien zu verknüpfen.</div>
</div>

<div class="step">
  <div class="step-number">4</div>
  <div class="content">Wählen Sie Ihr <code>Eindeutige-ID-Feld</code>.</div>
</div>

### Matrix

<div class="step">
  <div class="step-number">5</div>
  <div class="content">Wählen Sie die <code>Matrix-Tabelle</code>. Dies ist die <b>Tabelle mit der Quelle-Ziel-Matrix und dem Quell-Feld</b>.</div>
</div>

<div class="step">
  <div class="step-number">6</div>
  <div class="content">Wählen Sie Ihr <code>Ziel-Feld</code>. Dies ist <b>das Feld, das die Ziele in der Quelle-Ziel-Matrix enthält.</b></div>
</div>

<div class="step">
  <div class="step-number">7</div>
  <div class="content">Wählen Sie Ihr <code>Gewichtungs-Feld</code>. Dies ist das <b>Feld, das die Gewichtungen in der Quelle-Ziel-Matrix enthält</b>.</div>
</div>

<div class="step">
  <div class="step-number">8</div>
  <div class="content">Klicken Sie auf <code>Ausführen</code>.</div>
</div>

:::tip Hinweis

Je nach Komplexität der QZ-Matrix kann die Berechnung einige Minuten dauern. Die [Statusleiste](../../workspace/home#status-bar) zeigt den aktuellen Fortschritt an.

:::

### Ergebnisse 

Sobald der Berechnungsprozess abgeschlossen ist, werden die resultierenden Layer zur Karte hinzugefügt. Die Ergebnisse bestehen aus einem Layer namens **"Q-Z Relation"**, der die Linien zwischen den Quellen und Zielen zeigt, und einem Layer namens **"Q-Z Punkt"**, der alle Quell- und Zielpunkte bereitstellt (für Polygon-Geometrien werden die Schwerpunkte verwendet).

Wenn Sie auf ein "Q-Z Relation"-Element auf der Karte klicken, können Sie die Attributdetails anzeigen, wie die **Quelle**, das **Ziel** und die **Gewichtung** dieser Relation.

<img src={require('/img/toolbox/geoanalysis/origin_destination/result.png').default} alt="Quelle-Ziel Ergebnis in GOAT" style={{ maxHeight: "auto", maxWidth: "80%", objectFit: "cover"}}/>

:::tip Tipp
Möchten Sie Ihren Ergebnis-Layer stylen und schön aussehende Karten erstellen? Siehe [Styling](../../map/layer_style/style/styling).
:::