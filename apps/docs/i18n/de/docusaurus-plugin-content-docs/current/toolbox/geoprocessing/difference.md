# Differenz (Erase)

Dieses Werkzeug erstellt einen neuen Layer, indem es **Teile des Eingabe-Layers entfernt, die sich mit einem anderen Layer überschneiden**. Es funktioniert wie ein "Radiergummi", der Bereiche löscht.

## 1. Erklärung

Die Differenz-Operation (auch bekannt als Erase) zieht die Geometrie eines Layers von einem anderen ab.

- **Eingabe-Layer:** Der Layer, von dem Sie Teile entfernen möchten.
- **Erase-Layer:** Der Layer, dessen Form bestimmt, was entfernt wird.

Das Ergebnis enthält nur die Teile des Eingabe-Layers, die *nicht* mit dem Erase-Layer überlappen.

## 2. Beispiel-Anwendungsfälle

- **Ausschlussgebiete:** Entfernen von Wasserflächen oder Naturschutzgebieten aus einer Karte für bebaubare Flächen.
- **Infrastrukturplanung:** Ausschließen von bestehenden Gebäuden aus einem Layer, der potenzielle neue Parkflächen zeigt.
- **Datenbereinigung:** Entfernen von Gebieten, für die bereits Daten in einem anderen System vorhanden sind, um Dubletten zu vermeiden.

## 3. Wie verwendet man das Werkzeug?

<div class="step">
  <div class="step-number">1</div>
  <div class="content">Klicken Sie auf <code>Toolbox</code> <img src={require('/img/icons/toolbox.png').default} alt="Options" style={{ maxHeight: "20px", maxWidth: "20px", objectFit: "cover"}}/>.</div>
</div>

<div class="step">
  <div class="step-number">2</div>
  <div class="content">Unter dem Menü <code>Geoverarbeitung</code> klicken Sie auf <code>Erase</code>.</div>
</div>

<div class="step">
  <div class="step-number">3</div>
  <div class="content">Wählen Sie Ihren <code>Eingabe-Layer</code>: Der Layer, der bereinigt werden soll.</div>
</div>

<div class="step">
  <div class="step-number">4</div>
  <div class="content">Wählen Sie Ihren <code>Erase-Layer</code>: Der Layer, der die zu entfernenden Bereiche definiert.</div>
</div>

<div class="step">
  <div class="step-number">5</div>
  <div class="content">Klicken Sie auf <code>Ausführen</code>. Das Ergebnis wird der Karte hinzugefügt.</div>
</div>
