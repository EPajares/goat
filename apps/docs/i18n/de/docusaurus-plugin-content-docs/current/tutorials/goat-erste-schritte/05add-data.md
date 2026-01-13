---
slug: /tutorials/goat-erste-schritte/daten-hinzufügen
sidebar_position: 5
sidebar_label: ✏️ 5. Daten hinzufügen
---

# Daten zum Projekt hinzufügen

Für unsere Supermarkt-Erreichbarkeitsanalyse benötigen wir zwei wichtige Datensätze: Supermarkt-Standorte und Stadtgrenzen. Beide werden wir aus dem GOAT Katalog-Explorer hinzufügen.

## Supermarkt-Layer hinzufügen

1. **Klicken Sie auf `+ Layer hinzufügen`** unten links im linken Bereich
2. **Wählen Sie `Katalog-Explorer`**
3. **Suchen Sie den Datensatz "POI Einkaufen"**
4. **Klicken Sie auf `Layer hinzufügen`**, um ihn zu Ihrem Projekt hinzuzufügen

## Stadtgrenzen-Layer hinzufügen

1. **Klicken Sie erneut auf `+ Layer hinzufügen`** und wählen Sie `Katalog-Explorer`
2. **Suchen Sie den Layer "Regiostar Raumtypisierung"**, der alle Grenzen in Deutschland enthält
3. **Klicken Sie auf `Layer hinzufügen`**, um die Grenzen zu Ihrem Projekt hinzuzufügen

<div style={{ display: 'flex', justifyContent: 'center' }}>
<img src={require('/img/tutorials/01_erste_schritte/daten-hinzufugen.gif').default} alt="Catchment Area Calculation Result in GOAT" style={{ maxHeight: "100%", maxWidth: "auto"}}/>
</div>

<p></p>

:::tip Layer-Reihenfolge
Für eine optimale Kartenlesbarkeit müssen wir die Layer richtig anordnen:
**Wählen Sie im Layer-Bereich den neu hinzugefügten Layer "Regiostar Raumtypisierung" aus und ziehen Sie ihn unter den Layer "POI Einkaufen"**
:::




