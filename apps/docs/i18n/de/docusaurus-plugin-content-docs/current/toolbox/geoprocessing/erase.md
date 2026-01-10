---
sidebar_position: 7
---

# Radieren

Mit diesem Werkzeug können Sie **Teile von Eingabe-Features entfernen, die sich mit der Radier-Geometrie überlappen**.

## 1. Erklärung

Das **Radieren**-Werkzeug entfernt Teile von Eingabe-Features, die sich mit den Radier-Features überlappen. Es ist im Wesentlichen das Gegenteil von Zuschneiden. Die Ausgabe enthält nur die Eingabe-Features (oder Teile davon), die **außerhalb** der Ausdehnung des Radier-Layers liegen.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>

  <img src={require('/img/toolbox/geoprocessing/erase.png').default} alt="Buffer Types" style={{ maxHeight: "400px", maxWidth: "400px", objectFit: "cover"}}/>

</div> 

## 2. Beispiel-Anwendungsfälle

- Entfernen von Wasserkörpern aus einer Landflächenkarte.
- Ausschluss von Schutzgebieten aus einer Karte potenzieller Entwicklungsstandorte.

## 3. Wie verwendet man das Werkzeug?

<div class="step">
  <div class="step-number">1</div>
  <div class="content">Klicken Sie auf <code>Werkzeuge</code> <img src={require('/img/icons/toolbox.png').default} alt="Options" style={{ maxHeight: "20px", maxWidth: "20px", objectFit: "cover"}}/>. </div>
</div>

<div class="step">
  <div class="step-number">2</div>
  <div class="content">Unter dem Menü <code>Geoverarbeitung</code> klicken Sie auf <code>Radieren</code>.</div>
</div>

<div class="step">
  <div class="step-number">3</div>
  <div class="content">Wählen Sie den <code>Eingabe-Layer</code>.</div>
</div>

<div class="step">
  <div class="step-number">4</div>
  <div class="content">Wählen Sie den <code>Überdeckungs-Layer</code>, der als Radier-Maske verwendet wird.</div>
</div>

<div class="step">
  <div class="step-number">5</div>
  <div class="content">Klicken Sie auf <code>Ausführen</code>, um die Radier-Operation auszuführen. Das Ergebnis wird zur Karte hinzugefügt.</div>
</div>
