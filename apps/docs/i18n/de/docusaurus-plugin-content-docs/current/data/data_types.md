---
sidebar_position: 2
---

# Datentypen

GOAT unterstützt verschiedene Datentypen zur Verarbeitung unterschiedlicher Arten von Informationen in Ihren **Datensätzen**. Das Verständnis dieser Datentypen hilft Ihnen, effektiver mit Ihren **Daten** zu arbeiten und optimale Leistung zu gewährleisten.

## Räumliche Datenspeicherung

GOAT verwendet eine mächtige Kombination aus **PostgreSQL-Datenbank mit der PostGIS-Erweiterung zur Verarbeitung räumlicher Daten**. So funktioniert es:

- **Geometriespeicherung**: Alle räumlichen Features (Punkte, Linien, Polygone) werden mit dem **PostGIS-Geometrietyp** im Koordinatenreferenzsystem **EPSG:4326** gespeichert
- **Genaue Berechnungen**: Für präzise **Entfernungs**- und Flächenmessungen verwendet GOAT den PostGIS-Geografie-Typ, der meterbasierte Berechnungen mit höherer Genauigkeit bietet

## Unterstützte Datentypen

GOAT organisiert **Daten** in spezifische Typen, um die Datenbankleistung zu optimieren und Skalierbarkeit zu gewährleisten. Jeder Datentyp hat eine maximale Anzahl von Spalten, um effiziente Verarbeitung zu gewährleisten:

| Datentyp  | Beschreibung | Beispiele | Max. Spalten |
|------------|-------------|----------|-------------|
| **integer** | Ganze Zahlen ohne Dezimalstellen | 1, 100, -5 | 15 |
| **bigint** | Sehr große ganze Zahlen | Bevölkerungszahlen, große IDs | 5 |
| **float** | Zahlen mit Dezimalstellen | 3.14, -0.001, 45.67 | 10 |
| **text** | Text- und Zeichendaten | Straßennamen, Kategorien, Beschreibungen | 20 |
| **timestamp** | **Datums**- und Zeitinformationen | 2024-01-15 14:30:00 | 3 |
| **arrfloat** | Array von Dezimalzahlen | [1.5, 2.7, 3.9] | 3 |
| **arrint** | Array von ganzen Zahlen | [1, 5, 10, 15] | 3 |
| **arrtext** | Array von Textwerten | ["rot", "grün", "blau"] | 3 |
| **jsonb**    | Strukturierte **Daten** im JSON-**Format** | `{"name": "wert", "count": 42}` | 3 |
| **boolean** | Wahr/Falsch-Werte | wahr, falsch | 3 |

:::info Warum diese Begrenzungen?
Die Spaltenbegrenzungen gewährleisten optimale Datenbankleistung und verhindern Systemüberlastung. Wenn Sie mehr Spalten eines bestimmten Typs benötigen, erwägen Sie, Ihre **Daten** auf mehrere **Datensätze** aufzuteilen oder Array-Typen für verwandte Werte zu verwenden.
:::

## Wie man Datentypen anzeigt

Sie können einfach die Datentypen Ihrer **Layer**-Attribute überprüfen:

<div class="step">
  <div class="step-number">1</div>
  <div class="content">Klicken Sie auf <img src={require('/img/map/filter/3dots.png').default} alt="Optionen" style={{ maxHeight: "25px", maxWidth: "25px", objectFit: "cover"}}/> <code>Weitere Optionen</code> Schaltfläche bei Ihrem **Layer**</div>
</div>

<div class="step">
  <div class="step-number">2</div>
  <div class="content">Wählen Sie <code>Daten anzeigen</code> aus dem Menü</div>
</div>

<div class="step">
  <div class="step-number">3</div>
  <div class="content">In der Datentabelle sehen Sie den Datentyp über jeder Spaltenüberschrift angezeigt</div>
</div>

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/data/view-data-layer.png').default} alt="Weitere Optionen" style={{ maxHeight: "auto", maxWidth: "auto", objectFit: "cover"}}/>
  <p style={{ textAlign: 'center', fontStyle: 'italic', marginTop: '8px', color: '#666' }}>Zugriff auf die Option "Daten anzeigen"</p>
</div>

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/data/data-table.png').default} alt="Datentabelle mit Attributtypen" style={{ maxHeight: "auto", maxWidth: "auto", objectFit: "cover"}}/>
  <p style={{ textAlign: 'center', fontStyle: 'italic', marginTop: '8px', color: '#666' }}>Datentabelle mit Attributtypen über jeder Spalte</p>
</div>