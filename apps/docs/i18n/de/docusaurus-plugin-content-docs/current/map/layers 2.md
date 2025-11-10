---
sidebar_position: 3
---


import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';


# Layer

Im Bereich **Layer** können Layer **hinzugefügt und organisiert** werden. Unter anderem kann die Reihenfolge der Layer angepasst werden, Layer können angezeigt/ausgeblendet, dupliziert, umbenannt, heruntergeladen und entfernt werden.

<iframe width="100%" height="500" src="https://www.youtube.com/embed/c_EoWW7HJVU?si=PBahX_5OTRpT5pjq" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/map/layers/overview.png').default} alt="Layer View in GOAT" style={{ maxHeight: "auto", maxWidth: "auto", objectFit: "cover"}}/>
</div> 

## Layer hinzufügen

Sie können Ebenen aus [verschiedenen Quellen](../data/dataset_types) zu Ihrer Karte hinzufügen. Sie können entweder **Datensätze aus Ihrem Datenexplorer oder dem Katalogexplorer** integrieren oder neue **Datensätze von Ihrem lokalen Gerät** hochladen (GeoPackage, GeoJSON, Shapefile, KML, CSV oder XLSX). Externe Ebenen können durch Einfügen der **Url der externen Quelle** (WMS, WMTS oder MVT) hinzugefügt werden.

Führen Sie die folgenden Schritte aus, um der Karte eine Layer hinzuzufügen: 

<div class="step">
  <div class="step-number">1</div>
  <div class="content">Navigieren Sie über die linke Seitenleiste zum Menü <b>"Layer"</b>.</div>
</div>

<div class="step">
  <div class="step-number">2</div>
  <div class="content">Klicken Sie auf <code>+ Layer hinzufügen</code>. </div>
</div>

<div class="step">
  <div class="step-number">3</div>
  <div class="content">Wählen Sie aus, ob Sie einen Datensatz aus Ihrem  <b>Datenexplorer</b> einbinden möchten,  <b>einen neuen Datensatz hochladen</b> oder einen <b>externen Datensatz</b> hinzufügen möchten.</div>
</div>

<Tabs>
  <TabItem value="Dataset Explorer" label="Datensatz-Explorer" default className="tabItemBox">


<div class="step">
  <div class="step-number">4</div>
  <div class="content">Wählen Sie die Datei aus, die Sie importieren möchten.</div>
</div>

<div class="step">
  <div class="step-number">5</div>
  <div class="content">Klicken Sie auf <code>+ Layer hinzufügen</code>.</div>
</div>


</TabItem>
<TabItem value="Dataset Upload" label="Datensatz-Upload" className="tabItemBox">


<div class="step">
  <div class="step-number">4</div>
  <div class="content">Wählen Sie die Datei aus, die Sie importieren möchten.</div>
</div>

<div class="step">
  <div class="step-number">5</div>
  <div class="content">Bestimmen Sie den Namen des Datensatzes und fügen Sie ggf. eine Beschreibung hinzu.</div>
</div>

<div class="step">
  <div class="step-number">6</div>
  <div class="content">Kontrollieren Sie die Informationen und klicken Sie auf <code>Hochladen</code>.</div>
</div>

  </TabItem>
  <TabItem value="Dataset External" label="Katalog-Explorer" className="tabItemBox">

:::info demnächst verfügbar

Wir implementieren derzeit diese Funktion.  🧑🏻‍💻

:::


  </TabItem>
</Tabs>

:::tip Tipp

 Sie können alle Ihre Datasets auf der Seite [Datensätze-Seite](../workspace/datasets) verwalten. 

:::

## Organisieren von Layern

Sobald Sie einen Datensatz zur Karte hinzugefügt haben, wird er in der **Layerliste** angezeigt. Von dort aus können Sie die verschiedenen Layer organisieren.

### Layer-Reihenfolge

Wenn Sie mehrere Datensätze auf einmal visualisieren, ist die Reihenfolge der Layer entscheidend für die Erstellung guter Karten. Daher kann die **Layerreihenfolge** interaktiv geändert werden.
Wenn Sie mit der Maus über den linken Rand der Layer in der Layer-Liste fahren, erscheint ein Pfeilsymbol. Durch Ziehen und Ablegen können Layer verschoben und neu angeordnet werden. 

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
  <img src={require('/img/map/layers/layer_order.gif').default} alt="Layer Order" style={{ maxHeight: "600px", maxWidth: "600px", objectFit: "cover"}}/>
</div> 

### Layer anzeigen/ausblenden

Um einen Layer vorübergehend aus der Kartenansicht **auszublenden**, klicken Sie in der Layer-Liste auf das Augensymbol des betreffenden Layers. Wenn Sie erneut auf das Auge klicken, wird der Layer wieder **sichtbar**.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
  <img src={require('/img/map/layers/hide_layers.gif').default} alt="Hide Layer" style={{ maxHeight: "600px", maxWidth: "600px", objectFit: "cover"}}/>
</div> 

### Weitere Optionen

Durch Klicken auf die drei Punkte <img src={require('/img/map/filter/3dots.png').default} alt="Options" style={{ maxHeight: "25px", maxWidth: "25px", objectFit: "cover"}}/> erhalten Sie weitere Optionen zur Verwaltung und Organisation des ausgewählten Layers.


<img src={require('/img/map/layers/layer_options.png').default} alt="Layer Options" style={{ maxHeight: "250px", maxWidth: "250px", objectFit: "cover"}}/> 


:::tip Tipp

Möchten Sie das Design Ihres Layers ändern? Siehe [Layer Design](../category/layer-styling).  
Möchten Sie nur Teile Ihres Datensatzes visualisieren? Siehe [Filtern](../map/filter). 

:::