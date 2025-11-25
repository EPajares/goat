---
sidebar_position: 3
---

import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';

# Schnellstartanleitung
Willkommen bei GOAT! Diese Schnellstartanleitung hilft Ihnen dabei, schnell mit GOAT zu beginnen. Folgen Sie diesen einfachen Schritten, um den Workspace zu erkunden und Ihre erste Analyse und interaktive Karte zu erstellen.

<div style={{ display: 'flex', justifyContent: 'center' }}>
<iframe width="674" height="378" src="https://www.youtube.com/embed/oYdsVw0slLc?si=tpjSR3xi-r0dZ1cU&amp;start=46" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>
</div>

## Neues Projekt erstellen

<div class="step">
  <div class="step-number">1</div>
  <div class="content">Nach der Anmeldung landen Sie auf der <code>Workspace</code>-Seite. Klicken Sie auf die <code>+</code>-Schaltfläche, um ein neues Projekt zu erstellen.</div>
</div>

<div class="step">
  <div class="step-number">2</div>
  <div class="content">Wählen Sie einen <b>Folder location</b>, füllen Sie das Feld <b>project name</b> und <b>description</b> aus und klicken Sie auf die <code>Erstellen</code>-Schaltfläche.</div>
</div>

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/getting_started/new_project.gif').default} alt="Workspace bei GOAT" style={{ maxHeight: "auto", maxWidth: "75%", objectFit: "cover"}}/>
</div>

## Daten zu Ihrem Projekt hinzufügen
Sie sind in der Kartenansicht Ihres neuen Projekts gelandet. Jetzt ist es Zeit, einige Daten hinzuzufügen.

<div class="step">
  <div class="step-number">3</div>
  <div class="content">Klicken Sie auf <code>+ Layer hinzufügen</code> unten links im linken Panel.</div>
</div>

<div class="step">
  <div class="step-number">4</div>
  <div class="content">Wählen Sie aus, ob Sie einen Datensatz aus Ihrem <b>data explorer</b> integrieren, einen neuen Datensatz <b>upload</b>, den <b>catalog explorer</b> durchsuchen oder einen Datensatz über einen <b>external link</b> hinzufügen möchten.</div>
</div>

<Tabs>
    <TabItem value="Dataset Explorer" label="Datensatz-Explorer" default className="tabItemBox">
<div class="step">
    <div class="step-number">5</div>
    <div class="content">Wählen Sie die Datei aus, die Sie importieren möchten.</div>
</div>
<div class="step">
    <div class="step-number">6</div>
    <div class="content">Klicken Sie auf <code>+ Layer hinzufügen</code>.</div>
</div>
    </TabItem>

<TabItem value="Dataset Upload" label="Datensatz-Upload" className="tabItemBox">
<div class="step">
  <div class="step-number">5</div>
  <div class="content">Wählen Sie die Datei aus, die Sie importieren möchten.</div>
</div>
<div class="step">
  <div class="step-number">6</div>
  <div class="content">Definieren Sie den Namen des Datensatzes, die Beschreibung und klicken Sie auf <code>Hochladen</code>.</div>
</div>
</TabItem>
  
<TabItem value="Catalog Explorer" label="Katalog-Explorer" className="tabItemBox">
<div class="step">
  <div class="step-number">5</div>
  <div class="content">Durchsuchen Sie den GOAT-Datensatz-Katalog.</div>
</div>
<div class="step">
  <div class="step-number">6</div>
  <div class="content">Wählen Sie den Datensatz aus, den Sie importieren möchten, und klicken Sie auf <code>+ Layer hinzufügen</code>.</div>
</div>
</TabItem>

<TabItem value="Dataset External" label="Externer Datensatz" default className="tabItemBox">
<div class="step">
  <div class="step-number">5</div>
  <div class="content">Geben Sie Ihre externe URL ein und folgen Sie den Schritten <b>depending on the type of dataset</b>, den Sie hinzufügen möchten.</div>
</div>
<Tabs>
<TabItem value="WFS" label="WFS" default className="tabItemBox">
<div class="step">
    <div class="content"> <p>Wenn Sie einen WFS-Layer hinzufügen möchten, benötigen Sie einen <b>"GetCapabilities"</b>-Link. </p>
    Im nächsten Schritt können Sie wählen, welchen Layer Sie zu Ihrem Datensatz hinzufügen möchten. <i>Sie können nur einen Layer gleichzeitig auswählen.</i></div>
</div>
</TabItem>

<TabItem value="WMS" label="WMS" className="tabItemBox">
<div class="step">
    <div class="content"> <p>Wenn Sie einen WMS-Layer hinzufügen möchten, benötigen Sie einen <b>"GetCapabilities"</b>-Link.</p> Hier haben Sie die Möglichkeit, mehrere Layer auszuwählen, aber wenn sie zu GOAT hinzugefügt werden, <i>werden sie zu einem Layer zusammengeführt.</i> </div>
</div>
</TabItem>

<TabItem value="WMTS" label="WMTS" className="tabItemBox">
<div class="step">
    <div class="content"> <p>Sie können einen WMTS zu Ihrem Datensatz über eine <b>direkte URL</b> oder einen <b>"GetCapabilities"</b>-Link hinzufügen. Sie können nur <i>einen Layer</i> gleichzeitig auswählen, wenn Ihre URL mehr als einen Layer enthält.</p>
    Die Projektion muss <i>WEB Mercator (EPSG:3857) und GoogleMaps-kompatibel</i> sein. Da sie unterschiedliche Zoom-Level haben, würde der Datensatz nicht in der Liste der verfügbaren Layer angezeigt, wenn er nicht beide Anforderungen erfüllt.</div>
</div>
</TabItem>

</Tabs>
</TabItem>
</Tabs>

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/getting_started/add_data.png').default} alt="Workspace bei GOAT" style={{ maxHeight: "auto", maxWidth: "auto", objectFit: "cover"}}/>
</div>

## Analysewerkzeuge erkunden
Je nach den Layern, die Sie hinzugefügt haben, können Sie verschiedene Analysen aus der Werkzeugkiste ausführen.
<div class="step">
  <div class="step-number">7</div>
  <div class="content"> Klicken Sie auf die <code>Werkzeuge</code>-Schaltfläche im rechten Panel.</div>
</div>

<div class="step">
  <div class="step-number">8</div>
  <div class="content"> Wählen Sie das Analysewerkzeug aus, das Sie verwenden möchten. Sie können zwischen unseren <b> Accessibility indicators</b>, <b>Data management</b>, <b>Geoanalysis</b> oder <b>Geoprocessing</b>-Werkzeugen wählen und die Einstellungen vervollständigen.</div>
</div>

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/getting_started/toolbox.png').default} alt="Workspace bei GOAT" style={{ maxHeight: "auto", maxWidth: "auto", objectFit: "cover"}}/>
</div>

## Ihre Karte gestalten
Sobald Sie die Layer zu Ihrer Karte hinzugefügt und die Analyse berechnet haben, können Sie deren Erscheinungsbild anpassen, um die Visualisierung zu verbessern.

<div class="step">
  <div class="step-number">9</div>
  <div class="content">Klicken Sie auf <code>Layer Design <img src={require('/img/map/styling/styling_icon.webp').default} alt="Styling Icon" style={{ maxHeight: "15px", maxWidth: "21px", objectFit: "cover"}}/></code>, öffnen Sie das <code>Stil</code>-Menü, wählen Sie die gewünschte Farbe aus, oder wenn Sie nach Attribut gestalten möchten, klicken Sie auf <code>Optionen <img src={require('/img/map/styling/options_icon.png').default} alt="Options Icon" style={{ maxHeight: "15px", maxWidth: "15px", objectFit: "cover"}}/></code> und setzen Sie das gewünschte Feld im <code>Farbe basierend auf</code>-Menü.</div>
</div>

<div class="step">
  <div class="step-number">10</div>
  <div class="content">Sie können den <code>Stil</code> weiter einstellen, indem Sie die <b>color palette</b>, die <b>Stroke Color</b> wählen oder einen <b>Custom Marker</b> auswählen, wenn Sie mit einem Punkt-Layer arbeiten.</div>
</div>

<div class="step">
  <div class="step-number">11</div>
  <div class="content">Dann können Sie die <code>Beschriftungen</code> einschalten, wenn Sie möchten, und Ihre <code>Popups</code> und <code>Legende</code> bearbeiten.</div>
</div>

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/getting_started/layer_design.png').default} alt="Workspace bei GOAT" style={{ maxHeight: "auto", maxWidth: "auto", objectFit: "cover"}}/>
</div>

## Bereit, Ihre Arbeit zu teilen
Nachdem Sie Ihr erstes Projekt in GOAT erstellt haben, ist es Zeit, es mit anderen zu teilen. Sie können Ihr Projekt einfach teilen, indem Sie einen teilbaren Link generieren oder Mitarbeiter einladen, mit Ihnen am Projekt zu arbeiten.

<div class="step">
  <div class="step-number">12</div>
  <div class="content">Klicken Sie auf <code>Teilen</code> in der oberen rechten Ecke der Karte.</div>
</div>

<div class="step">
  <div class="step-number">13</div>
  <div class="content">Gehen Sie zum <code>Öffentlich</code>-Schalter und klicken Sie auf <code>Veröffentlichen</code>, um Ihre Karte öffentlich zu machen.</div>
</div>

<div class="step">
  <div class="step-number">14</div>
  <div class="content">Jetzt können Sie auf <code>URL kopieren</code> klicken und <b>den direkten Link teilen</b>, damit andere die Karte in ihrem Browser öffnen können. Oder klicken Sie auf <code>iframe-Code kopieren</code> und <b>betten Sie die Karte</b> in Websites oder <b>Werkzeuge</b> ein, die HTML und iframes unterstützen.</div>
</div>

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/getting_started/share.gif').default} alt="Workspace bei GOAT" style={{ maxHeight: "auto", maxWidth: "75%", objectFit: "cover"}}/>
</div>