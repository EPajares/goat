---
sidebar_position: 4
---

# Überschneiden

Mit diesem Werkzeug können Sie **die geometrische Überschneidung von Features aus zwei Layern berechnen**.

## 1. Erklärung

Berechnet die **geometrische Überschneidung zweier Vektor-Layer.** Die Ausgabe enthält nur die Bereiche, in denen sich beide Eingabe-Layer überschneiden. Im Gegensatz zu Zuschneiden werden die Attribute von **beiden** Layern kombiniert und in den Ausgabe-Features beibehalten.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>

  <img src={require('/img/toolbox/geoprocessing/intersection.png').default} alt="Buffer Types" style={{ maxHeight: "400px", maxWidth: "400px", objectFit: "cover"}}/>

</div> 

## 2. Beispiel-Anwendungsfälle

- Finden von Bereichen, in denen eine geplante Entwicklung mit geschützten Umweltzonen überlappt.
- Identifizieren von Grundstücken, die sich in einer bestimmten Hochwasserrisikozone befinden.

## 3. Wie verwendet man das Werkzeug?

<div class="step">
  <div class="step-number">1</div>
  <div class="content">Klicken Sie auf <code>Werkzeuge</code> <img src={require('/img/icons/toolbox.png').default} alt="Options" style={{ maxHeight: "20px", maxWidth: "20px", objectFit: "cover"}}/>. </div>
</div>

<div class="step">
  <div class="step-number">2</div>
  <div class="content">Unter dem Menü <code>Geoverarbeitung</code> klicken Sie auf <code>Überschneiden</code>.</div>
</div>

<div class="step">
  <div class="step-number">3</div>
  <div class="content">Wählen Sie den <code>Eingabe-Layer</code>, den Sie zuschneiden möchten.</div>
</div>

<div class="step">
  <div class="step-number">4</div>
  <div class="content">Wählen Sie den <code>Überdeckungs-Layer</code>, den Sie als zweite Eingabe verwenden möchten.</div>
</div>

<div class="step">
  <div class="step-number">5</div>
  <div class="content">Optional können Sie den Umschalter für <code>Feldauswahl</code> aktivieren, um auszuwählen, welche Attribute in die Ausgabe eingeschlossen werden sollen:
    <ul>
      <li>Wählen Sie spezifische Felder aus dem <code>Eingabe-Layer</code>, die im Ergebnis beibehalten werden sollen</li>
      <li>Wählen Sie spezifische Felder aus dem <code>Überdeckungs-Layer</code>, die im Ergebnis beibehalten werden sollen</li>
      <li>Ändern Sie bei Bedarf das <code>Überdeckungs-Felder-Präfix</code>, um Namenskonflikte zu vermeiden (Standard: "intersection_")</li>
    </ul>
  </div>
</div>

:::tip Hinweis

Wenn keine Felder ausgewählt werden, werden alle Attribute beider Layer in die Ausgabe eingeschlossen.

:::
    

<div class="step">
  <div class="step-number">6</div>
  <div class="content">Klicken Sie auf <code>Ausführen</code>, um die Überschneidung auszuführen. Das Ergebnis wird zur Karte hinzugefügt.</div>
</div>

