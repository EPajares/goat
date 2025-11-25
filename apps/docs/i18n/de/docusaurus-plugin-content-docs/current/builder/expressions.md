---
sidebar_position: 4
---


# Ausdrücke

**Diese Seite hilft Ihnen zu verstehen, wie Sie Ausdrücke im [Dashboard-Builder](/builder/widgets.md) verwenden.** Sie können Ausdrücke in den Widgets **Zahlen, Kategorien** und **Kreisdiagramm** eingeben. Wir listen und beschreiben die Ausdrücke, die Sie in GOAT verwenden können.

<b>Sie funktionieren genauso wie in QGIS, und durch ihre Kombination können Sie komplexere Berechnungen durchführen oder Ihre Daten filtern.</b>
<p></p>

:::info

Wenn Sie sich auf ein Feld beziehen, setzen Sie es nur in Klammern: **(Feldname)**.

:::

## Numerische Funktionen
Die folgenden Funktionen arbeiten nur mit Zahlenfeldern. Die Eingabe und die Ausgabe sind numerische Werte.

| Ausdruck | Funktion  |  Beispiel |
|------------|-----------|-----------|
| **abs(x)**  | gibt den Absolutwert einer Zahl zurück |  <button>abs(-5)</button> = 5 |
| **sqrt(x)**  | gibt die Quadratwurzel einer Zahl zurück  | <button>sqrt(16)</button> = 4 |
| **pow(x, y)**  | hebt *x* zur Potenz von *y*  | <button>pow(2, 3)</button> = 8 |
| **exp(x)**  | gibt *e* zur Potenz von *x* zurück| <button>exp(1)</button> = 2,718... |
| **ln(x)**  | natürlicher Logarithmus (Basis *e*) von *x*, Umkehrung von *exp* | <button>ln(10)</button> = 2.303...
| **log10(x)**  | Logarithmus zur Basis 10 von *x*  | <button>log10(100)</button> = 2 |
| **round(x, n)**  | rundet eine Zahl *x* auf *n* Dezimalstellen  | <button>round(1.235813, 2)</button> = 1.24 |
| **ceil(x)**  | rundet *auf* zur nächsten ganzen Zahl  | <button>ceil(1.3))</button> = 2 |
| **floor(x)**  | rundet *ab* zur vorherigen ganzen Zahl | <button>floor(1.3)</button> = 1 |
| **pi**  |gibt den Wert von *π* zurück  | <button>π</button> = 3.142.... |
| **sin(x)**  | gibt den Sinus von *x* (Radianten) zurück | <button>sin(1)</button> = 0.841... |
| **cos(x)**  | gibt den Kosinus von *x* (Radianten) zurück | <button>cos(1)</button> = 0.541... |
| **tan(x)**  |  gibt den Tangens von *x* (Radianten) zurück | <button>tan(0.75)</button> = 0.932... |
| **asin(x)**  |  gibt den Arkussinus von *x* (Radianten) zurück | <button>asin(1)</button> = 1.571... |
| **acos(x)**  |  gibt den Arkuskosinus von *x* (Radianten) zurück | <button>acos(0.5)</button> = 1.047... |
| **atan(x)**  |  gibt den Arkustangens von *x* (Radianten) zurück | <button>atan(1)</button> = 0.785... |
| **degrees(x)**  | konvertiert Winkel x *von Radianten zu Grad* | <button>degrees(1)</button> = 57.296... |
| **radians(x)**  | konvertiert Winkel x *von Grad zu Radianten* | <button>radians(180)</button> = 3.142... |
| **rand(x, y)**  | erzeugt eine Zufallszahl zwischen x und y | <button>rand(1, 5)</button> = 3.17 |

## String-Funktionen
Die folgenden Funktionen arbeiten nur mit Textfeldern. Die Eingabe und die Ausgabe sind Textwerte.

| Ausdruck | Funktion  |  Beispiel |
|------------|-----------|----------|
| **length(string)**  | gibt die *Anzahl der Zeichen* in einem String *ohne Leerzeichen* zurück | <button>length(mobility)</button> = 8 |
| **char_length(string)**  | gibt die *Anzahl der Zeichen* in einem String *mit Leerzeichen* zurück | <button>length(GOAT city)</button> = 9 |
| **upper(string)**  | konvertiert alle Buchstaben zu *Großbuchstaben*  | <button>upper(walking)</button> = WALKING |
| **lower(string)**  | konvertiert alle Buchstaben zu *Kleinbuchstaben* | <button>lower(GOAT)</button> = goat |
| **trim(string)**  | entfernt *führende und nachfolgende Leerzeichen* |  <button>trim(  biking   )</button> = biking |
| **ltrim(string)**  | entfernt *Leerzeichen nur auf der linken* Seite  |  <button>ltrim(  biking)</button> = biking |
| **rtrim(string)**  | entfernt *Leerzeichen nur auf der rechten* Seite  |<button>rtrim(biking  )</button> = biking |
| **substr(string, start, length)**  | gibt einen Teilstring zurück, der an Position *start* beginnt mit optionaler *Länge* | <button>substr(mobility, 1, 3)</button> = mob |
| **substring(string, start, length)**  |  gibt einen Teilstring zurück, der an Position *start* beginnt mit optionaler *Länge* | <button>substring(mobility, 1, 3)</button> = mob |
| **left(string, n)**  | gibt die *äußersten linken n Zeichen* zurück | <button>left(accessibility, 4)</button> = acce |
| **right(string, n)**  | gibt die *äußersten rechten n Zeichen* zurück | <button>right(accessibility, 4)</button> = lity |
| **replace(string, search, replace_with)** | ersetzt *alle Vorkommen eines Teilstrings durch einen anderen* | <button>replace(bike_lane, _ , )</button> = bike lane |
| **regexp_replace(string, pattern, replacement)** | verwendet *reguläre Ausdrücke um Teile eines Textes zu finden und zu ersetzen* |<button>regexp_replace(BusStop12, 0-9+, #)</button> = BusStop# |
| **regexp_substr(string, pattern)**  | extrahiert den *ersten Teilstring der einem regulären Ausdrucksmuster entspricht* |  <button>regexp_substr(StopID: 45B, 0-9+)</button> = 45  |
| **strpos(string, substring)**  | gibt die *Position (Index) zurück, an der ein Teilstring zum ersten Mal auftritt* und gibt 0 zurück, wenn nicht gefunden |  <button>strops(WalkScore, Score)</button> = 5  |
| **concat(a,b...)**  | *verbindet mehrere Strings oder Felder* miteinander |    |

## Datum-Zeit-Funktionen

Die folgenden Funktionen arbeiten nur mit Datum/Zeit-Feldern. Die Eingabe und die Ausgabe sind Datum/Zeit-Werte.

| Ausdruck | Funktion  |  Beispiel |
|------------|-----------|----------|
| **now()**  | gibt das *aktuelle Datum und die Uhrzeit* zurück |  <button>now()</button> = 2025-10-07 11:35:00 |
| **age(date1, date2)**  | gibt das *Zeitintervall* zwischen zwei Daten zurück  | <button>age(now(), birth_date)</button> = 25 years 3 mons 12 days  |
| **extract(part, date)**  | extrahiert eine spezifische Komponente aus einem Datum (Jahr, Monat, Tag, Stunde, Minute, Sekunde)  | <button>extract('year', "survey_date")</button> = 2025 |
| **date_part(part, date)**  | ähnlich wie *extract* gibt den spezifizierten Teil eines Datums zurück | <button>date_part('month', "survey_date")</button> = 10 |
| **make_date(year, month, day)**  | erstellt ein Datum aus numerischem Jahr, Monat, Tag | <button>make_date(2025, 10, 8)</button> = 2025-10-08 |
| **make_time(hour, minute, second)**  | erstellt eine Uhrzeit aus numerischer Stunde, Minute, Sekunde | <button>make_time(14, 30, 0)</button> =  14:30:00 |
| **make_timestamp(year, month, day, hour, minute, second)**  | kombiniert Datum und Uhrzeit zu einem Zeitstempel  | <button>make_timestamp(2025, 10, 8, 14, 30, 0)</button> = 2025-10-08 14:30:00 |
| **to_date(string, format)**  | konvertiert einen Textstring zu einem Datum unter Verwendung des gegebenen Formats  | <button>to_date('08/10/2025','DD/MM/YYYY')</button> = 2025-10-08  |
| **to_timestamp(string, format)**  | konvertiert einen Textstring zu einem Zeitstempel unter Verwendung des gegebenen Formats  |  <button>to_timestamp('08/10/2025 14:30','DD/MM/YYYY HH24:MI')</button> = 2025-10-08 14:30:00 |
| **to_char(date, format)**  | konvertiert ein Datum oder Zeitstempel zu einem formatierten Textstring  | <button>to_char("survey_date",'YYYY-MM-DD')</button> = '2025-10-08' |

## Konvertierungsfunktionen

Die folgenden Funktionen konvertieren einen Wert von einem Typ zu einem anderen. Die Eingabe und die Ausgabe haben unterschiedliche Typen.

| Ausdruck | Funktion  |  Beispiel |
|------------|-----------|----------|
| **to_int(x)**  | konvertiert x zu einer ganzen Zahl | <button>to_int(3.9)</button> = 3 |
| **to_real(x)**  | konvertiert *x* zu einer **reellen (Dezimal-)Zahl** | <button>to_real('3.9')</button> = 3.9 |
| **to_string(x)**  |  konvertiert *x* zu einem **Textstring** | <button>to_string(25)</button> = '25' |

## Allgemeine Funktionen

Die folgenden Funktionen arbeiten mit jedem Feldtyp. Die Eingabe und die Ausgabe haben denselben Typ.

| Ausdruck | Funktion  |  Beispiel |
|------------|-----------|----------|
| **coalesce(x, y, ...)** | gibt den **ersten Nicht-Null-Wert** aus der gegebenen Liste von Eingaben zurück | <button>coalesce(NULL, NULL, 5, 8)</button> = 5 |
| **nullif(x, y)** | gibt **NULL zurück wenn x gleich y ist**, andernfalls gibt es *x* zurück | <button>nullif(10, 10)</button> = NULL |

## Aggregationsfunktionen

Die folgenden Funktionen arbeiten mit jedem Feldtyp. Die Eingabe und die Ausgabe haben denselben Typ.

| Ausdruck | Funktion | Beispiel |
|------------|-----------|----------|
| **sum(field)** | gibt die **Gesamtsumme** aller Werte in einem Feld (oder einer Gruppe) zurück | <button>sum("population")</button> = 15230 |
| **avg(field)** | gibt den **Durchschnittswert** eines Feldes zurück | <button>avg("travel_time")</button> = 12.6 |
| **min(field)** | gibt den **kleinsten (Minimum-)Wert** in einem Feld zurück | <button>min("distance")</button> = 0.5 |
| **max(field)** | gibt den **größten (Maximum-)Wert** in einem Feld zurück | <button>max("distance")</button> = 18.2 |
| **count(field)** | gibt die **Anzahl der Features oder Nicht-Null-Werte** in einem Feld zurück | <button>count("POI_name")</button> = 347 |

## Metrische Unäre Funktionen

| Ausdruck | Funktion | Beispiel |
|------------|-----------|----------|
| **$area** | gibt die **Fläche** eines Polygon-Features in den **Koordinateneinheiten des Layers** zurück (z.B. m²) | <button>$area</button> = 12500 |
| **ST_Area(geometry)** | gibt die **Fläche einer spezifizierten Geometrie** zurück; wird in Ausdrücken mit Geometriefunktionen verwendet | <button>ST_Area($geometry)</button> = 12500 |
| **$length** | gibt die **Länge** eines Linien-Features in **Layer-Einheiten** zurück (z.B. Meter) | <button>$length</button> = 275.3 |
| **ST_Length(geometry)** | gibt die **Länge einer gegebenen Geometrie** (Linie oder Polygongrenze) zurück | <button>ST_Length($geometry)</button> = 275.3 |
| **perimeter** | gibt die **Umfangslänge** eines Polygon-Features zurück | <button>perimeter($geometry)</button> = 490.6 |
| **ST_Perimeter(geometry)** | gibt den **Umfang** einer Geometrie zurück, ähnlich wie `perimeter()` aber folgt der **PostGIS-Standard-Benennung** | <button>ST_Perimeter($geometry)</button> = 490.6 |

## Metrische Pufferfunktion

| Ausdruck | Funktion | Beispiel |
|------------|-----------|----------|
| **buffer(geometry, distance)** | erstellt einen **Polygon-Puffer** um eine Geometrie in der angegebenen *Entfernung* (in Layer-Einheiten, z.B. Meter) | <button>buffer($geometry, 100)</button> = Polygon, das eine 100 m Pufferfläche repräsentiert |

## Geometrie-Unäre Funktionen

| Ausdruck | Funktion | Beispiel |
|------------|-----------|----------|
| **centroid(geometry)** | gibt den **Mittelpunkt** (geometrische Mitte) eines Features zurück | <button>centroid($geometry)</button> = Point(13.41, 52.52) |
| **ST_Centroid(geometry)** | dasselbe wie `centroid()`, folgt der **PostGIS-Benennungskonvention** | <button>ST_Centroid($geometry)</button> = Point(13.41, 52.52) |
| **convex_hull(geometry)** | erstellt das **kleinste konvexe Polygon**, das alle Teile einer Geometrie umschließt | <button>convex_hull($geometry)</button> = Polygon(...) |
| **ST_ConvexHull(geometry)** | dasselbe wie `convex_hull()`, mit **PostGIS-Syntax** | <button>ST_ConvexHull($geometry)</button> = Polygon(...) |
| **envelope(geometry)** | gibt das **minimale Begrenzungsrechteck** einer Geometrie zurück | <button>envelope($geometry)</button> = Polygon((xmin, ymin), (xmax, ymax)) |
| **ST_Envelope(geometry)** | dasselbe wie `envelope()`, in **PostGIS-Form** | <button>ST_Envelope($geometry)</button> = Polygon(...) |
| **make_valid(geometry)** | repariert **ungültige Geometrien** (z.B. Selbstüberschneidungen, Lücken) | <button>make_valid($geometry)</button> = Polygon(...) |
| **ST_MakeValid(geometry)** | dasselbe wie `make_valid()`, **PostGIS-Version** | <button>ST_MakeValid($geometry)</button> = Polygon(...) |
| **is_empty(geometry)** | gibt **TRUE zurück wenn Geometrie keinen räumlichen Inhalt hat** | <button>is_empty($geometry)</button> = FALSE |
| **ST_IsEmpty(geometry)** | dasselbe wie `is_empty()`, **PostGIS-Form** | <button>ST_IsEmpty($geometry)</button> = FALSE |
| **is_valid(geometry)** | gibt **TRUE zurück wenn Geometrie gültig ist** | <button>is_valid($geometry)</button> = TRUE |
| **ST_IsValid(geometry)** | dasselbe wie `is_valid()`, **PostGIS-Version** | <button>ST_IsValid($geometry)</button> = TRUE |
| **x(geometry)** | gibt die **X-Koordinate** einer Punkt-Geometrie zurück | <button>x($geometry)</button> = 13.405 |
| **ST_X(geometry)** | dasselbe wie `x()`, **PostGIS-Version** | <button>ST_X($geometry)</button> = 13.405 |
| **y(geometry)** | gibt die **Y-Koordinate** einer Punkt-Geometrie zurück | <button>y($geometry)</button> = 52.520 |
| **ST_Y(geometry)** | dasselbe wie `y()`, **PostGIS-Version** | <button>ST_Y($geometry)</button> = 52.520 |
| **xmin(geometry)** | gibt die **minimale X-Koordinate** (linke Grenze) einer Geometrie zurück | <button>xmin($geometry)</button> = 13.30 |
| **ST_XMin(geometry)** | dasselbe wie `xmin()`, **PostGIS-Syntax** | <button>ST_XMin($geometry)</button> = 13.30 |
| **xmax(geometry)** | gibt die **maximale X-Koordinate** (rechte Grenze) einer Geometrie zurück | <button>xmax($geometry)</button> = 13.50 |
| **ST_XMax(geometry)** | dasselbe wie `xmax()`, **PostGIS-Syntax** | <button>ST_XMax($geometry)</button> = 13.50 |
| **ymin(geometry)** | gibt die **minimale Y-Koordinate** (untere Grenze) einer Geometrie zurück | <button>ymin($geometry)</button> = 52.45 |
| **ST_YMin(geometry)** | dasselbe wie `ymin()`, **PostGIS-Version** | <button>ST_YMin($geometry)</button> = 52.45 |
| **ymax(geometry)** | gibt die **maximale Y-Koordinate** (obere Grenze) einer Geometrie zurück | <button>ymax($geometry)</button> = 52.55 |
| **ST_YMax(geometry)** | dasselbe wie `ymax()`, **PostGIS-Version** | <button>ST_YMax($geometry)</button> = 52.55 |


Hier sind einige Beispiele für kombinierte Ausdrücke für komplexere Berechnungen:
https://github.com/plan4better/goat/blob/main/apps/core/src/core/expression_converter.py 



:::tip

Weitere Informationen finden Sie in der [QGIS-Dokumentation](https://docs.qgis.org/3.28/en/docs/user_manual/expressions/expressions.html).

:::