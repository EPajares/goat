---
sidebar_position: 3
---

# Add New Features

With your scenario active, it's time to add the hypothetical features that represent your planning proposal.

## Types of Scenario Edits

GOAT supports three types of edits:

<div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', justifyContent: 'center', marginBottom: '2rem' }}>
  <div style={{ textAlign: 'center' }}>
    <img src={require('/img/scenarios/add.png').default} alt="Add Features" style={{ height: "48px" }}/>
    <p><strong>Add</strong><br/>New features</p>
  </div>
  <div style={{ textAlign: 'center' }}>
    <img src={require('/img/scenarios/edit.png').default} alt="Edit Features" style={{ height: "48px" }}/>
    <p><strong>Modify</strong><br/>Existing features</p>
  </div>
  <div style={{ textAlign: 'center' }}>
    <img src={require('/img/scenarios/delete_feature.png').default} alt="Delete Features" style={{ height: "48px" }}/>
    <p><strong>Delete</strong><br/>Remove features</p>
  </div>
</div>

## Adding a New Point Feature

For our community center example:

### 1. Select the Editable Layer

Choose the POI or facilities layer you want to edit.

### 2. Enter Edit Mode

Click the **Edit** button or press `E` to enable editing.

### 3. Add a Point

1. Click **Add Feature** tool
2. Click on the map where you want the new facility
3. A form appears to enter attributes

### 4. Fill in Attributes

For a community center, enter:

| Attribute    | Value                  |
| ------------ | ---------------------- |
| Name         | "New Community Center" |
| Category     | "Community Facility"   |
| Capacity     | 500                    |
| Opening Year | 2027                   |

### 5. Save Changes

Click **Save** to commit your addition to the scenario.

## Adding Polygon Features

For buildings, parks, or zones:

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/scenarios/Polygon_drawing-final.gif').default} alt="Drawing Polygons" style={{ maxHeight: "400px", maxWidth: "100%", objectFit: "cover", borderRadius: "8px", boxShadow: "0 4px 12px rgba(0,0,0,0.15)"}}/>
  <p><em>Drawing polygon features in GOAT</em></p>
</div>

### Steps:
1. Select polygon drawing tool
2. Click to create vertices
3. Double-click to finish the shape
4. Fill in attribute form
5. Save

## Modifying Existing Features

Sometimes you need to change what already exists:

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/scenarios/modify_features.png').default} alt="Modifying Features" style={{ maxHeight: "300px", maxWidth: "100%", objectFit: "cover", borderRadius: "8px", boxShadow: "0 4px 12px rgba(0,0,0,0.15)"}}/>
  <p><em>Modifying existing features in a scenario</em></p>
</div>

**Common modifications:**
- Change facility capacity
- Update operating hours
- Relocate a feature
- Change land use type

## Editing the Street Network

For transport scenarios, you can modify the street network:

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/scenarios/street_network.png').default} alt="Street Network Editing" style={{ maxHeight: "400px", maxWidth: "100%", objectFit: "cover", borderRadius: "8px", boxShadow: "0 4px 12px rgba(0,0,0,0.15)"}}/>
  <p><em>Editing street network for transport scenarios</em></p>
</div>

**Possible edits:**
- Add new streets or bike paths
- Close streets to traffic
- Add pedestrian connections
- Modify speed limits

## Our Tutorial Scenario

For this tutorial, add:

1. **New Community Center** (Point)
   - Location: In an identified accessibility gap
   - Category: Community Facility
   
2. **Pedestrian Path** (Line) - Optional
   - Connect the center to nearby transit

## Verify Your Edits

Before running analysis:

- [ ] New features appear on the map
- [ ] Attributes are correctly filled
- [ ] Scenario is still active
- [ ] Changes are saved

## Next Step

Your scenario features are in place! Let's [run the comparative analysis](./compare-scenarios).

---

**Progress:** 2 of 4 steps completed
