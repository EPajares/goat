---
sidebar_position: 5
---

# Zusammenführen

Mit diesem Werkzeug können Sie **Features einer Ebene zusammenführen, die gemeinsame Attributwerte haben** oder alle Features zu einer einzigen Geometrie auflösen.

## 1. Erklärung

Das **Zusammenführen**-Werkzeug führt Features basierend auf gemeinsamen Attributwerten zusammen oder kombiniert alle Features zu einer einheitlichen Geometrie. Diese Operation eliminiert interne Grenzen zwischen Features mit den gleichen Eigenschaften und erstellt vereinfachte Ausgabe-Ebenen. Es wird häufig für die Konsolidierung von Verwaltungsgrenzen und die Datenverallgemeinerung verwendet.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>

  <img src={require('/img/toolbox/geoprocessing/dissolve.png').default} alt="Buffer Types" style={{ maxHeight: "400px", maxWidth: "400px", objectFit: "cover"}}/>

</div> 

## 2. Beispiel-Anwendungsfälle

- Zusammenführung benachbarter Bezirke, die zur gleichen Verwaltungseinheit gehören.
- Kombinierung angrenzender Parzellen mit der gleichen Landnutzungsklassifikation.

## 3. Wie verwendet man das Werkzeug?

<div class="step">
  <div class="step-number">1</div>
  <div class="content">Klicken Sie auf <code>Werkzeuge</code> <img src={require('/img/icons/toolbox.png').default} alt="Options" style={{ maxHeight: "20px", maxWidth: "20px", objectFit: "cover"}}/>. </div>
</div>

<div class="step">
  <div class="step-number">2</div>
  <div class="content">Unter dem Menü <code>Geoverarbeitung</code> klicken Sie auf <code>Zusammenführen</code>.</div>
</div>

<div class="step">
  <div class="step-number">3</div>
  <div class="content">Wählen Sie den <code>Eingabe-Layer</code>, der die Features enthält, die Sie zusammenführen möchten.</div>
</div>

<div class="step">
  <div class="step-number">4</div>
  <div class="content">In den <code>Zusammenführen-Einstellungen</code> wählen Sie die Felder aus, nach denen beim Zusammenführen gruppiert werden soll. Features mit übereinstimmenden Werten werden zusammengeführt. Wenn leer, werden alle Features zu einem zusammengeführt.</div>
</div>

<div class="step">
  <div class="step-number">5</div>
  <div class="content">Wenn Ihr Layer numerische Felder hat, aktivieren Sie <code>Statistiken</code> zur Berechnung von Zusammenfassungswerten. Wählen Sie die <code>Operation</code> (Summe, Mittelwert, Anzahl, etc.) und wählen Sie das <code>Feld</code> zur Aggregierung während des Zusammenführens.</div>
</div>

<div class="step">
  <div class="step-number">6</div>
  <div class="content">Klicken Sie auf <code>Ausführen</code>, um das Zusammenführen auszuführen. Das Ergebnis wird zur Karte hinzugefügt.</div>
</div>
