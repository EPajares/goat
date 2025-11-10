---
sidebar_position: 4
---

import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';

# Filter

Der **Filter** kann verwendet werden, um die auf der Karte sichtbaren Daten einzuschränken. Sie können entweder nach **logischem Ausdruck** filtern (z.B. nur Supermärkte mit einem bestimmten Namen anzeigen) oder nach **räumlichem Ausdruck** (z.B. nur Punkte innerhalb eines bestimmten Begrenzungsrahmens anzeigen).

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>

  <img src={require('/img/map/filter/filter_clicking.gif').default} alt="Filter-Tool in GOAT" style={{ maxHeight: "auto", maxWidth: "auto", objectFit: "cover" }}/>

</div> 

## 1. Erklärung

Der **Filter** <img src={require('/img/map/filter/filter_icon.png').default} alt="Filter Icon" style={{ maxHeight: "20px", maxWidth: "20px" }} /> ermöglicht es Benutzern, **nur bestimmte Elemente** aus einem größeren Datensatz basierend auf spezifischen Kriterien anzuzeigen. Dieses Tool hilft, ausgewählte Elemente aus einem großen geodatenbasierten Datensatz zu visualisieren, sodass Benutzer sich auf die Informationen konzentrieren können, die für sie am relevantesten sind.

Logische und räumliche Ausdrücke können basierend auf den Attributen von **Punkt-Layern** und **Polygon-Layern** mit unterschiedlichen Datentypen (`Zahl` und `String`) hinzugefügt werden.

:::info
Der **Filtervorgang ändert nicht die Originaldaten**. Er kann auf jede Ebene angewendet werden, um die zur Visualisierung und Analyse verwendeten Daten einzuschränken, ohne den zugrunde liegenden Datensatz zu ändern. Wenn der Filter zurückgesetzt wird, sind alle ursprünglichen Daten der Ebene wieder sichtbar.
:::

## 2. Beispielanwendungen
- Zeige alle Städte in Deutschland mit mehr als 50.000 Einwohnern.
- Zeige alle Carsharing-Stationen eines bestimmten Betreibers.
- Zeige die Regionen, die mehr als einen Flughafen haben.

## 3. Wie benutzt man den Filter?

### Einzelner Ausdruck filtern

<div class="step">
  <div class="step-number">1</div>
  <div class="content">Wählen Sie die Ebene aus, auf die Sie den Filter anwenden möchten. </div>
</div>

<div class="step">
  <div class="step-number">2</div>

  <div class="content">Klicken Sie auf <code>Filter</code> <img src={require('/img/map/filter/filter_icon.png').default} alt="Filter Icon" style={{ maxHeight: "20px", maxWidth: "20px" }} />. </div>
</div>

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/map/filter/filter.png').default} alt="Filter-Tool in GOAT" style={{ maxHeight: "auto", maxWidth: "auto", objectFit: "cover" }} />
</div> 

<p></p>
<div class="step">
  <div class="step-number">3</div>
  <div class="content">Die <code>Aktive Ebene</code> zeigt die derzeit ausgewählte Ebene, auf die der Filter angewendet wird.</div>
</div>

<div class="step">
  <div class="step-number">4</div>
  <div class="content">Klicken Sie auf <code>+ Ausdruck hinzufügen</code>.</div>
</div>

<div class="step">
  <div class="step-number">5</div>
  <div class="content">Wählen Sie, ob Sie basierend auf einem <b>logischen Ausdruck</b> oder einem <b>räumlichen Ausdruck</b> filtern möchten. </div>
</div>

<Tabs>
  <TabItem value="Logischer Ausdruck" label="Logischer Ausdruck" default className="tabItemBox">

<div class="step">
  <div class="step-number">6</div>
  <div class="content">Wählen Sie das <code>Feld</code> aus, also das Attribut, das Sie für die Filterung verwenden möchten.</div>
</div>

<div class="step">
  <div class="step-number">7</div>
  <div class="content">Wählen Sie den konkreten <code>Operator</code> aus, den Sie anwenden möchten. 
  <i>Hinweis: Die verfügbaren Optionen variieren je nach Datentyp des in Schritt 6 ausgewählten Attributs.</i>
  </div>
</div>

Die **Filterausdrücke** für `Zahl` (numerische Daten) und `String` (Textdaten) sind unten angegeben:

| Ausdrücke für `Zahl` | Ausdrücke für `String` |
| -------------------- | ---------------------- |
| ist  | ist |
| ist nicht  | ist nicht |
| enthält  | enthält  |
| schließt aus  |  schließt aus |
| ist mindestens  | beginnt mit |
| ist weniger als | endet mit |
| ist höchstens | enthält den Text |
| ist größer als | enthält den Text nicht |
| liegt zwischen | ist leerer String |
|  | ist kein leerer String |

:::tip Tipp
Für die Ausdrücke **"enthält"** und **"schließt aus"** können mehrere Werte ausgewählt werden.
:::

<div class="step">
  <div class="step-number">8</div>
  <div class="content">Legen Sie Ihre Filterkriterien fest. Die Karte wird automatisch mit den gefilterten Daten aktualisiert und das Filter-Symbol wird auf der gefilterten Ebene angezeigt.</div>
</div>

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/map/filter/filter_atlayer.webp').default} alt="Filterergebnis in GOAT" style={{ maxHeight: "auto", maxWidth: "auto", objectFit: "cover" }} />
</div> 

</TabItem>

<TabItem value="Räumlicher Ausdruck" label="Räumlicher Ausdruck" default className="tabItemBox">
<div class="step">
  <div class="step-number">6</div>
  <div class="content">Wählen Sie die <code>Schnittmethode</code> aus, also die Methode, die für die räumliche Begrenzung verwendet wird.</div>
</div>

<Tabs>
  <TabItem value="Kartenausdehnung" label="Kartenausdehnung" default className="tabItemBox">
<div class="step">
  <div class="step-number">7</div>
  <div class="content">Die Ebene wird automatisch auf die aktuelle Kartenausdehnung zugeschnitten. <p> Um den Filter zu ändern, zoomen Sie in die Karte hinein oder heraus, wählen Sie den gewünschten Ausschnitt und aktualisieren Sie die Kartenausdehnung mit der Schaltfläche.</p></div>
</div>

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>

  <img src={require('/img/map/filter/Map_extend.gif').default} alt="Attributauswahl" style={{ maxHeight: "auto", maxWidth: "auto", objectFit: "cover" }}/>

</div> 
</TabItem>

<TabItem value="Begrenzung" label="Begrenzung" default className="tabItemBox">

:::info coming soon

Dieses Feature wird derzeit entwickelt. 🧑🏻‍💻

:::
</TabItem>
</Tabs>

</TabItem>
</Tabs>

### Mehrfachausdruck-Filterung

Falls gewünscht, können Sie **mehrere Filter kombinieren** für eine Mehrfachausdruck-Filterung. Wiederholen Sie dazu einfach die Schritte 4-8 für jeden zusätzlichen Ausdruck. Im Feld <code>Logik-Operator</code> können Sie zwischen den logischen Kombinationen **UND** und **ODER** wählen.  
<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>

  <img src={require('/img/map/filter/filter-results.png').default} alt="Logische Operatoren" style={{ maxHeight: "300px", maxWidth: "300px", objectFit: "cover" }} />

</div> 

Wenn Sie **UND** auswählen, werden nur Elemente angezeigt, für die alle Filterausdrücke zutreffen. Bei der Auswahl von **ODER** werden Elemente angezeigt, wenn einer der Filterausdrücke zutrifft.

:::tip HINWEIS
Mehrfachausdruck-Filterung sollte sorgfältig und logisch angewendet werden, um das beste Ergebnis zu erzielen.
:::

### Ausdrücke und Filter löschen

Sie können entweder **einzelne Ausdrücke** aus dem Filter entfernen, indem Sie auf die drei Punkte <img src={require('/img/map/filter/3dots_horizontal.png').default} alt="Optionen" style={{ maxHeight: "25px", maxWidth: "25px", objectFit: "cover" }} /> neben dem Ausdruck klicken und dann auf `Löschen`. 


<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/map/filter/filter_delete.webp').default} alt="Löschen" style={{ maxHeight: "300px", maxWidth: "300px", objectFit: "cover" }} />

</div> 

Oder Sie können den **gesamten Filter** entfernen

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>

  <img src={require('/img/map/filter/clear_filter.webp').default} alt="Clear Filters" style={{ maxHeight: "300px", maxWidth: "300px", objectFit: "cover"}}/>

</div> 








