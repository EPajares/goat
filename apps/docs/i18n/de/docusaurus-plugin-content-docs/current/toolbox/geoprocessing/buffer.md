---
sidebar_position: 1
---

import thematicIcon from "/img/toolbox/data_management/join/toolbox.webp"
import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';



# Puffer

Dieses Werkzeug ermöglicht es Ihnen, **Zonen um Punkte, Linien oder Polygone mit einem bestimmten Abstand zu erstellen**.

<iframe width="674" height="378" src="https://www.youtube.com/embed/Yboi3CwOLPM?si=FuSPRmK6zTB-GVJ1" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>

## 1. Erklärung

Ein Puffer ist ein Werkzeug, das verwendet wird, um **das Einzugsgebiet um einen bestimmten Punkt, eine Linie oder ein Polygon abzugrenzen und die Ausdehnung des Einflusses oder der Reichweite von diesem Feature zu veranschaulichen.** Benutzer können die ``Entfernung`` des Puffers definieren und damit den Radius des abgedeckten Bereichs anpassen.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>

  <img src={require('/img/toolbox/geoprocessing/buffer/buffer_types.png').default} alt="Puffer-Typen" style={{ maxHeight: "400px", maxWidth: "400px", objectFit: "cover"}}/>

</div> 

## 2. Beispiel-Anwendungsfälle

- Analyse der Bevölkerung innerhalb von 500m um Bahnstationen
- Zählung der Geschäfte, die innerhalb von 1000m von Bushaltestellen erreichbar sind


## 3. Wie wird das Werkzeug verwendet?


<div class="step">
  <div class="step-number">1</div>
  <div class="content">Klicken Sie auf <code>Werkzeugleiste</code> <img src={thematicIcon} alt="toolbox" style={{width: "25px"}}/>. </div>
</div>

<div class="step">
  <div class="step-number">2</div>
  <div class="content">Klicken Sie im Menü <code>Geoprozessierung</code> auf <code>Puffer</code>.</div>
</div>

### Layer zum Puffern auswählen

<div class="step">
  <div class="step-number">3</div>
  <div class="content">Wählen Sie den <code>Layer zum Puffern</code>, um den Sie den Puffer erstellen möchten.</div>
</div>

### Puffer-Einstellungen

<div class="step">
  <div class="step-number">4</div>
  <div class="content">Definieren Sie über die <code>Puffer-Entfernung</code>: wie viele Meter von Ihren Punkten, Linien oder Formen der Puffer erstrecken soll.</div>
</div>

<div class="step">
  <div class="step-number">5</div>
  <div class="content">Definieren Sie in wie viele <code>Puffer-Schritte</code> der Puffer unterteilt werden soll.</div>
</div>

<div class="step">
  <div class="step-number">6</div>
  <div class="content">Wenn Sie die <code>Polygon-Vereinigung</code> deaktiviert lassen, generiert GOAT einzelne Puffer um jede Eingabegeometrie. Wenn Sie sie aktivieren, erstellt GOAT eine **geometrische Vereinigung** aller Schritte der Puffer-Polygone. In diesem Fall umfasst der Puffer mit der größten Ausdehnung auch alle Pufferbereiche der kleineren Ausdehnung. Dieser Ansatz ist nützlich, wenn Sie die Gesamtfläche sehen möchten, die von allen Ihren Pufferschritten zusammen abgedeckt wird.</div>
</div>

<div class="step">
  <div class="step-number">7</div>
  <div class="content">Wenn Sie die Polygon-Vereinigung aktiviert haben, können Sie die `Polygon-Differenz` aktivieren. GOAT erstellt eine **geometrische Differenz** der Puffer. Es subtrahiert ein Polygon von einem anderen, was zu Polygonformen führt, bei denen sich die **Puffer nicht überlappen**.</div>
</div>

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>

  <img src={require('/img/toolbox/geoprocessing/buffer/polygon_union_difference.png').default} alt="Polygon-Vereinigung + Polygon-Differenz Ergebnis in GOAT" style={{ maxHeight: "auto", maxWidth: "auto", objectFit: "cover"}}/>

</div> 
<div class="step">
  <div class="step-number">8</div>
  <div class="content">Klicken Sie auf <code>Ausführen</code>. Dies startet die Berechnung des Puffers.</div>
</div>

### Ergebnisse

Sobald diese Aufgabe abgeschlossen ist, wird der resultierende Layer namens **"Puffer"** zu Ihrer Karte hinzugefügt.

:::tip Tipp

Möchten Sie Ihre Puffer stylen und schön aussehende Karten erstellen? Siehe [Styling](../../map/layer_style/styling).

:::