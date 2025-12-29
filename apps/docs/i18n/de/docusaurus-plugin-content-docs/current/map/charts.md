---
sidebar_position: 5
---

# Diagramme

Die Diagramm-Funktion ermöglicht es Ihnen, **aggregierte Daten schnell zu visualisieren**, die aus den Werkzeugen **Polygone aggregieren** und **Punkte aggregieren** stammen, ohne komplexe Konfiguration und zeigt die Beziehung zwischen Ihren Quell- und Ziel-Layern.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/map/charts/charts.gif').default} alt="Diagramm-Werkzeug in GOAT" style={{ maxHeight: "auto", maxWidth: "80%", objectFit: "cover"}}/>
</div> 

## Wie man Diagramme verwendet

<div class="step">
  <div class="step-number">1</div>
  <div class="content">Finden Sie Ihren aggregierten Layer im <code>Layer</code>-Panel und klicken Sie auf das <img src={require('/img/icons/3dots.png').default} alt="Weitere Optionen" style={{ maxHeight: "20px", maxWidth: "20px", verticalAlign: "middle", marginRight: "4px" }}/> <b>Weitere Optionen</b>-Menü neben dem Layer-Namen.</div>
</div>

<div class="step">
  <div class="step-number">2</div>
  <div class="content">Wählen Sie <code>Diagramm anzeigen</code> aus dem Dropdown-Menü. Ein Popup-Fenster erscheint mit Ihrer Datenvisualisierung.</div>
</div>

<div class="step">
  <div class="step-number">3</div>
  <div class="content">Wählen Sie Ihren bevorzugten <code>Diagrammtyp</code> aus den verfügbaren Optionen:
    <ul>
      <li><b>Vertikales Balkendiagramm</b>: Klassisches Säulendiagramm-Format</li>
      <li><b>Horizontales Balkendiagramm</b>: Horizontale Balken für bessere Lesbarkeit der Beschriftungen</li>
      <li><b>Liniendiagramm</b>: Verbundene Punkte, die Datentrends zeigen</li>
    </ul>
  </div>
</div>

<div class="step">
  <div class="step-number">4</div>
  <div class="content">Aktivieren Sie die Option <code>Kumulierte Summe</code>, wenn Sie laufende Gesamtsummen anstelle von Einzelwerten anzeigen möchten.</div>
</div>

<div class="step">
  <div class="step-number">5</div>
  <div class="content">Bewegen Sie den Mauszeiger über Diagrammelemente, um präzise Werte und zusätzliche Details für jeden Datenpunkt zu sehen.</div>
</div>

:::info Hinweis

Diagrammachsen werden automatisch basierend auf Ihrer Aggregations-Einrichtung bestimmt und können nicht manuell konfiguriert werden. Wenn Sie die Diagrammoption nicht sehen, stellen Sie sicher, dass Ihr Layer aggregierte Daten aus räumlichen Analysewerkzeugen enthält.

:::