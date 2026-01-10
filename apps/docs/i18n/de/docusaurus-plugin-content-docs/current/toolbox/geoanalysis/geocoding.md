---
sidebar_position: 5
---
import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';

# Geokodierung

Dieses Werkzeug ermöglicht es Ihnen, **Adressen aus einem Layer mit dem Pelias-Geokodierungsdienst zu geokodieren**.

## 1. Erklärung

Geokodierung ist der Prozess der **Umwandlung von Adressen (wie "Agnes-Pockels-Bogen 1, 80992 München, Germany") in geografische Koordinaten (Breiten- und Längengrad)**, die verwendet werden können, um Marker auf einer Karte zu platzieren. Dieses Werkzeug nimmt eine Tabelle oder einen Layer mit Adressfeldern und wandelt sie in räumliche Punktobjekte um.

## 2. Anwendungsbeispiele

- Visualisierung einer Liste von Kundenadressen auf einer Karte.
- Konvertierung einer CSV-Datei mit Geschäftsstandorten in einen räumlichen Datensatz.

## 3. Wie benutzt man das Werkzeug?

<div class="step">
  <div class="step-number">1</div>
  <div class="content">Klicken Sie auf <code>Werkzeuge</code> <img src={require('/img/icons/toolbox.png').default} alt="Options" style={{ maxHeight: "20px", maxWidth: "20px", objectFit: "cover"}}/>. </div>
</div>

<div class="step">
  <div class="step-number">2</div>
  <div class="content">Im Menü <code>Geoanalyse</code> klicken Sie auf <code>Geokodierung</code>.</div>
</div>

<div class="step">
  <div class="step-number">3</div>
  <div class="content">Wählen Sie die <code>Eingabe-Layer</code> mit den Adressdaten aus.</div>
</div>

<div class="step">
  <div class="step-number">4</div>
  <div class="content">Wählen Sie den Eingabemodus für Ihre Adressen:
    <ul>
      <li><code>Vollständige Adresse:</code> Verwenden Sie dies, wenn Sie eine einzelne Spalte mit vollständigen Adressen haben (z.B. "Marienplatz 1, München, Deutschland")</li>
      <li><code>Strukturiert:</code> Verwenden Sie dies, wenn Ihre Adresskomponenten in separaten Spalten stehen (Straße, Stadt, Postleitzahl, etc.)</li>
    </ul>
  </div>
</div>

<div class="step">
  <div class="step-number">5</div>
  <div class="content">Konfigurieren Sie die Adresszuordnung basierend auf Ihrem gewählten Eingabemodus:

<Tabs>
  <TabItem value="full-address" label="Vollständige Adresse" default>
    <ul>
      <li>Wählen Sie die Spalte aus, die die vollständige Adresse enthält</li>
    </ul>
  </TabItem>
  <TabItem value="structured" label="Strukturiert">
    <ul>
      <li>Wählen Sie das <code>Straßenadresse</code>-Feld für die Spalte mit Straßeninformationen</li>
      <li>Wählen Sie die <code>Postleitzahl</code> aus einer Spalte (optional)</li>
      <li>Wählen Sie die <code>Stadt</code> aus einer Spalte (optional)</li>
      <li>Wählen Sie das <code>Land</code> entweder aus einer Spalte oder setzen Sie einen konstanten Wert (Standard: "Deutschland")</li>
      <li>Durch Klicken auf <img src={require('/img/icons/options.png').default} alt="Options Icon" style={{ maxHeight: "25px", maxWidth: "25px", objectFit: "cover"}}/> <code>Erweiterte Optionen</code> können Sie das <code>Bundesland</code> aus einer Spalte auswählen (optional)</li>
    </ul>

:::tip Hinweis

Keines der Felder ist außer der Straßenadresse zwingend erforderlich, aber die Angabe von mehr Details verbessert die Genauigkeit der Geokodierung.

:::
  </TabItem>
</Tabs>
  </div>
</div>

<div class="step">
  <div class="step-number">6</div>
  <div class="content">Klicken Sie auf <code>Ausführen</code>, um den Geokodierungsprozess zu starten. Das Ergebnis wird zur Karte hinzugefügt.</div>
</div>
