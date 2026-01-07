---
sidebar_position: 4
---

# Glossar



### Erreichbarkeit
**Erreichbarkeit** wurde erstmals 1959 definiert als „das Potenzial an Interaktionsmöglichkeiten“, das sich auf die Leichtigkeit bezieht, mit der Menschen oder Güter von einem bestimmten Ort aus erreicht werden können ([Hansen, 1959](https://doi.org/10.1080/01944365908978307 "Visit Reference")). Im Kontext von GIS und Stadtplanung bezieht es sich auf die Leichtigkeit, mit der Menschen wesentliche Dienstleistungen wie Gesundheitseinrichtungen, Schulen oder Supermärkte erreichen können. 

Generell ist die Gewährleistung einer angemessenen Erreichbarkeit ein entscheidender Aspekt der Stadt- und Verkehrsplanung, da sie die Lebensqualität der Menschen und ihre Verkehrsentscheidungen maßgeblich beeinflusst. Erreichbarkeit kann durch verschiedene Indikatoren ausgedrückt werden, die darauf abzielen, die Verfügbarkeit in verschiedenen räumlichen Maßstäben und für verschiedene Verkehrsträger zu modellieren.

### Erreichbarkeitsinstrument
Ein **Erreichbarkeitsinstrument** ist ein Instrument zur Berechnung und Analyse der Erreichbarkeit eines bestimmten Ortes oder einer Region. Es berücksichtigt Faktoren wie Transportmöglichkeiten, Entfernung und Reisezeit, um festzustellen, wie leicht die Menschen Zugang zu wichtigen Dienstleistungen wie Gesundheitsversorgung und Bildung haben. Normalerweise basiert ein Erreichbarkeitsinstrument technisch auf GIS-Technologie, Routing-Algorithmen und verschiedenen Datenquellen.

### Aktive Mobilität
**Aktive Mobilität** bezieht sich auf die Nutzung von Fortbewegungsmitteln, die vom Menschen angetrieben werden, wie z. B. zu Fuß gehen und Radfahren. Sie ist ein wichtiger Bestandteil des nachhaltigen Verkehrs, da sie die Abhängigkeit vom Auto verringert und emissionsfrei ist. Aktive Mobilität hat auch viele gesundheitliche Vorteile, wie die Verringerung des Risikos von Fettleibigkeit und Herz-Kreislauf-Erkrankungen. 

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/literature/glossary/active_mobility_freepik.webp').default} alt="Active Mobility" style={{ mixBlendMode: 'multiply'}}/>
  <p style={{ textAlign: 'center' }}>Image: Designed by pch.vector / <a href="http://www.freepik.com">Freepik</a></p>
</div>


### Area of Interest (AOI)
Ein **Area of Interest (AOI)** ist eine bestimmte geografische Region oder Grenze, die für eine bestimmte Studie oder Analyse von besonderem Interesse oder Bedeutung ist. Dabei kann es sich um ein Wassereinzugsgebiet, einen Wald, einen Park oder ein anderes für die Studie relevantes geografisches Gebiet handeln. Die AOI wird in der Regel durch eine Reihe von Koordinaten oder eine polygonale Grenze definiert, die die Region von Interesse umfasst.

### Konnektivität
Die **Konnektivität** bezieht sich auf das Ausmaß, in dem Wege miteinander verbunden sind. Je höher die Pfad- und Schnittpunktdichte ist, desto höher ist die Konnektivität. Haupthindernisse für die Konnektivität sind z. B. Flüsse, Eisenbahnlinien und Autobahnen.

Die Konnektivität wirkt sich direkt auf die Erreichbarkeit aus, da sie entscheidend für die Reisezeit ist, um ein bestimmtes Ziel zu erreichen. Eine hohe Konnektivität ist besonders wichtig für aktive Verkehrsträger, da diese besonders empfindlich auf Umwege reagieren. Daher ist eine gute Anbindung der Schlüssel zur Gewährleistung der Erreichbarkeit zu Dienstleistungen und Einrichtungen und zur Förderung einer nachhaltigen Mobilität.  

### Geodaten

**Geodaten** beziehen sich auf Daten, die mit bestimmten geografischen Orten auf der Erdoberfläche verbunden sind. Diese Daten enthalten in der Regel Informationen wie Koordinaten, Attribute und manchmal sogar Metadaten über die dargestellten geografischen Merkmale. Geodaten werden in verschiedenen Anwendungen wie Kartierung, Navigation, Stadtplanung, Umweltüberwachung und anderen eingesetzt. Sie sind entscheidend für die Analyse und das Verständnis räumlicher Beziehungen und Muster in der realen Welt.

### H3-Gitter

Das **H3-Gitter** <img src={require('/img/literature/glossary/H3_grid_logo.webp').default} width="1000px" alt="H3 grid logo" style={{width: "100px", height: "170px", maxHeight: "50px", maxWidth: "50px", objectFit: "cover"}}/> 
ist ein geospatiales Indexierungssystem von [Uber Technologies](https://investor.uber.com/home/default.aspx "About Uber Technologies"), das die Erdoberfläche in ein hierarchisches Gitter aus hexagonalen Zellen unterteilt, um eine effizientere und genauere Darstellung und Analyse von Geodaten zu ermöglichen. Es verwendet einen hexagonalen Kachelansatz auf der Grundlage eines Ikosaeders, der eine hierarchische Struktur mit mehreren Auflösungen schafft. Die sechseckige Form ermöglicht eine äquidistante und konsistente räumliche Darstellung mit unterschiedlichen Auflösungen. Die Auflösung von H3-Gittern wird in der Regel durch die Kantenlänge des Sechsecks auf jeder Layer beschrieben. Bei der Auflösung 3 beispielsweise decken die Sechsecke ein relativ großes Gebiet ab (ca. 69 km Kantenlänge), das der Größe von Ländern oder großen Staaten/Provinzen entspricht, während die Sechsecke bei der Auflösung 10 (ca. 75 m Kantenlänge) viel kleiner sind und sich für lokalisierte Analysen eignen.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/literature/glossary/H3_grid.webp').default}  alt="H3 Grid" style={{ width: "600px", height: "200px", objectFit: "cover", mixBlendMode: 'multiply'}}/>
  <p style={{ textAlign: 'center' }}>Image: <a href="https://www.uber.com/en-TR/blog/h3/">UBER</a></p>
</div>

### Heatmap
Eine **Heatmap** ist eine grafische Visualisierungsform, die verschiedene Farben verwendet, um die unterschiedlichen Werte eines Datensatzes anzuzeigen. Dies ermöglicht ein schnelles Verständnis der dargestellten Daten. 

In GOAT verwenden wir - neben anderen Indikatoren - Heatmaps, um die lokale Erreichbarkeit verschiedener Einrichtungen, wie Cafés, Restaurants oder Supermärkte, zu analysieren. Die Heatmap verwendet eine Reihe von Farben, um verschiedene Erreichbarkeitswerte darzustellen. Durch die Analyse dieser Daten erhalten wir Einblicke in die Verteilung von Reisezielen und die Qualität der verfügbaren Infrastruktur.

### Indikator
Ein **Indikator** ist ein Mittel, um ein bestimmtes Attribut oder Thema quantitativ zu analysieren. In der Regel wird dazu ein standardisiertes Verfahren angewandt, z.B. durch die Verwendung einer Formel. In der Planung können Indikatoren verwendet werden, um die aktuelle Situation zu bewerten, um verschiedene Standorte miteinander zu vergleichen und um den Fortschritt bei der Erreichung bestimmter Ziele zu überwachen, z. B. bei der Verbesserung der Erreichbarkeit. 

### Isochrone
Eine **Isochrone** oder ein Einzugsgebiet ist ein Indikator, der angibt, wie weit Personen in einer bestimmten Zeit und mit einer bestimmten Geschwindigkeit von einem ausgewählten Ort aus reisen können. Isochronen können für jeden Verkehrsträger berechnet werden, z. B. zu Fuß, mit dem Fahrrad, mit dem Auto oder mit öffentlichen Verkehrsmitteln. Je nach gewähltem Verkehrsmittel wird das entsprechende Streckennetz verwendet. 

Weitere Informationen zur Isochronenberechnung finden Sie in unserer  [indicator documentation](../toolbox/accessibility_indicators/catchments "Isochrone documentation"). 


### Flächennutzung
**Flächennutzung** ist die Kategorisierung und Verwaltung von Land entsprechend seiner funktionalen Rolle innerhalb eines bestimmten Gebiets. Dies umfasst eine Reihe von Zwecken wie Wohnen, Gewerbe, Industrie oder Natur. Darüber hinaus umfasst die Flächennutzung auch Aspekte der Stadtplanung und des Umweltmanagements, da die Art der Flächennutzung Faktoren wie die Bevölkerungsdichte und die Verteilung von Zielen maßgeblich beeinflusst. Folglich hat die Flächennutzung einen direkten und erheblichen Einfluss auf die Erreichbarkeit, da sie die Verfügbarkeit von Dienstleistungen, die Verkehrsanbindung und die Lebensqualität eines Gebiets beeinflusst.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/literature/glossary/landuse.webp').default}  alt="Landuse" style={{ width: "350px", height: "300px", objectFit: "cover"}}/>
<p style={{ textAlign: 'center' }}>Image: <a href="https://accelerator.chathamhouse.org/article/land-use-challenges">Chatham House Sustainability Accelerator</a></p>
</div>


### Lokale Erreichbarkeit
**Lokale Erreichbarkeit**, auch bekannt als Erreichbarkeit auf Stadtteilebene, bezieht sich auf die Leichtigkeit, mit der Menschen wesentliche Dienstleistungen innerhalb eines bestimmten Stadtteils oder Gebiets erreichen können ([Handy, 1992](http://www.jstor.org/stable/23288518 "Visit Reference")). Sie bezieht sich in der Regel auf aktive Verkehrsmittel und konzentriert sich auf kurze Entfernungen.  

### Mikromobilität
**Mikromobilität** ist ein wachsender Trend im städtischen Verkehr, der kleine, leichte Fahrzeuge wie Elektroroller und Skateboards umfasst. Diese kompakten Verkehrsmittel bieten bequeme Lösungen für kurze Strecken.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/literature/glossary/micromobility_freepik.webp').default} 
  alt="Micromobility" style={{ width: "600px", height: "300px", mixBlendMode: 'multiply'}} />
  <p style={{ textAlign: 'center' }}>Image: Designed by pch.vector / <a href="http://www.freepik.com">Freepik</a></p>
</div>

### Open Source 
**Open source** <img src={require('/img/literature/glossary/open_source.webp').default} width="1000px" alt="opensource" style={{width: "100px", height: "170px", maxHeight: "50px", maxWidth: "50px", objectFit: "cover"}}/>  bezieht sich auf Software oder andere Produkte, die der Öffentlichkeit zur Verfügung gestellt werden und deren Quellcode frei zugänglich und veränderbar ist. Dies ermöglicht es Einzelpersonen und Organisationen, das Produkt nach Bedarf zu verändern und zu verbessern, ohne Einschränkungen bei der Nutzung oder Verbreitung. 

### Planning Support System (PSS)
Ein **Planning Support System** ist ein digitales Werkzeug zur Unterstützung des Planungs- und Entscheidungsprozesses für die Stadt- und Regionalentwicklung. Es nutzt Daten und Modelle, um Informationen zu verschiedenen Aspekten der Planung wie Flächennutzung, Verkehr und Umweltauswirkungen zu liefern. Ein PPS ermöglicht es den Planern, verschiedene Szenarien zu untersuchen und die möglichen Folgen ihrer Entscheidungen zu bewerten.  

### Points of Interest (POI)
Ein **Point of Interest (POI)** ist ein bestimmter Ort oder eine bestimmte Stelle, die in einem bestimmten Kontext, einer Studie oder Analyse von Bedeutung ist. Im Kontext von GOAT beziehen sich POIs hauptsächlich auf Einrichtungen des täglichen Bedarfs, wie Supermärkte, Kindergärten oder Restaurants. 

### Quantile Klassifikation
Die **Quantil-Klassifizierung** ist eine in Geografischen Informationssystemen (GIS) häufig verwendete Methode zur Einteilung von Daten in gleiche Gruppen auf der Grundlage ihrer Werte. Diese Methode ist nützlich für die Analyse und Visualisierung von Mustern in Daten und kann dabei helfen, Trends und Muster zu erkennen, die möglicherweise nicht so leicht zu erkennen sind. 

In GIS wird die Quantilklassifizierung häufig zur Erstellung von Choroplethen-Karten verwendet, d. h. von Karten, die verschiedene Werte einer Variablen farblich darstellen. Ein Beispiel: eine Choroplethenkarte der Bevölkerungsdichte einer Stadt. Die Karte wäre z. B. in fünf farbcodierte Kategorien unterteilt, wobei jede Kategorie einen anderen Bereich der Bevölkerungsdichte darstellt. 

Die Quantil-Klassifizierung kann für [attribute-based styling](../map/layer_style/style/attribute_based_styling) in GOAT verwendet werden. 

### Routing 
**Routing** <img src={require('/img/literature/glossary/routing_logo.webp').default} width="1000px" alt="routing" style={{width: "100px", height: "170px", maxHeight: "50px", maxWidth: "50px", objectFit: "cover"}}/> bezieht sich auf den Prozess der Suche nach dem schnellsten oder kürzesten Weg von einem Ort zum anderen. Dies wird häufig in der Verkehrsplanung und in Navigationssystemen verwendet, um Menschen dabei zu helfen, von Punkt A nach Punkt B zu gelangen, ist aber auch für die Analyse der Barrierefreiheit von entscheidender Bedeutung.

### Nachhaltigkeit  
**Nachhaltigkeit** <img src={require('/img/literature/glossary/sustainability.webp').default} width="1000px" alt="sustainability" style={{width: "100px", height: "200px", maxHeight: "50px", maxWidth: "100px", objectFit: "cover"}}/> bedeutet, die Bedürfnisse der Gegenwart zu befriedigen, ohne die Möglichkeiten künftiger Generationen zur Befriedigung ihrer eigenen Bedürfnisse zu beeinträchtigen. Dazu gehören die Verringerung der Kohlenstoffemissionen, die Förderung aktiver Mobilität und die Erhaltung der natürlichen Ressourcen. 

### Verkehrsmittel
**Verkehrsmittel** bezieht sich auf die Art des Verkehrsmittels, das für eine bestimmte Reise oder Fahrt verwendet wird. Dazu gehören Verkehrsmittel wie Bus, Bahn und U-Bahn, Radfahren (Pedelec, Fahrrad), Gehen und Autofahren. Die Wahl des Verkehrsträgers kann einen erheblichen Einfluss auf Faktoren wie Reisezeit, Kosten und Umweltbelastung haben. 

______________________________________________________________________________

### Referenzen
Hansen, W.G. (1959). How accessibility shapes land use. Journal of the American Institute of Planners. 25, 73–76.
https://doi.org/10.1080/01944365908978307 

Handy, S. L. (1992). Regional Versus Local Accessibility: Neo-Traditional Development and its Implications for Non-work Travel. Built Environment (1978-), 18(4), 253–267. http://www.jstor.org/stable/23288518 


