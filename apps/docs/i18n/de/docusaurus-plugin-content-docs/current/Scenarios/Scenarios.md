---
sidebar_position: 4
---

import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';


# Szenarien

Szenarien **ermöglichen es Ihnen, "Was-wäre-wenn"-Situationen zu testen, indem Sie bestehende Layer modifizieren oder neue Features erstellen**. Fügen Sie Punkte, Linien und Polygone hinzu, bearbeiten oder löschen Sie sie, **und führen Sie dann Erreichbarkeitsindikatoren aus, um zu analysieren, wie sich diese Änderungen auf die Erreichbarkeit auswirken – alles ohne Ihre ursprünglichen Daten zu verändern**.

Sie können auch den **Straßennetz - Kanten** Basis-Layer modifizieren, der das Straßennetz darstellt und die Routing-Berechnungen beeinflusst.


:::info
Nur **geografische Layer** können in Szenarien modifiziert werden. Tabellen und Raster können nicht bearbeitet werden. Mehr zu [Datentypen](../data/data_types).
:::


## 1. Wie erstellt und bearbeitet man Szenarien?


<div class="step">
  <div class="step-number">1</div>
  <div class="content">Klicken Sie auf <code>Szenarien</code> <img src={require('/img/scenarios/compass-drafting.png').default} alt="Szenarien" style={{ maxHeight: "20px", maxWidth: "20px", objectFit: "cover"}}/>.</div>
</div>

<div class="step">
  <div class="step-number">2</div>
  <div class="content">Klicken Sie auf <code>Szenario erstellen</code> und benennen Sie Ihr Szenario.</div>
</div>

<div class="step">
  <div class="step-number">3</div>
  <div class="content">Klicken Sie auf <code>Weitere Optionen</code> <img src={require('/img/scenarios/3dots.png').default} alt="Optionen" style={{ maxHeight: "20px", maxWidth: "20px", objectFit: "cover"}}/> neben Ihrem Szenarionamen und wählen Sie dann <code>Bearbeiten</code>.</div>
</div>

<div class="step">
  <div class="step-number">4</div>
  <div class="content">Wählen Sie einen Layer in <code>Layer auswählen</code>, dann wählen Sie aus **Bearbeitungswerkzeuge**: <code>Zeichnen</code> <img src={require('/img/scenarios/add.png').default} alt="Zeichnen" style={{ maxHeight: "20px", maxWidth: "20px", objectFit: "cover"}}/>, <code>Modifizieren</code> <img src={require('/img/scenarios/edit.png').default} alt="Modifizieren" style={{ maxHeight: "20px", maxWidth: "20px", objectFit: "cover"}}/>, oder <code>Löschen</code> <img src={require('/img/scenarios/trash-solid.png').default} alt="Löschen" style={{ maxHeight: "20px", maxWidth: "20px", objectFit: "cover"}}/> von Features.
  </div>
</div>

<Tabs>
<TabItem value="Zeichnen" label="Zeichnen" default className="tabItemBox">

Abhängig vom Layer-Typ können Sie verschiedene geografische Formen zeichnen:

- `Punkt`: **Klicken Sie auf die Karte, wo Sie einen Punkt hinzufügen möchten**. Füllen Sie bei Bedarf Attribute aus und klicken Sie dann auf `Speichern`. **Neue Features erscheinen in blau**.

- `Linie`: **Klicken Sie, um mit dem Zeichnen zu beginnen, klicken Sie weiter, um die Linie zu formen, doppelklicken Sie zum Beenden**. Füllen Sie bei Bedarf Attribute aus und klicken Sie dann auf `Speichern`. **Neue Features erscheinen in blau**.

- `Polygon`: **Klicken Sie, um mit dem Zeichnen zu beginnen, klicken Sie weiter für jede Ecke, klicken Sie auf den Startpunkt, um zu vervollständigen**. Füllen Sie bei Bedarf Attribute aus und klicken Sie dann auf `Speichern`. **Neue Features erscheinen in blau**.

</TabItem>
  <TabItem value="Modifizieren" label="Modifizieren" default className="tabItemBox">

- **Klicken Sie auf ein Feature** , um es auszuwählen, bearbeiten Sie seine Attribute und klicken Sie dann auf `Speichern`. **Modifizierte Features erscheinen in gelb**.

</TabItem>

<TabItem value="Löschen" label="Löschen" default className="tabItemBox">

- **Klicken Sie auf das Feature**, das Sie entfernen möchten, und klicken Sie dann auf `Löschen`. **Gelöschte Features erscheinen in rot**.

</TabItem>

</Tabs>

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
  <img src={require('/img/scenarios/Polygon_drawing-final.gif').default} alt="Polygone zeichnen" style={{ maxHeight: '500px', maxWidth: '500px', objectFit: 'cover' }}/>
</div>


<div class="step">
  <div class="step-number">5</div>
  <div class="content">Klicken Sie auf `Werkzeugleiste` und wählen Sie einen <code>Erreichbarkeitsindikator</code>.</div>  
</div>
  
<div class="step">
  <div class="step-number">6</div>
  <div class="content">Nachdem Sie alle Einstellungen ausgewählt haben, wählen Sie das <code>Szenario</code> aus dem Dropdown-Menü, um Ihre Änderungen zu analysieren.</div>  
</div>

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
  <img src={require('/img/scenarios/scenario_indicator.png').default} alt="Layer-Analyse mit Szenarien" style={{ maxHeight: 'auto', maxWidth: 'auto', objectFit: 'cover' }}/>
</div>


## 2. Szenarien verwalten

Erstellen Sie mehrere Szenarien, um verschiedene Konfigurationen zu testen:

- **Auswählen**: Klicken Sie auf ein Szenario, um dessen Änderungen anzuzeigen
- **Modifizieren**: Verwenden Sie das Optionsmenü <img src={require('/img/scenarios/3dots.png').default} alt="Optionen" style={{ maxHeight: "20px", maxWidth: "20px", objectFit: "cover"}}/>, um umzubenennen, zu löschen oder zu bearbeiten
- **Änderungen verfolgen**: Modifizierte Layer zeigen <img src={require('/img/scenarios/compass-drafting.png').default} alt="Szenario-Indikator" style={{ maxHeight: "20px", maxWidth: "20px", objectFit: "cover"}}/> mit einer Zahl
- **Abwählen**: Klicken Sie erneut auf das aktive Szenario, um zur ursprünglichen Karte zurückzukehren


## 3. Straßennetz - Kanten

**Straßennetz - Kanten** ist ein Basis-Layer, der das [Straßennetz](../data/data_basis#street-network-and-topography) darstellt und in allen Projekten verfügbar ist. Sie können diesen Layer nur beim Bearbeiten von Szenarien bei hohen Zoom-Stufen sehen.


Verwenden Sie `Szenarien`, um Straßenlinien zu modifizieren – fügen Sie neue Straßen hinzu, schließen Sie bestehende oder ändern Sie Straßeneigenschaften.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
  <img src={require('/img/scenarios/street_network.png').default} alt="Drawing polygons" style={{ maxHeight: 'auto', maxWidth: '80%', objectFit: 'cover' }}/>
</div>
<p></p>

:::info
Änderungen am Straßennetz betreffen nur **[Einzugsgebiet](../further_reading/glossary#catchment-area)** Berechnungen. Andere Indikatoren verwenden das ursprüngliche Netzwerk.
:::
