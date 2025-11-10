---
sidebar_position: 3
---
import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';


# Beschriftungen

**Beschriftungen ermöglichen es, Text auf Ihren Karten-Features basierend auf jedem Attributfeld anzuzeigen.** Dies macht Ihre Karten informativer und leichter interpretierbar, indem wichtige Informationen direkt auf den Features angezeigt werden.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
  <img src={require('/img/map/styling/labels.png').default} alt="Beschriftungen auf Karten-Features angezeigt" style={{ maxHeight: "auto", maxWidth: "auto", objectFit: "cover"}}/>
</div>

## Wie man Beschriftungen hinzufügt und konfiguriert

### Allgemeine Einstellungen

<div class="step">
  <div class="step-number">1</div>
  <div class="content">Wählen Sie Ihren Layer und navigieren Sie zu <code>Layer Design</code> <img src={require('/img/map/styling/styling_icon.webp').default} alt="Styling Icon" style={{ maxHeight: "15px", maxWidth: "15px", objectFit: "cover"}}/> und finden Sie den <code>Beschriftungsbereich</code></div>
</div>

<div class="step">
  <div class="step-number">2</div>
  <div class="content">Bei <code>Beschriftung nach</code> wählen Sie das **Attributfeld**, dessen Werte Sie als Beschriftungen anzeigen möchten</div>
</div>

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
  <img src={require('/img/map/styling/label_by.gif').default} alt="Auswahl des Beschriftungsattributfelds" style={{ maxHeight: "auto", maxWidth: "500px", objectFit: "cover"}}/>
</div>

<div class="step">
  <div class="step-number">3</div>
  <div class="content">Bei <code>Größe</code> stellen Sie die **Beschriftungsgröße** mit dem Schieberegler (5-100) ein oder geben Sie den Wert manuell ein</div>
</div>

<div class="step">
  <div class="step-number">4</div>
  <div class="content">Bei <code>Farbe</code> wählen Sie eine **Beschriftungsfarbe** mit dem Farbwähler oder wählen Sie aus den voreingestellten Farben</div>
</div>

<div class="step">
  <div class="step-number">5</div>
  <div class="content">Stellen Sie die <code>Platzierung</code> ein, um zu definieren, **wo Beschriftungen relativ zu den Features erscheinen** (Mitte, oben, unten, links, rechts oder Eckpositionen)</div>
</div>

### Erweiterte Einstellungen

<div class="step">
  <div class="step-number">6</div>
  <div class="content">Klicken Sie auf den <code>Erweiterte Einstellungen</code> <img src={require('/img/map/styling/options_icon.png').default} alt="Optionen" style={{ maxHeight: "15px", maxWidth: "15px", objectFit: "cover"}}/> Button, um **zusätzliche Optionen** zu erreichen</div>
</div>

<div class="step">
  <div class="step-number">7</div>
  <div class="content">Passen Sie <code>Offset X</code> und <code>Offset Y</code> an, um die **Beschriftungsposition** durch horizontale oder vertikale Bewegung feinzustellen</div>
</div>

<div class="step">
  <div class="step-number">8</div>
  <div class="content">Konfigurieren Sie <code>Überlappung zulassen</code>: **Aktivieren** um alle Beschriftungen zu zeigen (kann visuelles Durcheinander verursachen) oder **Deaktivieren** für automatische Gruppierung bei niedrigeren Zoom-Stufen (saubereres Aussehen)</div>
</div>

<div class="step">
  <div class="step-number">9</div>
  <div class="content">Fügen Sie eine <code>Halo-Farbe</code> hinzu, um einen **farbigen Umriss** um den Text zu erstellen für bessere Lesbarkeit auf belebten Hintergründen</div>
</div>

<div class="step">
  <div class="step-number">10</div>
  <div class="content">Stellen Sie die <code>Halo-Breite</code> ein, um die **Umrissdicke** zu kontrollieren (Maximum ist ein Viertel der Schriftgröße)</div>
</div>

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
  <img src={require('/img/map/styling/labels_overlap.gif').default} alt="Beschriftungsüberlappung und Halo-Effekte" style={{ maxHeight: "auto", maxWidth: "500px", objectFit: "cover"}}/>
</div>

## Bewährte Praktiken

- Verwenden Sie **kleinere Schriftarten** für dichte Layer, um visuelles Durcheinander zu reduzieren
- Fügen Sie **Halos** mit kontrastierenden Farben hinzu (helle Halos auf dunklen Karten, dunkle Halos auf hellen Karten), um die Textlesbarkeit zu verbessern
- Lassen Sie **Überlappung standardmäßig deaktiviert** für ein saubereres Aussehen, obwohl einige Beschriftungen in überfüllten Bereichen verborgen sein können
- Testen Sie Ihre Beschriftungseinstellungen bei verschiedenen Zoom-Stufen, um sicherzustellen, dass sie in allen Maßstäben lesbar und nützlich bleiben