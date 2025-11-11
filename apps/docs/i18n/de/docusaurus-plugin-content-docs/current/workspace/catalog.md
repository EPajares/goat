---
sidebar_position: 5
---

# Katalog

Der **Daten-Katalog** ist Ihr Zugang zur Erkundung von Plan4Betters umfassender Sammlung hochwertiger [Geodaten](../further_reading/glossary#geospatial-data). **Diese kuratierte Bibliothek bietet zuverlässige, sofort einsatzfähige Daten von offiziellen Open-Data-Anbietern und anderen vertrauenswürdigen Quellen**, die es Ihnen ermöglichen, sofort mit der Analyse und Visualisierung in Ihren GOAT-**Projekten** zu beginnen. Aus dem **Katalog** können Sie:

- **Unsere Datensatz-Sammlung erkunden**, die mehrere thematische Bereiche und geografische Regionen umfasst
- **Durchsuchen und filtern** nach Schlüsselwort, räumlicher Ausdehnung und **Datensatz**-Attributen

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/workspace/catalog/catalog_general.png').default} alt="Daten-Katalog" style={{ maxHeight: "700px", maxWidth: "800px"}}/>
</div>

## Den Katalog erkunden

Greifen Sie auf den Daten-**Katalog** vom [Workspace](../category/workspace) oder direkt über die <code>+ Layer hinzufügen</code>-Schaltfläche in Ihren GOAT-**Projekten** zu. Der **Katalog** bietet leistungsstarke Entdeckungs-**Werkzeuge**, einschließlich:

- **Schlüsselwort-Suche** zum Finden spezifischer **Datensätze** oder Themen
- **Filter** zum Durchsuchen von **Datensätzen** nach Typ, [Datenkategorie](#datenkategorie), Region, Sprache, Anbieter-Name und Lizenz
- **Interaktive Vorschau** zur Bewertung der Datenqualität und des Inhalts vor der Verwendung

### Datensatz-Kategorie {#datenkategorie}

Eine Möglichkeit, den **Katalog** zu filtern, ist über **Datenkategorie**, die **Datensätze** in klare thematische Kategorien für einfache Navigation organisiert:

- **Grenzen** - Administrative, politische und geografische Grenzen einschließlich Grenzen und Bezirke
- **Landnutzung** - Klassifizierungen von Landgebieten nach Nutzungstyp (Wohn-, Gewerbe-, Industrie- usw.)
- **Menschen** - Demografische **Daten** einschließlich Bevölkerungsdichte, Altersgruppen und sozioökonomische Eigenschaften
- **Orte** - Points of Interest wie Schulen, Krankenhäuser, Touristenattraktionen und Dienstleistungen
- **Verkehr** - Straßennetze, Eisenbahnen, Flughäfen, Häfen und öffentliche Verkehrsinfrastruktur

### Datensatz-Metadaten

Jeder **Datensatz** enthält umfassende Metadaten, die durch Klicken auf den **Datensatz**-Namen zugänglich sind. Die Metadaten-Ansicht bietet:

- **Detaillierte Beschreibungen**, die Inhalt und Umfang des **Datensatzes** erklären
- **Datensatz**-Typ-Klassifizierung und technische Spezifikationen
- **Geografische Abdeckung** mit **ISO 3166-1 alpha-2** Ländercodes
- **Quellinformationen** einschließlich Anbieter-Name und Kontaktdaten
- **Lizenz-Details**, die Nutzungsrechte und Beschränkungen spezifizieren
- **Interaktive Karten-Vorschau** für visuelle Datenerkundung
- **Attribut-Informationen**, die verfügbare Datenfelder und Eigenschaften zeigen

### Verfügbare Datensatz-Typen

Der **Katalog** umfasst vielfältige **Datensätze**, die als Feature-Layer verwaltet werden, die räumliche Features (Punkte, Linien, Polygone) oder nicht-räumliche tabellarische **Daten** enthalten. Diese **Datensätze** können direkt zu Ihren **Projekten** für Analyse und Visualisierung hinzugefügt werden.

#### Points of Interest (POIs)
Strategische Standorte von Annehmlichkeiten, Einrichtungen und Attraktionen, die für Erreichbarkeitsplanung und Stadtanalyse wesentlich sind, wie öffentliche Verkehrshaltestellen und -stationen, Einkaufszentren und Einzelhandelsstandorte, Tourismus- und Freizeiteinrichtungen, Lebensmittel- und Getränkebetriebe, Gesundheitseinrichtungen und Krankenhäuser, Bildungseinrichtungen und Schulen.

*Datenquellen:* [Overture Maps Foundation](https://overturemaps.org/), [OpenStreetMap (OSM)](https://wiki.openstreetmap.org/), Regierungsabteilungen, Krankenversicherungsanbieter und Einzelhandelsunternehmen. Zusätzliche Felderhebungen werden bei Bedarf durchgeführt.

#### Bevölkerung und Gebäude
Detaillierte demografische **Daten**, die auf Gebäude- und lokale Ebenen disaggregiert sind, erweitert mit Landnutzungsinformationen für verbesserte Genauigkeit. Wir bieten Gebäudeebenen-Bevölkerungs**daten** für deutsche Bezirke und Gemeinden, lokale Bevölkerungs**daten** aus dem deutschen Zensus 2022 und europäische NUTS-3-Ebenen-Bevölkerungsstatistiken (Nomenklatur der territorialen Einheiten für die Statistik).

*Datenquellen:* [Deutscher Zensus 2022](https://ergebnisse.zensus2022.de/datenbank/online/), einzelne Gemeinden und Bezirke, und 3D-Stadtmodelle deutscher Bundesländer.

#### Administrative Grenzen
Umfassende Grenzen-**Datensätze**, die Regierungs- und Verwaltungshoheitsgebiete auf mehreren Maßstäben definieren, wie Gemeindegrenzen, Bezirksgrenzen, Bundeslandgrenzen und Postleitzahl-Regionen.

*Datenquellen:* [Bundesamt für Kartographie und Geodäsie (BKG)](https://www.bkg.bund.de/) und [OpenStreetMap (OSM)](https://wiki.openstreetmap.org/).

## Katalog-Daten zu Ihren Projekten hinzufügen

Folgen Sie diesen Schritten, um **Datensätze** aus dem **Katalog** zu Ihren GOAT-**Projekten** hinzuzufügen:

<div class="step">
  <div class="step-number">1</div>
  <div class="content">Navigieren Sie in Ihrem **Projekt** zum <strong>Layer</strong>-Tab und klicken Sie auf <code>+ Layer hinzufügen</code></div>
</div>

<div class="step">
  <div class="step-number">2</div>
  <div class="content">Wählen Sie <code>Katalog-Explorer</code>, um den Daten-**Katalog** zu durchsuchen</div>
</div>

<div class="step">
  <div class="step-number">3</div>
  <div class="content">Durchsuchen oder suchen Sie nach Ihrem gewünschten **Datensatz**, dann klicken Sie auf <code>Layer hinzufügen</code>, um ihn in Ihr **Projekt** einzuschließen</div>
</div>

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/workspace/catalog/catalog_add-layer.gif').default} alt="Katalog-Explorer" style={{ maxHeight: "700px", maxWidth: "800px"}}/>
</div>

<p></p>

:::tip Hinweis
Nach dem Hinzufügen des Layers können Sie [Filter](../map/filter.md "Datensatz filtern") anwenden, um große **Datensätze** auf spezifische geografische Ausdehnungen oder Attribute zu beschränken, die für Ihre Analyse benötigt werden
:::


## Datenqualität und Wartung

Plan4Better gewährleistet die Zuverlässigkeit und Aktualität der **Katalog**-**Daten** durch umfassende Datenmanagement-Prozesse:

### Datensammlung und -vorbereitung

Unser Datensammlungsprozess folgt strengen Standards, um Qualität und Zuverlässigkeit zu gewährleisten:

- **Quellenidentifizierung** - Wir priorisieren offizielle Open-Data-Portale und öffentlich verfügbare Initiativen
- **Format-Standardisierung** - Verschiedene **Formate** (Shapefiles, GeoJSON, usw.) werden zu konsistenten Schemata konvertiert
- **Datenintegration** - Mehrere **Datensätze** werden kombiniert und an lokale Kontexte durch Fusionsworkflows angepasst
- **Qualitätsvalidierung** - Umfassende Validierungsprozesse gewährleisten Genauigkeit und Zuverlässigkeit
- **Kontinuierliche Erweiterung** - Wir suchen aktiv und integrieren zusätzliche **Datensätze** basierend auf Benutzerbedürfnissen

### Update-Zeitplan

Um Datenaktualität und Relevanz zu erhalten:

- **Jährliche Updates** - Alle **Datensätze** werden mindestens einmal pro Jahr aktualisiert
- **Dynamische Daten** - Sich schnell verändernde **Daten** (POIs, öffentlicher Verkehr) erhalten häufigere Updates
- **On-Demand-Updates** - Kritische **Datensätze** können bei Bedarf basierend auf Benutzeranforderungen aktualisiert werden