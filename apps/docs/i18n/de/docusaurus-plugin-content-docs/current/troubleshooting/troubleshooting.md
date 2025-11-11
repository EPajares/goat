---
sidebar_position: 10
slug: /troubleshooting
---

# Fehlerbehebung

Diese Seite hilft Ihnen bei Problemen oder Einschränkungen bei der Verwendung von GOAT, um diese einfacher zu lösen und mit Ihrer Analyse fortzufahren. 

:::tip INFO 
Zögern Sie nicht, uns für Unterstützung oder weitere Fragen [hier](https://plan4better.de/de/contact/ "hier") zu kontaktieren. 
:::

## Job-Fehler

Wenn Sie eine Analyse in einem Projekt ausführen, wird die Aufgabe in der Software als **Job** bezeichnet. Eine Fehlermeldung mit **Job-Fehler** bedeutet, dass die Aufgabe nicht ausgeführt werden konnte. Um mehr über die Ursache des Fehlers zu erfahren, überprüfen Sie bitte die [Statusleiste](workspace/home#statusleiste). Nachfolgend finden Sie häufige Ursachen für Job-Fehler und Vorschläge zu deren Behebung.

* Jobs dürfen eine Dauer von zwei Minuten nicht überschreiten. Es gibt außerdem eine Begrenzung für die Anzahl der Features, die für jeden Indikator analysiert werden können.
<div style={{ display: "flex", alignItems: "center" }}>
  <img 
    src={require('/img/troubleshooting/arrow-right.png').default} 
    alt="Layers" 
    style={{ maxHeight: "20px", maxWidth: "20px", objectFit: "cover", marginRight: "8px" }} 
  />
  <span>
    <strong>Sie können den  <a href="map/filter">Filter</a> verwenden, um Ihre Analyse in kleinere Ebenen zu unterteilen.</strong>
  </span>
</div>

  ![Filtern zur Berechnung größerer Flächen](/img/troubleshooting/filtering.jpg "Filtern zur Berechnung größerer Flächen")
  

 * Wenn Sie einen Indikator berechnen, das Ergebnis jedoch leer ist, wird kein Output generiert und ein Job-Fehler tritt auf. Beispiel: Wenn Sie den Indikator Abfahrten ÖPNV in einem Gebiet und einem Zeitraum verwenden, in dem keine Fahrten stattfinden, schlägt der Job mit dem Fehler fehl: **The Layer is None**.
<div style={{ display: "flex", alignItems: "center" }}>
  <img 
    src={require('/img/troubleshooting/arrow-right.png').default} 
    alt="Layers" 
    style={{ maxHeight: "20px", maxWidth: "20px", objectFit: "cover", marginRight: "8px" }} 
  />
  <span>
    <strong>Versuchen Sie, den räumlichen oder zeitlichen Bereich Ihrer Analyse zu erweitern.</strong>
  </span>
</div>


## Erreichbarkeitsindikatoren
### Heatmap - Durchschnitt Reisezeit
* Die Sensitivität einer Gaußschen Impedanzfunktion darf 1.000.000 nicht überschreiten.
<div style={{ display: "flex", alignItems: "center" }}>
  <img 
    src={require('/img/troubleshooting/arrow-right.png').default} 
    alt="Layers" 
    style={{ maxHeight: "20px", maxWidth: "20px", objectFit: "cover", marginRight: "8px" }} 
  />
  <span>
    <strong>Sie können die vorgeschlagenen Empfindlichkeiten in GOAT als Referenz verwenden.</strong>
  </span>
</div>
  
### Einzugsgebiet
* Die Startpunkte des Indikators müssen sich innerhalb von 100 m vom Straßennetz befinden.
<div style={{ display: "flex", alignItems: "center" }}>
  <img 
    src={require('/img/troubleshooting/arrow-right.png').default} 
    alt="Layers" 
    style={{ maxHeight: "20px", maxWidth: "20px", objectFit: "cover", marginRight: "8px" }} 
  />
  <span>
    <strong>Um Ihre Startpunkte auf der Karte genau festzulegen, können Sie das Netzwerk entweder direkt mit der Basiskarte oder mit der Straßennetzschicht im Szenario visualisieren.</strong>
  </span>
</div>
  

![Startpunkt der Streckenführung](/img/troubleshooting/routing_start.jpeg "Startpunkt der Streckenführung")



## Hochladen von Datensätzen

* Wenn Sie versuchen, einen Datensatz hochzuladen, der von GOAT nicht unterstützt wird, tritt ein Fehler auf. Siehe die autorisierten [Datensatztypen](data/dataset_types).
