---
sidebar_position: 2
---

# Data Types

GOAT supports various data types to handle different kinds of information in your datasets. Understanding these data types helps you work more effectively with your data and ensures optimal performance.

## Spatial Data Storage

GOAT uses a powerful combination of **PostgreSQ database with the PostGIS extension to handle spatial data**. Here's how it works:

- **Geometry Storage**: All spatial features (points, lines, polygons) are stored using the **PostGIS geometry type** in the **EPSG:4326** coordinate reference system
- **Accurate Calculations**: For precise distance and area measurements, GOAT uses the PostGIS geography type, which provides meter-based calculations with higher accuracy

## Supported Data Types

GOAT organizes data into specific types to optimize database performance and ensure scalability. Each data type has a maximum number of columns to maintain efficient processing:

| Data Type  | Description | Examples | Max Columns |
|------------|-------------|----------|-------------|
| **integer** | Whole numbers without decimal points | 1, 100, -5 | 15 |
| **bigint** | Very large whole numbers | Population counts, large IDs | 5 |
| **float** | Numbers with decimal points | 3.14, -0.001, 45.67 | 10 |
| **text** | Text and character data | Street names, categories, descriptions | 20 |
| **timestamp** | Date and time information | 2024-01-15 14:30:00 | 3 |
| **arrfloat** | Array of decimal numbers | [1.5, 2.7, 3.9] | 3 |
| **arrint** | Array of whole numbers | [1, 5, 10, 15] | 3 |
| **arrtext** | Array of text values | ["red", "green", "blue"] | 3 |
| **jsonb**    | Structured data in JSON format | `{"name": "value", "count": 42}` | 3 |
| **boolean** | True/false values | true, false | 3 |

:::info Why These Limits?
The column limits ensure optimal database performance and prevent system overload. If you need more columns of a specific type, consider splitting your data across multiple datasets or using array types for related values.
:::

## How to view Data Types

You can easily check the data types of your layer attributes:

<div class="step">
  <div class="step-number">1</div>
  <div class="content">Click on <img src={require('/img/map/filter/3dots.png').default} alt="Options" style={{ maxHeight: "25px", maxWidth: "25px", objectFit: "cover"}}/> <code>More Options</code> button on your layer</div>
</div>

<div class="step">
  <div class="step-number">2</div>
  <div class="content">Select <code>View Data</code> from the menu</div>
</div>

<div class="step">
  <div class="step-number">3</div>
  <div class="content">In the data table, you'll see the data type displayed above each column header</div>
</div>

<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/data/view-data-layer.png').default} alt="More Options" style={{ maxHeight: "auto", maxWidth: "auto", objectFit: "cover"}}/>
  <p style={{ textAlign: 'center', fontStyle: 'italic', marginTop: '8px', color: '#666' }}>Accessing the View Data option</p>
</div>



<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
  <img src={require('/img/data/data-table.png').default} alt="Data table showing attribute types" style={{ maxHeight: "auto", maxWidth: "auto", objectFit: "cover"}}/>
  <p style={{ textAlign: 'center', fontStyle: 'italic', marginTop: '8px', color: '#666' }}>Data table displaying attribute types above each column</p>
</div>

