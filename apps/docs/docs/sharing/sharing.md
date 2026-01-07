---
sidebar_position: 1
---

# Teams & Members

Sharing datasets and projects allows for a more efficient workflow because **granting access to other members enables them to simultaneously edit and/or view your datasets or projects**. 

::::info
Sharing **does not duplicate** your data, only grants access to it.
::::



## Managing Teams and Members

<div class="step">
   <div class="step-number">1</div>
   <div class="content">Go to the <code>Settings</code> section.</div>
</div>

<div class="step">
   <div class="step-number">2</div>
   <div class="content">Click on a <code>Team</code> and <b>view the list of Teams</b> you are part of. Teams can represent departments or groups within your organization.</div>
</div>
<div class="step">
   <div class="step-number">3</div>
   <div class="content">Then click on the <code>Members</code> tab to <b>see the members and their roles</b>.</div>
</div>

<div class="step">
   <div class="step-number">4</div>
   <div class="content">If you are the <b>Owner</b> of the Organization, you can:
      <ul>
         <li>Click <code>+ New Member</code> to add a new member.</li>
         <li>Click the <code>More options</code> <img src={require('/img/icons/3dots.png').default} alt="More options" style={{ maxHeight: '20px', maxWidth: '20px', verticalAlign: 'middle'}}/> menu and then on <code>Delete</code> to remove a member</li>
      </ul>
   </div>
</div>

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/sharing/manage_team_members.gif').default} alt="Teams in GOAT" style={{ maxHeight: "750px", maxWidth: "750px", objectFit: "cover"}}/>
</div>
<p> </p>

:::important
When you share a dataset/project with a Team/Organization, all members will have access to it.
:::

---

## Managing access to a Dataset or Project

<div class="step">
   <div class="step-number">1</div>
   <div class="content">Click the <code>More options</code> <img src={require('/img/icons/3dots.png').default} alt="More options" style={{ maxHeight: '20px', maxWidth: '20px'}}/> menu on your dataset or project.</div>
</div>
<div class="step">
   <div class="step-number">2</div>
   <div class="content">Select <code>Share</code> and choose to share with an Organization or Team.</div>
</div>
<div class="step">
   <div class="step-number">3</div>
   <div class="content">Grant all members <code>viewer</code> or <code>editor</code> access as needed.</div>
</div>

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/sharing/share_project.gif').default} alt="Sharing Access in GOAT" style={{ maxHeight: "750px", maxWidth: "750px", objectFit: "cover"}}/>
</div>
<p> </p>


<div class="step">
   <div class="step-number">4</div>
   <div class="content">If you want to withdraw access, click the <code>More options</code> <img src={require('/img/icons/3dots.png').default} alt="More options" style={{ maxHeight: '20px', maxWidth: '20px'}}/> menu on your dataset or project and select <code>no access</code>.</div>
</div>

### Accessing Shared Items

You can find shared items in your workspace:

- **Projects shared with you**: <code>Workspace</code> → <code>Projects</code> → <code>Teams</code> / <code>Organizations</code>
  
- **Datasets shared with you**: <code>Workspace</code> → <code>Datasets</code> → <code>Teams</code> / <code>Organizations</code>


## Roles

See the table below to learn what each user can do within an Organization/Team and in a shared Dataset/Project:

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/sharing/sharing_roles_table.png').default} alt="Roles Table in GOAT" style={{ maxHeight: "Auto", maxWidth: "80%", objectFit: "cover"}}/>
</div>
<p> </p>

:::info Important

Deleting a dataset from a shared project **that you own** will cause it to be *deleted for other users as well*.
**As an editor** if you delete a dataset or (layer from the) project, the *owner will still have it in their personal dataset*.

:::