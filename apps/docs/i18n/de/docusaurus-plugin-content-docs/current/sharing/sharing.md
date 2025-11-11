---
sidebar_position: 6
slug: /sharing
---

# Teilen

Das Teilen von Datensätzen und Projekten ermöglicht einen effizienteren Arbeitsablauf, da das Gewähren von Zugriff auf andere Mitglieder ihnen gleichzeitig erlaubt, **Ihre Datensätze oder Projekte zu bearbeiten und/oder anzusehen**.

::::info
Das Teilen **dupliziert nicht** Ihre Daten, sondern gewährt nur Zugriff darauf.
::::

## **Verwalten von Teams und Mitgliedern**

In den [Einstellungen](../workspace/settings.md) finden Sie die Teams, denen Sie angehören, und können die Mitglieder und deren Rolle sehen. Teams können Abteilungen innerhalb einer Organisation darstellen und es ermöglichen Ihnen, Mitglieder so zu gruppieren, wie es Ihrem Arbeitsablauf am besten entspricht.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/sharing/sharing_teams.png').default} alt="Übersicht über die Home-Oberfläche in GOAT" style={{ maxHeight: "750px", maxWidth: "750px", objectFit: "cover"}}/>
</div>
<p> </p>

Die <b>Besitzer oder Administratoren</b> einer <b>Organisation</b> können die Mitglieder in den [Einstellungen](../workspace/settings.md) einsehen und verwalten.

<p> </p>
<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/sharing/sharing_organization.png').default} alt="Übersicht über die Home-Oberfläche in GOAT" style={{ maxHeight: "750px", maxWidth: "750px", objectFit: "cover"}}/>
</div>
<p> </p>

:::important
Wenn Sie einen Datensatz oder ein Projekt mit einem Team oder einer Organisation teilen, haben alle Mitglieder Zugriff darauf.
:::

## **Teilen eines Datensatzes/Projekts**
Klicken Sie im Drei-Punkte-Menü <img src={require('/img/map/filter/3dots.png').default} alt="Optionen" style={{ maxHeight: "25px", maxWidth: "25px"}}/> auf Ihren Datensatz oder Ihr Projekt und teilen Sie es mit einer Organisation/einem Team und gewähren Sie allen Mitgliedern **Viewer**- oder **Editor**-Zugriff.

<p> </p>
<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/sharing/sharing_access.png').default} alt="Übersicht über die Home-Oberfläche in GOAT" style={{ maxHeight: "750px", maxWidth: "750px", objectFit: "cover"}}/>
</div>
<p> </p>

<p>
Sie finden die Liste der mit Ihnen geteilten Projekte unter <code>Workspace</code> --> <code>Projects</code> --> <code>Teams</code> / <code>Organizations</code> Abschnitte.</p>
Sie finden die Liste der mit Ihnen geteilten Datensätze unter <code>Workspace</code> -->  <code>Datasets</code> --> <code>Teams</code> / <code>Organizations</code> Abschnitte.

<p> </p>
<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/sharing/sharing_teamsandorg.png').default} alt="Übersicht über die Home-Oberfläche in GOAT" style={{ maxHeight: "750px", maxWidth: "750px", objectFit: "cover"}}/>
</div>

## **Zugriff entziehen**

Klicken Sie im Drei-Punkte-Menü <img src={require('/img/map/filter/3dots.png').default} alt="Optionen" style={{ maxHeight: "25px", maxWidth: "25px"}}/> auf Ihren Datensatz oder Ihr Projekt und wählen Sie <code>Teilen</code>, dann wählen Sie die Organisation/das Team und wählen <code>Kein Zugriff</code> aus dem Dropdown-Menü.

<p> </p>
<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/sharing/sharing_whitdraw.png').default} alt="Übersicht über die Home-Oberfläche in GOAT" style={{ maxHeight: "500px", maxWidth: "500px", objectFit: "cover"}}/>
</div>

## **Rollen**

Sehen Sie sich die Tabelle an, um zu erfahren, was jeder Benutzer innerhalb einer Organisation/eines Teams und in einem geteilten Datensatz/Projekt tun kann.

<p> </p>
<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/sharing/sharing_roles_table.png').default} alt="Übersicht über die Home-Oberfläche in GOAT" style={{ maxHeight: "Auto", maxWidth: "Auto", objectFit: "cover"}}/>
</div>
<p> </p>

:::info Wichtig

Das Löschen eines Datensatzes aus einem geteilten Projekt, **das Sie besitzen**, führt dazu, dass es *auch für andere Benutzer gelöscht wird*.

**Als Editor** können Sie, wenn Sie einen Datensatz oder eine (Ebene aus dem) Projekt löschen, den *Besitzer wird es weiterhin in seinem persönlichen Datensatz haben*.

:::
