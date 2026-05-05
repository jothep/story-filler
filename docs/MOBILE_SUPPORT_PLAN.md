# Mobile & Tablet Support Implementation Plan

**Date**: 2026-05-01  
**Goal**: Enable full functionality on mobile (iOS/Android) and tablet (iPad) devices  
**Current Status**: Desktop-only (mouse-based drag-and-drop)

---

## Problem Analysis

### Current Implementation

**Technology**: `@dnd-kit/core` v6.3.1

**Components**:
1. **WordList.jsx** - Draggable word buttons using `useDraggable`
2. **DroppableBlank.jsx** - Drop zones using `useDroppable`
3. **StoryPlayerUI.jsx** - DndContext with DragOverlay
4. **WordInteractionContext.jsx** - Drag event handlers

**Key Features to Preserve**:
- ✅ Visual feedback during drag (DragOverlay shows dragged word)
- ✅ Hover effect on drop zones (gray background when over blank)
- ✅ Correct placement (green border + word displayed)
- ✅ Wrong placement (red border + shake animation)
- ✅ Click to select word for tips (TriggerTips component)
- ✅ Filled blanks cannot be dropped on again

### Why It Doesn't Work on Mobile

1. **@dnd-kit/core limitations**:
   - Primarily designed for mouse events (`mousedown`, `mousemove`, `mouseup`)
   - Touch events (`touchstart`, `touchmove`, `touchend`) not fully supported
   - No native mobile sensors (accelerometer, pressure) integration

2. **Missing touch-specific handling**:
   - No touch event listeners on draggable items
   - No touch-based drag overlay positioning
   - No scroll behavior during touch drag

3. **CSS/Layout issues**:
   - Fixed layouts may not adapt to smaller screens
   - Touch targets may be too small (< 44px recommended)
   - Viewport scaling not optimized for mobile

---

## Solution: Hybrid Interaction Approach

### Strategy

Implement a **unified interaction system** that works across all devices:

1. **Desktop**: Mouse drag-and-drop (existing)
2. **Mobile/Tablet**: Touch tap-to-select-and-place OR touch drag-and-drop
3. **Universal**: Click/tap to select for tips (existing)

### Recommended Approach: Option A - Touch-Enabled Drag-and-Drop

Keep drag-and-drop metaphor but add touch support.

**Advantages**:
- Consistent UX across devices
- Preserves existing visual feedback
- Minimal learning curve for users

**Implementation**:
1. Add `@dnd-kit/modifiers` for touch support
2. Implement custom touch sensors
3. Add viewport detection and responsive CSS

---

## Technical Implementation Plan

### Phase 1: Add Touch Sensor to @dnd-kit

**Install touch support package**:
```bash
npm install @dnd-kit/modifiers
```

**Update StoryPlayerUI.jsx**:
```jsx
import {
  DndContext,
  DragOverlay,
  TouchSensor,
  MouseSensor,
  useSensor,
  useSensors,
} from '@dnd-kit/core';
import { restrictToWindowEdges } from '@dnd-kit/modifiers';

function StoryPlayerUI() {
  // Configure sensors for both mouse and touch
  const mouseSensor = useSensor(MouseSensor, {
    activationConstraint: {
      distance: 5, // 5px movement before drag starts (prevents accidental drags)
    },
  });

  const touchSensor = useSensor(TouchSensor, {
    activationConstraint: {
      delay: 250, // 250ms press before drag starts (prevents scroll conflicts)
      tolerance: 5, // 5px movement tolerance
    },
  });

  const sensors = useSensors(mouseSensor, touchSensor);

  return (
    <DndContext
      sensors={sensors}
      onDragStart={handleDragStart}
      onDragEnd={handleDragEnd}
      modifiers={[restrictToWindowEdges]} // Keep overlay within viewport
    >
      {/* ... rest of UI */}
    </DndContext>
  );
}
```

**Key Changes**:
- `TouchSensor`: Handles touch events (touchstart, touchmove, touchend)
- `activationConstraint.delay`: Prevents conflict with scroll gestures
- `restrictToWindowEdges`: Keeps drag overlay visible on small screens

---

### Phase 2: Responsive Layout Adjustments

**Current Layout Issues**:
- Fixed grid layout (`StoryPlayer.css`)
- Small touch targets
- No mobile breakpoints

**Solution: Add Mobile-First CSS**:

**Create `frontend/src/assets/StoryPlayer.mobile.css`**:
```css
/* Mobile devices (portrait phones, < 768px) */
@media (max-width: 767px) {
  .game-screen {
    grid-template-columns: 1fr; /* Single column */
    grid-template-rows: auto auto 1fr auto auto auto;
    grid-template-areas:
      "nav"
      "pic"
      "text"
      "list"
      "w-pic"
      "w-audio"
      "tips";
    gap: 0.5rem;
    height: auto;
    min-height: 100vh;
  }

  .layout-nav h1 {
    font-size: 1.2rem; /* Smaller title */
  }

  .layout-pic,
  .layout-w-pic {
    height: 200px; /* Fixed height for images */
  }

  .layout-text {
    min-height: 300px; /* Ensure text is readable */
  }

  /* Increase touch target size */
  .nes-btn {
    min-height: 44px;
    min-width: 120px;
    font-size: 0.9rem;
  }

  /* Word list: horizontal scrollable */
  .layout-list > div {
    flex-direction: row;
    overflow-x: auto;
    overflow-y: hidden;
  }
}

/* Tablets (portrait iPads, 768px - 1024px) */
@media (min-width: 768px) and (max-width: 1024px) {
  .game-screen {
    grid-template-columns: 1fr 2fr; /* Two columns */
    grid-template-rows: auto 1fr auto auto auto;
    grid-template-areas:
      "nav nav"
      "list text"
      "pic text"
      "w-pic w-audio"
      "tips tips";
    gap: 1rem;
  }

  .nes-btn {
    min-height: 48px; /* Larger for tablet */
  }
}

/* Prevent text selection during drag */
.dragging {
  user-select: none;
  -webkit-user-select: none;
  -moz-user-select: none;
  -ms-user-select: none;
}
```

**Update StoryPlayerUI.jsx to import mobile styles**:
```jsx
import '../assets/StoryPlayer.css';
import '../assets/StoryPlayer.mobile.css'; // Add this
```

---

### Phase 3: Enhance Touch Feedback

**Problem**: No visual feedback during touch drag on mobile.

**Solution**: Add haptic feedback and improved visual cues.

**Update WordList.jsx**:
```jsx
import { useDraggable, useDndContext } from '@dnd-kit/core';

function DraggableWordButton({ word }) {
  const { setSelectedWord } = useWordInteraction();
  const { attributes, listeners, setNodeRef, isDragging } = useDraggable({
    id: word.id,
  });

  const { active } = useDndContext();
  const isBeingDragged = active && active.id === word.id;

  // Haptic feedback on touch start
  const handleTouchStart = (e) => {
    if (listeners.onTouchStart) {
      listeners.onTouchStart(e);
    }
    // Trigger haptic feedback (iOS only)
    if (window.navigator && window.navigator.vibrate) {
      window.navigator.vibrate(50); // 50ms vibration
    }
  };

  const style = {
    width: 'auto',
    visibility: isBeingDragged ? 'hidden' : 'visible',
    opacity: isBeingDragged ? 0.5 : 1,
    transform: isBeingDragged ? 'scale(1.05)' : 'scale(1)',
    transition: 'transform 0.2s ease',
  };

  return (
    <button
      type="button"
      className="nes-btn"
      onClick={() => setSelectedWord(word)}
      ref={setNodeRef}
      style={style}
      {...attributes}
      {...listeners}
      onTouchStart={handleTouchStart}
    >
      {word.maori_word}
    </button>
  );
}
```

**Update DroppableBlank.jsx for better touch feedback**:
```jsx
function DroppableBlank({ blank, uniqueId, filledWord, isWrong }) {
  const { isOver, setNodeRef } = useDroppable({
    id: uniqueId,
    data: {
      type: 'blank',
      correctWordId: blank.word.id,
    },
    disabled: !!filledWord,
  });

  // ... existing color logic ...

  const style = {
    display: 'inline-block',
    margin: '0 0.25rem',
    minWidth: '150px',
    minHeight: '44px', // Ensure touch-friendly height
    verticalAlign: 'middle',
    backgroundColor: isOver ? colors.hover : 'transparent',
    borderRadius: '4px',
    border: `3px solid ${borderColor}`, // Thicker border for visibility
    color: textColor,
    animation: isWrong ? 'shake 0.5s' : 'none',
    padding: '0.5rem',
    textAlign: 'center',
    fontWeight: 'bold',
    fontSize: 'inherit',
    // Add pulse animation when hovering on mobile
    ...(isOver && {
      animation: 'pulse 0.5s ease-in-out',
    }),
  };

  return (
    <span ref={setNodeRef} style={style}>
      {filledWord ? filledWord.maori_word : null}
    </span>
  );
}
```

---

### Phase 4: Add Viewport Meta Tag

**Problem**: Mobile browsers may zoom incorrectly.

**Update `frontend/index.html`**:
```html
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no" />
    <!-- ^^^ Add this for mobile -->
    <title>Maori Story Filler</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>
```

**Attributes**:
- `width=device-width`: Match screen width
- `initial-scale=1.0`: No zoom on load
- `maximum-scale=1.0, user-scalable=no`: Prevent pinch-zoom during drag (optional)

---

### Phase 5: Add Device Detection Hook

**Create `frontend/src/hooks/useDeviceDetection.js`**:
```javascript
import { useState, useEffect } from 'react';

export function useDeviceDetection() {
  const [isMobile, setIsMobile] = useState(false);
  const [isTablet, setIsTablet] = useState(false);

  useEffect(() => {
    const checkDevice = () => {
      const width = window.innerWidth;
      const isTouchDevice = 'ontouchstart' in window || navigator.maxTouchPoints > 0;

      setIsMobile(width < 768 && isTouchDevice);
      setIsTablet(width >= 768 && width <= 1024 && isTouchDevice);
    };

    checkDevice();
    window.addEventListener('resize', checkDevice);

    return () => window.removeEventListener('resize', checkDevice);
  }, []);

  return { isMobile, isTablet, isDesktop: !isMobile && !isTablet };
}
```

**Usage in StoryPlayerUI.jsx**:
```jsx
import { useDeviceDetection } from '../hooks/useDeviceDetection';

function StoryPlayerUI() {
  const { isMobile, isTablet } = useDeviceDetection();

  // Adjust sensor activation based on device
  const touchSensorConfig = isMobile
    ? { delay: 150, tolerance: 5 } // Shorter delay on mobile
    : { delay: 250, tolerance: 5 }; // Longer delay on tablet

  const touchSensor = useSensor(TouchSensor, {
    activationConstraint: touchSensorConfig,
  });

  // ... rest of component
}
```

---

### Phase 6: Add Mobile-Specific Animations

**Create `frontend/src/assets/mobile-animations.css`**:
```css
/* Pulse animation for drop zones on mobile */
@keyframes pulse {
  0%, 100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.05);
  }
}

/* Enhanced shake animation for wrong attempts */
@keyframes shake {
  0%, 100% { transform: translateX(0); }
  10%, 30%, 50%, 70%, 90% { transform: translateX(-5px); }
  20%, 40%, 60%, 80% { transform: translateX(5px); }
}

/* Fade-in for drag overlay on mobile */
@keyframes fadeIn {
  from {
    opacity: 0;
    transform: scale(0.8);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

/* Mobile: Add visual feedback for dragging */
.mobile-drag-active {
  cursor: grabbing !important;
  animation: fadeIn 0.2s ease-in;
}

/* Desktop: Standard cursor */
.desktop-drag-active {
  cursor: move;
}

/* Prevent text selection during drag (all devices) */
body.dragging {
  user-select: none;
  -webkit-user-select: none;
  -moz-user-select: none;
  -ms-user-select: none;
}
```

**Update StoryPlayerUI.jsx to add body class during drag**:
```jsx
function StoryPlayerUI() {
  const handleDragStart = (event) => {
    document.body.classList.add('dragging');
    originalDragStart(event);
    // ... existing code
  };

  const handleDragEnd = (event) => {
    document.body.classList.remove('dragging');
    originalDragEnd(event);
    // ... existing code
  };

  // ... rest of component
}
```

---

## Alternative: Tap-to-Select-and-Place (Fallback Option)

If touch drag-and-drop proves unreliable, implement tap-based interaction:

### How It Works

1. **Tap word** → Word becomes "selected" (highlighted)
2. **Tap blank** → Selected word fills the blank
3. **Visual feedback**: Same as drag-and-drop

### Implementation

**Update WordInteractionContext.jsx**:
```jsx
export function WordInteractionProvider({ children, wordsInBank }) {
  const [selectedWord, setSelectedWord] = useState(null);
  const [selectedForPlacement, setSelectedForPlacement] = useState(null); // NEW
  const [filledBlanks, setFilledBlanks] = useState({});
  const [wrongAttempt, setWrongAttempt] = useState(null);

  // NEW: Handle tap-to-place
  function handleWordSelect(word) {
    setSelectedForPlacement(word);
    setSelectedWord(word); // Also show in tips
  }

  function handleBlankTap(uniqueBlankId, correctWordId) {
    if (!selectedForPlacement) return;

    if (selectedForPlacement.id === correctWordId) {
      setFilledBlanks((prev) => ({
        ...prev,
        [uniqueBlankId]: selectedForPlacement,
      }));
      setSelectedForPlacement(null);
      setWrongAttempt(null);
    } else {
      setWrongAttempt(uniqueBlankId);
    }
  }

  const value = {
    selectedWord,
    selectedForPlacement, // NEW
    handleWordSelect, // NEW
    handleBlankTap, // NEW
    filledBlanks,
    wrongAttempt,
    handleDragStart,
    handleDragEnd,
  };

  return (
    <WordInteractionContext.Provider value={value}>
      {children}
    </WordInteractionContext.Provider>
  );
}
```

**Update DroppableBlank.jsx**:
```jsx
function DroppableBlank({ blank, uniqueId, filledWord, isWrong }) {
  const { isOver, setNodeRef } = useDroppable({
    id: uniqueId,
    data: {
      type: 'blank',
      correctWordId: blank.word.id,
    },
    disabled: !!filledWord,
  });

  const { selectedForPlacement, handleBlankTap } = useWordInteraction();
  const { isMobile } = useDeviceDetection();

  const handleClick = () => {
    if (isMobile && selectedForPlacement && !filledWord) {
      handleBlankTap(uniqueId, blank.word.id);
    }
  };

  const isHighlighted = isMobile && selectedForPlacement && !filledWord;

  let borderColor = colors.default;
  if (filledWord) {
    borderColor = colors.correct;
  } else if (isWrong) {
    borderColor = colors.wrong;
  } else if (isHighlighted) {
    borderColor = '#ffd700'; // Gold color for tap target
  }

  const style = {
    // ... existing styles
    cursor: isMobile && selectedForPlacement ? 'pointer' : 'default',
    border: `3px solid ${borderColor}`,
  };

  return (
    <span ref={setNodeRef} style={style} onClick={handleClick}>
      {filledWord ? filledWord.maori_word : null}
    </span>
  );
}
```

---

## Testing Plan

### Device Testing Matrix

| Device | OS | Browser | Test Cases |
|--------|----|---------| ----------|
| iPhone 12+ | iOS 16+ | Safari | Drag, tap, scroll, rotate |
| Samsung Galaxy | Android 12+ | Chrome | Drag, tap, scroll, rotate |
| iPad Pro | iPadOS 16+ | Safari | Drag, tap, split-view |
| iPad Air | iPadOS 15+ | Chrome | Drag, tap, landscape |
| Desktop | macOS | Chrome/Safari/Firefox | Regression test |

### Test Cases

1. **Basic Drag-and-Drop**:
   - [ ] Touch and drag word to blank
   - [ ] Word appears in DragOverlay
   - [ ] Drop zone highlights on hover
   - [ ] Correct placement shows green
   - [ ] Wrong placement shows red + shake

2. **Touch Interactions**:
   - [ ] Long press activates drag (250ms)
   - [ ] Scroll doesn't trigger drag
   - [ ] Haptic feedback on drag start (iOS)
   - [ ] Drag overlay follows finger

3. **Layout**:
   - [ ] Portrait mode: single column
   - [ ] Landscape mode: appropriate grid
   - [ ] Rotation doesn't break layout
   - [ ] Text is readable (font size)
   - [ ] Touch targets are 44px+ height

4. **Edge Cases**:
   - [ ] Drag while scrolling
   - [ ] Multi-touch (two fingers)
   - [ ] Screen edge cases
   - [ ] Keyboard appearance (iOS)
   - [ ] Browser chrome shows/hides

5. **Performance**:
   - [ ] No lag during drag
   - [ ] Animations smooth (60fps)
   - [ ] No memory leaks
   - [ ] Works on older devices (2+ years old)

---

## Implementation Steps

### Week 1: Foundation
1. Install `@dnd-kit/modifiers`
2. Add TouchSensor to DndContext
3. Create mobile CSS file
4. Update viewport meta tag
5. Test on iOS simulator

### Week 2: Enhancements
1. Add device detection hook
2. Implement haptic feedback
3. Add mobile animations
4. Adjust touch target sizes
5. Test on Android emulator

### Week 3: Refinement
1. Add tap-to-place fallback
2. Test on real devices (iPhone, iPad, Android)
3. Fix edge cases
4. Performance optimization
5. Cross-browser testing

### Week 4: QA & Polish
1. User acceptance testing
2. Fix reported bugs
3. Update documentation
4. Deploy to staging
5. Production release

---

## Rollout Strategy

### Phase 1: Beta (1 week)
- Deploy to staging environment
- Invite 5-10 testers with mobile devices
- Collect feedback

### Phase 2: Gradual Rollout (1 week)
- Deploy to production
- Feature flag: Enable for 25% of mobile users
- Monitor error rates and user behavior
- Increase to 50%, then 100%

### Phase 3: Full Release
- Enable for all users
- Update architecture docs
- Add "Mobile-friendly" badge to landing page

---

## Success Metrics

- [ ] **Functionality**: 100% feature parity with desktop
- [ ] **Performance**: < 100ms drag latency on mid-range phones
- [ ] **Compatibility**: Works on iOS 15+, Android 11+
- [ ] **User Satisfaction**: > 80% completion rate on mobile
- [ ] **Error Rate**: < 5% failed drag attempts

---

## Risks & Mitigation

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Touch conflicts with scroll | High | High | Use activation delay (250ms) |
| DragOverlay off-screen on small phones | Medium | Medium | Use `restrictToWindowEdges` modifier |
| Performance on old devices | Medium | Low | Test on iPhone 8 / Galaxy S9 |
| Browser compatibility issues | Low | Low | Use polyfills, test all major browsers |

---

## Open Questions

1. Should we disable pinch-zoom during drag? (UX consideration)
2. Should tap-to-place be default on mobile, or drag-and-drop?
3. Do we need landscape-specific layouts?
4. Should we support split-screen multitasking (iPad)?

---

## Resources

- **@dnd-kit/core docs**: https://docs.dndkit.com/
- **Touch events MDN**: https://developer.mozilla.org/en-US/docs/Web/API/Touch_events
- **iOS Safari touch handling**: https://webkit.org/blog/5610/more-responsive-tapping-on-ios/
- **Android touch guide**: https://developer.android.com/guide/topics/ui/ui-events

---

## Next Steps

**Immediate Actions**:
1. Review this plan with team
2. Create GitHub issue for mobile support
3. Set up iOS/Android testing devices
4. Install @dnd-kit/modifiers package
5. Start Phase 1 implementation

**Timeline**: 4 weeks to full mobile support

---

**Document Owner**: Xiang Zhu  
**Last Updated**: 2026-05-01  
**Status**: Draft - Awaiting Approval
