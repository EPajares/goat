# Schnittmenge (Intersect)

Dieses Werkzeug berechnet die **geometrische Schnittmenge von Features aus zwei Layern**. Das Ergebnis enthält nur die Bereiche, in denen sich die Features beider Layer überschneiden.

## 1. Erklärung

Die Schnittmengen-Operation (Intersection) findet die überlappenden Teile von zwei Datensätzen.

- **Eingabe-Layer:** Der primäre Datensatz.
- **Schnitt-Layer:** Der Datensatz, mit dem die Überschneidungen gesucht werden.

Im Gegensatz zum [Clip-Werkzeug](./clip.md) kombiniert das Intersect-Werkzeug die Attribute beider Layer für die resultierenden Features. Wenn sich beispielsweise ein Wald-Polygon und ein Landkreis-Polygon überschneiden, enthält das Ergebnis-Polygon sowohl die Wald-Informationen als auch die Landkreis-Informationen.

## 2. Beispiel-Anwendungsfälle

- **Landnutzung:** Identifizierung von Wohngebieten, die innerhalb einer Hochwassergefahrenzone liegen.
- **Politische Analyse:** Feststellung, welche Wahlbezirke von einem geplanten Infrastrukturprojekt betroffen sind.
- **Ressourcenmanagement:** Berechnung der Waldfläche innerhalb verschiedener Bodentypen.

## 3. Wie verwendet man das Werkzeug?

<div class="step">
  <div class="step-number">1</div>
  <div class="content">Klicken Sie auf <code>Toolbox</code> <img src={require('/img/icons/toolbox.png').default} alt="Options" style={{ maxHeight: "20px", maxWidth: "20px", objectFit: "cover"}}/>.</div>
</div>

<div class="step">
  <div class="step-number">2</div>
  <div class="content">Unter dem Menü <code>Geoverarbeitung</code> klicken Sie auf <code>Intersect</code>.</div>
</div>

<div class="step">
  <div class="step-number">3</div>
  <div class="content">Wählen Sie Ihren <code>Eingabe-Layer</code>.</div>
</div>

<div class="step">
  <div class="step-number">4</div>
  <div class="content">Wählen Sie Ihren <code>Schnitt-Layer</code>.</div>
</div>

<div class="step">
  <div class="step-number">5</div>
  <div class="content">Klicken Sie auf <code>Ausführen</code>. Das Ergebnis wird der Karte hinzugefügt.</div>
</div>
