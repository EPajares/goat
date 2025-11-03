---
sidebar_position: 20
---

# Basic Styling

Wenn Sie einen neue Layer zu Ihrem Projekt hinzufügen, wird ihr ein Standardstil zugewiesen, welche je nach Datensatz unterschiedlich sein kann. Durch die Anpassung der Optionen im Menü <code>Layer Design<img src={require('/img/map/styling/styling_icon.webp').default} alt="Styling Icon" style={{ maxHeight: "15px", maxWidth: "15px", objectFit: "cover"}}/></code> können Sie die Darstellung des Layers anpassen und **ansprechende Karten** erstellen. Die verfügbaren Gestaltungsoptionen hängen von der Art der in einer Layer enthaltenen Daten ab, d. h. davon, ob es sich um Punkte, Linien oder Polygone handelt. Dabei können mehrere visuelle Aspekte wie **Farben**, **Striche** und **Optionen** angepasst werden.

<iframe width="100%" height="500" src="https://www.youtube.com/embed/RZej6OfSBOs?si=L30N4-S753Hu6cm-" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>

## Farbeinstellungen

### Füllfarbe

Die Füllfarbe wird verwendet, um das **Innere** von **Punkt- oder Polygon-Features** auf einer Karte darzustellen. Die Füllfarbe ist ein Aspekt der Kartographie und der GIS-Visualisierung, da sie zur besseren Lesbarkeit der Karte beiträgt. Der [Farbwähler](#farbwähler--voreingestellte-farben) bietet verschiedene Optionen, um die Farben Ihrer Wahl auszuwählen.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>

  <img src={require('/img/map/styling/fill_color.gif').default} alt="Fill-Stroke Color" style={{ maxHeight: "auto", maxWidth: "auto", objectFit: "cover"}}/>

</div> 

#### Deckkraft

Um die Deckkraft Ihrer Layerstile für die Füllfarbe anzupassen, ändern Sie die Deckkraft einfach auf einen beliebigen **Wert zwischen 0 und 1**. Mit dieser numerischen Skala können Sie genau den gewünschten Grad der Deckkraft festlegen, wobei **0 transparent** und **1 undurchsichtig** ist. Stellen Sie die Deckkraft nach Ihren Wünschen ein, indem Sie entweder den Schieberegler verwenden oder den genauen Wert direkt in das Textfeld eingeben.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>

  <img src={require('/img/map/styling/opacity.gif').default} alt="Opacity" style={{ maxHeight: "auto", maxWidth: "auto", objectFit: "cover"}}/>

</div> 


### Strichfarbe

Ähnlich wie die Füllfarbe kann auch die Strichfarbe eingestellt werden. Die Strichfarbe bezieht sich auf die Farbe, die auf die **Außenlinien oder Kanten** von Kartenmerkmalen wie Polygonen, Linien und Punkten angewendet wird. Sie wird verwendet, um die Kanten von räumlichen Elementen abzugrenzen, sie voneinander zu unterscheiden und ihre Sichtbarkeit auf der Karte zu verbessern. Der [Farbwähler](#farbwähler--voreingestellte-farben) bietet verschiedene Optionen, um die Farben Ihrer Wahl auszuwählen.


### Farbwähler & voreingestellte Farben

Wann immer Sie eine Farbe ändern möchten, sei es **Füllfarbe** oder **Strichfarbe**, öffnet sich das Farbmenü. Sie können die Farben entweder über den <code>Farbwähler</code> einstellen, indem Sie die Maus im Farbfeld **bewegen** oder **hex-Code** bzw. **RGB-Werte** definieren. Ansonsten können Sie eine der Farben auswählen, die wir unter <code>Voreingestellte Farben</code> bereitstellen.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>

  <img src={require('/img/map/styling/color_picker.gif').default} alt="Color Picker" style={{ maxHeight: "400px", maxWidth: "400px", objectFit: "cover"}}/>

</div> 

## Benutzerdefinierte Icons

Für Punktlayer können benutzerdefinierte Icons für die Visualisierung verwendet werden. Das Icon kann aus einer **Symbolbibliothek** ausgewählt oder ein **eigenes benutzerdefiniertes Icon hochgeladen** werden. Mit der **Suchleiste** finden Sie die benötigten Symbole schnell. Die Icongröße kann über den Schieberegler angepasst werden.  

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>

  <img src={require('/img/map/styling/custom_marker.gif').default} alt="Marker" style={{ maxHeight: "500px", maxWidth: "auto", objectFit: "cover"}}/>

</div> 

### Hochladen ein benutzerdefiniertes Icon

Nachdem Sie die Markerliste geöffnet haben, klicken Sie auf <code>Symbol hochladen</code>. Wählen Sie anschließend erneut <code>Symbol hochladen</code> und danach Ihre **jpeg-, png- oder svg-Datei**. Denken Sie beim Benennen Ihrer Datei daran, dass dieser Name später zur Suche nach dem Symbol verwendet wird.  

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>

  <img src={require('/img/map/styling/custom_marker_upload.png').default} alt="Marker" style={{ maxHeight: "600px", maxWidth: "auto", objectFit: "cover"}}/>

</div> 

Im Tab <code>Ikonen verwalten</code> können Sie Ihre hochgeladenen Symbole **umbenennen** und **löschen**.  

:::info

Nur die Symbole aus der Bibliothek können in der Farbe bearbeitet werden.  

:::


## Breite & Radius

### Strichbreite

Neben der Farbe kann auch die **Strichstärke** der Striche für **Linienlayern** definiert werden. Passen Sie die Strichstärke nach Ihren Wünschen an, indem Sie entweder den Schieberegler für die Strichstärke verwenden oder die genaue Größe direkt in das dafür vorgesehene Textfeld eingeben.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>

  <img src={require('/img/map/styling/stroke_width.png').default} alt="Stroke Width" style={{ maxHeight: "300px", maxWidth: "300px", objectFit: "cover"}}/>

</div> 


### Radius

Bei **Punktdatensätzen** kann der **Radius** angepasst werden. Daher können Sie entweder den Radius-Schieberegler verwenden, um schrittweise Änderungen vorzunehmen, oder die gewünschte Radiusgröße direkt in das Textfeld eingeben, um eine präzise Eingabe zu ermöglichen.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>

  <img src={require('/img/map/styling/radius.png').default} alt="Radius" style={{ maxHeight: "300px", maxWidth: "300px", objectFit: "cover"}}/>

</div> 


## Weitere Optionen

Durch Klicken auf die drei Punkte <img src={require('/img/map/filter/3dots.png').default} alt="Options" style={{ maxHeight: "25px", maxWidth: "25px", objectFit: "cover"}}/>,  öffnen sich weitere Einstellungen. 

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>

  <img src={require('/img/map/styling/default.png').default} alt="Default Settings" style={{ maxHeight: "300px", maxWidth: "300px", objectFit: "cover"}}/>

</div> 

Wenn Sie <code>Speichern als Standard</code> wählen, werden die aktuellen Stileinstellungen an den Datensatz angehängt. Wann immer Sie diesen Datensatz zu einem Projekt hinzufügen, wird dieser Standardstil verwendet (*Hinweis: bestehende Projekte, in denen dieser Datensatz angezeigt wird, sind davon nicht betroffen*). 

Wenn Sie auf <code>Zurücksetzen</code> klicken, können Sie die aktuellen Designeinstellungen des Layers im Projekt wieder auf die Standardwerte zurücksetzen. 


:::tip TIPP
Interessieren Sie sich für **Smart Styling** Optionen? Schauen Sie sich unser  [Attribute-based Styling](../layer_style/attribute_based_styling) an.
:::
