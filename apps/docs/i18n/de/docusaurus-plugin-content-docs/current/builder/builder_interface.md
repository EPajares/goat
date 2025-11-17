---
sidebar_position: 1
---


# Builder-Kartenoberfläche

**Der Wechsel in den Builder-Modus öffnet die Builder-Kartenoberfläche, in der Sie Dashboards gestalten können, indem Sie Panels und Widgets anordnen und Ihr Workspace-Layout anpassen.**

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
  <img src={require('/img/builder/builder_interface.png').default} alt="Builder Interface Overview in GOAT" style={{ maxHeight: "auto", maxWidth: "auto", objectFit: "cover"}}/>
</div>

--- 

## Panels

Panels sind die Hauptbereiche, in denen Sie Ihre Widgets organisieren. Sie können Panels hinzufügen, anordnen und stylen, um Ihr Dashboard-Layout zu erstellen.

<div class="step">
  <div class="step-number">1</div>
  <div class="content">Sie können auf die <code> + </code> Schaltfläche klicken, um ein neues Panel zu jeder Seite der Karte hinzuzufügen.</div>
</div>

<div class="step">
  <div class="step-number">2</div>
  <div class="content">Klicken Sie auf das <code> Panel </code>, um die Einstellungen zu öffnen und das Erscheinungsbild zu bearbeiten.</div>
</div>

<div class="step">
  <div class="step-number">3</div>
  <div class="content">Sie können auch auf den <code> Pfeil </code> an der Seite eines Panels klicken, um es auf volle Höhe/Breite zu erweitern.</div>
</div>


<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
  <img src={require('/img/builder/new_panel.gif').default} alt="Panel options and appearance" style={{ maxHeight: "auto", maxWidth: "400px", objectFit: "cover"}}/>
</div>


Sie können den Panel-Stil folgendermaßen einstellen:
- `Standard`: Widgets füllen das Panel mit kontinuierlichem Hintergrund
- `Abgerundet`: Widgets haben abgerundete Ecken und Rand-Abstand
- `Schwebend`: Widgets sind separat mit abgerundeten Ecken

Unter **Erscheinungsbild** können Sie ändern:
- `Deckkraft` (0 = transparent, 1 = weiß)
- `Hintergrund-Unschärfe` (1–20)
- `Schatten` (0–10)

Unter **Position** können Sie einstellen:
- `Ausrichtung`: Anfang, Mitte, Ende
- `Abstand`: 0–10 (Entfernung zwischen Widgets)

Um ein Panel zu löschen, klicken Sie unten in den Einstellungen auf `Löschen`. 


## Widgets

Widgets sind die Bausteine Ihres Dashboards. Sie ermöglichen es Ihnen, Daten, Statistiken, Diagramme und Projektelemente wie Text oder Bilder anzuzeigen. Jedes Widget ist hochgradig anpassbar: Sie können den Inhalt, das Erscheinungsbild und das Verhalten nach Ihren Bedürfnissen anpassen, egal ob Sie wichtige Kennzahlen hervorheben, Trends visualisieren oder Kontext mit Text und Grafiken hinzufügen möchten.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
  <img src={require('/img/builder/widgets.png').default} alt="Builder Interface Overview in GOAT" style={{ maxHeight: "auto", maxWidth: "auto", objectFit: "cover"}}/>
</div>

<div class="step">
  <div class="step-number">1</div>
  <div class="content">Ziehen Sie <code>Widgets</code> einfach per Drag & Drop aus der rechten Seitenleiste auf jedes Panel Ihres Dashboards.</div>
</div>

<div class="step">
  <div class="step-number">2</div>
  <div class="content">Klicken Sie auf das <code>Widget</code>, um dessen Einstellungen anzupassen.</div>
</div>

<div class="step">
  <div class="step-number">3</div>
  <div class="content">Um das Widget neu anzuordnen, können Sie darauf klicken und es am <code>gepunkteten Symbol</code> ziehen.</div>
</div>

<div class="step">
  <div class="step-number">4</div>
  <div class="content">Sie können auf das <code>Löschen-Symbol</code> klicken, um das Widget von Ihrem Dashboard zu entfernen.</div>
</div>

<div class="step">
  <div class="step-number">5</div>
  <div class="content">Ändern Sie den <code>Titel</code>, der oben im Widget erscheint, und die <code>Beschreibung</code>, die unten im Widget angezeigt wird.</div>
</div>

Weitere Details finden Sie unter [Widgets](builder/widgets/).

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/builder/widget_drag.gif').default} alt="recent datasets" style={{ maxHeight: "400px", maxWidth: "auto", objectFit: "cover"}}/>
</div>

## Einstellungen

In den Einstellungen können Sie **Werkzeuge**, **Bedienelemente** und **Ansichtsoptionen** für Ihr Dashboard aktivieren oder deaktivieren.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
  <img src={require('/img/builder/interface_settings.png').default} alt="Dragging a widget to the panel" style={{ maxHeight: "auto", maxWidth: "auto", objectFit: "cover"}}/>
</div>

Weitere Details finden Sie unter [Einstellungen](builder/settings.md).