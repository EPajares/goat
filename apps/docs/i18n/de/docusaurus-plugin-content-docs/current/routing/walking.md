---
sidebar_position: 1
 
---
 
# Zu Fuß
 
Das **Verkehrsmittel Zu Fuß**  wird für alle Analysen in GOAT verwendet, die zu Fuß zurückgelegte Strecken enthalten. 
 
## 1. Ziele

Das Verkehrsmittel "Zu Fuß" wird für viele Indikatoren in GOAT verwendet, wie z.B. [Catchment Areas](../toolbox/accessibility_indicators/catchments "Visit Docs on Catchment Areas"), [Heatmaps](../toolbox/accessibility_indicators/connectivity "Visit Docs on Heatmaps"), und [PT Nearby Stations](../toolbox/accessibility_indicators/nearby_stations "Visit Docs on PT Nearby Stations"). Da GOAT auch die Erstellung von [Szenarien für das Straßennetz](../Scenarios#4-straßennetz---kanten), erlaubt, wird ein **angepasster Routing-Algorithmus** benötigt, der auch die Änderungen des Szenarios in den Erreichbarkeitsanalysen widerspiegelt. Für den Modus des Gehens werden dabei **nur Wege berücksichtigt, die für Fußgänger geeignet sind**. Die Gehgeschwindigkeit `Geschwindigkeit` kann vom Benutzer bei jeder Erreichbarkeitsanalyse angepasst werden. 

## 2. Daten

### Verkehrsmittel-Netzwerk

Die Daten der **[Overture Maps Foundation](https://overturemaps.org/)** werden in GOAT als Routing-Netzwerk verwendet. Es umfasst die Verkehrsinfrastruktur mit **Kanten** (für jeden durchgehenden Weg, der nicht durch einen anderen halbiert wird) und **Knoten** (für jeden Punkt, an dem sich zwei verschiedene Wege kreuzen), die reale Netzwerke darstellen.

## 3. Technische Details

### Datenvorverarbeitung

Die folgenden Schritte werden an den Daten durchgeführt, um **schnelles** und **genaues** Gehen zu ermöglichen:

 1. **Attribut-Parsing:** Kategorisierung der Attribute der Kanten (Straßen `Klasse`).
 2. **Geospatial Indexing:**  Nutzung des **[Uber H3 auf Gitter basierend](../further_reading/glossary#h3-grid)** Indexing für effizientes Routing.

### Routing-Prozess-Schritte

#### Extraktion von Teilnetzen

1. **Pufferregion:** Basierend auf Benutzerherkunft, Reisezeit und Geschwindigkeit.
2. **Kantenfilterung:** Es werden nur relevante Kanten für Fußgänger berücksichtigt.

Für das Routing von Fußgängern werden die Kanten der folgenden Straßenklassen berücksichtigt:

`Sekindär`, `Tertiär`, `Wohngebiet`, `verkehrsberuhigter Bereich`, `Fernstraße`, `nicht klassifiziert`, `Parkreihe`, `Auffahrt`, `Gasse`, `Fußgänger`, `Fußweg`, `Gehweg`, `Zebrastreifen,`, `Treppen`, `Pfad`, `Reitweg` and `unbekannt`.

Weitere Informationen zu dieser Klassifizierung finden Sie im [Overture Wiki](https://docs.overturemaps.org/schema/reference/transportation/segment).

#### Erstellung künstlicher Kanten

Die vom Benutzer bereitgestellten Ausgangspunkte befinden sich in der Regel in geringer Entfernung zum Straßennetz. Um die zusätzliche Zeit (oder die Kosten) für den Fußweg vom Ausgangspunkt zur nächstgelegenen Straße zu berücksichtigen, werden künstliche (oder simulierte) Kanten erstellt.

#### Berechnung der Kantenkosten

Für alle Kanten im Teilnetz wird ein Kostenwert (dargestellt als Zeit) auf der Grundlage der Weglänge und der Gehgeschwindigkeit berechnet.
Die Kostenfunktion für das Gehen:
`Kosten = Dauer / Geschwindigkeit`

#### Netzwerkausbreitung

Um den kürzesten Weg vom Ausgangspunkt zu verschiedenen Zielen zu berechnen, wird eine benutzerdefinierte Implementierung des bekannten [Dijkstra Algorithm](https://de.wikipedia.org/wiki/Dijkstra-Algorithmus) verwendet.


<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/routing/walk/dijkstra.gif').default}  alt="Dijkstra Algorithm" style={{ width: "auto", height: "auto", objectFit: "cover"}}/>
<p style={{ textAlign: 'center' }}>GIF: <a href="https://de.wikipedia.org/wiki/Dijkstra-Algorithmus">Dijkstra Algorithm</a></p>
</div>

Die Implementierung hat eine Zeitkomplexität von *O(ElogV)*, ist in **Python** geschrieben und verwendet den Just-in-Time-Compiler **Numba**.


