# Mittelpunkt (Zentroid)

Dieses Werkzeug erstellt **Punkt-Features am geometrischen Mittelpunkt** jedes Features im Eingabe-Layer. Es ist nützlich, um Polygone oder Linien für Analysen, die Punkt-Eingaben erfordern, in Punkte umzuwandeln.

## 1. Erklärung

Ein Zentroid ist der geometrische Mittelpunkt eines Objekts. Bei einem Polygon ist es der "Massenmittelpunkt". Bei einer Linie ist es der Punkt, der von allen Punkten der Linie im Durchschnitt am wenigsten entfernt ist.

Das Ergebnis ist ein neuer Punkt-Layer, wobei jeder Punkt die Attribute des ursprünglichen Features erbt.

## 2. Beispiel-Anwendungsfälle

- **Standortanalyse:** Umwandeln von Wohnblöcken (Polygonen) in Punkte, um sie als Startpunkte für Erreichbarkeitsanalysen zu verwenden.
- **Visualisierung:** Erstellen von Punkten in der Mitte von Stadtteilen für eine übersichtlichere Kartendarstellung bei kleinen Maßstäben.
- **Datenkonvertierung:** Vorbereitung von Flächendaten für Werkzeuge, die nur Punkt-Geometrien unterstützen.

## 3. Wie verwendet man das Werkzeug?

<div class="step">
  <div class="step-number">1</div>
  <div class="content">Klicken Sie auf <code>Toolbox</code> <img src={require('/img/icons/toolbox.png').default} alt="Options" style={{ maxHeight: "20px", maxWidth: "20px", objectFit: "cover"}}/>.</div>
</div>

<div class="step">
  <div class="step-number">2</div>
  <div class="content">Unter dem Menü <code>Geoverarbeitung</code> klicken Sie auf <code>Centroid</code>.</div>
</div>

<div class="step">
  <div class="step-number">3</div>
  <div class="content">Wählen Sie Ihren <code>Eingabe-Layer</code>: Der Layer, für den Zentroide berechnet werden sollen.</div>
</div>

<div class="step">
  <div class="step-number">4</div>
  <div class="content">Klicken Sie auf <code>Ausführen</code>. Das Ergebnis wird der Karte hinzugefügt.</div>
</div>
