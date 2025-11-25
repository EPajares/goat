---
sidebar_position: 4
---
import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';


# Filter


**Filter begrenzt die Datensichtbarkeit auf Ihrer Karte** durch logische Ausdrücke (z.B. Supermärkte mit bestimmten Namen) oder räumliche Ausdrücke (z.B. Punkte innerhalb eines Begrenzungsrahmens). **Das Filter-Tool ermöglicht es Ihnen, sich auf relevante Informationen zu konzentrieren, ohne die ursprünglichen Daten zu verändern.** Es funktioniert mit **Punkt-Layern** und **Polygon-Layern**, die `Zahlen` und `String`-Datentypen enthalten.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>

  <img src={require('/img/map/filter/filter_clicking.gif').default} alt="Filter tool in GOAT" style={{ maxHeight: "auto", maxWidth: "auto", objectFit: "cover"}}/>

</div> 


## Wie benutzt man den Filter?

### Einzelausdruck-Filterung

<div class="step">
  <div class="step-number">1</div>
  <div class="content">Wählen Sie den zu filternden Layer aus und klicken Sie auf das <code>Filter</code> <img src={require('/img/map/filter/filter_icon.png').default} alt="Filter Icon" style={{ maxHeight: "20px", maxWidth: "20px"}}/> Symbol in der <b>Werkzeugleiste</b> rechts.</div>
</div>

<div class="step">
  <div class="step-number">2</div>
  <div class="content">Der <code>Aktive Layer</code>-Selektor <strong>zeigt den aktuell ausgewählten Layer</strong> für die Filterung an.</div>
</div>

<div class="step">
  <div class="step-number">3</div>
  <div class="content">Klicken Sie auf <code>+ Ausdruck hinzufügen</code>, um <strong>einen neuen Filterausdruck hinzuzufügen</strong>.</div>
</div>

<div class="step">
  <div class="step-number">4</div>
  <div class="content">Wählen Sie <code>Logischer Ausdruck</code> oder <code>Räumlicher Ausdruck</code>, um <strong>Ihren Filtertyp zu definieren</strong>.</div>
</div>

<Tabs>
  <TabItem value="Logical expression" label="Logischer Ausdruck" default className="tabItemBox">

<div class="step">
  <div class="step-number">5</div>
  <div class="content">Wählen Sie das <code>Feld</code> (Attribut), um <strong>zu filtern</strong>.</div>
</div>

<div class="step">
  <div class="step-number">6</div>
  <div class="content">Wählen Sie den <code>Operator</code>. Verfügbare Optionen variieren je nach Datentyp: Zahl und String.</div>
</div>

<div style={{ display: 'flex', justifyContent: 'center' }}>

| Ausdrücke für `Zahl` | Ausdrücke für `String` |
| -------|----|
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

</div>

:::tip Hinweis
Für die Ausdrücke **"enthält"** und **"schließt aus"** können mehrere Werte ausgewählt werden.
:::

<div class="step">
  <div class="step-number">7</div>
  <div class="content">Legen Sie Ihre Filterkriterien fest. Die Karte wird <strong>automatisch aktualisiert</strong> und zeigt ein Filtersymbol auf dem gefilterten Layer an.</div>
</div>

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/map/filter/filter_atlayer.webp').default} alt="Filter Result in GOAT" style={{ maxHeight: "auto", maxWidth: "auto", objectFit: "cover"}}/>
</div> 
</TabItem>

<TabItem value="Spatial expression" label="Räumlicher Ausdruck" default className="tabItemBox">
<div class="step">
  <div class="step-number">5</div>
  <div class="content">Wählen Sie die <code>Schnittmethode</code> für die <strong>räumliche Begrenzung</strong>.</div>
</div>

<Tabs>
  <TabItem value="Map extent" label="Kartenausdehnung" default className="tabItemBox">
<div class="step">
  <div class="step-number">6</div>
  <div class="content">Layer wird <strong>automatisch auf die aktuelle Kartenausdehnung zugeschnitten</strong>. Um den Filter zu ändern, <strong>zoomen Sie hinein/heraus</strong> und aktualisieren Sie die Kartenausdehnung.</div>
</div>

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>

  <img src={require('/img/map/filter/Map_extend.gif').default} alt="Attribute Selection" style={{ maxHeight: "auto", maxWidth: "auto", objectFit: "cover"}}/>

</div> 
</TabItem>

<TabItem value="Boundary" label="Begrenzung" default className="tabItemBox">

:::info demnächst verfügbar

Diese Funktion wird derzeit entwickelt. 🧑🏻‍💻

:::
</TabItem>
</Tabs>

</TabItem>
</Tabs>

### Mehrfachausdruck-Filterung

<strong>Kombinieren Sie mehrere Filter</strong>, indem Sie die Schritte 3-7 für jeden Ausdruck wiederholen. In <code>Filter Ergebnisse</code> wählen Sie <code>Alle Filter erfüllen</code> (UND) oder <code>Mindestens einen Filter erfüllen</code> (ODER), um <strong>zu steuern, wie Filter interagieren</strong>.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/map/filter/filter-results.png').default} alt="Logic Operators" style={{ maxHeight: "300px", maxWidth: "300px", objectFit: "cover"}}/>
</div>
  
### Ausdrücke und Filter löschen

<strong>Einzelne Ausdrücke entfernen</strong>: Klicken Sie auf das <code>Weitere Optionen</code> <img src={require('/img/map/filter/3dots_horizontal.png').default} alt="Options" style={{ maxHeight: "25px", maxWidth: "25px", objectFit: "cover"}}/> Menü neben dem Ausdruck, dann klicken Sie auf <code>Löschen</code>, um <strong>den Ausdruck zu entfernen</strong>.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/map/filter/filter_delete.png').default} alt="Delete" style={{ maxHeight: "300px", maxWidth: "300px", objectFit: "cover"}}/>
</div>

<p></p>
<strong>Gesamten Filter entfernen</strong>: Klicken Sie auf <code>Filter löschen</code> am unteren Rand des Filtermenüs, um <strong>alle Filter zu entfernen</strong>.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>

  <img src={require('/img/map/filter/filter_clear.png').default} alt="Clear Filters" style={{ maxHeight: "300px", maxWidth: "300px", objectFit: "cover"}}/>

</div> 
