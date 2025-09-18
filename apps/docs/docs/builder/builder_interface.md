---
sidebar_position: 1
---


# Builder Interface

Switching to Builder mode from Data mode will leady you to a map interface, where you can **create dashboards by adding widgets on panels, applying filters, and costumizing the layout.**

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
  <img src={require('/img/builder/builder_switch.gif').default} alt="switching_to_builder_mode" style={{ maxHeight: "auto", maxWidth: "auto", objectFit: "cover"}}/>
</div> 

## Interface Elements

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
  <img src={require('/img/builder/builder_interface.png').default} alt="overview_of_the_builder_interface" style={{ maxHeight: "auto", maxWidth: "auto", objectFit: "cover"}}/>
</div> 

### Panels

To add a widget to your dashboard you need to have **panels** first, you can arrange your widgets on its area. The left side panel will automatically appear when switching to the Builder mode.

<div> </div>

You can add new panels to any side of the map by clicking on the **"+" icon**.
You can further arrange the panels by **clicking on the arrow on the side of the panel**, which will then **expand the panel** to the full height or width of the map, depending on where the panel is located.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
  <img src={require('/img/builder/new_panel.gif').default} alt="Dragging a widget to the panel" style={{ maxHeight: "auto", maxWidth: "auto", objectFit: "cover"}}/>
</div> 

<div> </div>

 By *clicking on the panel itself*, the **Panel-Settings** will open up. You can freely **edit the panels anytime with or without widgets**. For better visualization, we recommend to have at least one [Widget](/builder/builder_interface.md#widgets) in the panel when editing its appearance.

<div> </div>

You can set the **panel style** as:
- **Default**, which will show the widgets with a *continous background and fills in the panel completely*
- **Rounded**, which also *keeps the widgets together on the continous background, but with rounded corners and leaves some space at the panel border*
- **Floating**, which will *show the widgets separately with rounded corner for each element*

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
  <img src={require('/img/builder/panel_options.gif').default} alt="Dragging a widget to the panel" style={{ maxHeight: "auto", maxWidth: "400px", objectFit: "cover"}}/>
</div> 

At the **Appearance** you can change the widget's:
- **Opacity**, where 0 is fully transparent, 1 is fully white
- **Background blur**, which ranges fromm 1 to 20
- **Shadow**, which ranges from 0 to 10

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
  <img src={require('/img/builder/panel_appearance.gif').default} alt="Dragging a widget to the panel" style={{ maxHeight: "auto", maxWidth: "400px", objectFit: "cover"}}/>
</div> 

In the **Position** you can set the:
- **Alignment** to the *Start*, *Center*, or to the *End* of the Panel
- **Spacing**, which ranges from 0 to 10. This will change the distance in between the widgets

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
  <img src={require('/img/builder/panel_position.gif').default} alt="Dragging a widget to the panel" style={{ maxHeight: "auto", maxWidth: "400px", objectFit: "cover"}}/>
</div> 


<div></div>
At the bottom you can <button>Delete</button> the panel completely, which will remove the consisting widgets as well. 


### Widgets

The widgets are the building blocks of your dashboard. You can **drag and drop** them from the right sidebar to any panel. Read more about the different types of widgets and how to use them in the [Widgets](builder/widgets.md) section.


<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
  <img src={require('/img/builder/widget_drag.gif').default} alt="Dragging a widget to the panel" style={{ maxHeight: "auto", maxWidth: "auto", objectFit: "cover"}}/>
</div> 

<div></div>

**Drag the chosen widget from the right sidebar to any panel** - you can **rearrange**, **remove** or **edit** them any time.

### Settings

In the settings you can **enable or disable Tools, Controls and the View options.**
Check out the [Settings](builder/settings.md) section for a more detailed explanation.

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
  <img src={require('/img/builder/interface_settings.png').default} alt="Dragging a widget to the panel" style={{ maxHeight: "auto", maxWidth: "auto", objectFit: "cover"}}/>
</div> 