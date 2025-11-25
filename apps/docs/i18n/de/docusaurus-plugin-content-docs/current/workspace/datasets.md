---
sidebar_position: 4
---

# Datensätze

Die **Datensätze**-Seite ist Ihr Datenmanagement-Hub, wo Sie alle Ihre räumlichen und nicht-räumlichen **Daten** in GOAT **hochladen**, organisieren und teilen können. Dieser zentrale **Workspace** bietet eine organisierte Ansicht Ihrer **Datensätze**, kategorisiert in **Persönliche Datensätze**, **Team-Datensätze** und **Organisationsweite geteilte Datensätze**. Hier können Sie:

- **Neue Datensätze hinzufügen**
- **Datensätze filtern und organisieren** für bessere Datenstruktur und -verwaltung
- **Datensätze verwalten** durch Teilen, Verschieben, Löschen und andere Funktionen.
  
<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
  <img src={require('/img/workspace/datasets/datasets_general.png').default} alt="Datensätze-Seite im Workspace von GOAT" style={{ maxHeight: "auto", maxWidth: "auto", objectFit: "cover"}}/>
</div> 

## Datensätze hinzufügen

Sie können **Datensätze** auf zwei Arten zu GOAT hinzufügen: durch **Hochladen** von Dateien von Ihrem Computer oder durch Verbindung zu externen Datenquellen.

### Daten hochladen

GOAT unterstützt mehrere Dateiformate zum **Hochladen**: **GeoPackage**, **GeoJSON**, **Shapefile**, **KML**, **CSV** und **XLSX**-Dateien.

<div class="step">
  <div class="step-number">1</div>
  <div class="content">Navigieren Sie zur <code>Datensätze</code>-Seite über die Seitenleisten-Navigation.</div>
</div>

<div class="step">
  <div class="step-number">2</div>
  <div class="content">Klicken Sie auf <code>+ Datensatz hinzufügen</code> und wählen Sie <code>Datensatz hochladen</code>.</div>
</div>

<div class="step">
  <div class="step-number">3</div>
  <div class="content">Wählen Sie die Datei von Ihrem lokalen Gerät über den Dateibrowser aus.</div>
</div>

<div class="step">
  <div class="step-number">4</div>
  <div class="content">
    <p>Konfigurieren Sie Ihren **Datensatz**:</p>
    <ul> 
      <li><strong>Zielordner</strong> - Wählen Sie, wo Sie Ihren **Datensatz** organisieren möchten</li>
      <li><strong>Name</strong> - Geben Sie Ihrem **Datensatz** einen beschreibenden Namen</li>
      <li><strong>Beschreibung</strong> (optional) - Fügen Sie Details über den Inhalt und Zweck Ihres **Datensatzes** hinzu</li>
    </ul>
  </div>
</div>

<div class="step">
  <div class="step-number">5</div>
  <div class="content">Klicken Sie auf <code>Hochladen</code>, um den **Datensatz** zu Ihrem **Workspace** hinzuzufügen.</div>
</div>

### Externe Datenquellen

Verbinden Sie sich mit externen Datendiensten einschließlich **Web Feature Service (WFS)**, **Web Map Service (WMS)**, **Web Map Tile Service (WMTS)** und **XYZ-Kacheln**.

<div class="step">
  <div class="step-number">1</div>
  <div class="content">Navigieren Sie zur <code>Datensätze</code>-Seite über die Seitenleisten-Navigation.</div>
</div>

<div class="step">
  <div class="step-number">2</div>
  <div class="content">Klicken Sie auf <code>+ Datensatz hinzufügen</code> und wählen Sie <code>Externer Datensatz</code>.</div>
</div>

<div class="step">
  <div class="step-number">3</div>
  <div class="content">Geben Sie die URL des externen Datendienstes ein.</div>
</div>

<div class="step">
  <div class="step-number">4</div>
  <div class="content">Wählen Sie den spezifischen Layer aus, den Sie hinzufügen möchten, aus den verfügbaren Optionen und klicken Sie auf <code>Weiter</code>.</div>
</div>

<div class="step">
  <div class="step-number">5</div>
  <div class="content">
  <p>Konfigurieren Sie Ihren **Datensatz**:</p>
    <ul>
      <li><strong>Zielordner</strong> - Wählen Sie, wo Sie Ihren **Datensatz** organisieren möchten</li>
      <li><strong>Name</strong> - Geben Sie Ihrem **Datensatz** einen beschreibenden Namen</li>
      <li><strong>Beschreibung</strong> (optional) - Fügen Sie Details über die externe Datenquelle hinzu</li>
    </ul>
  </div>
</div>

<div class="step">
  <div class="step-number">6</div>
  <div class="content">Überprüfen Sie Ihre Konfiguration und klicken Sie auf <code>Speichern</code>, um den externen **Datensatz** hinzuzufügen.</div>
</div>

:::tip Alternative Upload-Methode
Sie können **Datensätze** auch direkt während der Arbeit in der [Karte](../map/layers) Oberfläche **hochladen** für die sofortige Verwendung in Ihren **Projekten**.
:::


## Datensätze filtern und organisieren

### Nach Datensatz-Typ filtern

Filtern Sie Ihre **Datensätze** einfach nach [Datensatz-Typ](../data/dataset_types "Was sind die Datensatz-Typen?"), um genau das zu finden, was Sie brauchen. Verfügbare Filter umfassen:

- **Features** - Räumliche **Datensätze** mit Punkten, Linien oder Polygonen
- **Tabellen** - Nicht-räumliche tabellarische **Daten**
- **Externe Bilder** - Raster-**Daten** aus externen Quellen  
- **Externe Vektor-Kacheln** - Vektor-Kacheln aus externen Diensten

Klicken Sie auf das Filter-Symbol <img src={require('/img/map/filter/filter_icon.png').default} alt="Filter-Symbol" style={{ maxHeight: "20px", maxWidth: "20px"}}/>, um Ihren gewünschten **Datensatz**-Typ auszuwählen.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
  <img src={require('/img/workspace/datasets/dataset_filter.gif').default} alt="Datensätze-Filterung im Workspace von GOAT" style={{ maxHeight: "auto", maxWidth: "auto", objectFit: "cover"}}/>
</div>

### Ordner erstellen und verwalten

Organisieren Sie Ihre **Datensätze** in Ordnern für bessere Struktur und einfachere Navigation.

**Um einen neuen Ordner zu erstellen:**

<div class="step">
  <div class="step-number">1</div>
  <div class="content">Klicken Sie auf das <img src={require('/img/workspace/datasets/folder_icon.png').default} alt="Ordner-Symbol" style={{ maxHeight: "25px", maxWidth: "25px"}}/> Ordner-Symbol.</div>
</div>

<div class="step">
  <div class="step-number">2</div>
  <div class="content">Geben Sie einen beschreibenden Namen für Ihren neuen Ordner ein</div>
</div>

<div class="step">
  <div class="step-number">3</div>
  <div class="content">Drücken Sie <code>Erstellen</code>, um den Ordner zu finalisieren</div>
</div>

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
  <img src={require('/img/workspace/datasets/new_folder.gif').default} alt="Neue Ordner im Workspace von GOAT erstellen" style={{ maxHeight: "auto", maxWidth: "auto", objectFit: "cover"}}/>
</div>

<p></p>

**Um Datensätze in Ordner zu verschieben:**

<div class="step">
  <div class="step-number">1</div>
  <div class="content">Klicken Sie auf die drei Punkte <img src={require('/img/map/filter/3dots.png').default} alt="Optionen" style={{ maxHeight: "25px", maxWidth: "25px"}}/> neben Ihrem **Datensatz**</div>
</div>

<div class="step">
  <div class="step-number">2</div>
  <div class="content">Wählen Sie <code>In Ordner verschieben</code> aus dem Menü</div>
</div>

<div class="step">
  <div class="step-number">3</div>
  <div class="content">Wählen Sie Ihren Zielordner aus dem Dropdown-Menü und drücken Sie <code>Verschieben</code>.</div>
</div>

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
  <img src={require('/img/workspace/datasets/move_to_folder.gif').default} alt="Ihre Datensätze in die Ordner im Workspace von GOAT verschieben" style={{ maxHeight: "auto", maxWidth: "auto", objectFit: "cover"}}/>
</div>

## Datensatz-Verwaltung

Greifen Sie auf umfassende **Datensatz**-Verwaltungsoptionen über das <img src={require('/img/map/filter/3dots.png').default} alt="Optionen" style={{ maxHeight: "25px", maxWidth: "25px", objectFit: "cover"}}/> <code>Weitere Optionen</code>-Menü neben jedem **Datensatz** zu. Verfügbare Aktionen umfassen:

- **Info anzeigen/bearbeiten** - Zugriff und Änderung von **Datensatz**-Metadaten
- **In Ordner verschieben** - Ihre **Datensatz**-Struktur neu organisieren  
- **Herunterladen** - **Datensätze** auf Ihr lokales Gerät exportieren
- **Teilen** - Zusammenarbeiten durch Teilen mit Teammitgliedern oder Organisation
- **Löschen** - **Datensätze** entfernen, die Sie nicht mehr benötigen

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/workspace/datasets/managing_datasets.png').default} alt="Datensatz-Verwaltungsoptionen" style={{ maxHeight: "300px", maxWidth: "300px"}}/>
</div>

#### Datensatz-Metadaten und Vorschau

Zeigen Sie detaillierte Informationen über Ihre **Datensätze** an, um deren Inhalt und Struktur besser zu verstehen. Greifen Sie auf zwei Arten auf Metadaten zu:

- Klicken Sie auf **Info** aus dem <img src={require('/img/map/filter/3dots.png').default} alt="Optionen" style={{ maxHeight: "25px", maxWidth: "25px", objectFit: "cover"}}/> <code>Weitere Optionen</code>-Menü 
- Klicken Sie direkt auf den **Datensatz**-Namen

Die Metadaten-Ansicht bietet:

- **Daten-Zusammenfassung** - Übersicht über **Datensatz**-Eigenschaften und Statistiken
- **Attributtabelle** - Detaillierte Ansicht aller Datenfelder und Werte  
- **Karten-Vorschau** - Räumliche Visualisierung mit interaktiver Legende
- **Bearbeitungsoptionen** - **Datensatz**-Name, Beschreibung und andere Eigenschaften ändern

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
  <img src={require('/img/workspace/datasets/metadata.gif').default} alt="Metadaten der Datensätze im Workspace von GOAT" style={{ maxHeight: "auto", maxWidth: "auto", objectFit: "cover"}}/>
</div>