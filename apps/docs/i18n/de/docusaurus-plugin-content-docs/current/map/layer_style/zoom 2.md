---
sidebar_position: 1
---
import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';


# Sichtbarkeit Zoomen

Mit der Zoom-Sichtbarkeitsleiste können Sie den Zoom-Bereich einstellen, in dem jeder Layer auf der Karte erscheint. Dies hilft Ihnen, die **relevantesten Daten auf verschiedenen Zoom-Leveln anzuzeigen**: zum Beispiel detaillierte Informationen bei der Vergrößerung.

::::info
Standardmäßig sind alle Layer im Bereich von 1-22 Zoom-Level sichtbar, sofern dies nicht geändert wird.
::::

Der Bereich reicht von **Weltansicht (0) bis Straßenebenen-Detail (22)**, und das aktuelle Zoom-Level wird auf der Skala angezeigt.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>

  <img src={require('/img/map/styling/zoom_scale.png').default} alt="zoom scale" style={{ maxHeight: "auto", maxWidth: "auto", objectFit: "cover"}}/>

</div> 

<br></br>

Sie können die Zoom-Level **manuell** eingeben oder sie direkt **auf der Skala anpassen**.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
  <img src={require('/img/map/styling/zoom_adjust.gif').default} alt="Color Picker" style={{ maxHeight: "400px", maxWidth: "400px", objectFit: "cover"}}/>
</div> 

## Tipps

- Layer mit *vielen Details* (z. B. Gebäude oder POIs) sind oft besser bei **höheren Zoom-Leveln** zu sehen.
- **Engere Zoom-Bereiche** helfen, dichte Layer übersichtlich zu halten.
- Für *Hintergrund- oder Kontext-Layer* ist ein **breiterer Bereich** in der Regel am besten.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>

  <img src={require('/img/map/styling/zooming_out.gif').default} alt="zoom scale screen" style={{ maxHeight: "auto", maxWidth: "auto", objectFit: "cover"}}/>

</div> 