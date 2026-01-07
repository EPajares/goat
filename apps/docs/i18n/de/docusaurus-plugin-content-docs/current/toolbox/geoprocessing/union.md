# Vereinigung (Union)

Dieses Werkzeug berechnet die **geometrische Vereinigung von Features aus zwei Layern**. Das Ergebnis enthält alle Features aus beiden Layern, wobei überlappende Bereiche geteilt und Attribute kombiniert werden.

## 1. Erklärung

Die Unions-Operation kombiniert zwei Layer so, dass die gesamte Ausdehnung beider Eingaben erhalten bleibt.

- In Bereichen, in denen sich die Layer **überlappen**, werden neue Features erstellt, die die Attribute beider Layer tragen.
- In Bereichen, in denen **keine Überlappung** stattfindet, bleiben die Features erhalten, erhalten aber Null-Werte für die Attribute des jeweils anderen Layers.

Dieses Werkzeug ist nützlich, um eine umfassende Karte zu erstellen, die alle Variationen und Kombinationen von zwei Datensätzen zeigt.

## 2. Beispiel-Anwendungsfälle

- **Kombinierte Planung:** Zusammenführen von zwei verschiedenen Bebauungsplänen, um alle geplanten Flächennutzungen zu sehen.
- **Risikobewertung:** Kombination von Karten für Hitzeinseln und Karten für vulnerable Bevölkerungsgruppen, um alle Gebiete mit mindestens einem Risiko abzubilden.
- **Datenintegration:** Vereinigung von zwei Nachbarschaftskarten, um eine vollständige Abdeckung ohne Lücken zu gewährleisten.

## 3. Wie verwendet man das Werkzeug?

<div class="step">
  <div class="step-number">1</div>
  <div class="content">Klicken Sie auf <code>Toolbox</code> <img src={require('/img/icons/toolbox.png').default} alt="Options" style={{ maxHeight: "20px", maxWidth: "20px", objectFit: "cover"}}/>.</div>
</div>

<div class="step">
  <div class="step-number">2</div>
  <div class="content">Unter dem Menü <code>Geoverarbeitung</code> klicken Sie auf <code>Union</code>.</div>
</div>

<div class="step">
  <div class="step-number">3</div>
  <div class="content">Wählen Sie Ihren <code>Eingabe-Layer</code>.</div>
</div>

<div class="step">
  <div class="step-number">4</div>
  <div class="content">Wählen Sie Ihren <code>Vereinigungs-Layer</code>.</div>
</div>

<div class="step">
  <div class="step-number">5</div>
  <div class="content">Klicken Sie auf <code>Ausführen</code>. Das Ergebnis wird der Karte hinzugefügt.</div>
</div>
