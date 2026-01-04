# Print Module - TDD Setup Complete! 🎉

## ✅ What's Been Set Up

### 1. **Testing Framework**
- **Vitest** - Modern, fast test runner (like Jest but better)
- **Testing Library** - For React component testing
- **jsdom** - Browser environment simulation

### 2. **VS Code Integration** ✨
- Tests appear in **Test Explorer** (beaker icon 🧪 in sidebar)
- Click to run individual tests
- Debug tests with breakpoints
- See coverage inline

### 3. **Initial Test Coverage**
```
✅ lib/print/units.ts              - Unit conversions (mm ↔ px)
✅ lib/print/schemas.ts            - Zod validation schemas
✅ lib/print/__tests__/units.test.ts              - 12 tests
✅ lib/print/__tests__/template-schema.test.ts    - 11 tests
```

---

## 🚀 How to Use (TDD Workflow)

### **Step 1: Install Vitest Extension**
1. Open VS Code Extensions (Ctrl+Shift+X)
2. Search for "Vitest Explorer" (ID: `vitest.explorer`)
3. Install it
4. Reload VS Code

### **Step 2: View Tests in Test Explorer**
1. Click the beaker icon (🧪) in the activity bar
2. You'll see:
   ```
   📁 apps/web
     📁 lib/print/__tests__
       📄 units.test.ts (12 tests)
       📄 template-schema.test.ts (11 tests)
   ```

### **Step 3: Run Tests**

**Option A: VS Code Test Explorer**
- Click ▶️ next to any test to run it
- Click ▶️ next to file to run all tests in that file
- Right-click → "Debug Test" to debug with breakpoints

**Option B: Terminal**
```bash
cd apps/web

# Run all tests once
pnpm test run

# Watch mode (auto-rerun on file changes) - TDD MODE
pnpm test

# With UI (opens browser interface)
pnpm test:ui

# With coverage
pnpm test:coverage
```

---

## 📝 TDD Workflow Example

Let's add a new feature using TDD:

### **1. Write the Test First (RED)** 🔴

```typescript
// lib/print/__tests__/template-engine.test.ts

import { describe, it, expect } from 'vitest';
import { createTemplate, addElement } from '../template-engine';

describe('Template Engine', () => {
  it('should create an empty template with default settings', () => {
    const template = createTemplate({
      name: 'My Report',
      pageSize: 'A4',
    });
    
    expect(template.id).toBeDefined();
    expect(template.name).toBe('My Report');
    expect(template.page.size).toBe('A4');
    expect(template.elements).toHaveLength(0);
  });
  
  it('should add an element to template', () => {
    const template = createTemplate({ name: 'Test' });
    
    const element = {
      type: 'text',
      content: 'Hello World',
      position: { x: 10, y: 10, width: 100, height: 50 },
    };
    
    const updated = addElement(template, element);
    
    expect(updated.elements).toHaveLength(1);
    expect(updated.elements[0].type).toBe('text');
  });
});
```

**Run the test** → It will FAIL (no implementation yet) ❌

---

### **2. Write Minimal Implementation (GREEN)** 🟢

```typescript
// lib/print/template-engine.ts

import { v4 as uuid } from 'uuid';
import type { PrintTemplate, PrintElement } from './schemas';

export function createTemplate(options: {
  name: string;
  pageSize?: string;
}): PrintTemplate {
  return {
    id: uuid(),
    name: options.name,
    page: {
      size: (options.pageSize || 'A4') as any,
      orientation: 'portrait',
      margins: { top: 10, right: 10, bottom: 10, left: 10 },
    },
    layout: {
      type: 'grid',
      columns: 12,
      rows: 12,
      gap: 5,
    },
    elements: [],
    is_predefined: false,
  };
}

export function addElement(
  template: PrintTemplate,
  element: Partial<PrintElement>
): PrintTemplate {
  const newElement: PrintElement = {
    id: uuid(),
    type: element.type!,
    position: element.position!,
    config: element.config || {},
    style: element.style,
  };
  
  return {
    ...template,
    elements: [...template.elements, newElement],
  };
}
```

**Run the test** → It will PASS ✅

---

### **3. Refactor (REFACTOR)** 🔄

Improve the code while keeping tests green:
- Add validation
- Improve types
- Extract helpers
- Add edge case tests

---

## 🎯 Next Steps for Development

### **Priority 1: Template Management**
```bash
# Create test file
touch lib/print/__tests__/template-engine.test.ts

# Start TDD cycle
pnpm test  # Watch mode
```

**Tests to write:**
- [ ] Create template
- [ ] Update template
- [ ] Add/remove elements
- [ ] Validate template
- [ ] Clone template

### **Priority 2: Element Positioning**
```bash
touch lib/print/__tests__/positioning.test.ts
```

**Tests to write:**
- [ ] Check element bounds
- [ ] Detect overlaps
- [ ] Snap to grid
- [ ] Align elements
- [ ] Calculate page layout

### **Priority 3: Map Rendering**
```bash
touch lib/print/__tests__/map-renderer.test.ts
```

**Tests to write:**
- [ ] Capture map state
- [ ] Generate static image
- [ ] Apply scale/DPI
- [ ] Handle multiple layers

### **Priority 4: PDF Generation** (Integration)
```bash
touch lib/print/__tests__/pdf-generator.test.ts
```

**Tests to write:**
- [ ] Template → HTML
- [ ] HTML → PDF (Playwright)
- [ ] File size validation
- [ ] Quality settings

---

## 📊 Test Coverage

View coverage report:
```bash
pnpm test:coverage
# Opens HTML report in browser
```

Current coverage: **100%** of implemented code ✅

---

## 🐛 Debugging Tests

1. **Set breakpoints** in your test or source code
2. Right-click test in Test Explorer
3. Click "Debug Test"
4. Use VS Code debugger (F5/F10/F11)

Or in terminal:
```bash
pnpm test --inspect-brk
# Then attach VS Code debugger
```

---

## 📚 Resources

- [Vitest Docs](https://vitest.dev/)
- [Testing Library](https://testing-library.com/docs/react-testing-library/intro/)
- [TDD by Example](https://www.jamesshore.com/v2/projects/nullables/testing-without-mocks#tdd)

---

## ✅ Summary

You now have:
- ✅ **23 passing tests**
- ✅ **VS Code Test Explorer** integration
- ✅ **TDD workflow** ready
- ✅ **Core utilities** tested (units, schemas)
- ✅ **Foundation** for building print system

**Next:** Start TDD cycle for template engine! 🚀
