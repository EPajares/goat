---
sidebar_position: 3

---

# Public Transport

The **Public Transport Routing** in GOAT is essential for performing analyses that include public transport trips.

## 1. Objectives

Public transport routing facilitates **intermodal analysis** by integrating access and egress modes, such as walking or biking to and from the station. This is more complex than the other routing modes as it requires the merging of different datasets (such as sidewalks & bike lanes, public transport stops & schedules, etc.) and calculation approaches.

Public transport routing is used for indicators such as [Catchment Areas](../toolbox/accessibility_indicators/catchments) in GOAT.


## 2. Data

### Transit Data

Utilizes data in the **[GTFS](https://gtfs.org/)** (General Transit Feed Specification) format for static public transport network information (stops, routes, schedules, transfers, and more).


### Street Data

Incorporates street-level information from  **[OpenStreetMap](https://wiki.openstreetmap.org/)** to support multi-modal routing and real-world path connections (includes sidewalks, bike lanes, and crosswalks).


## 3. Technical Details

Public transport routing is performed using the **[R5 Routing Engine](https://github.com/conveyal/r5)** (_Rapid Realistic Routing on Real-world and Reimagined networks_). R5 is the routing engine from **[Conveyal](https://conveyal.com/)**, a web-based platform that allows users to create transportation scenarios and evaluate them in terms of cumulative opportunities and accessibility indicators.


### Routing Options

#### Modes

Analyses for the following modes of public transport are currently supported by GOAT. Choose between one or more, keeping in mind that some modes may not be available in all regions.

`bus` `tram` `rail` `subway` `ferry` `cable_car` `gondola` `funicular`

#### Travel time limit

The maximum journey duration to consider for public transport routing. A maxium of `90 min` is currently supported. This includes the time spent during access and egress from public transport stations.

#### Day

The day of the week to consider for public transport routing. Choose between `Weekday`, `Saturday` and `Sunday`. This is useful for evaluating changes in service between weekdays and weekends.

#### Start and End time

A time window for public transport routing. All the fastest journeys during this time window are considered, resulting in for example, the largest possible catchment area from your specified origin point. A journey is considered to fall within the time window solely based on its start time, regardless of its end time or duration.

#### Other (Default Configurations)

The following default configurations are used while performing public transport routing. They are not currently user-configurable.

- **Access Mode:** walk
- **Egress Mode:** walk
- **Decay function type:** logistic
- **Standard deviation:** 12 minutes
- **Width:** 10 minutes
- **Walk speed:** 5 km/h
- **Maximum walk time:** 20 minutes
- **Bike speed:** 15 km/h
- **Maximum bike time:** 20 minutes
- **Bike traffic stress:** 4
- **Maximum rides:** 4
- **Zoom level:** 9
- **Percentiles:** 1st
- **Monte Carlo draws:** 200