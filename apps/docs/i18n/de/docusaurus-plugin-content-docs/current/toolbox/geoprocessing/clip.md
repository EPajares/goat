---
sidebar_position: 2
---

# Ausschneiden

Mit diesem Werkzeug können Sie **Eingabe-Features extrahieren, die innerhalb des Zuschnitt-Layers liegen**.

## 1. Erklärung

Bezieht sich auf den Prozess der **Extraktion eines Teils eines Vektor-Datensatzes basierend auf der Grenze eines anderen Polygon-Layers.** Es funktioniert wie ein "Plätzchenausstecher" – nur die Features (oder Teile von Features) aus dem Eingabe-Layer, die innerhalb des Zuschnitt-Layers liegen, werden beibehalten. Die Attribute der Eingabe-Features werden erhalten, aber die Attribute des Zuschnitt-Layers werden nicht übertragen.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>

  <img src={require('/img/toolbox/geoprocessing/clip.png').default} alt="Buffer Types" style={{ maxHeight: "400px", maxWidth: "400px", objectFit: "cover"}}/>

</div> 

## 2. Beispiel-Anwendungsfälle

- Extrahieren einer Teilmenge von Stadtstraßen basierend auf einer bestimmten Stadtteilgrenze.
- Zuschneiden einer Landnutzungskarte auf ein Projektgebiet von Interesse.

## 3. Wie verwendet man das Werkzeug?

<div class="step">
  <div class="step-number">1</div>
  <div class="content">Klicken Sie auf <code>Werkzeuge</code> <img src={require('/img/icons/toolbox.png').default} alt="Options" style={{ maxHeight: "20px", maxWidth: "20px", objectFit: "cover"}}/>. </div>
</div>

<div class="step">
  <div class="step-number">2</div>
  <div class="content">Unter dem Menü <code>Geoverarbeitung</code> klicken Sie auf <code>Ausschneiden</code>.</div>
</div>

<div class="step">
  <div class="step-number">3</div>
  <div class="content">Wählen Sie den <code>Eingabe-Layer</code>, den Sie zuschneiden möchten.</div>
</div>

<div class="step">
  <div class="step-number">4</div>
  <div class="content">Wählen Sie den <code>Überdeckungs-Layer</code>, den Sie als Zuschnitt-Layer verwenden möchten.</div>
</div>

<div class="step">
  <div class="step-number">5</div>
  <div class="content">Klicken Sie auf <code>Ausführen</code>, um das Werkzeug auszuführen. Das Ergebnis wird zur Karte hinzugefügt.</div>
</div>
