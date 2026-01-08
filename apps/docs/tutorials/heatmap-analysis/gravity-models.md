---
sidebar_position: 2
---

# Understanding Gravity Models

Before running a heatmap analysis, let's understand the theory behind gravity-based accessibility modeling.

## What is a Gravity Model?

Gravity models in accessibility analysis are inspired by Newton's law of gravitation. The basic concept:

> **The attractiveness of a destination decreases with distance (or travel time)**

### The Formula

The accessibility score at any location is calculated as:

$$
A_i = \sum_{j} \frac{O_j}{f(t_{ij})}
$$

Where:
- $A_i$ = Accessibility at location $i$
- $O_j$ = Opportunities at destination $j$ (e.g., number of jobs, shops)
- $t_{ij}$ = Travel time from $i$ to $j$
- $f()$ = Impedance function (how distance affects attractiveness)

### Impedance Functions

GOAT supports several impedance functions:

| Function        | Behavior           | Best For                                |
| --------------- | ------------------ | --------------------------------------- |
| **Linear**      | Gradual decrease   | General analysis                        |
| **Exponential** | Sharp decay        | Short-distance trips                    |
| **Gaussian**    | Bell curve         | Peak attractiveness at certain distance |
| **Power**       | Customizable decay | Research applications                   |

## Real-World Example

Imagine you're analyzing access to supermarkets:

**Location A:** Has 3 supermarkets within 5 minutes walking
**Location B:** Has 1 supermarket at 3 minutes, 2 at 15 minutes

Even though both have access to 3 supermarkets, **Location A has better accessibility** because all stores are close by. The gravity model captures this nuance!

## Why This Matters for Planning

Gravity-based heatmaps help planners:

- 🎯 **Identify underserved areas** with poor accessibility
- 📊 **Quantify accessibility inequalities** across neighborhoods  
- 🏗️ **Evaluate new facility locations** before building
- 🔄 **Compare scenarios** to find optimal solutions

:::info Key Insight
Unlike simple "count within buffer" approaches, gravity models recognize that a nearby facility is more valuable than a distant one.
:::

## Next Step

Now that you understand the theory, let's [configure your heatmap analysis](./configure-heatmap)!

---

**Progress:** 1 of 4 steps completed
