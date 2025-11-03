---
sidebar_position: 1
---

import thematicIcon from "/img/toolbox/data_management/join/toolbox.webp"
import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';



# Puffer

Der Puffer erstellt einen **Puffer um** angegebene **Punkte, Linien oder Polygone** mit einer festgelegten Pufferdistanz.

<iframe width="100%" height="500" src="https://www.youtube.com/embed/QSikKxqHeYw?si=lOqZGxxMrO3OL3Vi" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>

## 1. Erklärung

Ein **Puffer** ist ein Werkzeug, das verwendet wird, um das Einzugsgebiet um einen bestimmten Punkt, eine Linie oder ein Polygon zu definieren und das Ausmaß des Einflusses oder der Reichweite von diesem Punkt darzustellen. Benutzer können den ``Pufferabstand`` definieren und so den Radius des abgedeckten Bereichs anpassen.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>

  <img src={require('/img/toolbox/geoprocessing/buffer/buffer_types.png').default} alt="Buffer Types" style={{ maxHeight: "500px", maxWidth: "500px", objectFit: "cover"}}/>

</div> 

## 2. Anwendungsbeispiele 

- Wie viele Menschen leben innerhalb einer 500m Pufferdistanz vom Bahnhof? 
- Wie viele Geschäfte sind innerhalb einer 1000m Pufferdistanz von einer Bushaltestelle erreichbar?

## 3. Wie benutzt man das Werkzeug?

<div class="step">
  <div class="step-number">1</div>
  <div class="content">Klicken Sie auf <code>Werkzeuge</code> <img src={thematicIcon} alt="toolbox" style={{width: "25px"}}/>. </div>
</div>

<div class="step">
  <div class="step-number">2</div>
  <div class="content">Wählen Sie im Menü <code>Geoverarbeitung</code> das Werkzeug <code>Puffer</code> aus.</div>
</div>

<img src={require('/img/toolbox/geoprocessing/buffer/overview.png').default} alt="Buffer Tool in GOAT" style={{ maxHeight: "auto", maxWidth: "auto", objectFit: "cover"}}/>

### Puffer-Layer auswählen

<div class="step">
  <div class="step-number">3</div>
  <div class="content">Wählen Sie den <code>Puffer-Layer</code>, um welchen Sie einen Puffer erstellen möchten.</div>
</div>

### Puffer-Einstellungen

<div class="step">
  <div class="step-number">4</div>
  <div class="content">Definieren Sie über den Puffer-<code>abstand</code>, wie viele Meter sich der Puffer von Ihren Punkten, Linien oder Formen ausdehnen soll.</div>
</div>

<div class="step">
  <div class="step-number">5</div>
  <div class="content">Legen Sie fest, in wie viele <code>Pufferstufen</code> der Puffer unterteilt werden soll.</div>
</div>

:::tip Tipp
Abhängig davon, welche geometrischen Ergebnisse Sie anstreben, können Sie zuerst auswählen, ob alle Geometrien kombiniert werden sollen (**Vereinigen (Union)**). Dies bedeutet, wenn z.B. ein Puffer um benachbarte Punkte erstellt wird, ob Sie **einzelne Puffer** (**keine Vereinigung**) oder **kombinierte Puffer** (**Vereinigung**) als Ergebnis haben möchten.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>

  <img src={require('/img/toolbox/geoprocessing/buffer/no_union_vs_union.png').default} alt="Buffer Union-No union Comparison" style={{ maxHeight: "400px", maxWidth: "400px", objectFit: "cover"}}/>

</div> 

Zusätzlich, wenn Sie sich für eine Polygonvereinigung entscheiden, können Sie entscheiden, ob jeder Puffer als **gefülltes Polygon (ohne Unterschied)** angezeigt werden soll oder ob Sie einen **geometrischen Unterschied zwischen jeder Pufferstufe(Unterschied)** anwenden möchten.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>

  <img src={require('/img/toolbox/geoprocessing/buffer/union_vs_union+difference.png').default} alt="Buffer Union-Buffer Difference Comparison" style={{ maxHeight: "400px", maxWidth: "400px", objectFit: "cover"}}/>

</div> 

:::

<Tabs>
<TabItem value="nounion" label="Keine Vereinigung" default className="tabItemBox">

#### Keine Vereinigung
Wenn Sie einen Puffer **ohne Vereinigung** berechnen, erstellt GOAT einzelne Puffer um jede Eingabegeometrie.

<div class="step">
  <div class="step-number">6</div>
  <div class="content">Deaktivieren Sie <code>Vereinigen (Union)</code>.</div>
</div>

<div class="step">
  <div class="step-number">7</div>
  <div class="content">Drücken Sie auf <code>Ausführen</code>. Dies startet die Berechnung des Puffers.</div>
</div>

### Ergebnisse

<div class="step">
  <div class="step-number">8</div>
  <div class="content">Sobald diese Aufgabe abgeschlossen ist, wird der resultierende Layer namens <b>"Puffer"</b> Ihrer Karte hinzugefügt.</div>
</div>

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>

  <img src={require('/img/toolbox/geoprocessing/buffer/result_no_union.png').default} alt="No union Result in GOAT" style={{ maxHeight: "auto", maxWidth: "auto", objectFit: "cover"}}/>

</div> 

</TabItem>

  <TabItem value="polygonunion" label="Vereinigung" default className="tabItemBox">

#### Vereinigen (Union)
Das Werkzeug ``Vereinigen (Union)`` erstellt eine **geometrische Vereinigung** aller Schritte der Pufferpolygone. Sie **kombiniert** mehrere Polygone zu einem einzigen Polygon, das alle Bereiche der einzelnen Polygone umfasst, d.h. der Puffer mit der größten Ausdehnung schließt auch alle Pufferbereiche der kleineren Ausdehnung ein. Dieser Ansatz ist nützlich, wenn Sie die Gesamtfläche sehen möchten, die durch all Ihre Puffer-Schritte zusammen abgedeckt wird.

<div style={{ display: 'flex', flexDirection: 'column' }}>

  <img src={require('/img/toolbox/geoprocessing/buffer/polygon_union.png').default} alt="Polygon Union in GOAT" style={{ maxHeight: "auto", maxWidth: "auto", objectFit: "cover"}}/>

</div> 

<div class="step">
  <div class="step-number">6</div>
  <div class="content">Aktivieren Sie <code>Vereinigen (Union)</code>.</div>
</div>

<div class="step">
  <div class="step-number">7</div>
  <div class="content">Drücken Sie auf <code>Ausführen</code>. Dies startet die Berechnung des Puffers.</div>
</div>

### Ergebnisse

<div class="step">
  <div class="step-number">8</div>
  <div class="content">Sobald diese Aufgabe abgeschlossen ist, wird der resultierende Layer namens <b>"Puffer"</b> Ihrer Karte hinzugefügt.</div>
</div>

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>

  <img src={require('/img/toolbox/geoprocessing/buffer/result_union.png').default} alt="Polygon Union Result in GOAT" style={{ maxHeight: "auto", maxWidth: "auto", objectFit: "cover"}}/>

</div> 

  </TabItem>
  <TabItem value="polygondifference" label="Vereinigung + Unterschied " className="tabItemBox">

#### Vereinigen (Union) + Differenz zwischen Schritten
Die ``Differenz zwischen Schritten``-Operation erstellt einen **geometrischen Unterschied** der Puffer. Sie subtrahiert ein Polygon von einem anderen, was zu Polygonformen führt, bei denen sich die **Puffer nicht überlappen**.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>

  <img src={require('/img/toolbox/geoprocessing/buffer/polygon_difference.png').default} alt="Polygon Union+ Polygon Difference Result in GOAT" style={{ maxHeight: "auto", maxWidth: "auto", objectFit: "cover"}}/>

</div> 

<div class="step">
  <div class="step-number">6</div>
  <div class="content">Aktivieren Sie <code>Differenz zwischen Schritten</code>.</div>
</div>

<div class="step">
  <div class="step-number">7</div>
  <div class="content">Drücken Sie auf <code>Ausführen</code>. Dies startet die Berechnung des Puffers.</div>
</div>

### Ergebnisse

<div class="step">
  <div class="step-number">8</div>
  <div class="content">Sobald diese Aufgabe abgeschlossen ist, wird der resultierende Layer namens <b>"Puffer"</b> Ihrer Karte hinzugefügt.</div>
</div>

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>

  <img src={require('/img/toolbox/geoprocessing/buffer/result_union.png').default} alt="Polygon Difference Result in GOAT" style={{ maxHeight: "auto", maxWidth: "auto", objectFit: "cover"}}/>

</div> 

  </TabItem>


</Tabs>

:::tip TIPP

Möchten Sie Ihre Puffer bearbeiten und ansprechende Karten erstellen? Dies können Sie unter [Layer Design](../../map/layer_style/styling.md).

:::

