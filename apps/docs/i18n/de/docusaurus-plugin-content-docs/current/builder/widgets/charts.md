---
sidebar_position: 3
---


# Diagramme

**Stellen Sie Ihre Daten in einem visuellen Format mit verschiedenen Diagrammtypen dar: Kategorien, Histogramm und Kreisdiagramm.** 

## Kategorien

Das Kategorien-Widget ermöglicht es Ihnen, die Verteilung eines kategorischen Feldes aus einem ausgewählten Layer zu visualisieren, indem es statistische Analysen berechnet und **Gruppen nach dem ausgewählten Feld** generiert.

<div class="step">
  <div class="step-number">1</div>
  <div class="content"><b>Ziehen Sie</b> das <code>Layer</code> Widget per <b>Drag & Drop</b> auf ein Panel und wählen Sie Ihren <code>Layer</code> aus.</div>
</div>

<div class="step">
  <div class="step-number">2</div>
  <div class="content">Wählen Sie die <code>statistische Methode</code>, die Sie anwenden möchten. Es kann <code>Anzahl</code>, <code>Summe</code>, <code>Min</code>, <code>Max</code> sein oder Sie fügen Ihren eigenen <a href="../expressions"><code>Ausdruck</code></a> hinzu.</div>
</div>

<div class="step">
  <div class="step-number">3</div>
  <div class="content">Wählen Sie das <code>Feld</code> aus, <b>auf das die Statistik angewendet werden soll</b>. <i>Summe, Min und Max können nur auf numerische Felder angewendet werden.</i></div>
</div>

<div class="step">
  <div class="step-number">4</div>
  <div class="content">Unter <code>Gruppieren nach Feld</code> wählen Sie das Feld aus, <b>nach dem Ihre Ergebnisse gruppiert werden sollen</b>.</div>
</div>

<div class="step">
  <div class="step-number">5</div>
  <div class="content">Aktivieren oder deaktivieren Sie <code>Kreuzfilter</code>, <b>um dieses Widget abhängig von allen anderen verbundenen Widgets auf Ihrem Dashboard zu aktualisieren.</b></div>
</div>

<div class="step">
  <div class="step-number">6</div>
  <div class="content">Aktivieren oder deaktivieren Sie die Option <code>Filteransichtsfenster</code>, <b>wodurch nur die Daten innerhalb der aktuellen Kartenansicht sichtbar werden</b>.</div>
</div>

<div class="step">
  <div class="step-number">7</div>
  <div class="content">Legen Sie das <code>Zahlenformat</code> aus der Dropdown-Liste fest. Das <code>Standard-Zahlenformat</code> ist dynamisch basierend auf der Sprache der Kartenoberfläche. </div>
</div>

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/builder/builder_categories.gif').default} alt="recent datasets" style={{ maxHeight: "500px", maxWidth: "auto", objectFit: "cover"}}/>
</div> 

<p></p>

::::info
Der Wert mit der **höchsten Zahl wird an die Spitze** des Diagramms springen.
::::

## Histogramm

Das Histogramm-Widget ermöglicht es Ihnen, die **Verteilung eines numerischen Feldes aus einem ausgewählten Layer durch `Anzahl`** zu visualisieren.

<div class="step">
  <div class="step-number">1</div>
  <div class="content"><b>Ziehen Sie</b> das <code>Layer</code> Widget per <b>Drag & Drop</b> auf ein Panel und wählen Sie Ihren <code>Layer</code> aus.</div>
</div>

<div class="step">
  <div class="step-number">2</div>
  <div class="content">Wählen Sie das <code>numerische Feld</code>, das Sie visualisieren möchten. Die angewendete statistische Methode wird <code>Anzahl</code> sein. </div>
</div>

<div class="step">
  <div class="step-number">3</div>
  <div class="content">Aktivieren oder deaktivieren Sie <code>Kreuzfilter</code>, <b>um dieses Widget abhängig von allen anderen verbundenen Widgets auf Ihrem Dashboard zu aktualisieren</b>.</div>
</div>

<div class="step">
  <div class="step-number">4</div>
  <div class="content">Aktivieren oder deaktivieren Sie die Option <code>Filteransichtsfenster</code>, <b>wodurch nur die Daten innerhalb der aktuellen Kartenansicht sichtbar werden</b>.</div>
</div>

<div class="step">
  <div class="step-number">5</div>
  <div class="content">Legen Sie das <code>Zahlenformat</code> aus der Dropdown-Liste fest. Das <code>Standard-Zahlenformat</code> ist dynamisch basierend auf der Sprache der Kartenoberfläche. </div>
</div>

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/builder/builder_histogram.gif').default} alt="recent datasets" style={{ maxHeight: "500px", maxWidth: "auto", objectFit: "cover"}}/>
</div> 


## Kreisdiagramm

Das Kreisdiagramm-Widget ermöglicht es Ihnen, **die Verteilung eines Feldes** aus einem ausgewählten Layer zu visualisieren.

<div class="step">
  <div class="step-number">1</div>
  <div class="content"><b>Ziehen Sie</b> das <code>Layer</code> Widget per <b>Drag & Drop</b> auf ein Panel und wählen Sie Ihren <code>Layer</code> aus.</div>
</div>

<div class="step">
  <div class="step-number">2</div>
  <div class="content">Wählen Sie die <code>statistische Methode</code>, die Sie anwenden möchten. Es kann <code>Anzahl</code>, <code>Summe</code>, <code>Min</code>, <code>Max</code> sein oder Sie fügen Ihren eigenen <a href="../expressions"><code>Ausdruck</code></a> hinzu.</div>
</div>

<div class="step">
  <div class="step-number">3</div>
  <div class="content">Wählen Sie das <code>Feld</code> aus, <b>auf das die Statistik angewendet werden soll</b>. <i>Summe, Min und Max können nur auf numerische Felder angewendet werden.</i></div>
</div>

<div class="step">
  <div class="step-number">4</div>
  <div class="content">Wählen Sie das <code>Feld</code> aus, nach dem Ihre Ergebnisse <b>gruppiert werden sollen</b>.</div>
</div>

<div class="step">
  <div class="step-number">5</div>
  <div class="content">Aktivieren oder deaktivieren Sie <code>Kreuzfilter</code>, <b>um dieses Widget abhängig von allen anderen verbundenen Widgets auf Ihrem Dashboard zu aktualisieren</b>.</div>
</div>

<div class="step">
  <div class="step-number">6</div>
  <div class="content">Aktivieren oder deaktivieren Sie die Option <code>Filteransichtsfenster</code>, <b>wodurch nur die Daten innerhalb der aktuellen Kartenansicht sichtbar werden</b>.</div>
</div>

::::info
Ergebnisse werden in **Prozent** visualisiert.
::::


<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/builder/builder_pie_chart.gif').default} alt="recent datasets" style={{ maxHeight: "500px", maxWidth: "auto", objectFit: "cover"}}/>
</div> 


::::tip

Wo **statistische Methoden angewendet werden können**, sind *Anzahl, Summe, Min, Max und <a href="../expressions">Ausdruck</a>* die verfügbaren Optionen. Schauen Sie sich unsere **<a href="../expressions">Ausdrücke-Dokumentation</a>** für weitere Informationen an.
::::