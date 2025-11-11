---
sidebar_position: 1
---

import thematicIcon from "/img/toolbox/data_management/join/toolbox.webp";


# Verknüpfen & Gruppieren

Dieses **Werkzeug** ermöglicht es Ihnen, **Daten aus zwei Layern zu kombinieren und zusammenzufassen, indem ein Attribut in beiden abgeglichen wird**. Dies ist wesentlich für räumliche Analysen, Datenanreicherung und die Erstellung umfassender **Datensätze**.


## 1. Erklärung

Dieses **Werkzeug** ermöglicht es Ihnen, zwei **Datensätze** zu kombinieren, indem ihre Features durch ein gemeinsames Attribut (zum Beispiel eine ID oder einen Namen) verknüpft werden. **Das Ergebnis ist ein neuer Layer, der alle Attribute vom Ziel-Layer behält, plus einer zusätzlichen Spalte, die ausgewählte Informationen vom Verknüpfungs-Layer zusammenfasst.**

**GOAT verwendet einen Inner Join, um die **Daten** zu kombinieren**. Das bedeutet, es gleicht Features (Zeilen) vom Ziel-Layer und dem Verknüpfungs-Layer ab, wo sie denselben Wert im gewählten Abgleichsfeld (Spalte) teilen.
**Nur Features, die in beiden Layern mit demselben Wert existieren, werden in die Ausgabe eingeschlossen.** Wenn ein Feature im Ziel-Layer kein passendes im Verknüpfungs-Layer hat, erscheint es nicht im Ergebnis.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>

  <img src={require('/img/toolbox/data_management/join/join_and_group.png').default} alt="Verknüpfungs-Werkzeug in GOAT" style={{ maxHeight: "auto", maxWidth: "auto", objectFit: "cover"}}/>

</div> 

## 2. Beispiel-Anwendungsfälle

- Bevölkerungs**daten** zu Postleitzahl-Gebieten hinzufügen (Abgleich über Postleitzahl).
- Umfrage**daten** mit Zensus-Bezirksgrenzen kombinieren (Abgleich über Bezirks-ID).
- Pendlerzahlen mit Stadtgrenzen verknüpfen (Abgleich über Stadtname).

## 3. Wie verwendet man das Werkzeug?

<div class="step">
  <div class="step-number">1</div>
  <div class="content">Klicken Sie auf <code>Werkzeugkiste</code> <img src={thematicIcon} alt="Werkzeugkiste" style={{width: "25px"}}/>. </div>
</div>

<div class="step">
  <div class="step-number">2</div>
  <div class="content">Unter dem <code>Datenverwaltung</code>-Menü klicken Sie auf <code>Verknüpfen & Gruppieren</code>.</div>
</div>

### Layer zum Verknüpfen auswählen 

<div class="step">
  <div class="step-number">3</div>
  <div class="content">  Wählen Sie Ihren <code>Ziel-Layer</code>: die primäre Tabelle oder Layer, zu dem Sie zusätzliche **Daten** hinzufügen möchten. </div>
</div>

<div class="step">
  <div class="step-number">4</div>
  <div class="content">Wählen Sie Ihren <code>Verknüpfungs-Layer</code>: die sekundäre Tabelle oder **Datensatz**, der die Datensätze und Attribute enthält, die in den Ziel-Layer eingefügt werden sollen. </div>
</div>

### Felder zum Abgleichen

<div class="step">
  <div class="step-number">5</div>
  <div class="content">Wählen Sie das <code>Zielfeld</code> des Ziel-Layers, das Sie für den Abgleich der Datensätze beider Layer verwenden möchten.</div>
</div>

<div class="step">
  <div class="step-number">6</div>
  <div class="content"> Wählen Sie das passende Attribut des Verknüpfungs-Layers als <code>Verknüpfungsfeld</code>. </div>
</div>

### Statistiken

<div class="step">
  <div class="step-number">7</div>
  <div class="content"> Wählen Sie die <code>Statistikmethode</code>, die verwendet werden soll, um das Attribut zu verknüpfen. </div>
</div>

Sie können zwischen verschiedenen statistischen Operationen wählen. Einige Methoden sind nur für spezifische Datentypen verfügbar. Die folgende Liste bietet eine Übersicht über die verfügbaren Methoden:

| Methode | Datentypen | Beschreibung |
| -------|------| ------------|
| Anzahl  | `string`,`number`    | Zählt die Anzahl der nicht-null Werte in der ausgewählten Spalte|
| Summe    | `number`   | Berechnet die Summe aller Zahlen in der ausgewählten Spalte|
| Mittelwert   | `number`   | Berechnet den Durchschnitt (Mittelwert) aller numerischen Werte in der ausgewählten Spalte|
| Median | `number`   | Ergibt den mittleren Wert in der sortierten Liste numerischer Werte der ausgewählten Spalte|
| Min    | `number`   | Ergibt den Minimalwert der ausgewählten Spalte|
| Max    | `number`   | Ergibt den Maximalwert der ausgewählten Spalte|

<div class="step">
  <div class="step-number">8</div>
  <div class="content">Wählen Sie die <code>Feldstatistiken</code>, für die Sie die statistische Operation anwenden möchten.</div>
</div>

<div class="step">
  <div class="step-number">9</div>
  <div class="content">Klicken Sie auf <code>Ausführen</code>.</div>
</div>


### Ergebnisse
  
Der resultierende Layer **"Verknüpfung"** wird zu Ihrem **Projekt** und zu den [Datensätzen](../../workspace/datasets) in Ihrem **Workspace** hinzugefügt. Dieser Layer enthält alle Informationen vom Ziel-Layer plus einer **zusätzlichen Spalte** mit den Ergebnissen aus der **statistischen Operation**. Sie können die Attribute anzeigen, indem Sie auf ein beliebiges Feature in der Karte klicken.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>

  <img src={require('/img/toolbox/data_management/join/result.png').default} alt="Verknüpfungsergebnis in GOAT" style={{ maxHeight: "auto", maxWidth: "auto", objectFit: "cover"}}/>

</div> 


:::tip Tipp

Möchten Sie das Erscheinungsbild des Ergebnis-Layers anpassen? Schauen Sie sich das [attributbasierte Styling](../../map/layer_style/style/attribute_based_styling.md) an.

:::