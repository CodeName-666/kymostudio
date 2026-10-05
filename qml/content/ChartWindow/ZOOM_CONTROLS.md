# Chart Zoom Controls - User Guide

## 🎯 Overview

The chart now features modern, non-intrusive zoom controls that maximize your viewing area while providing powerful zoom capabilities.

---

## 🖱️ Zoom Methods

### 1. **Mouse Wheel Zoom** (Recommended)
- **Action:** Scroll mouse wheel over chart
- **Behavior:**
  - Scroll **UP** = Zoom IN (10% per scroll)
  - Scroll **DOWN** = Zoom OUT (10% per scroll)
  - **Smart**: Zooms centered on mouse cursor position
- **Best for:** Quick, precise zooming while analyzing data

### 2. **Toolbar Controls**
Located in the **top-right corner** of the chart:

| Button | Function | Description |
|--------|----------|-------------|
| **+** | Zoom In | Zoom in by 20% |
| **−** | Zoom Out | Zoom out by 25% |
| **⊡** | Reset Zoom | Return to initial view (0-10 range) |
| **⛶** | Fit to View | Auto-fit chart to show all data with 10% padding |

**Features:**
- Semi-transparent when not in use (opacity 30%)
- Full opacity on mouse hover
- Compact design: only 160×44 pixels
- Tooltips show keyboard shortcuts

### 3. **Pan (Drag)**
- **Action:** Click and drag **left mouse button**
- **Behavior:** Scroll chart horizontally and vertically
- **Best for:** Moving around in zoomed view

---

## ⌨️ Keyboard Shortcuts (Future Enhancement)

Planned shortcuts:
- `Ctrl` + `+` → Zoom In
- `Ctrl` + `−` → Zoom Out
- `Ctrl` + `0` → Reset Zoom
- `Ctrl` + `F` → Fit to View

---

## 🎨 Design Improvements

### Before:
- 2 large button panels (125×100px each)
- Always visible, blocking chart area
- Total obstruction: ~250×200 pixels

### After:
- 1 compact toolbar (160×44px)
- Semi-transparent, auto-hide on exit
- Total obstruction: **90% smaller**
- Professional, modern look

---

## 🔧 Technical Details

### Zoom Algorithm
```
Proportional Zoom:
- Maintains aspect ratio
- Centers on view center (toolbar) or mouse position (wheel)
- Smooth 10-25% increments

Fit-to-Data:
- Analyzes all data points across all graphs
- Calculates min/max bounds
- Adds 10% padding for visual clarity
```

### Files Modified
- `ChartWindowUi.ui.qml` - Removed old ZoomButtons, added ChartControls
- `ChartWindow.qml` - New zoom logic and mouse wheel handling
- `ChartControls.qml` - New compact toolbar component

---

## 💡 Tips

1. **For Detailed Analysis**: Use mouse wheel zoom - it's the most intuitive
2. **Lost in Zoom?**: Click **Reset** (⊡) button to return to default view
3. **Auto-Scale Data**: Click **Fit** (⛶) to automatically adjust to your data range
4. **Panning**: Left-drag to move around when zoomed in

---

## 🐛 Known Issues

- None currently reported

---

## 📝 Future Enhancements

- [ ] Keyboard shortcuts implementation
- [ ] Zoom history (undo/redo)
- [ ] Axis-specific zoom (X-only or Y-only)
- [ ] Minimap overview
- [ ] Touch gesture support

---

**Last Updated:** 2025-12-07
