---
sidebar_position: 3
---

# Mittelpunkt

Mit diesem Werkzeug können Sie **Punkt-Features am geometrischen Zentrum jedes Eingabe-Features erstellen**.

## 1. Erklärung

Berechnet das **geometrische Zentrum (Zentroid) von Polygon- oder Linien-Features und stellt sie als Punkte dar.** Für Polygone ist der Zentroid der "Massenmittelpunkt". Beachten Sie, dass bei unregelmäßig geformten Polygonen der wahre Zentroid außerhalb der Polygongrenze liegen könnte.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>

  <img src={require('/img/toolbox/geoprocessing/centroid.png').default} alt="Buffer Types" style={{ maxHeight: "400px", maxWidth: "400px", objectFit: "cover"}}/>

</div> 

## 2. Beispiel-Anwendungsfälle

- Umwandlung von Gebäudegrundrissen in Punkte für vereinfachte Visualisierung oder Analyse.
- Finden des Mittelpunkts von Stadtteilen für die Beschriftung.

## 3. Wie verwendet man das Werkzeug?

<div class="step">
  <div class="step-number">1</div>
  <div class="content">Klicken Sie auf <code>Werkzeuge</code> <img src={require('/img/icons/toolbox.png').default} alt="Options" style={{ maxHeight: "20px", maxWidth: "20px", objectFit: "cover"}}/>. </div>
</div>

<div class="step">
  <div class="step-number">2</div>
  <div class="content">Unter dem Menü <code>Geoverarbeitung</code> klicken Sie auf <code>Mittelpunkt</code>.</div>
</div>

<div class="step">
  <div class="step-number">3</div>
  <div class="content">Wählen Sie den Eingabe-Layer.</div>
</div>

<div class="step">
  <div class="step-number">4</div>
  <div class="content">Klicken Sie auf <code>Ausführen</code>, um die Zentroide zu generieren. Das Ergebnis wird der Karte hinzugefügt.</div>
</div>
