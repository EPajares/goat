---
sidebar_position: 1
---


# Builder-Benutzeroberfläche

Der Wechsel vom Daten-Modus in den Builder-Modus führt Sie zu einer Kartenoberfläche, in der Sie **Dashboards erstellen können, indem Sie Widgets zu Panels hinzufügen, Filter anwenden und das Layout anpassen.**

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
  <img src={require('/img/builder/builder_switch.gif').default} alt="switching_to_builder_mode" style={{ maxHeight: "auto", maxWidth: "auto", objectFit: "cover"}}/>
</div> 

## Oberflächenelemente

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
  <img src={require('/img/builder/builder_interface.png').default} alt="overview_of_the_builder_interface" style={{ maxHeight: "auto", maxWidth: "auto", objectFit: "cover"}}/>
</div> 

### Panels

Um ein Widget zu Ihrem Dashboard hinzuzufügen, benötigen Sie zunächst **Panels**, auf deren Bereich Sie Ihre Widgets anordnen können. Das linke Panel wird automatisch angezeigt, wenn Sie in den Builder-Modus wechseln.

<div> </div>

Sie können neue Panels zu jeder Seite der Karte hinzufügen, indem Sie auf die <code>+</code>-Schaltfläche klicken.
Sie können die Panels weiter anordnen, indem Sie auf die <code>&lt;</code> <code>&gt;</code>-Schaltflächen an den Seiten des Panels klicken, wodurch das **Panel auf die volle Höhe oder Breite der Karte erweitert** wird, je nachdem, wo sich das Panel befindet.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
  <img src={require('/img/builder/new_panel.gif').default} alt="Dragging a widget to the panel" style={{ maxHeight: "auto", maxWidth: "auto", objectFit: "cover"}}/>
</div> 

<div> </div>

 Durch *Klicken auf das Panel selbst* öffnen sich die **Panel-Einstellungen**. Sie können die Panels jederzeit **mit oder ohne Widgets bearbeiten**. Für eine bessere Visualisierung empfehlen wir, mindestens ein [Widget](/builder/builder_interface.md#widgets) im Panel zu haben, wenn Sie dessen Aussehen bearbeiten.

<div> </div>

Sie können den **Panel-Stil** folgendermaßen einstellen:
- **Standard**, zeigt die Widgets mit einem *kontinuierlichen Hintergrund an und füllt das Panel vollständig aus*
- **Abgerundet**, *hält die Widgets ebenfalls auf dem kontinuierlichen Hintergrund zusammen, aber mit abgerundeten Ecken und lässt etwas Platz am Panel-Rand*
- **Schwebend**, zeigt die *Widgets separat mit abgerundeten Ecken für jedes Element*

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
  <img src={require('/img/builder/panel_options.gif').default} alt="Dragging a widget to the panel" style={{ maxHeight: "auto", maxWidth: "400px", objectFit: "cover"}}/>
</div> 

Unter **Erscheinungsbild** können Sie Folgendes ändern:
- **Deckkraft**, wobei 0 vollständig transparent und 1 vollständig weiß ist
- **Hintergrund-Unschärfe**, die von 1 bis 20 reicht
- **Schatten**, der von 0 bis 10 reicht

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
  <img src={require('/img/builder/panel_appearance.gif').default} alt="Dragging a widget to the panel" style={{ maxHeight: "auto", maxWidth: "400px", objectFit: "cover"}}/>
</div> 

In der **Position** können Sie Folgendes festlegen:
- **Ausrichtung** am *Anfang*, in der *Mitte* oder am *Ende* des Panels
- **Abstand**, der von 0 bis 10 reicht. Dies ändert den Abstand zwischen den Widgets

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
  <img src={require('/img/builder/panel_position.gif').default} alt="Dragging a widget to the panel" style={{ maxHeight: "auto", maxWidth: "400px", objectFit: "cover"}}/>
</div> 


<div></div>
Unten können Sie das Panel mit <code>Löschen</code> vollständig entfernen, wodurch auch die enthaltenen Widgets entfernt werden. 


### Widgets

Die Widgets sind die Bausteine Ihres Dashboards. Sie können sie aus der rechten Seitenleiste **per Drag & Drop** auf jedes Panel ziehen. Sie können auch **das gewählte Widget aus der rechten Seitenleiste auf jedes Panel ziehen**, **neu anordnen**, **entfernen** oder **bearbeiten** - und das jederzeit. Lesen Sie mehr über die verschiedenen Widget-Typen und deren Verwendung im Widgets-Abschnitt.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
  <img src={require('/img/builder/widget_drag.gif').default} alt="Dragging a widget to the panel" style={{ maxHeight: "auto", maxWidth: "auto", objectFit: "cover"}}/>
</div> 

<div></div>

### Einstellungen

In den Einstellungen können Sie **Tools, Bedienelemente und die Ansichtsoptionen aktivieren oder deaktivieren.**
Schauen Sie sich den Abschnitt [Einstellungen](builder/settings.md) für eine detailliertere Erklärung an.