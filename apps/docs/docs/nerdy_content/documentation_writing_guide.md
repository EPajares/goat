# Documentation Writing Guide

Standards and best practices for GOAT documentation.

## General Rules

### Writing Style
- **Focus on user benefits**, not tool names in the intro
- Use simple, direct language and shorter sentences
- `code` for buttons/fields, **Bold** for UI elements.
- Use the glossary.md to write the right terms from GOAT UI and to make the german translations.

### Images
- Center images with consistent styling (maxHeight: "400px")
- Use descriptive alt text

### Others

- Include glossary links: `[Join](./glossary.md#join)`
- Use info boxes for important notes: `:::info` and `:::tip`
- After the main title and before the explanation, add the Youtube video, if available, using the following iframe format and size:
 <iframe width="674" height="378" src="https://www.youtube.com/embed/VIDEO_ID" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>


## Page Types

### Toolbox Tools
```markdown
# Tool Name
Brief description highlighting **what users can accomplish**.

## 1. Explanation
Concise explanation of what the tool does and how it works.

## 2. Example use cases
- Simple, actionable examples
- Write simple use cases with action verbs

## 3. How to use the tool
Step-by-step instructions using the standard step format (use the glossary.md for terms).

### Results
What users get as output (within the "How to use the tool" section).

## 4. Technical details (optional)
Background for advanced users.
```

### Data Pages
```markdown
# Data Topic
Description focusing on **user understanding**.

## 1. Explanation
What this data concept means for users.

## 2. [Context-specific sections]
- Data types, formats, etc.
- Examples and use cases where relevant
```

### Workspace Pages
```markdown
# Workspace Feature
Description of **what users can do** with this feature.

## 1. Explanation
How this workspace feature works.

## 2. [Feature-specific sections]
- Interface overview
- Management options
- Configuration details
```

### Map/Interface Pages
```markdown
# Interface Element
Description of **functionality and purpose**.

## 1. Explanation
What this interface element does.

## 2. [Element-specific sections]
- Usage instructions
- Options and settings
- Examples
```

## Step Format
Use this standard format for all step-by-step instructions:
```markdown
<div class="step">
  <div class="step-number">1</div>
  <div class="content">Clear, actionable instruction.</div>
</div>
```