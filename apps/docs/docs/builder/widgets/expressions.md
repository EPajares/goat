---
sidebar_position: 4
---

# Expressions

This page helps you to understand how to use the expressions in the [Dashboard builder](/builder/widgets.md). You can enter expressions in the **Numbers, Categories,** and **Pie chart widgets.** We're listing and describing the expressions that you could use in GOAT.

They work the same way as in QGIS, and by combining them you can compute more complex calculations or filter your data. 

:::info

When referring to a field, insert it only in paratheses: **(FieldName)**.

:::

## Numeric functions
The following functions work with number fields only. The input and the output will be numeric values.

| Expression | Function  |  Example |
|------------|-----------|-----------|
| **abs(x)**  | returns the absolute value of a number |  <button>abs(-5)</button> = 5 |
| **sqrt(x)**  | returns the square root of a number  | <button>sqrt(16)</button> = 4 |
| **pow(x, y)**  | raises *x* to the power of *y*  | <button>pow(2, 3)</button> = 8 |
| **exp(x)**  | returns *e* raised to the power of *x*| <button>exp(1)</button> = 2,718... |
| **ln(x)**  | natural logarithm (base *e*) of *x*, inverse of *exp* | <button>ln(10)</button> = 2.303...
| **log10(x)**  | logarithm base 10 of *x*  | <button>log10(100)</button> = 2 |
| **round(x, n)**  | rounds a number *x* to *n* decimal places  | <button>round(1.235813, 2)</button> = 1.24 |
| **ceil(x)**  | rounds *up* to the next whole numer  | <button>ceil(1.3))</button> = 2 |
| **floor(x)**  | rounds *down* to the previous whole numer | <button>floor(1.3)</button> = 1 |
| **pi**  |returns the value of *π*  | <button>π</button> = 3.142.... |
| **sin(x)**  | returns the sine of *x* (radians) | <button>sin(1)</button> = 0.841... |
| **cos(x)**  | returns the cosine of *x* (radians) | <button>cos(1)</button> = 0.541... |
| **tan(x)**  |  returns the tangent of *x* (radians) | <button>tan(0.75)</button> = 0.932... |
| **asin(x)**  |  returns the arcsine of *x* (radians) | <button>asin(1)</button> = 1.571... |
| **acos(x)**  |  returns the arccosine of *x* (radians) | <button>acos(0.5)</button> = 1.047... |
| **atan(x)**  |  returns the arctangent of *x* (radians) | <button>atan(1)</button> = 0.785... |
| **degrees(x)**  | converts angle x *from radians to degrees* | <button>degrees(1)</button> = 57.296... |
| **radians(x)**  | converts angle x *from degrees to radians* | <button>radians(180)</button> = 3.142... |
| **rand(x, y)**  | generates a random number between x and y | <button>rand(1, 5)</button> = 3.17 |

## String functions
The following functions work with text fields only. The input and the output will be text values.

| Expression | Function  |  Example |
|------------|-----------|----------|
| **length(string)**  | returns the *number of characters* in a string *excluding space* | <button>length(mobility)</button> = 8 |
| **char_length(string)**  | returns the *number of characters* in a string *including space* | <button>length(GOAT city)</button> = 9 |
| **upper(string)**  | converts all letters to *uppercase*  | <button>upper(walking)</button> = WALKING |
| **lower(string)**  | converts all letters to *lowercase* | <button>lower(GOAT)</button> = goat |
| **trim(string)**  | removes *leading and trailing spaces* |  <button>trim(  biking   )</button> = biking |
| **ltrim(string)**  | removes *spaces only on the left* side  |  <button>ltrim(  biking)</button> = biking |
| **rtrim(string)**  | removes *spaces only on the right* side  |<button>rtrim(biking  )</button> = biking |
| **substr(string, start, length)**  | returns a substring starting at *start* position with optional *length* | <button>substr(mobility, 1, 3)</button> = mob |
| **substring(string, start, length)**  |  returns a substring starting at *start* position with optional *length* | <button>substring(mobility, 1, 3)</button> = mob |
| **left(string, n)**  | returns the *leftmost n characters* | <button>left(accessibility, 4)</button> = acce |
| **right(string, n)**  | retunrs the *rightmost n characters* | <button>right(accessibility, 4)</button> = lity |
| **replace(string, search, replace_with)** | replaces *all occurences of one substring with another* | <button>replace(bike_lane, _ , )</button> = bike lane |
| **regexp_replace(string, pattern, replacement)** | uses *regular expressions to find and replace part of a text* |<button>regexp_replace(BusStop12, 0-9+, #)</button> = BusStop# |
| **regexp_substr(string, pattern)**  | extracts the *first substring that matches a regular expression pattern* |  <button>regexp_substr(StopID: 45B, 0-9+)</button> = 45  |
| **strpos(string, substring)**  | returns the *position (index) where a substring first appears* and returns 0 if not found |  <button>strops(WalkScore, Score)</button> = 5  |
| **concat(a,b...)**  | *joins multiple strings or fields* together |    |

## Date time functions

The following functions work with date/time fields only. The input and the output will be date/time values.

| Expression | Function  |  Example |
|------------|-----------|----------|
| **now()**  | returns the *current date and time* |  <button>now()</button> = 2025-10-07 11:35:00 |
| **age(date1, date2)**  | returns the *time interval* between two dates  | <button>age(now(), birth_date)</button> = 25 years 3 mons 12 days  |
| **extract(part, date)**  | extracts a specific component from a date (year, month, day, hour, minute, second)  | <button>extract('year', "survey_date")</button> = 2025 |
| **date_part(part, date)**  | similar to *extract* returns the specified part of a date | <button>date_part('month', "survey_date")</button> = 10 |
| **mmake_date(year, month, day)**  | creates a date from numeric year, month, day | <button>make_date(2025, 10, 8)</button> = 2025-10-08 |
| **make_time(hour, minute, second)**  | creates a time from numeric hour, minute, second | <button>make_time(14, 30, 0)</button> =  14:30:00 |
| **make_timestamp(year, month, day, hour, minute, second)**  | combines date and time into a timestamp  | <button>make_timestamp(2025, 10, 8, 14, 30, 0)</button> = 2025-10-08 14:30:00 |
| **to_date(string, format)**  | converts a text string to a date using the given format  | <button>to_date('08/10/2025','DD/MM/YYYY')</button> = 2025-10-08  |
| **to_timestamp(string, format)**  | converts a text string to a timestamp using the given format  |  <button>to_timestamp('08/10/2025 14:30','DD/MM/YYYY HH24:MI')</button> = 2025-10-08 14:30:00 |
| **to_char(date, format)**  | converts a date or timestamp to a formatted text string  | <button>to_char("survey_date",'YYYY-MM-DD')</button> = '2025-10-08' |

## Casting functions

The following functions convert a value from one type to another. The input and the output will be of different types.

| Expression | Function  |  Example |
|------------|-----------|----------|
| **to_int(x)**  | converts x to an integer (whole number) | <button>to_int(3.9)</button> = 3 |
| **to_real(x)**  | converts *x* to a **real (decimal) number** | <button>to_real('3.9')</button> = 3.9 |
| **to_string(x)**  |  converts *x* to a **text string** | <button>to_string(25)</button> = '25' |

## Generic functions

The following functions work with any type of field. The input and the output will be of the same type.



| Expression | Function  |  Example |
|------------|-----------|----------|
| | **coalesce(x, y, ...)** | returns the **first non-null value** from the given list of inputs | <button>coalesce(NULL, NULL, 5, 8)</button> = 5 |
| **nullif(x, y)** | returns **NULL if x equals y**, otherwise returns *x* | <button>nullif(10, 10)</button> = NULL |


## Aggregate functions

The following functions work with any type of field. The input and the output will be of the same type.

| Expression | Function | Example |
|------------|-----------|----------|
| **sum(field)** | returns the **total sum** of all values in a field (or group) | <button>sum("population")</button> = 15230 |
| **avg(field)** | returns the **average (mean)** value of a field | <button>avg("travel_time")</button> = 12.6 |
| **min(field)** | returns the **smallest (minimum)** value in a field | <button>min("distance")</button> = 0.5 |
| **max(field)** | returns the **largest (maximum)** value in a field | <button>max("distance")</button> = 18.2 |
| **count(field)** | returns the **number of features or non-null values** in a field | <button>count("POI_name")</button> = 347 |

## Metric unary functions

| Expression | Function | Example |
|------------|-----------|----------|
| **$area** | returns the **area** of a polygon feature in the **layer’s coordinate units** (e.g., m²) | <button>$area</button> = 12500 |
| **ST_Area(geometry)** | returns the **area of a specified geometry**; used in expressions with geometry functions | <button>ST_Area($geometry)</button> = 12500 |
| **$length** | returns the **length** of a line feature in **layer units** (e.g., meters) | <button>$length</button> = 275.3 |
| **ST_Length(geometry)** | returns the **length of a given geometry** (line or polygon boundary) | <button>ST_Length($geometry)</button> = 275.3 |
| **perimeter** | returns the **perimeter length** of a polygon feature | <button>perimeter($geometry)</button> = 490.6 |
| **ST_Perimeter(geometry)** | returns the **perimeter** of a geometry, similar to `perimeter()` but following the **PostGIS standard naming** | <button>ST_Perimeter($geometry)</button> = 490.6 |


## Metric buffer function

| Expression | Function | Example |
|------------|-----------|----------|
| **buffer(geometry, distance)** | creates a **polygon buffer** around a geometry at the specified *distance* (in layer units, e.g. meters) | <button>buffer($geometry, 100)</button> = Polygon representing a 100 m buffer area |


## Geometry unary functions

| Expression | Function | Example |
|------------|-----------|----------|
| **centroid(geometry)** | returns the **center point** (geometric middle) of a feature | <button>centroid($geometry)</button> = Point(13.41, 52.52) |
| **ST_Centroid(geometry)** | same as `centroid()`, follows **PostGIS naming convention** | <button>ST_Centroid($geometry)</button> = Point(13.41, 52.52) |
| **convex_hull(geometry)** | creates the **smallest convex polygon** that encloses all parts of a geometry | <button>convex_hull($geometry)</button> = Polygon(...) |
| **ST_ConvexHull(geometry)** | same as `convex_hull()`, using **PostGIS syntax** | <button>ST_ConvexHull($geometry)</button> = Polygon(...) |
| **envelope(geometry)** | returns the **minimum bounding rectangle** of a geometry | <button>envelope($geometry)</button> = Polygon((xmin, ymin), (xmax, ymax)) |
| **ST_Envelope(geometry)** | same as `envelope()`, in **PostGIS form** | <button>ST_Envelope($geometry)</button> = Polygon(...) |
| **make_valid(geometry)** | fixes **invalid geometries** (e.g. self-intersections, gaps) | <button>make_valid($geometry)</button> = Polygon(...) |
| **ST_MakeValid(geometry)** | same as `make_valid()`, **PostGIS version** | <button>ST_MakeValid($geometry)</button> = Polygon(...) |
| **is_empty(geometry)** | returns **TRUE if geometry has no spatial content** | <button>is_empty($geometry)</button> = FALSE |
| **ST_IsEmpty(geometry)** | same as `is_empty()`, **PostGIS form** | <button>ST_IsEmpty($geometry)</button> = FALSE |
| **is_valid(geometry)** | returns **TRUE if geometry is valid** | <button>is_valid($geometry)</button> = TRUE |
| **ST_IsValid(geometry)** | same as `is_valid()`, **PostGIS version** | <button>ST_IsValid($geometry)</button> = TRUE |
| **x(geometry)** | returns the **X-coordinate** of a point geometry | <button>x($geometry)</button> = 13.405 |
| **ST_X(geometry)** | same as `x()`, **PostGIS version** | <button>ST_X($geometry)</button> = 13.405 |
| **y(geometry)** | returns the **Y-coordinate** of a point geometry | <button>y($geometry)</button> = 52.520 |
| **ST_Y(geometry)** | same as `y()`, **PostGIS version** | <button>ST_Y($geometry)</button> = 52.520 |
| **xmin(geometry)** | returns the **minimum X-coordinate** (left boundary) of a geometry | <button>xmin($geometry)</button> = 13.30 |
| **ST_XMin(geometry)** | same as `xmin()`, **PostGIS syntax** | <button>ST_XMin($geometry)</button> = 13.30 |
| **xmax(geometry)** | returns the **maximum X-coordinate** (right boundary) of a geometry | <button>xmax($geometry)</button> = 13.50 |
| **ST_XMax(geometry)** | same as `xmax()`, **PostGIS syntax** | <button>ST_XMax($geometry)</button> = 13.50 |
| **ymin(geometry)** | returns the **minimum Y-coordinate** (bottom boundary) of a geometry | <button>ymin($geometry)</button> = 52.45 |
| **ST_YMin(geometry)** | same as `ymin()`, **PostGIS version** | <button>ST_YMin($geometry)</button> = 52.45 |
| **ymax(geometry)** | returns the **maximum Y-coordinate** (top boundary) of a geometry | <button>ymax($geometry)</button> = 52.55 |
| **ST_YMax(geometry)** | same as `ymax()`, **PostGIS version** | <button>ST_YMax($geometry)</button> = 52.55 |





https://github.com/plan4better/goat/blob/main/apps/core/src/core/expression_converter.py 

Here are some examples of combined expressions for more complex calculations:


:::tip

Find further information in the [QGIS documentation](https://docs.qgis.org/3.28/en/docs/user_manual/expressions/expressions.html).

:::
