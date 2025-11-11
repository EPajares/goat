---
sidebar_position: 3
---

# Diagramme

Dieser Abschnitt umfasst verschiedene Diagrammtypen zur Anzeige Ihrer Daten: **Kategorien**, **Histogramm** und **Kreisdiagramm**. Ziehen Sie einfach **per Drag & Drop** Widgets aus dem rechten Panel auf jedes Panel Ihres Dashboards. Passen Sie jedes Widget an, indem Sie darauf klicken, wodurch die **Widget-Einstellungen** im rechten Panel geöffnet werden.

### Kategorien

Dieses Diagramm berechnet statistische Analysen und gruppiert Ergebnisse nach dem ausgewählten Feld.

<div class="step">
  <div class="step-number">1</div>
  <div class="content">Wählen Sie Ihren <b>Layer</b> aus. </div>
</div>

<div class="step">
  <div class="step-number">2</div>
  <div class="content">Wählen Sie die <b>statistische Methode</b>, die Sie anwenden möchten. Es kann <b>Anzahl, Summe, Min, Max</b> sein oder Sie fügen Ihren eigenen <b>Ausdruck</b> hinzu.  </div>
</div>

<div class="step">
  <div class="step-number">3</div>
  <div class="content">Wenn die <b>statistische Methode</b> <b>Summe, Min oder Max</b> war, wählen Sie das Feld aus, auf das die Statistik angewendet werden soll.</div>
</div>

<div class="step">
  <div class="step-number">4</div>
  <div class="content">Wählen Sie das <b>Feld</b> aus, nach dem Ihre Ergebnisse <b>gruppiert werden sollen.</b></div>
</div>

<div class="step">
  <div class="step-number">5</div>
  <div class="content">Legen Sie das <b>Zahlenformat</b> aus der Dropdown-Liste fest. Das <b>Standard-Zahlenformat</b> ist dynamisch basierend auf der Sprache der Benutzeroberfläche. </div>
</div>

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/builder/builder_categories.gif').default} alt="recent datasets" style={{ maxHeight: "500px", maxWidth: "auto", objectFit: "cover"}}/>
</div> 

<p></p>

::::info

Der Wert mit der <b>höchsten Zahl wird an die Spitze</b> des Diagramms springen.

::::


### Histogramm

Es visualisiert die Verteilung eines numerischen Feldes aus einem ausgewählten Layer durch Zählung der Häufigkeit von Werten. Es hilft dabei, Muster wie Cluster, Lücken oder Ausreißer zu erkennen. 

<div class="step">
  <div class="step-number">1</div>
  <div class="content">Wählen Sie Ihren <b>Layer</b> aus. </div>
</div>

<div class="step">
  <div class="step-number">2</div>
  <div class="content">Wählen Sie das <b>numerische Feld</b>, das Sie visualisieren möchten. Die angewendete statistische Methode wird <b>Anzahl</b> sein.  </div>
</div>

<div class="step">
  <div class="step-number">3</div>
  <div class="content">Legen Sie das <b>Zahlenformat</b> aus der Dropdown-Liste fest. Das <b>Standard-Zahlenformat</b> ist dynamisch basierend auf der Sprache der Benutzeroberfläche. </div>
</div>

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/builder/builder_histogram.gif').default} alt="recent datasets" style={{ maxHeight: "500px", maxWidth: "auto", objectFit: "cover"}}/>
</div> 


### Kreisdiagramm

Es visualisiert den Anteil von Werten innerhalb eines **Feldes** aus dem ausgewählten Layer.

<div class="step">
  <div class="step-number">1</div>
  <div class="content">Wählen Sie Ihren <b>Layer</b> aus. </div>
</div>

<div class="step">
  <div class="step-number">2</div>
  <div class="content">Wählen Sie die <b>statistische Methode</b>, die Sie anwenden möchten. Es kann <b>Anzahl, Summe, Min, Max</b> sein oder Sie fügen Ihren eigenen <b>Ausdruck</b> hinzu.  </div>
</div>

<div class="step">
  <div class="step-number">3</div>
  <div class="content">Wählen Sie das <b>Feld</b> aus, auf das die Statistik angewendet werden soll. <i>Summe, Min und Max können nur auf numerische Felder angewendet werden.</i></div>
</div>

<div class="step">
  <div class="step-number">4</div>
  <div class="content">Wählen Sie das <b>Feld</b> aus, nach dem Ihre Ergebnisse <b>gruppiert werden sollen.</b></div>
</div>

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/builder/builder_chart.gif').default} alt="recent datasets" style={{ maxHeight: "500px", maxWidth: "auto", objectFit: "cover"}}/>
</div> 


::::info

Ergebnisse werden in <b>Prozent</b> visualisiert.

::::

::::tip

Wo **statistische Methoden angewendet werden können**, sind *Anzahl, Summe, Min, Max und Ausdruck* die verfügbaren Optionen. Schauen Sie sich unsere **[Ausdrücke-Dokumentation](/data/expressions.md)** für weitere Informationen an.

::::