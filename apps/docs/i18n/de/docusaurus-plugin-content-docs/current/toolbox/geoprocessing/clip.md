# Clip

Dieses Werkzeug ermöglicht es Ihnen, **einen Layer auf die Ausdehnung eines anderen Layers zuzuschneiden**. Es funktioniert wie eine Ausstechform, bei der nur die Teile des Eingabe-Layers erhalten bleiben, die innerhalb der Geometrie des Clip-Layers liegen.

## 1. Erklärung

Das Zuschneiden (Clipping) ist eine grundlegende geoprocessing-Operation, die verwendet wird, um einen Datensatz auf ein bestimmtes Untersuchungsgebiet zu begrenzen.

- **Eingabe-Layer:** Der Layer, den Sie zuschneiden möchten (z. B. alle Straßen in einem Land).
- **Clip-Layer:** Der Layer, der die Grenzen definiert (z. B. eine Stadtgrenze).

Das Ergebnis enthält nur die Features (oder Teile von Features) aus dem Eingabe-Layer, die sich innerhalb des Clip-Layers befinden. Die Attribute des Eingabe-Layers bleiben erhalten.

## 2. Beispiel-Anwendungsfälle

- **Stadtplanung:** Zuschneiden eines nationalen Eisenbahnnetzes auf die Grenzen einer bestimmten Region.
- **Umweltanalyse:** Extrahieren von Waldgebieten, die innerhalb eines Naturschutzgebietes liegen.
- **Datenmanagement:** Erstellen eines kleineren, handlicheren Datensatzes für ein lokales Projekt aus einem globalen Datensatz.

## 3. Wie verwendet man das Werkzeug?

<div class="step">
  <div class="step-number">1</div>
  <div class="content">Klicken Sie auf <code>Toolbox</code> <img src={require('/img/icons/toolbox.png').default} alt="Options" style={{ maxHeight: "20px", maxWidth: "20px", objectFit: "cover"}}/>.</div>
</div>

<div class="step">
  <div class="step-number">2</div>
  <div class="content">Unter dem Menü <code>Geoverarbeitung</code> klicken Sie auf <code>Clip</code>.</div>
</div>

<div class="step">
  <div class="step-number">3</div>
  <div class="content">Wählen Sie Ihren <code>Eingabe-Layer</code>: Der Layer, der zugeschnitten werden soll.</div>
</div>

<div class="step">
  <div class="step-number">4</div>
  <div class="content">Wählen Sie Ihren <code>Clip-Layer</code>: Der Layer, der die Zuschneidegrenze definiert (muss ein Polygon sein).</div>
</div>

<div class="step">
  <div class="step-number">5</div>
  <div class="content">Klicken Sie auf <code>Ausführen</code>. Das Ergebnis wird der Karte hinzugefügt.</div>
</div>
