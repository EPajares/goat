---
sidebar_position: 6
---

# Vereinigen

Mit diesem Werkzeug können Sie **die geometrische Vereinigung von Features aus zwei Layern berechnen**.

## 1. Erklärung

Kombiniert **Features aus zwei Polygon-Layern** zu einem einzigen Layer. Die Ausgabe enthält alle Geometrien aus beiden Eingaben (wie eine boolesche ODER-Operation). Wo sich Features überlappen, werden sie geteilt, und Attribute aus beiden Layern werden den überlappenden Bereichen zugeordnet. Nicht überlappende Bereiche behalten nur Attribute aus ihrem ursprünglichen Layer.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>

  <img src={require('/img/toolbox/geoprocessing/union.png').default} alt="Buffer Types" style={{ maxHeight: "400px", maxWidth: "400px", objectFit: "cover"}}/>

</div> 

## 2. Beispiel-Anwendungsfälle

- Kombinieren zweier verschiedener Landnutzungsdatensätze zu einer einzigen umfassenden Karte.
- Zusammenführung von Zonierungsbezirken mit Schulbezirken zur Analyse aller einzigartigen Kombinationen von Verwaltungsgrenzen.

## 3. Wie verwendet man das Werkzeug?

<div class="step">
  <div class="step-number">1</div>
  <div class="content">Klicken Sie auf <code>Werkzeuge</code> <img src={require('/img/icons/toolbox.png').default} alt="Options" style={{ maxHeight: "20px", maxWidth: "20px", objectFit: "cover"}}/>. </div>
</div>

<div class="step">
  <div class="step-number">2</div>
  <div class="content">Unter dem Menü <code>Geoverarbeitung</code> klicken Sie auf <code>Vereinigen</code>.</div>
</div>

<div class="step">
  <div class="step-number">3</div>
  <div class="content">Wählen Sie den ersten <code>Eingabe-Layer</code>.</div>
</div>

<div class="step">
  <div class="step-number">4</div>
  <div class="content">Wählen Sie den zweiten Layer für <code>Überdeckungs-Layer</code>.</div>
</div>

<div class="step">
  <div class="step-number">5</div>
  <div class="content">Wählen Sie das <code>Überdeckungs-Felder-Präfix</code>, das den Attributen aus dem Überdeckungs-Layer hinzugefügt wird, um sie in der Ausgabe zu unterscheiden.</div>
</div>

<div class="step">
  <div class="step-number">6</div>
  <div class="content">Klicken Sie auf <code>Ausführen</code>, um die Vereinigung auszuführen. Das Ergebnis wird zur Karte hinzugefügt.</div>
</div>
