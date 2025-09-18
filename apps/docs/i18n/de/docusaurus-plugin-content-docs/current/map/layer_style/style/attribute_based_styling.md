---
sidebar_position: 21
---

# Attribut-basiertes Styling

GOAT unterstützt **attributbasiertes Styling**, um die Visualisierung von Daten auf Karten zu verbessern. Dieser Ansatz erlaubt es der visuellen Darstellung, Variationen und Muster in den Daten widerzuspiegeln, wodurch es einfacher wird, komplexe räumliche Informationen zu verstehen.

Im Menü unter<code>Layer Design <img src={require('/img/map/styling/styling_icon.webp').default} alt="Styling Icon" style={{ maxHeight: "15px", maxWidth: "21px", objectFit: "cover"}}/></code> sind Styling-Optionen für die ausgewählten Layer zu finden. Jeder Aspekt der Visualisierung eines Layers (<i>Füllfarbe</i>, <i>Strichfarbe</i>, <i>Benutzerdefinierte Icon</i> und <i>Beschriftungen</i>) kann individuell entsprechend einem Feld oder Attribut in den Daten des Layers gestaltet wserden. Um das attributbasierte Styling für einen Layer zu aktivieren Klicken Sie auf <b>Erweiterte Einstellungen</b> <code><img src={require('/img/map/styling/options_icon.png').default} alt="Options Icon" style={{ maxHeight: "15px", maxWidth: "15px", objectFit: "cover"}}/></code>.


:::tip TIPP
Wenn Sie Ihre Styling-Einstellungen speichern und in weiteren Projekten verwenden möchten, können Sie dies durch [Speichern als Standard](../layer_style/styling/#default-settings) tun. 
:::

## Attribut auswählen 

Um einen Stil basierend auf einem Attribut zu erstellen, wählen Sie es aus dem Dropdown-Menü des Feldes <code>Farbe basierend auf</code> aus. Daraufhin werden alle Attribute oder Spalten aufgelistet, die in den Daten Ihres Layers verfügbar sind.

Die Visualisierung wird dann automatisch entsprechend dem Wertebereich der Daten gestaltet. Eine <code>Farbpalette</code> und eine <code>Farbskala</code> sind standardmäßig zugewiesen, können aber angepasst werden, um Ihren Daten und Visualisierungsanforderungen besser zu entsprechen. Die *Farbskala* verwendet eine [**Datenklassifizierungsmethode**](#datenklassifizierungsmethoden), um zu bestimmen, wie Datenwerte verschiedenen Farbkategorien zugewiesen werden.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>

  <img src={require('/img/map/styling/attribute_selection.gif').default} alt="Attribute Selection" style={{ maxHeight: "auto", maxWidth: "auto", objectFit: "cover"}}/>

</div> 

## Farbpalette

In diesem Abschnitt finden Sie GOATs umfassende Paletten, die alle für eine **visuell eindrucksvolle räumliche Datendarstellung** entwickelt wurden. Eine Palette ist eine Sammlung von Farben, die ausgewählt wurden, um die Skala der Werte oder Kategorien in den Daten Ihrer Layer darzustellen.
 
  Für weitere Anpassungen können Sie einen anderen <code>Typ</code> der Palette, eine andere Anzahl von <code>Schritten</code> oder <code>Umgekehrt</code> der Farbreihenfolge wählen. Sie können auch eine benutzerdefinierte Farbpalette definieren, indem Sie die <code>Benutzerdefiniert</code>-Schaltfläche aktivieren.
 
 GOAT bietet einen umfassenden Satz an vordefinierten Paletten, die in vier verschiedene *Palettentypen* unterteilt sind, um die Auswahl und Anwendung zu erleichtern.

<p></p>

| Palettentyp | Beispiel | Beschreibung |
| :-: | --- | ---|
| Divergierend | <img src={require('/img/map/styling/diverging_palette.png').default} alt="diverging" style={{ maxHeight: "auto", maxWidth: "auto", objectFit: "cover"}}/> | Diese Art von Farbpalette ist ideal für die Darstellung von Daten, die um einen kritischen Mittelpunkt zentriert sind oder eine natürliche Teilung aufweisen. Sie eignet sich besonders für die Darstellung von Daten, die sowohl positive als auch negative Abweichungen von einem zentralen Wert aufweisen, so dass diese Abweichungen klar und effektiv visualisiert werden können. |
| Sequentiell | <img src={require('/img/map/styling/sequential_palette.png').default} alt="sequential" style={{ maxHeight: "auto", maxWidth: "auto", objectFit: "cover"}}/> | Diese Farbpalette ist für Daten gedacht, die einem natürlichen Verlauf oder einer geordneten Abfolge folgen. Sie eignet sich hervorragend zur Visualisierung von kontinuierlichen Daten, bei denen die Werte entlang eines Spektrums entweder schrittweise ansteigen oder abfallen. Sie eignet sich daher besonders für die klare Darstellung von Daten, die sich allmählich von einem Extrem zum anderen verändern. |
| Qualitativ | <img src={require('/img/map/styling/qualitative_palette.png').default} alt="qualitative" style={{ maxHeight: "auto", maxWidth: "auto", objectFit: "cover"}}/> | Diese Farbpalette ist für Daten gedacht, die in bestimmte, eindeutige Gruppen oder Klassen eingeteilt sind. Qualitative Farbpaletten sind so konzipiert, dass sie zwischen einzelnen Kategorien unterscheiden. Wichtig ist, dass diese Paletten dies tun, ohne eine inhärente Ordnung oder relative Bedeutung zwischen den verschiedenen Kategorien zu suggerieren. |
| Einzelner Farbton| <img src={require('/img/map/styling/singlehue_palette.png').default} alt="singlehue" style={{ maxHeight: "auto", maxWidth: "auto", objectFit: "cover"}}/> | Bei dieser Farbpalette handelt es sich um ein Farbschema, das in der Datenvisualisierung verwendet wird und verschiedene Farbtöne, Schattierungen und Nuancen einer einzigen Farbe verwendet. Dieser Ansatz schafft eine visuell kohärente und harmonische Ästhetik, die besonders effektiv sein kann, um Informationen ohne die Ablenkung durch mehrere Farben zu vermitteln. |


<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>

  <img src={require('/img/map/styling/color_palettes.gif').default} alt="Color Palettes" style={{ maxHeight: "auto", maxWidth: "auto", objectFit: "cover"}}/>

</div> 

## Farbskala

Unter <code>Palette</code> finden Sie die **Farbe basierend auf** und die **Farbskala**, die Datenwerte mit einem Farbspektrum verbindet. Sie wandelt einen gegebenen Datenwert innerhalb eines gegebenen Bereichs in eine entsprechende Farbe aus einem gegebenen Farbspektrum um. GOAT bietet sechs vordefinierte **Datenklassifizierungsmethoden**: [Quantil](#quantil), [Standardabweichung](#standardabweichung), [Gleiches Intervall](#gleiches-intervall), [Heads und Tails](#heads-und-tails), [Benutzerdefinierte Schritte](#benutzerdefinierte-schritte-für-zahlen), und [Benutzerdefinierte Ordinalskala](#benutzerdefinierte-ordinalskala-für-zeichen).

## Datenklassifizierungsmethoden

### Quantil

Die Quantil-Klassifizierung unterteilt Daten in **Gruppen mit einer gleichen Anzahl von Werten in jeder Klasse**, basierend auf ihren Attributwerten. Diese Methode ist nützlich für die Analyse und Visualisierung von Mustern in Daten und kann dabei helfen, Trends und Muster zu erkennen, die vielleicht nicht so leicht zu erkennen sind. Die Tatsache, dass die Datenwerte in jeder Klasse in gleichen Mengen gruppiert werden, macht diesen Ansatz **ideal für Daten, die linear verteilt sind**. Standardmäßig werden die Daten in 7 Klassen aufgeteilt. 

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>

  <img src={require('/img/map/styling/quantile.png').default} alt="Quantile" style={{ maxHeight: "auto", maxWidth: "auto", objectFit: "cover"}}/>

</div>  


:::tip TIPP
Möchten Sie besser verstehen, was eine Quantilklassifizierung ist? Schauen Sie in unser [Glossar](../../further_reading/glossary/#quantile-classification).
:::

### Standardabweichung

Die Methode der Standardabweichung ist ein **statistischer Ansatz**, der in der Datenvisualisierung verwendet wird. Sie verwendet das Konzept der Standardabweichung, ein Maß für das **Ausmaß der Variation oder Streuung in einer Gruppe von Werten**, um zu bestimmen, wie Datenpunkte verschiedenen Farbkategorien zugeordnet werden. Diese Methode ist wertvoll, da sie eine statistische Perspektive auf die Daten bietet und es den Benutzern ermöglicht, die **relative Streuung und Verteilung der Werte** innerhalb des Datensatzes schnell zu erfassen. Standardmäßig werden die Daten in 7 Klassen aufgeteilt. 

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>

  <img src={require('/img/map/styling/standard_deviation.png').default} alt="Standard Deviation" style={{ maxHeight: "auto", maxWidth: "auto", objectFit: "cover"}}/>

</div> 

### Gleiches Intervall

Bei der Klassifizierung „Gleiches Intervall“ wird der Bereich der Attributwerte in **gleiche Intervallklassen** unterteilt. Standardmäßig werden die Daten in 7 Klassen aufgeteilt. 

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>

  <img src={require('/img/map/styling/equal_interval.png').default} alt="Equal Interval" style={{ maxHeight: "auto", maxWidth: "auto", objectFit: "cover"}}/>

</div> 

### Heads und Tails

Die Heads und Tails-Methode wird für **Datensätze mit einer schiefen Verteilung** verwendet. Sie wurde entwickelt, um die Extreme in den Daten hervorzuheben, indem sie sich auf die **'Heads' (die sehr hohen Werte)** und die **'Tails' (die sehr niedrigen Werte)** konzentriert. Diese Methode ist besonders nützlich für Datensätze, bei denen die wichtigsten Informationen in den Extremen zu finden sind, und bei denen die Hervorhebung dieser Werte zu einem besseren Einblick und Verständnis führen kann. Standardmäßig werden die Daten in 7 Klassen aufgeteilt.  

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>

  <img src={require('/img/map/styling/heads_tails.png').default} alt="Heads and Tails" style={{ maxHeight: "auto", maxWidth: "auto", objectFit: "cover"}}/>

</div> 


### Benutzerdefinierte Schritte (für <code>Zahlen</code>)

Die Klassifizierung Benutzerdefinierte Schritte ist eine Datenvisualisierungsmethode für **numerische Daten**. Sie ermöglicht die Definition von **benutzerdefinierten Zwischenpunkten** oder **Schwellenwerten** und bietet damit einen maßgeschneiderten Ansatz für kontextspezifische Visualisierungen. 


### Benutzerdefinierte Ordinalskala (für <code>Zeichen</code>)

Die benutzerdefinierte Ordinalskala ist eine Methode zur Datensortierung und -visualisierung, die auf **Zeichen-Daten** angewendet wird, wie z. B. Kategorien, Etiketten oder textbasierte Variablen. Im Gegensatz zu numerischen Daten, bei denen die Reihenfolge typischerweise auf der Größe basiert, fehlt bei Textdaten oft eine natürliche Reihenfolge. Die Benutzerdefinierte Ordinalskala ermöglicht es daher, **eigene Ordnungsregeln für Textfelder** zu definieren und eine individuelle, auf die eigenen Bedürfnisse zugeschnittene Reihenfolge zu erstellen. 

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>

  <img src={require('/img/map/styling/ordinal.png').default} alt="Custom Ordinal for strings" style={{ maxHeight: "auto", maxWidth: "auto", objectFit: "cover"}}/>

</div>


So können zusätzliche Schritte hinzugefügt und mehrere Text-Werte pro Gruppe aus einem Dropdown-Menü ausgewählt werden. Das Dropdown-Menü listet dabei alle Attributwerte des Datensatzes auf. 

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>

  <img src={require('/img/map/styling/custom_ordinal.gif').default} alt="Custom Ordinal for strings" style={{ maxHeight: "300px", maxWidth: "300px", objectFit: "cover"}}/>

</div> 



import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';

## Layer Design

<Tabs>
 <TabItem value="fill color" label="Füllfarbe" default> Die Füllfarbe kann entweder eine einzelne Farbe oder eine Farbpalette sein. GOAT bietet eine Reihe von voreingestellten Farben und Paletten zur Gestaltung Ihrer Karte an. 
Für die attributbasierte Füllfarbe wählen Sie ein Feld aus dem ausgewählten <code>Layer</code> aus.
GOAT wendet eine zufällige Farbpalette auf Ihre Ergebnisse an.
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>

   <img src={require('/img/map/layers/fill-color.gif').default} alt="Custom Ordinal for strings" style={{ maxHeight: "500px", maxWidth: "500px", objectFit: "cover"}}/>

   </div> 

  </TabItem>
  <TabItem value="stroke color" label="Strichfarbe"> Die Strichfarbe ist standardmäßig eine einzige Farbe. Wenden Sie attributbasiertes Styling an, um eine Farbskala auf den Strichfabe für den Layer anzuwenden. 
    Für die attributbasierte Strichfarbe wählen Sie ein Feld aus der ausgewählten <code>Layer</code>.
    GOAT wendet eine zufällige Farbpalette auf Ihre Ergebnisse an. 

   <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>

   <img src={require('/img/map/layers/stroke-color.gif').default} alt="Custom Ordinal for strings" style={{ maxHeight: "500px", maxWidth: "500px", objectFit: "cover"}}/>

   </div> 



  </TabItem>
  <TabItem value="custom marker" label="Benutzerdefinierter Icon"> Diese sind verfügbar für Punktlayer. Aus einer Übersicht können passende Icons ausgewählt werden. Sie können auch Ihre eigenen hochgeladenen Symbole verwenden.
 
<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>

   <img src={require('/img/map/layers/attribute-based-custom-marker.gif').default} alt="Custom Ordinal for strings" style={{ maxHeight: "500px", maxWidth: "500px", objectFit: "cover"}}/>

   </div> 

  </TabItem>
</Tabs>
