---
sidebar_position: 3
---

# Diagramme

Stellen Sie Ihre Daten in einem visuellen Format mit verschiedenen Diagrammtypen dar: **Kategorien**, **Histogramm** und **Kreisdiagramm**. Ziehen Sie einfach **per Drag & Drop** Widgets aus der rechten Seitenleiste auf jedes Panel Ihres Dashboards. Passen Sie jedes Widget an, indem Sie darauf klicken, wodurch die **Widget-Einstellungen** im rechten Panel geöffnet werden.

## Kategorien

Das Kategorien-Widget ermöglicht es Ihnen, die Verteilung eines kategorischen Feldes aus einem ausgewählten Layer zu visualisieren, indem es statistische Analysen berechnet und **Gruppen nach dem ausgewählten Feld** generiert.

<div class="step">
  <div class="step-number">1</div>
  <div class="content">Wählen Sie Ihren <code>Layer</code> aus. </div>
</div>

<div class="step">
  <div class="step-number">2</div>
  <div class="content">Wählen Sie die <code>statistische Methode</code>, die Sie anwenden möchten. Es kann <code>Anzahl</code>, <code>Summe</code>, <code>Min</code>, <code>Max</code> sein oder Sie fügen Ihren eigenen [<code>Ausdruck</code>](/data/expressions.md) hinzu.</div>
</div>

<div class="step">
  <div class="step-number">3</div>
  <div class="content">Wählen Sie das <code>Feld</code> aus, auf das die Statistik angewendet werden soll. <i>Summe, Min und Max können nur auf numerische Felder angewendet werden.</i></div>
</div>

<div class="step">
  <div class="step-number">4</div>
  <div class="content">Unter <code>Gruppieren nach Feld</code> wählen Sie das Feld aus, nach dem Ihre Ergebnisse gruppiert werden sollen.</div>
</div>

<div class="step">
  <div class="step-number">5</div>
  <div class="content">Aktivieren oder deaktivieren Sie <code>Kreuzfilter</code>, um dieses Widget abhängig von allen anderen verbundenen Widgets auf Ihrem Dashboard zu aktualisieren.</div>
</div>

<div class="step">
  <div class="step-number">6</div>
  <div class="content">Aktivieren oder deaktivieren Sie die Option <code>Filteransichtsfenster</code>, wodurch nur die Daten innerhalb der aktuellen Kartenansicht sichtbar werden.</div>
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
  <div class="content">Wählen Sie Ihren <code>Layer</code> aus. </div>
</div>

<div class="step">
  <div class="step-number">2</div>
  <div class="content">Wählen Sie das <code>numerische Feld</code>, das Sie visualisieren möchten. Die angewendete statistische Methode wird <code>Anzahl</code> sein.  </div>
</div>

<div class="step">
  <div class="step-number">3</div>
  <div class="content">Aktivieren oder deaktivieren Sie <code>Kreuzfilter</code>, um dieses Widget abhängig von allen anderen verbundenen Widgets auf Ihrem Dashboard zu aktualisieren.</div>
</div>

<div class="step">
  <div class="step-number">4</div>
  <div class="content">Aktivieren oder deaktivieren Sie die Option <code>Filteransichtsfenster</code>, wodurch nur die Daten innerhalb der aktuellen Kartenansicht sichtbar werden.</div>
</div>

<div class="step">
  <div class="step-number">5</div>
  <div class="content">Legen Sie das <code>Zahlenformat</code> aus der Dropdown-Liste fest. Das <code>Standard-Zahlenformat</code> ist dynamisch basierend auf der Sprache der Kartenoberfläche. </div>
</div>

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/builder/builder_histogram.gif').default} alt="recent datasets" style={{ maxHeight: "500px", maxWidth: "auto", objectFit: "cover"}}/>
</div> 


## Kreisdiagramm

Das Kreisdiagramm-Widget ermöglicht es Ihnen, die Verteilung eines **Feldes** aus einem ausgewählten Layer zu visualisieren.

<div class="step">
  <div class="step-number">1</div>
  <div class="content">Wählen Sie Ihren <code>Layer</code> aus. </div>
</div>

<div class="step">
  <div class="step-number">2</div>
  <div class="content">Wählen Sie die <code>statistische Methode</code>, die Sie anwenden möchten. Es kann <code>Anzahl</code>, <code>Summe</code>, <code>Min</code>, <code>Max</code> sein oder Sie fügen Ihren eigenen [<code>Ausdruck</code>](/data/expressions.md) hinzu.  </div>
</div>

<div class="step">
  <div class="step-number">3</div>
  <div class="content">Wählen Sie das <code>Feld</code> aus, auf das die Statistik angewendet werden soll. <i>Summe, Min und Max können nur auf numerische Felder angewendet werden.</i></div>
</div>

<div class="step">
  <div class="step-number">4</div>
  <div class="content">Wählen Sie das <code>Feld</code> aus, nach dem Ihre Ergebnisse <code>gruppiert werden sollen</code>.</div>
</div>

<div class="step">
  <div class="step-number">5</div>
  <div class="content">Aktivieren oder deaktivieren Sie <code>Kreuzfilter</code>, um dieses Widget abhängig von allen anderen verbundenen Widgets auf Ihrem Dashboard zu aktualisieren.</div>
</div>

<div class="step">
  <div class="step-number">6</div>
  <div class="content">Aktivieren oder deaktivieren Sie die Option <code>Filteransichtsfenster</code>, wodurch nur die Daten innerhalb der aktuellen Kartenansicht sichtbar werden.</div>
</div>

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/builder/builder_pie_chart.gif').default} alt="recent datasets" style={{ maxHeight: "500px", maxWidth: "auto", objectFit: "cover"}}/>
</div> 


::::info
Ergebnisse werden in **Prozent** visualisiert.
::::

::::tip
Wo **statistische Methoden angewendet werden können**, sind *Anzahl, Summe, Min, Max und [Ausdruck](/data/expressions.md)* die verfügbaren Optionen. Schauen Sie sich unsere **[Ausdrücke-Dokumentation](/data/expressions.md)** für weitere Informationen an.
::::