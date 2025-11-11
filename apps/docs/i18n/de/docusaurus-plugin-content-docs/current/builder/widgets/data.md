---
sidebar_position: 2
---

# Daten
Dieser Abschnitt enthält: **Filter** und **Zahlen**. Ziehen Sie einfach **per Drag & Drop** Widgets aus dem rechten Panel auf jedes Panel Ihres Dashboards. Passen Sie jedes Widget an, indem Sie darauf klicken, wodurch die **Widget-Einstellungen** im rechten Panel geöffnet werden.

### Filter
Dieses Widget ist ein **interaktives Element**, das es Benutzern ermöglicht, Daten auf dem konfigurierten Layer basierend auf dem ausgewählten Attributfeld zu filtern.

<div class="step">
  <div class="step-number">1</div>
  <div class="content">Wählen Sie Ihren <b>Layer</b> aus. </div>
</div>

<div class="step">
  <div class="step-number">2</div>
  <div class="content">Wählen Sie das <b>Feld</b> aus, nach dem Sie filtern möchten. </div>
</div>

<div class="step">
  <div class="step-number">3</div>
  <div class="content">Wählen Sie die Layout-Option: <b>Dropdown</b> oder <b>Schaltfläche</b>.</div>
</div>

<div class="step">
  <div class="step-number">4</div>
  <div class="content">Fügen Sie optional einen <b>Platzhalter</b>-Text hinzu, der vor der Anwendung des Filters erscheint.</div>
</div>

<div class="step">
  <div class="step-number">5</div>
  <div class="content">Aktivieren oder deaktivieren Sie die Option <b>Mehrfachauswahl zulassen</b>. Die Auswahl entspricht <b>allen</b> ausgewählten Kriterien.</div>
</div>

<div class="step">
  <div class="step-number">6</div>
  <div class="content">Sie können <b>Zur Auswahl zoomen</b> aktivieren, wodurch die Kartenansicht automatisch zu den gefilterten Daten geschwenkt wird.</div>
</div>

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/builder/builder_filter.gif').default} alt="recent datasets" style={{ maxHeight: "500px", maxWidth: "auto", objectFit: "cover"}}/>
</div> 

### Zahlen

Das Zahlen-Widget zeigt numerische Daten basierend auf dem ausgewählten Layer und der gewählten statistischen Methode an.

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
  <div class="content">Legen Sie das <b>Zahlenformat</b> aus der Dropdown-Liste fest. Das <b>Standard-Zahlenformat</b> ist dynamisch basierend auf der Sprache der Benutzeroberfläche.</div>
</div>

<div class="step">
  <div class="step-number">5</div>
  <div class="content">Aktivieren oder deaktivieren Sie die Option <b>Mehrfachauswahl zulassen</b>. Die Auswahl entspricht <b>allen</b> ausgewählten Kriterien.</div>
</div>


<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/builder/builder_number.gif').default} alt="recent datasets" style={{ maxHeight: "500px", maxWidth: "auto", objectFit: "cover"}}/>
</div> 