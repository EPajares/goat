---
sidebar_position: 3

---

# Öffentliche Verkehrsmittel

Das **Verkehrsmittel ÖPNV** in GOAT ist essentiell für die Durchführung von Analysen, welche Fahrten mit öffentlichen Verkehrsmitteln beinhalten.

## 1. Zielsetzung

Das ÖPNV-Routing erleichtert die **intermodale Analyse** durch die Wahl von Zu- und Abgang, wie z.B. zu Fuß oder mit dem Fahrrad zum und vom Bahnhof. Dies ist komplexer als die anderen Routing-Modi, da es die Zusammenführung verschiedener Datensätze (z. B. Bürgersteige und Radwege, Haltestellen und Fahrpläne des öffentlichen Verkehrs usw.) und Berechnungsansätze erfordert.

Das Routing im öffentlichen Verkehr wird in GOAT für Indikatoren wie [Einzugsgebiete](../toolbox/accessibility_indicators/catchments) verwendet.


## 2. Daten

### ÖV-Daten

Verwendet Daten im Format **[GTFS](https://gtfs.org/)** (General Transit Feed Specification) für statische Informationen zum öffentlichen Verkehrsnetz (Haltestellen, Linien, Fahrpläne, Umsteigeverbindungen und mehr).


### Straßen und Wege

Integriert straßenbezogene Informationen aus **[OpenStreetMap](https://wiki.openstreetmap.org/)** zur Unterstützung multimodaler Routenführung und realistischer Wegeketten (einschließlich Gehwegen, Radwegen und Zebrastreifen).


## 3. Technische Einzelheiten

Das Routing für den öffentlichen Verkehr wird mit der **[R5 Routing Engine](https://github.com/conveyal/r5)** (_Rapid Realistic Routing on Real-world and Reimagined networks_) durchgeführt. R5 ist die Routing-Engine von **[Conveyal](https://conveyal.com/)**, einer webbasierten Plattform, die es den Nutzern ermöglicht, Planungsszenarien zu erstellen und verschiedene Erreichbarkeitsindikatoren zu berechnen.


### Routing-Optionen

#### Modi

Analysen für die folgenden öffentlichen Verkehrsmodi werden derzeit von GOAT unterstützt. Wählen Sie einen oder mehrere aus – beachten Sie dabei, dass einige Modi nicht in allen Regionen verfügbar sind.

`Bus`, `Straßenbahn`, `Bahn`, `U-Bahn`, `Fähre`, `Seilbahn`, `Gondel`, `Standseilbahn`.

#### Reisezeitlimit

Die maximale Reisedauer, die beim Routing im öffentlichen Verkehr berücksichtigt wird. Aktuell wird ein Maximum von `90 Minuten` unterstützt. Dies beinhaltet auch die Zeit für den Zugang und Abgang zu bzw. von den ÖPNV-Haltestellen.

#### Tag

Der Wochentag, der beim Routing im öffentlichen Verkehr berücksichtigt wird. Wählen Sie zwischen `Werktag`, `Samstag` und `Sonntag`. Dies ist nützlich, um Unterschiede im Verkehrsangebot zwischen Werktagen und Wochenenden zu analysieren.

#### Start- und Endzeit

Ein Zeitfenster für das Routing im öffentlichen Verkehr. Es werden alle schnellstmöglichen Verbindungen innerhalb dieses Zeitfensters berücksichtigt, was z.B. zu einem möglichst großen Einzugsgebiet vom angegebenen Startpunkt führen kann.  
Eine Verbindung gilt als innerhalb des Zeitfensters liegend, **ausschließlich basierend auf ihrer Startzeit** – unabhängig von ihrer Endzeit oder Gesamtdauer.


#### Sonstiges (Standardkonfigurationen)

Die folgenden Standardkonfigurationen werden beim Routing für den öffentlichen Verkehr verwendet. Sie sind derzeit nicht vom Benutzer konfigurierbar.
- **Zugang:** Wie Nutzer von ihrem Ausgangsort zur Haltestelle gelangen (`Fuß`).
- **Abgang:** Wie Nutzer von der Haltestelle zu ihrem Zielort gelangen (`Fuß`).
- **Decay function type:** logistic
- **Standard deviation:** 12 minutes
- **Width:** 10 minutes
- **Walk speed:** 5 km/h
- **Maximum walk time:** 20 minutes
- **Bike speed:** 15 km/h
- **Maximum bike time:** 20 minutes
- **Bike traffic stress:** 4
- **Maximum rides:** 4
- **Zoom level:** 9
- **Percentiles:** 5
- **Monte Carlo draws:** 200