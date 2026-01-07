---
sidebar_position: 2
---


# Daten

**Dieser Abschnitt enthält Widgets, die Ihnen helfen, mit Ihren Daten zu interagieren und sie zu analysieren**: **Filter** und **Zahlen**. 

## Filter

Dieses Widget ist ein interaktives Element, das **es Benutzern ermöglicht, Daten auf dem konfigurierten Layer basierend auf dem ausgewählten Attributfeld zu filtern**. Betrachter können dies als **Zuschneide-Werkzeug auf den Karten** verwenden.

<div class="step">
  <div class="step-number">1</div>
  <div class="content">Ziehen Sie das <code>Filter</code> Widget per Drag & Drop auf ein Panel.</div>
</div>

<div class="step">
  <div class="step-number">2</div>
  <div class="content">Wählen Sie Ihren <code>Layer</code> und wählen Sie das <code>Feld</code>, <b>nach dem Sie filtern möchten</b>.</div>
</div>

<div class="step">
  <div class="step-number">3</div>
  <div class="content">Fügen Sie optional einen <code>Platzhalter</code>-Text hinzu, der vor der Anwendung des Filters erscheint.</div>
</div>

<div class="step">
  <div class="step-number">4</div>
  <div class="content">Aktivieren oder deaktivieren Sie <code>Kreuzfilter</code>, um <b>dieses Widget mit anderen Daten-Widgets interagieren zu lassen</b>. Wenn aktiviert, wird das Filtern von Daten in einem Widget automatisch alle anderen verbundenen Widgets auf Ihrem Dashboard aktualisieren.</div>
</div>

<div class="step">
  <div class="step-number">5</div>
  <div class="content">Aktivieren oder deaktivieren Sie die Option <code>Zoomen zur Auswahl</code>, wodurch die <b>Kartenansicht automatisch zu den gefilterten Daten geschwenkt wird</b>.</div>
</div>

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/builder/builder_filter.gif').default} alt="recent datasets" style={{ maxHeight: "500px", maxWidth: "auto", objectFit: "cover"}}/>
</div> 

## Zahlen

Wählen Sie aus verschiedenen statistischen Methoden, die auf einem Layer berechnet werden sollen.

<div class="step">
  <div class="step-number">1</div>
  <div class="content">Ziehen Sie das <code>Zahlen</code> Widget per Drag & Drop auf ein Panel.</div>
</div>

<div class="step">
  <div class="step-number">2</div>
  <div class="content">Wählen Sie Ihren <code>Layer</code> aus. </div>
</div>

<div class="step">
  <div class="step-number">3</div>
  <div class="content">Wählen Sie die <code>statistische Methode</code>, die Sie anwenden möchten. Es kann <code>Anzahl</code>, <code>Summe</code>, <code>Min</code>, <code>Max</code> sein oder Sie fügen Ihren eigenen [<code>Ausdruck</code>](../expressions) hinzu. </div>
</div>

<div class="step">
  <div class="step-number">4</div>
  <div class="content">Wählen Sie das <code>Feld</code> aus, <b>auf das die Statistik angewendet werden soll</b>. <i>Summe, Min und Max können nur auf numerische Felder angewendet werden.</i></div>
</div>

<div class="step">
  <div class="step-number">5</div>
  <div class="content">Aktivieren oder deaktivieren Sie <code>Kreuzfilter</code>, um dieses <b>Widget abhängig von allen anderen verbundenen Widgets auf Ihrem Dashboard zu aktualisieren</b>.</div>
</div>

<div class="step">
  <div class="step-number">6</div>
  <div class="content">Aktivieren oder deaktivieren Sie die Option <code>Filteransichtsfenster</code>, wodurch <b>nur die Daten innerhalb der aktuellen Kartenansicht sichtbar werden</b>.</div>
</div>

<div class="step">
  <div class="step-number">7</div>
  <div class="content">Legen Sie das <code>Zahlenformat</code> aus der Dropdown-Liste fest. Das <code>Standard-Zahlenformat</code> ist dynamisch basierend auf der Sprache der Kartenoberfläche.</div>
</div>


<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/builder/builder_number.gif').default} alt="recent datasets" style={{ maxHeight: "500px", maxWidth: "auto", objectFit: "cover"}}/>
</div> 