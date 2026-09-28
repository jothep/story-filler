# Mobile Testing Guide - iPhone 14

**Date**: 2026-05-01  
**Changes Implemented**: Touch-enabled drag-and-drop support

---

## What Was Changed

### 1. Touch Sensor Added
- Long press (250ms) to activate drag
- Prevents conflict with scroll gestures
- Haptic feedback (vibration) on drag start

### 2. Responsive Layout
- Mobile CSS added for screens < 768px
- Vertical single-column layout
- Larger touch targets (44px minimum)

### 3. Visual Enhancements
- Thicker borders (3px) for better visibility
- Pulse animation when hovering over blanks
- Drag overlay constrained to screen edges

---

## How to Test on iPhone 14

### Setup Steps

1. **Start Local Dev Server**:
   ```bash
   cd frontend  # from the repository root
   npm run dev
   ```
   
2. **Find Your Local IP**:
   ```bash
   ifconfig | grep "inet " | grep -v 127.0.0.1
   ```
   Example output: `inet 192.168.1.100`

3. **Access from iPhone**:
   - Connect iPhone to same WiFi as Mac
   - Open Safari on iPhone
   - Go to: `http://192.168.1.100:5173`
   - (Replace IP with your actual IP from step 2)

### Alternative: Use Vite Network Mode

```bash
npm run dev -- --host
```
This will show:
```
  ➜  Local:   http://localhost:5173/
  ➜  Network: http://192.168.1.100:5173/
```
Use the Network URL on your iPhone.

---

## Test Cases

### ✅ Test 1: Touch Drag-and-Drop

**Steps**:
1. Navigate to a story (e.g., `/story/1`)
2. Long press (250ms) on a word in the word bank
3. Drag the word to a blank space
4. Release

**Expected Result**:
- Vibration on drag start ✓
- Word appears in drag overlay ✓
- Blank highlights when word hovers over it (gray background) ✓
- Correct word: green border, word fills blank ✓
- Wrong word: red border, shake animation ✓

**Common Issues**:
- If drag doesn't start: Press longer (full 250ms)
- If page scrolls instead: Try dragging more slowly after press

---

### ✅ Test 2: Layout Responsiveness

**Steps**:
1. View story page in portrait mode
2. Rotate to landscape mode
3. Rotate back to portrait

**Expected Result** (Portrait):
- Single column layout ✓
- Nav bar at top ✓
- Story picture below nav ✓
- Text area in middle ✓
- Word bank at bottom (horizontal scroll) ✓
- Word info at bottom ✓

**Expected Result** (Landscape):
- Grid layout (if screen height > 500px) ✓
- All elements visible without scrolling ✓

---

### ✅ Test 3: Touch Target Size

**Steps**:
1. Try tapping each word button
2. Try tapping navigation buttons (Prev/Next)
3. Try tapping "Complete Story" button

**Expected Result**:
- All buttons are easy to tap (no misses) ✓
- Minimum size: 44px height ✓
- No accidental taps on nearby elements ✓

---

### ✅ Test 4: Scroll Behavior

**Steps**:
1. Try scrolling the word bank (should scroll horizontally)
2. Try scrolling the text area (should scroll if content is long)
3. Try scrolling while a word is selected (should not start drag)

**Expected Result**:
- Scrolling works smoothly ✓
- No conflict between scroll and drag ✓
- Can't accidentally drag while scrolling ✓

---

### ✅ Test 5: Multiple Blanks

**Steps**:
1. Fill first blank correctly
2. Fill second blank incorrectly
3. Fill second blank correctly
4. Fill remaining blanks

**Expected Result**:
- Each blank works independently ✓
- Green blanks stay filled ✓
- Wrong attempts show shake animation ✓
- Can complete entire story ✓

---

### ✅ Test 6: Click-to-Select for Tips

**Steps**:
1. Tap (don't drag) a word button
2. Check if word info appears in "tips" area

**Expected Result**:
- Tapping still works for selecting word ✓
- Word picture/audio/definition shown ✓
- Doesn't conflict with drag gesture ✓

---

### ✅ Test 7: Edge Cases

**Test 7a: Drag Off-Screen**
- Drag word to edge of screen
- **Expected**: Overlay stops at screen edge ✓

**Test 7b: Drag to Already-Filled Blank**
- Try dragging to a green (filled) blank
- **Expected**: Nothing happens, blank stays green ✓

**Test 7c: Release Outside Drop Zone**
- Drag word, release over empty area
- **Expected**: Word returns to bank ✓

**Test 7d: Fast Drag**
- Quickly press and drag word
- **Expected**: Still activates after 250ms ✓

---

## Known Issues & Workarounds

### Issue 1: Safari Private Mode
**Problem**: Vibration may not work in Safari Private Mode  
**Workaround**: Test in regular Safari mode  
**Impact**: Low (vibration is optional feedback)

### Issue 2: iOS Double-Tap Zoom
**Problem**: Double-tapping might zoom page  
**Workaround**: Viewport meta tag prevents this  
**Status**: Should be fixed ✓

### Issue 3: Keyboard Appearance
**Problem**: iOS keyboard may appear if text input focused  
**Workaround**: No text inputs in story page  
**Impact**: None expected

---

## Performance Checklist

- [ ] Drag feels responsive (< 100ms latency)
- [ ] Animations are smooth (60fps)
- [ ] No lag when switching pages
- [ ] Page loads within 2 seconds
- [ ] No memory leaks (can play multiple stories)

---

## Debugging Tips

### If Drag Doesn't Work

1. **Check Console**:
   - Open Safari on iPhone
   - Connect to Mac via USB
   - Safari (Mac) → Develop → [Your iPhone] → [Page]
   - Check console for errors

2. **Check Touch Events**:
   ```javascript
   // Add to StoryPlayerUI.jsx temporarily
   console.log('Touch sensor config:', touchSensor);
   ```

3. **Reduce Activation Delay**:
   ```javascript
   // Try shorter delay for testing
   delay: 150, // instead of 250
   ```

### If Layout is Broken

1. **Check Screen Size**:
   - Safari → Develop → Enter Responsive Design Mode
   - Test different viewport sizes

2. **Check CSS Loading**:
   - View Source → Check if StoryPlayer.mobile.css is loaded

---

## Success Criteria

All test cases pass:
- ✅ Touch drag-and-drop works
- ✅ Layout adapts to portrait/landscape
- ✅ Touch targets are large enough
- ✅ Scrolling doesn't interfere with drag
- ✅ All visual feedback works (colors, animations)
- ✅ Performance is smooth

---

## Next Steps After Testing

### If Tests Pass ✅
1. Commit changes
2. Deploy to staging
3. Update architecture docs to support mobile

### If Tests Fail ❌
1. Document specific issue
2. Check console errors
3. Adjust sensor configuration
4. Re-test

---

## Quick Reference

**Long Press Duration**: 250ms  
**Touch Target Minimum**: 44px  
**Viewport Width (Mobile)**: < 768px  
**Haptic Feedback**: 50ms vibration  
**Animation**: Pulse on hover, shake on wrong

---

**Tester**: Xiang Zhu  
**Device**: iPhone 14  
**iOS Version**: (Check in Settings → General → About)  
**Browser**: Safari (default)
