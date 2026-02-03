# UI Component Library

RambotOS's unified UI component library, designed in VisionOS style, with all components performance-optimized using `React.memo`.

## Component List

### Button
Multipurpose button component, supporting various styles and sizes.

**Props:**
- `variant`: 'primary' | 'secondary' | 'ghost' | 'danger' (Default: 'primary')
- `size`: 'sm' | 'md' | 'lg' (Default: 'md')
- `disabled`: boolean
- `onClick`: Function
- `className`: string (Extra CSS classes)

**Example:**
```jsx
import { Button } from './components/ui';

<Button variant="primary" size="md" onClick={handleClick}>
    Confirm
</Button>

<Button variant="ghost" size="sm">
    Cancel
</Button>
```

---

### Card
Glassmorphism card container, suitable for grouping content.

**Props:**
- `title`: string (Optional title)
- `variant`: 'default' | 'dark' | 'light' (Default: 'default')
- `onClick`: Function (Optional, makes the card clickable)
- `className`: string

**Example:**
```jsx
import { Card } from './components/ui';

<Card title="System Status" variant="default">
    <p>All systems operational</p>
</Card>

<Card variant="dark" onClick={handleCardClick}>
    Click to view details
</Card>
```

---

### Input
Text input field, supporting various input types.

**Props:**
- `value`: string
- `onChange`: Function
- `placeholder`: string
- `type`: 'text' | 'password' | 'email' | 'number' (Default: 'text')
- `disabled`: boolean
- `onKeyPress`: Function
- `className`: string

**Example:**
```jsx
import { Input } from './components/ui';

<Input
    value={inputValue}
    onChange={(e) => setInputValue(e.target.value)}
    placeholder="Type a message..."
    onKeyPress={(e) => e.key === 'Enter' && handleSend()}
/>
```

---

### Modal
Full-screen modal with background blur effect.

**Props:**
- `isOpen`: boolean (Controls visibility)
- `onClose`: Function (Close callback)
- `title`: string (Optional title)
- `showCloseButton`: boolean (Default: true)
- `className`: string

**Features:**
- Close with ESC key
- Close by clicking background
- Automatic focus management

**Example:**
```jsx
import { Modal } from './components/ui';

<Modal
    isOpen={isModalOpen}
    onClose={() => setIsModalOpen(false)}
    title="Settings"
>
    <p>Modal content goes here</p>
</Modal>
```

---

## Usage Guide

### Importing Components

```jsx
// Single import
import { Button } from './components/ui';

// Multiple imports
import { Button, Card, Input, Modal } from './components/ui';
```

### Style Customization

All components support adding custom styles via the `className` prop:

```jsx
<Button className="mt-4 w-full">
    Custom Styled Button
</Button>
```

### Performance Optimization

All components are optimized with `React.memo` and only re-render when props actually change.

To maximize performance:
1. Wrap functions passed to components with `useCallback`
2. Cache complex calculations with `useMemo`
3. Avoid creating new objects or arrays in render

```jsx
// ✅ Good Practice
const handleClick = useCallback(() => {
    console.log('clicked');
}, []);

<Button onClick={handleClick}>Click Me</Button>

// ❌ Bad Practice
<Button onClick={() => console.log('clicked')}>Click Me</Button>
```

---

## Design Principles

1. **Consistency**: All components follow a unified VisionOS design language.
2. **Performance**: Optimized components to reduce unnecessary renders.
3. **Accessibility**: Supports keyboard navigation and screen readers.
4. **Responsive**: Adapts to different screen sizes.
5. **Extensible**: Easily customizable via `className` and other props.

---

## Roadmap

- [ ] Badge
- [ ] Tooltip
- [ ] Dropdown
- [ ] Switch
- [ ] Slider
- [ ] Progress
- [ ] Toast

---

## Contributing

When creating new components, please follow these guidelines:

1. Wrap the component with `React.memo`.
2. Use `useCallback` and `useMemo` for performance.
3. Add `displayName` for easier debugging.
4. Support the `className` prop for custom styles.
5. Add JSDoc comments to describe props.
6. Include usage examples in this README.
