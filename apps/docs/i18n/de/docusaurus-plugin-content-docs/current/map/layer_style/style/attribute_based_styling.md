---
sidebar_position: 2
---

# Attribut-basiertes Styling

GOAT unterstützt ***attribut-basiertes Styling***, um die Visualisierung von Daten auf Karten zu verbessern. Dies hilft dabei, Unterschiede und Muster in den Daten zu zeigen, indem ihr Stil auf Datenattributen basiert, was es einfacher macht, komplexe räumliche Informationen zu verstehen. Jeder Aspekt der Visualisierung eines Layers, wie **Füllfarbe**, **Strichfarbe**, **Benutzerdefinierte Marker** und **Beschriftungen**, kann individuell nach einem Feld der Layer-Daten gestaltet werden.

<iframe width="100%" height="500" src="https://www.youtube.com/embed/LKzuWNFk88s?si=SvKpL3hKkA9b1pov" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>

## Wie wird gestylt?

<div class="step">
  <div class="step-number">1</div>
  <div class="content">Klicken Sie auf <code>Layer Design <img src={require('/img/map/styling/styling_icon.webp').default} alt="Styling Icon" style={{ maxHeight: "15px", maxWidth: "21px", objectFit: "cover"}}/></code>, öffnen Sie das <code> Stil</code>-Menü, stellen Sie sicher, dass der Attribut-Toggle aktiviert ist, und klicken Sie dann auf <code>Optionen <img src={require('/img/map/styling/options_icon.png').default} alt="Options Icon" style={{ maxHeight: "15px", maxWidth: "15px", objectFit: "cover"}}/></code>, um mit dem Styling zu beginnen.</div>
</div>

<div class="step">
  <div class="step-number">2</div>
  <div class="content">Im Menü <code>Farbe basierend auf</code> wählen Sie das <strong>Feld</strong> aus, nach dem Sie stylen möchten.</div>
</div>

<div class="step">
  <div class="step-number">3</div>
  <div class="content">Oben im Menü <code>Palette</code> können Sie eine andere <strong>Farbpalette</strong> auswählen oder die Standardpalette beibehalten. Mehr über die in GOAT verfügbaren Optionen erfahren Sie im Abschnitt Farbpalette auf dieser Seite.</div>
</div>

<div class="step">
  <div class="step-number">4</div>
  <div class="content">Unter dem Menü <code>Farbskala</code> können Sie die <strong>Datenklassifizierungsmethode</strong> auswählen, die Sie benötigen. Mehr über die verschiedenen verfügbaren Methoden erfahren Sie <a href="#datenklassifizierungsmethoden"><strong>hier</strong></a></div>
</div>

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>

  <img src={require('/img/map/styling/attribute_selection.gif').default} alt="Attribute Selection" style={{ maxHeight: "auto", maxWidth: "auto", objectFit: "cover"}}/>

</div> 

## Farbpalette
Eine Palette ist eine Reihe von Farben, die verwendet wird, um die Skala der Werte oder Kategorien in den Daten Ihres Layers darzustellen.

In GOAT können Sie Ihre Palette anpassen, indem Sie den <code>Typ</code> auswählen, die Anzahl der <code>Schritte</code> anpassen und die Farben <code>Umkehren</code>. Sie können auch einen benutzerdefinierten Farbbereich erstellen, indem Sie die <code>Benutzerdefiniert</code>-Schaltfläche aktivieren.

GOAT bietet eine breite Palette vordefinierter Paletten, die in vier Typen kategorisiert sind, um die Auswahl und Anwendung zu erleichtern.

<p></p>

| Palettentyp | Beispiel | Beschreibung |
| :-: | --- | ---|
| Divergierend | <img src={require('/img/map/styling/diverging_palette.png').default} alt="diverging" style={{ maxHeight: "auto", maxWidth: "auto", objectFit: "cover"}}/> | **Nützlich für Daten mit einem zentralen Mittelpunkt**, wie positive und negative Werte. Hilft dabei, Variationen um diesen Mittelpunkt klar zu zeigen. |
| Sequentiell | <img src={require('/img/map/styling/sequential_palette.png').default} alt="sequential" style={{ maxHeight: "auto", maxWidth: "auto", objectFit: "cover"}}/> | **Ideal für Daten, die einer natürlichen Progression oder geordneten Sequenz folgen**, wie ansteigende oder abnehmende Werte. Eignet sich hervorragend für die Visualisierung kontinuierlicher Daten und zeigt graduelle Änderungen von einem Extrem zum anderen.|
| Qualitativ | <img src={require('/img/map/styling/qualitative_palette.png').default} alt="qualitative" style={{ maxHeight: "auto", maxWidth: "auto", objectFit: "cover"}}/> | **Entwickelt für unterschiedliche Kategorien oder Klassen.** Hilft dabei, zwischen diskreten Kategorien zu unterscheiden, ohne eine Ordnung oder Wichtigkeit zu implizieren.|
| Einzelfarbton | <img src={require('/img/map/styling/singlehue_palette.png').default} alt="singlehue" style={{ maxHeight: "auto", maxWidth: "auto", objectFit: "cover"}}/> | **Verwendet verschiedene Schattierungen und Töne einer einzigen Farbe.** Schafft ein harmonisches Aussehen und ist effektiv für die Informationsvermittlung ohne die Ablenkung mehrerer Farben.|

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>

  <img src={require('/img/map/styling/color_palettes.gif').default} alt="Color Palettes" style={{ maxHeight: "auto", maxWidth: "auto", objectFit: "cover"}}/>

</div> 

## Datenklassifizierungsmethoden

Unter der <code>Farbskala</code> finden Sie die **Datenklassifizierungsmethode** und die **Farbskala**, die Datenwerte mit Farben verknüpft. Sie ordnet jedem Datenwert basierend auf seiner Position innerhalb eines Bereichs eine Farbe zu. GOAT bietet sechs vordefinierte **Datenklassifizierungsmethoden**: [Quantil](#quantil), [Standardabweichung](#standardabweichung), [Gleiches Intervall](#gleiches-intervall), [Heads und Tails](#heads-und-tails), [Benutzerdefinierte Schritte](#benutzerdefinierte-schritte-für-zahlen), und [Benutzerdefinierte Ordinalskala](#benutzerdefinierte-ordinalskala-für-zeichen).

### Quantil

**Es unterteilt Daten in Klassen mit einer gleichen Anzahl von Beobachtungen**. Dies macht diesen Ansatz **ideal für Daten, die linear verteilt sind**, kann aber ungleichmäßige Klassenbereiche erstellen, wodurch einige Kategorien viel breiter als andere werden. Standardmäßig werden die Daten in 7 Klassen aufgeteilt.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>

  <img src={require('/img/map/styling/quantile.png').default} alt="Quantile" style={{ maxHeight: "auto", maxWidth: "75%", objectFit: "cover"}}/>

</div>  

<p></p>

:::tip TIPP
Möchten Sie besser verstehen, was eine Quantilklassifizierung ist? Schauen Sie in unser [Glossar](../../further_reading/glossary/#quantile-classification).
:::

### Standardabweichung

**Es klassifiziert Daten basierend darauf, wie stark die Werte vom Durchschnitt abweichen**. Diese Methode ist wertvoll für ihre Fähigkeit, eine statistische Perspektive auf die Daten zu bieten, wodurch Benutzer schnell die **relative Streuung, Verteilung der Werte und Ausreißer** innerhalb des Datensatzes erfassen können, funktioniert aber möglicherweise nicht gut, wenn die Daten nicht normal verteilt sind. Standardmäßig werden die Daten in 7 Klassen aufgeteilt.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>

  <img src={require('/img/map/styling/standard_deviation.png').default} alt="Standard Deviation" style={{ maxHeight: "auto", maxWidth: "75%", objectFit: "cover"}}/>

</div> 

### Gleiches Intervall

**Es unterteilt Daten in gleichmäßig große Bereiche, wodurch es einfach wird, Werte zu vergleichen**. Diese Methode funktioniert gut für gleichmäßig verteilte Daten, kann aber irreführend sein, wenn die Daten schief sind, da einige Klassen nahezu leer sein könnten. Standardmäßig werden die Daten in 7 Klassen aufgeteilt.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>

  <img src={require('/img/map/styling/equal_interval.png').default} alt="Equal Interval" style={{ maxHeight: "auto", maxWidth: "75%", objectFit: "cover"}}/>

</div> 

### Heads und Tails

**Es behandelt Datensätze mit einer schiefen Verteilung**. Es wurde entwickelt, um Extreme in den Daten hervorzuheben, wobei der Fokus auf den **'Heads' (den sehr hohen Werten)** und den **'Tails' (den sehr niedrigen Werten)** liegt. Diese Methode ist besonders nützlich für Datensätze, bei denen die wichtigsten Informationen in den Extremen zu finden sind und wo es wichtig ist, Disparitäten oder Schlüsselbereiche für Interventionen hervorzuheben. Standardmäßig werden die Daten in 7 Klassen aufgeteilt.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>

  <img src={require('/img/map/styling/heads_tails.png').default} alt="Heads and Tails" style={{ maxHeight: "auto", maxWidth: "75%", objectFit: "cover"}}/>

</div> 

### Benutzerdefinierte Ordinalskala (für **Zeichen**)

**Es hilft beim Sortieren und Visualisieren von Zeichendaten**, wie Kategorien, Etiketten oder textbasierten Variablen. Da Zeichendaten oft keine natürliche Reihenfolge haben, **ermöglicht die benutzerdefinierte Ordinalmethode Benutzern, ihre eigenen Ordnungsregeln zu definieren**. Dies erstellt eine benutzerdefinierte Sequenz, die auf ihre spezifischen Bedürfnisse zugeschnitten ist.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>

  <img src={require('/img/map/styling/ordinal.png').default} alt="Custom Ordinal for strings" style={{ maxHeight: "auto", maxWidth: "75%", objectFit: "cover"}}/>

</div>

<p></p>

Daher können Sie weitere Schritte hinzufügen und mehrere Zeichenwerte pro Gruppe aus einem Dropdown-Menü auswählen. Das Menü listet alle Attributwerte aus dem Datensatz auf.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>

  <img src={require('/img/map/styling/custom_ordinal.gif').default} alt="Custom Ordinal for strings" style={{ maxHeight: "300px", maxWidth: "300px", objectFit: "cover"}}/>

</div> 

### Benutzerdefinierte Schritte (für **Zahlen**)

**Es wird für numerische Daten verwendet. Es ermöglicht Benutzern, benutzerdefinierte Schwellenwerte oder Grenzwerte zu definieren** und bietet somit einen maßgeschneiderten Ansatz für kontextspezifische Visualisierungen. **Es kann auch dabei helfen, Konsistenz zwischen Karten zu gewährleisten**. Diese Methode gibt volle Kontrolle über Klassifizierungen und stellt sicher, dass sie mit realen Kontexten übereinstimmen.

import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';

## Stil-Einstellungen

<Tabs>
  <TabItem value="fill color" label="Füllfarbe" default> Die Füllfarbe kann entweder eine einzelne Farbe oder eine Farbpalette sein. GOAT bietet eine Reihe von voreingestellten Farben und Paletten zur Gestaltung Ihrer Karte an. 
    Für die attributbasierte Füllfarbe wählen Sie ein Feld aus dem ausgewählten <code>Layer</code> aus.
    GOAT wendet eine zufällige Farbpalette auf Ihre Ergebnisse an.
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>

   <img src={require('/img/map/layers/fill-color.gif').default} alt="Custom Ordinal for strings" style={{ maxHeight: "500px", maxWidth: "500px", objectFit: "cover"}}/>

   </div> 

  </TabItem>
  <TabItem value="stroke color" label="Strichfarbe"> Die Strichfarbe ist standardmäßig eine einzige Farbe. Wenden Sie attributbasiertes Styling an, um eine Farbskala auf den Strich des Layers anzuwenden. 
    Für die attributbasierte Strichfarbe wählen Sie ein Feld aus dem ausgewählten <code>Layer</code>.
    GOAT wendet eine zufällige Farbpalette auf Ihre Ergebnisse an. 

   <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>

   <img src={require('/img/map/layers/stroke-color.gif').default} alt="Custom Ordinal for strings" style={{ maxHeight: "500px", maxWidth: "500px", objectFit: "cover"}}/>

   </div> 



  </TabItem>

  <TabItem value="custom marker" label="Benutzerdefinierte Marker"> Wenn verfügbar, hat der benutzerdefinierte Marker eine Icon-Bibliothek, um Ihren Datensatz am besten darzustellen.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>

   <img src={require('/img/map/layers/attribute-based-custom-marker.gif').default} alt="Custom Ordinal for strings" style={{ maxHeight: "500px", maxWidth: "500px", objectFit: "cover"}}/>

   </div> 

  </TabItem>
</Tabs>


:::tip TIPP
Wenn Sie Ihre Styling-Einstellungen speichern und in weiteren Projekten verwenden möchten, können Sie dies durch [Speichern eines Stils als Standard](../layer_style/styling#default-settings) tun. 
:::
