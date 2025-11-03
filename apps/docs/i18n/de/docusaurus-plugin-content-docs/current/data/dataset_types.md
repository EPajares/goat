---
sidebar_position: 1
---

# Datensatztypen

Benutzer können auf Datensätze im **Catalog Explorer** und über den **Dataset Explorer** zugreifen. Die im [Katalog](../workspace/Catalog) enthaltenen Datensätze werden von Plan4Better bereitgestellt und gepflegt. Wenn Sie einen externen Datensatz über eine URL hinzufügen, einen Datensatz von Ihrem lokalen Computer hochladen oder eine Ebene in GOAT erstellen, sind diese im Dataset Explorer sichtbar.

**Hinzufügen von Datensätzen**

![GOAT-Datentypen](/img/data/data_basis/original_files/dataset_types.png "Datensatztypen")

:::info Externe Datensätze

Im Gegensatz zu anderen Datensätzen stammen externe Datensätze von **Drittanbietern** über den von Ihnen bereitgestellten Link. Diese Datensätze können entweder [Features](#1-features) oder [Raster](#2-raster) sein, die unterschiedliche Zwecke erfüllen. *Externe Feature-Layer* werden in GOAT abgerufen und dort gespeichert, während *externe Raster-Layer* live abgerufen werden (um sie in der Karte zu überlagern), aber nicht gespeichert werden.
<p>
</p>
Folgende externe Datensätze werden in GOAT unterstützt: Web Map Service (WMS), Web Map Tile Service (WMTS), Web Feature Service (WFS), XYZ Tiles.

:::

## Datensatztypen

### 1. Features

#### 1.1 Räumliche Features
Feature-Datensätze dienen als dynamisches Repository für **räumliche Features** wie Punkte, Linien oder Polygone – sie enthalten räumlich referenzierte geografische Features. Benutzer können Daten aus **Shapefiles**, **Geopackages**, **GeoJSON** und **KML**-Dateien hochladen oder einen **WFS**-Link von einer externen URL hinzufügen. Feature-Datensätze können auf der Karte visualisiert, [gestylt](../category/layer-styling) und für Analysen mit Werkzeugen aus der [Toolbox](../category/toolbox) verwendet werden. Darüber hinaus können Feature-Datensätze als Datenbasis für die [Szenarioerstellung](../Scenarios) dienen.

<p> </p>
<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/data/spatial.png').default} alt="Übersicht über die Home-Oberfläche in GOAT" style={{ maxHeight: "750px", maxWidth: "750px", objectFit: "cover"}}/>
</div>
<p> </p>

Im GOAT-Framework gibt es zwei verschiedene Arten von Feature-Datensätzen, um unterschiedliche Aspekte der Geofunktionalität zu adressieren:

- **Feature Dataset Standard:** Dies ist der primäre Feature-Typ, der automatisch ausgewählt wird, wenn ein Benutzer eine Datei hochlädt. Es unterstützt eine Vielzahl von Formaten, einschließlich GeoJSON, GPKG, KML und ZIP-Dateien. Dieser Datensatz dient als Grundlage für grundlegende geografische Operationen in GOAT.

- **Feature Dataset Tool:** Dieser Datensatz umfasst alle Datensätze, die mit den in GOAT verfügbaren Werkzeugen erstellt wurden.

#### 1.2 Nicht-räumliche Datensätze
**Tabellen** sind **nicht-räumliche Datensätze**, die sich von den geografischen Datensätzen dadurch unterscheiden, dass sie keine geografischen Referenzpunkte enthalten, und daher nicht auf der Karte visualisiert werden können. Diese Datensätze können für ausgewählte Analyse- und Datenverwaltungsprozesse verwendet werden. Benutzer können Tabellendatensätze in weit verbreiteten Formaten wie **CSV** (Comma-Separated Values) und **XLSX** (Microsoft Excel Open XML Spreadsheet) importieren.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/data/table.png').default} alt="Übersicht über die Home-Oberfläche in GOAT" style={{ maxHeight: "750px", maxWidth: "750px", objectFit: "cover"}}/>
</div>
<p> </p>

### 2. Raster

:::info Hinweis

Sie können Raster-Layer weder bearbeiten noch Analysen darauf ausführen.

:::

Rasterdatensätze werden von externen Quellen wie **WMS** (Web Map Service) oder **WMTS** (Web Map Tile Service) bereitgestellt. Damit können eine Vielzahl von georeferenzierten Kartenbildern, wie topografische Karten, von externen Servern abgerufen und in GOAT integriert werden. Während diese Bilder als statische Karten eingebunden werden können, ist es wichtig zu beachten, dass sie keine analytischen Funktionen unterstützen.

:::tip Hinweis

Die Darstellung dieser externen Bilddatensätze hängt vom externen Dienst ab, der den WMS- oder WMTS-Service bereitstellt (z.B. Dienst von GeoServer https://wm&#8203;s.websitehai.com/geoserver/ows?SERVICE=WMS&). Folglich kann die visuelle Präsentation des Kartenmaterials, einschließlich Elemente wie Farbschemata und Darstellung geografischer Merkmale, im GOAT-Framework nicht geändert werden.

:::
<p> </p>
<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/data/raster.png').default} alt="Übersicht über die Home-Oberfläche in GOAT" style={{ maxHeight: "750px", maxWidth: "750px", objectFit: "cover"}}/>
</div>
<p> </p>

**WMS (Web Map Service)**
Dieser Layer-Typ unterstützt Zoom und Schwenken und ist ideal für Grundkarten, aber das Ergebnis ist immer ein statisches Bild und wird langsamer geladen.

**WMTS (Web Map Tile Service)**
WMTS-Layer haben vorgerenderte, festgelegte Kacheln und laden daher schnell. Sie können schnell hineinzoomen und sie sanft schwenken. Es ist ideal für Grundkarten großer Flächen und eignet sich am besten, wenn Sie einen konsistenten Kartenstil haben möchten.

**XYZ Tiles**
Dieser Layer-Typ bietet schnelles und effizientes Karten-Zoomen und Schwenken, da die Kachel durch ihre Längen- (X), Breiten- (Y) und Zoom-Stufen-Koordinaten (Z) definiert ist. Es wird am häufigsten verwendet, wenn Sie eine schnell ladende Karte benötigen, die in verschiedenen Zoomstufen die gleiche Leistung erbringt.

|   | WMS | WMTS und XYZ Tiles |
|----|-------------|--------------|
| **URL-Typ in GOAT**    | Capabilities-URL | Capabilities (nur WMTS), direkte URL |
| **Datenoutput** | Dynamische Kartenbilder | Vorgerenderte, zwischengespeicherte Kachelkarten |
| **Struktur** | Keine Kacheln – Bilder werden bei Bedarf generiert | Strukturierte Kacheln basierend auf einem Raster |
| **Leistung** | Langsamer (Bilder werden auf Anfrage generiert) | Schneller (Kacheln werden zwischengespeichert) |
| **Anpassbarkeit** | Eingeschränkt | Eingeschränkt |
| **Skalierbarkeit** | Weniger skalierbar | Hoch skalierbar |
|**Zoomstufe** | Variabel, durch Anfrageparameter festgelegt | Feste Zoomstufe, vom Server vorgegeben |

:::info INFO
Sie können herausfinden, welche Datentypen von GOAT unterstützt werden, unter [**Attributtypen**](../data/data_types).
:::