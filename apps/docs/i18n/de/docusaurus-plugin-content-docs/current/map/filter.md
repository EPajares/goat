---
sidebar_position: 4
---
import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';


# Filter

**Filter begrenzt die Datensichtbarkeit auf Ihrer Karte** durch logische Ausdrücke (z.B. Supermärkte mit bestimmten Namen) oder räumliche Ausdrücke (z.B. Punkte innerhalb eines Begrenzungsrahmens). Das <code>Filter</code> <img src={require('/img/map/filter/filter_icon.png').default} alt="Filter Icon" style={{ maxHeight: "20px", maxWidth: "20px"}}/> Tool **zeigt nur ausgewählte Elemente** aus größeren Datensätzen basierend auf spezifischen Kriterien an und ermöglicht es, sich auf relevante Informationen zu konzentrieren, ohne die ursprünglichen Daten zu verändern.

Funktioniert mit **Punkt-Layern** und **Polygon-Layern**, die `Zahlen` und `String`-Datentypen enthalten. **Filter verändert die ursprünglichen Daten nicht** - setzen Sie den Filter zurück, um alle ursprünglichen Layer-Daten wiederherzustellen.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>

  <img src={require('/img/map/filter/filter_clicking.gif').default} alt="Filter tool in GOAT" style={{ maxHeight: "auto", maxWidth: "auto", objectFit: "cover"}}/>

</div> 

## Wie benutzt man den Filter?

### Einzelausdruck-Filterung

<div class="step">
  <div class="step-number">1</div>
  <div class="content">Wählen Sie den zu filternden Layer aus und klicken Sie auf das <code>Filter</code> <img src={require('/img/map/filter/filter_icon.png').default} alt="Filter Icon" style={{ maxHeight: "20px", maxWidth: "20px"}}/> Symbol in der **Werkzeugleiste** rechts.</div>
</div>

<div class="step">
  <div class="step-number">2</div>
  <div class="content">Der <code>Aktive Layer</code>-Selektor **zeigt den aktuell ausgewählten Layer** für die Filterung an.</div>
</div>

<div class="step">
  <div class="step-number">3</div>
  <div class="content">Klicken Sie auf <code>+ Ausdruck hinzufügen</code>, um **einen neuen Filterausdruck hinzuzufügen**.</div>
</div>

<div class="step">
  <div class="step-number">4</div>
  <div class="content">Wählen Sie <code>Logischer Ausdruck</code> oder <code>Räumlicher Ausdruck</code>, um **Ihren Filtertyp zu definieren**.</div>
</div>

<Tabs>
  <TabItem value="Logical expression" label="Logischer Ausdruck" default className="tabItemBox">

<div class="step">
  <div class="step-number">5</div>
  <div class="content">Wählen Sie das <code>Feld</code> (Attribut) zum **Filtern aus**.</div>
</div>

<div class="step">
  <div class="step-number">6</div>
  <div class="content">Wählen Sie den <code>Operator</code>. Verfügbare Optionen **variieren je nach Datentyp**: Zahl und String.</div>
</div>

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


:::tip Hinweis
Für die Ausdrücke **"enthält"** und **"schließt aus"** können mehrere Werte ausgewählt werden.
:::

<div class="step">
  <div class="step-number">7</div>
  <div class="content">Legen Sie Ihre Filterkriterien fest. Die Karte **wird automatisch aktualisiert** und zeigt ein Filtersymbol auf dem gefilterten Layer an.</div>
</div>

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/map/filter/filter_atlayer.webp').default} alt="Filter Result in GOAT" style={{ maxHeight: "auto", maxWidth: "auto", objectFit: "cover"}}/>
</div> 
</TabItem>

<TabItem value="Spatial expression" label="Räumlicher Ausdruck" default className="tabItemBox">
<div class="step">
  <div class="step-number">5</div>
  <div class="content">Wählen Sie die <code>Schnittmethode</code> für die **räumliche Begrenzung**.</div>
</div>

<Tabs>
  <TabItem value="Map extent" label="Kartenausdehnung" default className="tabItemBox">
<div class="step">
  <div class="step-number">6</div>
  <div class="content">Layer wird **automatisch auf die aktuelle Kartenausdehnung zugeschnitten**. Um den Filter zu ändern, **zoomen Sie hinein/heraus** und aktualisieren Sie die Kartenausdehnung.</div>
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

**Kombinieren Sie mehrere Filter**, indem Sie die Schritte 3-7 für jeden Ausdruck wiederholen. In <code>Filter Ergebnisse</code> wählen Sie <code>Alle Filter erfüllen</code> (UND) oder <code>Mindestens einen Filter erfüllen</code> (ODER), um **zu steuern, wie Filter interagieren**.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/map/filter/filter-results.png').default} alt="Logic Operators" style={{ maxHeight: "300px", maxWidth: "300px", objectFit: "cover"}}/>
</div>
  
### Ausdrücke und Filter löschen

- **Einzelne Ausdrücke entfernen**: Klicken Sie auf das <code>Weitere Optionen</code> <img src={require('/img/map/filter/3dots_horizontal.png').default} alt="Options" style={{ maxHeight: "25px", maxWidth: "25px", objectFit: "cover"}}/> Menü neben dem Ausdruck, dann klicken Sie auf <code>Löschen</code>, um **den Ausdruck zu entfernen**.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/map/filter/filter_delete.png').default} alt="Delete" style={{ maxHeight: "300px", maxWidth: "300px", objectFit: "cover"}}/>
</div>

<p></p>
- **Gesamten Filter entfernen**: Klicken Sie auf <code>Filter löschen</code> am unteren Rand des Filtermenüs, um **alle Filter zu entfernen**.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>

  <img src={require('/img/map/filter/filter_clear.png').default} alt="Clear Filters" style={{ maxHeight: "300px", maxWidth: "300px", objectFit: "cover"}}/>

</div> 
