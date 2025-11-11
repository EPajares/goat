---
sidebar_position: 1
---

# Datensatz-Typen

Auf GOAT können Sie mit **Datensätzen** aus Plan4Betters **Katalog** arbeiten oder Ihre eigenen von Ihrem Computer **hochladen**. Es akzeptiert verschiedene **Formate** für sowohl **Feature-Datensätze** als auch **Raster-Datensätze**. Hier erklären wir die verschiedenen Typen von **Datensätzen**, die Sie in GOAT verwenden können.

## Feature-Datensätze

### 1.1 Räumliche Features

Feature-**Datensätze** speichern **räumliche Features wie Punkte, Linien oder Polygone**. Auf GOAT können Sie **Daten** aus **Shapefiles**, **GeoPackages**, **GeoJSON** oder **KML**-Dateien **hochladen** oder einen **WFS**-Link von einer externen URL hinzufügen. Sie können diese **Datensätze** mit den verschiedenen **Werkzeugen** aus der **Werkzeugkiste** visualisieren, gestalten und analysieren.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/data/spatial.png').default} alt="Räumliche Features in GOAT" style={{ maxHeight: "750px", maxWidth: "750px", objectFit: "cover"}}/>
  <p style={{ textAlign: 'center', fontStyle: 'italic', marginTop: '8px', color: '#666' }}> Beispiel für räumliche Features, die in GOAT angezeigt werden</p>
</div>

<p></p>

GOAT erkennt zwei Typen von Feature-**Datensätzen** basierend auf ihrer Quelle:

- **Feature-Datensatz Standard**: Dies sind die **Datensätze**, die Sie selbst **hochladen** (wie **GeoJSON**, **GeoPackage**, **KML** und **ZIP**-Dateien). Betrachten Sie diese als Ihre "Rohmaterialien" - die ursprünglichen **Daten**, die Sie in GOAT einbringen, um damit zu arbeiten.

- **Feature-Datensatz Werkzeug**: Dies sind **Datensätze**, die von GOATs Analyse-**Werkzeugen** erstellt werden. Wenn Sie eine Analyse durchführen (wie die Erstellung von Einzugsgebieten oder Heatmaps), werden die Ergebnisse zu diesem Typ von **Datensatz**.

### 1.2 Nicht-räumliche Datensätze

**Tabellen** sind **nicht-räumliche Datensätze** ohne geografische Referenzpunkte, daher können sie nicht auf der Karte visualisiert werden. Importieren Sie sie in **CSV**- oder **XLSX**-**Formaten** für Analyse und Datenmanagement.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/data/table.png').default} alt="Nicht-räumliche Datensätze in GOAT" style={{ maxHeight: "750px", maxWidth: "750px", objectFit: "cover"}}/>
  <p style={{ textAlign: 'center', fontStyle: 'italic', marginTop: '8px', color: '#666' }}> Beispiel einer in GOAT angezeigten Tabelle</p>
</div>

## Raster-Datensätze

Raster-**Datensätze** können aus externen Quellen wie **WMS** (Web Map Service) oder **WMTS** (Web Map Tile Service) kommen. Sie bieten georeferenzierte Kartenbilder, wie topografische Karten, aber auf GOAT sind sie statisch, daher unterstützen sie keine Analyse oder Bearbeitung.

:::tip Hinweis
Raster-**Styling** hängt vom externen Service ab (z.B. GeoServer). Sie können das Farbschema oder die Feature-Darstellung in GOAT nicht ändern.
:::

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/data/raster.png').default} alt="Raster-Datensätze in GOAT" style={{ maxHeight: "750px", maxWidth: "750px", objectFit: "cover"}}/>
  <p style={{ textAlign: 'center', fontStyle: 'italic', marginTop: '8px', color: '#666' }}> Beispiel eines in GOAT angezeigten Raster-Layers</p>

</div>

- **WMS (Web Map Service)**: Unterstützt Zoomen und Schwenken, ideal für **Grundkarten**, aber gibt statische Bilder aus und lädt langsamer.

- **WMTS (Web Map Tile Service)**: Verwendet vorgerenderte Kacheln für schnelles Laden und sanftes Zoomen. Am besten für große Gebiete und konsistente Kartenstile.

- **XYZ-Kacheln**: Bietet schnelles Zoomen und Schwenken mit Kacheln, die durch X (Längengrad), Y (Breitengrad) und Z (Zoom-Level) Koordinaten definiert sind. Ideal für schnell ladende Karten mit konsistenter Leistung auf verschiedenen Zoom-Leveln.

|   | WMS | WMTS und XYZ-Kacheln |
|----|-------------|--------------|
| **URL-Typ in GOAT**    | Capabilities-URL | Capabilities (nur WMTS), Direkte URL |
| **Datenausgabe** | Dynamische Kartenbilder | Vorgerenderte, zwischengespeicherte Kartenkacheln |
| **Struktur** | Keine Kacheln - Bilder werden spontan generiert | Strukturierte Kacheln basierend auf Raster |
| **Leistung** | Langsamer (Bilder werden pro Anfrage generiert) | Schneller (Kacheln zwischengespeichert) |
| **Anpassung** | Begrenzt | Begrenzt |
| **Skalierbarkeit** | Weniger skalierbar | Hoch skalierbar |
| **Zoom-Level** | Variabel, durch Anfrageparameter festgelegt | Fester Zoom-Level, vom Server vorbestimmt |