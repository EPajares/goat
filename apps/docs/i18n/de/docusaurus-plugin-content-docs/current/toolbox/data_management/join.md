---
sidebar_position: 1
---

# Join

Dieses Werkzeug ermöglicht es Ihnen, **Daten aus zwei Layern basierend auf Attributabgleichen oder räumlichen Beziehungen zu kombinieren**. Dies ist wesentlich für räumliche Analysen, Datenanreicherung und die Erstellung umfassender Datensätze.

## 1. Erklärung

Das Verknüpfen (Join) ist der Prozess des Anhängens von Feldern aus einem Layer (Verknüpfungs-Layer) an einen anderen Layer (Ziel-Layer).

**GOAT unterstützt drei Arten von Verknüpfungen:**
1. **Attribut-Verknüpfung:** Gleicht Features basierend auf einem gemeinsamen Feld ab (z. B. Abgleich der "Postleitzahl" in beiden Layern).
2. **Räumliche Verknüpfung:** Gleicht Features basierend auf ihrer geometrischen Beziehung ab (z. B. "Features, die sich schneiden" oder "Features innerhalb einer Entfernung").
3. **Räumliche & Attribut-Verknüpfung:** Erfordert **sowohl** eine räumliche Überschneidung als auch ein passendes Attribut, um Features zu verknüpfen.

Das Ergebnis ist ein neuer Layer, der die Geometrie und Attribute des Ziel-Layers sowie die Attribute des Verknüpfungs-Layers enthält.

## 2. Beispiel-Anwendungsfälle

### Attribut-Verknüpfung
- Bevölkerungsdaten zu Postleitzahl-Gebieten hinzufügen (Abgleich über Postleitzahl).
- Umfragedaten mit Zensus-Bezirksgrenzen kombinieren (Abgleich über Bezirks-ID).

### Räumliche Verknüpfung
- Anzahl der Schulen in jedem Stadtbezirk zählen (Punkte in Polygonen).
- Die nächstgelegene Feuerwehrstation zu jedem Gebäude finden.
- Summierung der Gesamtlänge von Straßen innerhalb eines Parks.

## 3. Wie verwendet man das Werkzeug?

<div class="step">
  <div class="step-number">1</div>
  <div class="content">Klicken Sie auf <code>Toolbox</code> <img src={require('/img/icons/toolbox.png').default} alt="Options" style={{ maxHeight: "20px", maxWidth: "20px", objectFit: "cover"}}/>. </div>
</div>

<div class="step">
  <div class="step-number">2</div>
  <div class="content">Unter dem Menü <code>Datenverwaltung</code> klicken Sie auf <code>Join</code>.</div>
</div>

### Layer auswählen

<div class="step">
  <div class="step-number">3</div>
  <div class="content">Wählen Sie Ihren <code>Ziel-Layer</code>: Der Hauptlayer, den Sie behalten möchten.</div>
</div>

<div class="step">
  <div class="step-number">4</div>
  <div class="content">Wählen Sie Ihren <code>Verknüpfungs-Layer</code>: Der Layer, der die Daten enthält, die Sie hinzufügen möchten.</div>
</div>

### Verknüpfungsmethode wählen

<div class="step">
  <div class="step-number">5</div>
  <div class="content">Wählen Sie die <code>Verknüpfungsmethode</code>:</div>
</div>

- **Attribut:** Abgleich basierend auf Feldern.
- **Räumlich:** Abgleich basierend auf dem Standort.
- **Räumlich & Attribut:** Abgleich basierend auf beidem.

---

### Einstellungen (je nach Methode)

**Bei Attribut-Verknüpfung:**
- Wählen Sie das **Zielfeld** (Schlüssel im Ziel-Layer).
- Wählen Sie das **Verknüpfungsfeld** (Schlüssel im Verknüpfungs-Layer).

**Bei räumlicher Verknüpfung:**
- Wählen Sie die **Räumliche Beziehung** (z. B. Schnitt (Intersects), Innerhalb einer Entfernung, Vollständig enthalten).
- Bei "Innerhalb einer Entfernung" geben Sie die Suchentfernung und Einheiten an.

---

### Verknüpfungsoptionen (Kardinalität)

<div class="step">
  <div class="step-number">6</div>
  <div class="content">Wählen Sie die <code>Verknüpfungsoperation</code> (Eins-zu-Eins oder Eins-zu-Vielen).</div>
</div>

**Eins-zu-Eins:**
Wenn mehrere Features im Verknüpfungs-Layer auf ein einzelnes Feature im Ziel-Layer passen, müssen Sie wählen, wie diese behandelt werden sollen:
- **Erster Datensatz:** Verwendet den ersten passenden Datensatz (willkürliche Sortierung).
- **Statistiken berechnen:** Aggregiert die passenden Datensätze (z.B. Summe, Mittelwert, Minimum, Maximum).
- **Nur zählen:** Zählt lediglich, wie viele Übereinstimmungen gefunden wurden.

**Eins-zu-Vielen:**
Erstellt für *jedes* passende Feature im Verknüpfungs-Layer ein separates Feature in der Ausgabe (kann Zielgeometrien duplizieren).

### Ausführen

<div class="step">
  <div class="step-number">7</div>
  <div class="content">Klicken Sie auf <code>Ausführen</code>. Das Ergebnis wird der Karte hinzugefügt.</div>
</div>



### Ergebnisse
  
Der resultierende Layer **"Verknüpfung"** wird zu Ihrem Projekt und zu den [Datensätzen](../../workspace/datasets) in Ihrem Workspace hinzugefügt. Dieser Layer enthält alle Informationen vom Ziel-Layer plus einer **zusätzlichen Spalte** mit den Ergebnissen aus der **statistischen Operation**. Sie können die Attribute anzeigen, indem Sie auf ein beliebiges Feature in der Karte klicken.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>

  <img src={require('/img/toolbox/data_management/join/result.png').default} alt="Verknüpfungsergebnis in GOAT" style={{ maxHeight: "auto", maxWidth: "auto", objectFit: "cover"}}/>

</div> 

<p></p>


:::tip Tipp

Möchten Sie das Erscheinungsbild des Ergebnis-Layers anpassen? Schauen Sie sich das [attributbasierte Styling](../../map/layer_style/style/attribute_based_styling.md) an.

:::