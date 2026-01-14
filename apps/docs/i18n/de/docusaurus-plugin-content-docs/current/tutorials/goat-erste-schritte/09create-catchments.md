---
slug: /tutorials/goat-erste-schritte/einzugsgebiete-erstellen
sidebar_position: 10
sidebar_label: ✏️ 10. Einzugsgebiete erstellen
---

# Einzugsgebiete erstellen

1. **Klicken Sie auf `Werkzeugkasten`** rechts neben dem linken Panel
2. **Unter "Erreichbarkeitsindikatoren"** klicken Sie auf `Einzugsgebiet`
3. **Wählen Sie `Zu Fuß`** als Routing-Typ für die Einzugsgebietsberechnung
4. **Wählen Sie die Berechnung des Einzugsgebiets basierend auf `Zeit`**
5. **Konfigurieren Sie die Parameter:**
   - **Reisezeit-Grenzwert:** 15 (Minuten)
   - **Reisegeschwindigkeit:** 5km/h (Standard belassen)
   - **Anzahl der Unterbrechungen:** 3
6. **Wählen Sie `Aus Layer auswählen`** als Startpunkt-Methode
7. **Wählen Sie den Layer "Supermärkte"** als Punkt-Layer
8. **Klicken Sie auf `Ausführen`** 

<div style={{ display: 'flex', justifyContent: 'center' }}>
<img src={require('/img/tutorials/01_erste_schritte/einzugsgebiet.gif').default} alt="Catchment Area Calculation Result in GOAT" style={{ maxHeight: "100%", maxWidth: "auto"}}/>
</div>

## Ergebnisse interpretieren

Sobald die Berechnung abgeschlossen ist ein neuer Layer "Einzugsgebiet" wird zur Karte hinzugefügt. Sie sehen farbige Polygone um jeden Supermarkt und die verschiedene Farben zeigen verschiedene Reisezeit-Zonen.

**💡 Klicken Sie auf ein beliebiges Einzugsgebiets-Polygon** - das Attribut `travel_cost` zeigt die Reisezeit in Minuten basierend auf unseren Berechnungseinstellungen.

Betrachten Sie Ihre Karte und notieren Sie:

🔍 **Gut versorgte Gebiete:** Bereiche mit starker Überlappung der Einzugsgebiete  
🔍 **Versorgungslücken:** Bereiche in Mannheim, die von keinem Einzugsgebiet abgedeckt sind  
🔍 **Randgebiete:** Stadtteile am Rand der 15-Minuten-Zonen  

:::success Glückwunsch!
Sie haben erfolgreich Ihre erste Erreichbarkeitsanalyse in GOAT erstellt! Die Einzugsgebiete zeigen nun visuell, welche Teile Mannheims gut mit Supermärkten versorgt sind.
:::