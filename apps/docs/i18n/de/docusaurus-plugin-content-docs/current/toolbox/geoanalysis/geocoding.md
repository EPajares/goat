# Geokodierung

Dieses Werkzeug ermöglicht es Ihnen, **Adressinformationen in geografische Koordinaten (Punkte) umzuwandeln**. Es nutzt den Pelias-Geokodierungsdienst, um Textadressen auf der Karte zu verorten.

## 1. Erklärung

Geokodierung ist der Prozess, bei dem eine Beschreibung eines Ortes (wie eine Adresse oder ein Name eines Points of Interest) in numerische Koordinaten (Breiten- und Längengrad) umgewandelt wird.

GOAT ermöglicht es Ihnen, einen ganzen Layer mit Adressen (z.B. eine CSV-Datei mit einer Spalte "Adresse") zu geokodieren. Das Werkzeug erstellt für jeden gefundenen Ort einen Punkt.

## 2. Beispiel-Anwendungsfälle

- **Kundenanalyse:** Umwandeln einer Liste von Kundenadressen in Punkte auf einer Karte, um Cluster zu identifizieren.
- **Standortplanung:** Geokodieren potenzieller neuer Standorte für Filialen basierend auf deren Adressen.
- **Datenanreicherung:** Hinzufügen von geografischen Standorten zu einer bestehenden Datenbank von öffentlichen Einrichtungen.

## 3. Wie verwendet man das Werkzeug?

<div class="step">
  <div class="step-number">1</div>
  <div class="content">Klicken Sie auf <code>Toolbox</code> <img src={require('/img/icons/toolbox.png').default} alt="Options" style={{ maxHeight: "20px", maxWidth: "20px", objectFit: "cover"}}/>.</div>
</div>

<div class="step">
  <div class="step-number">2</div>
  <div class="content">Unter dem Menü <code>Geoanalyse</code> klicken Sie auf <code>Geocoding</code>.</div>
</div>

<div class="step">
  <div class="step-number">3</div>
  <div class="content">Wählen Sie Ihren <code>Eingabe-Layer</code>: Der Layer, der die Adressen enthält.</div>
</div>

<div class="step">
  <div class="step-number">4</div>
  <div class="content">Wählen Sie das <code>Adressfeld</code>: Die Spalte in Ihrem Layer, die die vollständige Adresse oder den Ortsnamen enthält.</div>
</div>

<div class="step">
  <div class="step-number">5</div>
  <div class="content">Klicken Sie auf <code>Ausführen</code>. Ein neuer Punkt-Layer mit den geokodierten Standorten wird erstellt.</div>
</div>
