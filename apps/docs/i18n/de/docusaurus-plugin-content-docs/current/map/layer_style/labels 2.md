---
sidebar_position: 3
---
import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';

# Beschriftungen

Sie können Beschriftungen auf Ihren Layern **basierend auf jedem Attribut** anzeigen. Beschriftungen machen Ihre Karte *leichter lesbar und informativer*.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
  <img src={require('/img/map/styling/style_label.png').default} alt="label font size" style={{ maxHeight: "Auto", maxWidth: "Auto", objectFit: "cover"}}/>
</div> 

## Beschriftung nach

Zuerst **wählen Sie das Attributfeld** aus, dessen Werte Sie als Beschriftungen auf der Karte darstellen möchten. Gehen Sie dann zu weiteren Einstellungen über.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
  <img src={require('/img/map/styling/label_by.gif').default} alt="label by function" style={{ maxHeight: "Auto", maxWidth: "500px", objectFit: "cover"}}/>
</div> 

## Beschriftungseinstellungen

### Größe

Legen Sie die **Größe des Beschriftungstexts** fest. Werte können zwischen 5 und 100 liegen. Sie können sie auf der Skala einstellen oder die Zahl manuell eingeben.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
  <img src={require('/img/map/styling/label_size.gif').default} alt="label font size" style={{ maxHeight: "Auto", maxWidth: "600px", objectFit: "cover"}}/>
</div> 

### Farbe

Wählen Sie **eine beliebige Farbe** mit dem <code>Color Picker</code> oder wählen Sie eine aus unseren <code>Preset Colors</code>.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
  <img src={require('/img/map/styling/label_color.png').default} alt="label font size" style={{ maxHeight: "200px", maxWidth: "Auto", objectFit: "cover"}}/>
</div> 

### Position

Definieren Sie, wo die Beschriftung **in Bezug auf das Objekt** erscheint: zentriert, oben, unten, links, rechts, oben links, oben rechts, unten links oder unten rechts.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
  <img src={require('/img/map/styling/label_placement.gif').default} alt="label font size" style={{ maxHeight: "Auto", maxWidth: "500px", objectFit: "cover"}}/>
</div> 

<br></br> 

---

::::info
Öffnen Sie weitere Einstellungen mit dem Button <b>Erweiterte Einstellungen</b> <code><img src={require('/img/map/styling/options_icon.png').default} alt="Options Icon" style={{ maxHeight: "15px", maxWidth: "15px", objectFit: "cover"}}/></code>.
::::

### Offset

**Passen Sie die Position der Beschriftung** an, indem Sie sie horizontal (<code>Offset X</code>) oder vertikal (<code>Offset Y</code>) verschieben. Verwenden Sie die Skala, um Einstellungen zu erstellen, oder geben Sie die Zahl manuell ein.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
  <img src={require('/img/map/styling/offset.gif').default} alt="label font size" style={{ maxHeight: "Auto", maxWidth: "500px", objectFit: "cover"}}/>
</div> 

### Überlappung zulassen

Wenn **aktiviert**, erscheinen Beschriftungen auf *allen Zoom-Leveln*. Wenn **deaktiviert**, werden die Beschriftungen bei niedrigeren Zoom-Leveln *gruppiert*.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
  <img src={require('/img/map/styling/overlap.gif').default} alt="label font size" style={{ maxHeight: "Auto", maxWidth: "500px", objectFit: "cover"}}/>
</div> 

### Halo-Farbe

Ein Halo ist ein **Umriss um die Beschriftung**, der die Lesbarkeit auf belebten Hintergründen verbessert. Wählen Sie eine Farbe mit dem <code>Farbwähler</code> oder wählen Sie eine aus unseren <code>Voreingestellten Farben</code>.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
  <img src={require('/img/map/styling/halo_color.png').default} alt="label font size" style={{ maxHeight: "200px", maxWidth: "Auto", objectFit: "cover"}}/>
</div> 

### Halo-Breite

Legen Sie die **Dicke des Halos** fest. Der maximale Wert beträgt ein Viertel der Beschriftungsschriftgröße. Verwenden Sie die Skala, um die Einstellung zu erstellen, oder geben Sie die Zahl manuell ein.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
  <img src={require('/img/map/styling/halo_width.gif').default} alt="label font size" style={{ maxHeight: "Auto", maxWidth: "500px", objectFit: "cover"}}/>
</div> 


## Tipps

- Verwenden Sie **kleinere Schriften** für *dichte Layer*, um visuelles Durcheinander zu reduzieren.
- Ein **heller Halo** auf **dunklen Karten** (oder umgekehrt) kann Beschriftungen viel *leichter lesbar* machen.
- **Standardmäßig ist die Überlappung von Beschriftungen deaktiviert**, was *die Klarheit verbessert*, aber einige Beschriftungen könnten fehlen, wenn der Platz begrenzt ist.