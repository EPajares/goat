---
sidebar_position: 3
---

# Integrierte Datensätze

## Die Grundlage hinter GOATs Indikatoren

GOATs mächtige Erreichbarkeitsindikatoren und Analysetools basieren auf hochwertigen integrierten **Datensätzen**, die im Hintergrund arbeiten. **Diese Datensätze sind für Benutzer nicht direkt zugänglich, aber sie ermöglichen alle Routing-Berechnungen und Erreichbarkeitsanalysen in GOAT.**

Das Verständnis dieser zugrundeliegenden **Datensätze** hilft Ihnen:
- **Die Datenqualität zu kennen**, die Sie von GOATs Indikatoren erwarten können
- **Die geografische Abdeckung** verschiedener Analyse-**Werkzeuge** zu verstehen
- **Ergebnisse zu interpretieren** mit Kenntnis der Datenquellen

:::info Benutzerdaten vs. integrierte Daten
**Integrierte Datensätze** (auf dieser Seite beschrieben) ermöglichen GOATs interne Berechnungen und Indikatoren. Für **Datensätze**, die Sie hochladen können, oder bestehende Datensätze aus unserem [**Katalog**](../workspace/catalog.md).
:::

## Netzwerk-Datensätze für Routing

GOAT umfasst umfassende Netzwerk-**Datensätze**, die alle routing-basierten **Erreichbarkeitsindikatoren** und Analyse-**Werkzeuge** antreiben.

### Öffentliches Verkehrsnetz

Unser **öffentliches Verkehrsnetz** deckt mehrere Verkehrsmittel ab, einschließlich **Bus**, **Tram**, **U-Bahn**, **Bahn** und **Fähre**. Dieses Netzwerk ermöglicht GOATs [Öffentlicher Verkehr](../routing/public_transport) **Routing**-Funktionen.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/data/data_basis/pt_network_banner.png').default} alt="Öffentliches Verkehrsnetz" style={{ maxHeight: "auto", maxWidth: "auto", objectFit: "cover"}}/>
</div>

**Was enthalten ist:**
- **Haltestellen**: Namen, Standorte, Typen und Barrierefreiheitsinformationen
- **Routen**: Service-Typen, Barrierefreiheitsdetails und Routeninformationen  
- **Fahrpläne**: **Abfahrtszeiten**, Service-Häufigkeit und Betriebstage
- **Umsteigeverbindungen**: Umsteigeangaben und Bahnhofsverbindungen
- **Fahrtmuster**: Haltestellensequenzen und Zeitinformationen
- **Routenverläufe**: Geospatiale Darstellung von Verkehrslinien

**Datenquellen:**
- **Deutschland**: [DELFI](https://www.delfi.de/) - Deutschlands nationale Datenplattform für öffentliche Verkehrsmittel
- **Straßenebene-Daten**: [OpenStreetMap (OSM)](https://wiki.openstreetmap.org/) - Für Bahnhofszugang, Fußgängerverbindungen und multimodales Routing

**Wie wir die Daten verarbeiten:**
1. **Import**: **Daten** werden im [GTFS (General Transit Feed Specification)](https://gtfs.org/)-**Format** gesammelt
2. **Überprüfen & Korrigieren**: Wir validieren Haltestellenbeziehungen, Bahnsteigverbindungen und Service-Typ-Klassifizierungen
3. **Optimieren**: Netzwerke werden optimiert, um nur die repräsentativsten Service-Muster für jede Route zu enthalten
4. **Fahrplan-Typen**: Die Analyse unterstützt drei Tagestypen - **Werktag** (typischerweise Dienstag), **Samstag** und **Sonntag**

### Straßennetzwerk und Topografie

Unser Straßennetzwerk repräsentiert reale Verkehrsinfrastruktur einschließlich Straßen, Autobahnen, **Fahrradwegen** und Fußwegen. Dies ermöglicht GOATs [Zu Fuß](../routing/walking), [**Fahrrad**](../routing/bicycle), [**Pedelec**](../routing/bicycle) und [**Auto**](../routing/car) **Routing**.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/data/data_basis/street_network_banner.png').default} alt="Straßennetzwerk" style={{ maxHeight: "auto", maxWidth: "auto", objectFit: "cover"}}/>
</div>

**Netzwerk-Komponenten:**
- **Segmente (Kanten)**: Kontinuierliche Wegabschnitte zwischen Kreuzungen
- **Kreuzungen (Knoten)**: Punkte, an denen sich verschiedene Wege treffen oder kreuzen

**Datenquellen:**
- **Straßennetze**: [Overture Maps Foundation](https://overturemaps.org/) - Hochwertige, europaweite Verkehrsdaten
- **Höhendaten**: [Copernicus](https://www.copernicus.eu/en) Digitales Höhenmodell (DEM) für genaue Steigungsberechnungen

**Verarbeitungsworkflow:**
1. **Datenimport**: Straßennetzwerkdaten werden im Geoparquet-**Format** aus Overture Maps' [Transportation theme](https://docs.overturemaps.org/guides/transportation/) importiert
2. **Höhenverarbeitung**: Europäische DEM-Kacheln werden verarbeitet, um topografische Informationen zu extrahieren
3. **Räumliche Indexierung**: Netzwerksegmente werden mit [Ubers H3-Gittersystem](../further_reading/glossary#h3-grid) für effiziente Verarbeitung organisiert
4. **Steigungsberechnung**: Oberflächengefälle und Steigungswiderstand werden für jedes Straßensegment berechnet
5. **Attributanalyse**: Straßenklassifizierungen, **Geschwindigkeitsbegrenzungen**, Abbiegebeschränkungen und Einbahnstraßenbezeichnungen werden identifiziert und standardisiert
6. **Geschwindigkeitsbegrenzungs-Interpolation**: Fehlende Geschwindigkeitsbegrenzungen werden basierend auf Straßentyp und modalen Geschwindigkeiten geschätzt

:::info Demnächst
Während GOAT derzeit integrierte Netzwerke für öffentliche Verkehrsmittel und Straßen-**Routing** verwendet, arbeiten wir daran, Benutzern zu ermöglichen, ihre eigenen benutzerdefinierten Netzwerke **hochzuladen**. Interessiert an diesem Feature? [Kontaktieren Sie uns](https://plan4better.de/en/contact/ "Support kontaktieren"), um mehr zu erfahren.
:::