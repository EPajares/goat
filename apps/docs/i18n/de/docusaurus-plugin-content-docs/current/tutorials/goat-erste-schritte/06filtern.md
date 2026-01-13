---
slug: /tutorials/goat-erste-schritte/data-preparation
sidebar_position: 6
sidebar_label: ✏️ 6. Daten vorbereiten
---

# Daten vorbereiten

Um unsere Analyse speziell auf Mannheim zu fokussieren, filtern wir beide Layer.

### Den Grenzen-Layer filtern

1. **Klicken Sie auf den Layer "Regiostar Raumtypisierung"** - ein Panel erscheint rechts
2. **Wählen Sie die Registerkarte `Filter`**
3. **Klicken Sie auf `+ Ausdruck hinzufügen`** und wählen Sie `Logischer Ausdruck`
4. **Konfigurieren Sie den Filter:**
   - **Feld:** "name"
   - **Operator:** "ist"  
   - **Wert:** "mannheim" (suchen Sie nach diesem Wert)

<div style={{ display: 'flex', justifyContent: 'center' }}>
<img src={require('/img/tutorials/01_erste_schritte/filtern.gif').default} alt="Catchment Area Calculation Result in GOAT" style={{ maxHeight: "100%", maxWidth: "auto"}}/>
</div>

### Den Layer "POI Einkaufen" filtern & auschneiden

1. **Klicken Sie auf den Layer "POI Einkaufen"** - ein Panel erscheint rechts
2. **Wählen Sie die Registerkarte `Filter`**
3. **Klicken Sie auf `+ Ausdruck hinzufügen`** und wählen Sie `Logischer Ausdruck`
4. **Konfigurieren Sie den Filter:**
   - **Feld:** "category"
   - **Operator:** "Enthält"
   - **Wert:** "supermarket", "discount_supermarket" und "hypermarket"
  
5. **Klicken Sie auf `Toolbox`** in der oberen Menüleiste
6. **Unter dem `Geoverarbeitung` Menü klicken Sie auf `Ausschneiden`**
7. **Wählen Sie die folgenden Einstellungen:**
   - **Input layer:** "POI Einkaufen" (der Layer, den Sie ausschneiden möchten)
   - **Overlay layer:** "Regiostar Raumtypisierung" (Mannheim als Ausschnitt-Layer)
8. **Klicken Sie auf `Ausführen`**, um das Tool zu starten. Der neue ausgeschnittene Layer wird zur Karte hinzugefügt.
9. **Entfernen Sie den ursprünglichen "POI Einkaufen" Layer** und behalten Sie nur den neuen ausgeschnittenen Layer im Projekt.

### Layer umbenennen 

Für bessere Übersicht benennen wir die Layer um:

1. **Klicken Sie auf `Weitere Optionen` (⋯)** neben dem Layer "Regiostar Raumtypisierung" 
2. **Wählen Sie `Umbenennen`** und geben Sie "Mannheim" ein
3. **Wiederholen Sie für den neuen ausgeschnittenen Layer** und benennen Sie ihn in "Supermärkte" um