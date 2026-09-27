# PlotterApp - Floating Multi-Chart-Type System

**Version 2.0 COMPLETE REDESIGN**
Vollständige Umstellung auf Floating Windows mit Multi-Chart-Type Support

---

## 🎯 Projektziele

### Hauptziele:

1. ✅ **Vollständiges Floating Window System**
   - Jedes Chart ist ein frei bewegliches, größenveränderbares Fenster
   - Docking an Fensterränder möglich
   - Multi-Monitor Support
   - Speichern/Laden von Window-Layouts

2. ✅ **Multi-Chart-Type Architektur**
   - X/Y Charts (2D Line Charts) - Standard
   - X/Y/Z Charts (3D Surface/Scatter) - Neu
   - Erweiterbar für weitere Chart-Types (Bar, Pie, Heatmap, etc.)
   - Plugin-System für Custom Chart-Types

3. ✅ **Flexible Daten-Zuweisung**
   - ChartLines flexibel Charts zuweisen
   - Mehrere Lines pro Chart
   - Unterschiedliche Datenformate pro Chart-Type
   - Auto-Routing basierend auf Datenformat

---

## 🏗️ Neue Architektur-Übersicht

### Konzeptionelles Design:

```
PlotterApp (Root)
│
├── FloatingChartManager (NEU)
│   ├── ChartRegistry (verwaltet alle Charts)
│   ├── WindowLayoutManager (Positionen, Größen)
│   └── DockingSystem (Snap-to-edge)
│
├── ChartTypeFactory (NEU)
│   ├── XYChartType (2D Line/Scatter)
│   ├── XYZChartType (3D Surface/Scatter)
│   ├── BarChartType (optional)
│   └── CustomChartType (Plugin-Interface)
│
├── FloatingChartWindow (x N) (NEU)
│   ├── WindowChrome (Title, Minimize, Maximize, Close)
│   ├── ChartTypeRenderer (polymorphisch)
│   │   ├── XYRenderer → QtCharts.ChartView
│   │   ├── XYZRenderer → Qt3D.Scene3D
│   │   └── CustomRenderer → QQuickItem
│   ├── ChartControls (Zoom, Pan, Rotate für 3D)
│   └── DataBindings (Lines zu Renderer)
│
└── DataRouter (NEU)
    ├── ConnectionManager
    ├── DataParser
    └── ChartAssignmentEngine
```

---

## 📊 Chart-Type System Design

### Abstrakte Basis-Klasse:

```python
# python/Backend/Charts/base_chart.py

from abc import ABC, abstractmethod
from enum import Enum

class ChartType(Enum):
    XY_LINE = "xy_line"           # 2D Line Chart
    XY_SCATTER = "xy_scatter"     # 2D Scatter Plot
    XYZ_SURFACE = "xyz_surface"   # 3D Surface Plot
    XYZ_SCATTER = "xyz_scatter"   # 3D Scatter Plot
    BAR = "bar"                   # Bar Chart
    HEATMAP = "heatmap"           # 2D Heatmap
    CUSTOM = "custom"             # Custom Plugin

class BaseChart(ABC):
    """Abstract base class for all chart types"""

    def __init__(self, chart_id: str, name: str, chart_type: ChartType):
        self.chart_id = chart_id
        self.name = name
        self.chart_type = chart_type
        self.data_lines = {}  # {uniqueId: DataLine}
        self.visible = True
        self.window_state = WindowState()

    @abstractmethod
    def add_data_line(self, uniqueId: str, config: dict) -> bool:
        """Add a data line to this chart"""
        pass

    @abstractmethod
    def remove_data_line(self, uniqueId: str) -> bool:
        """Remove a data line from this chart"""
        pass

    @abstractmethod
    def append_point(self, uniqueId: str, point: DataPoint) -> bool:
        """Append a data point to a line"""
        pass

    @abstractmethod
    def get_required_dimensions(self) -> int:
        """Return number of dimensions required (2 for XY, 3 for XYZ)"""
        pass

    @abstractmethod
    def validate_data_point(self, point: DataPoint) -> bool:
        """Validate if data point is compatible with this chart type"""
        pass

    @abstractmethod
    def get_qml_component(self) -> str:
        """Return QML component path for this chart type"""
        pass
```

### Konkrete Implementierungen:

```python
# python/Backend/Charts/xy_chart.py

class XYLineChart(BaseChart):
    """2D Line Chart (standard PlotterApp chart)"""

    def __init__(self, chart_id: str, name: str):
        super().__init__(chart_id, name, ChartType.XY_LINE)
        self.axis_x_min = 0
        self.axis_x_max = 10
        self.axis_y_min = 0
        self.axis_y_max = 10

    def get_required_dimensions(self) -> int:
        return 2  # X, Y

    def validate_data_point(self, point: DataPoint) -> bool:
        return hasattr(point, 'x') and hasattr(point, 'y')

    def get_qml_component(self) -> str:
        return "qrc:/qt/qml/content/ChartTypes/XYChart.qml"

# python/Backend/Charts/xyz_chart.py

class XYZScatterChart(BaseChart):
    """3D Scatter Plot"""

    def __init__(self, chart_id: str, name: str):
        super().__init__(chart_id, name, ChartType.XYZ_SCATTER)
        self.axis_x_min = 0
        self.axis_x_max = 10
        self.axis_y_min = 0
        self.axis_y_max = 10
        self.axis_z_min = 0
        self.axis_z_max = 10
        self.camera_position = (10, 10, 10)
        self.rotation = (0, 0, 0)

    def get_required_dimensions(self) -> int:
        return 3  # X, Y, Z

    def validate_data_point(self, point: DataPoint) -> bool:
        return hasattr(point, 'x') and hasattr(point, 'y') and hasattr(point, 'z')

    def get_qml_component(self) -> str:
        return "qrc:/qt/qml/content/ChartTypes/XYZChart.qml"
```

---

## 🪟 Floating Window System Design

### Window Manager:

```python
# python/Backend/Windows/window_manager.py

from dataclasses import dataclass
from typing import Dict, List, Optional

@dataclass
class WindowState:
    """Window position and size state"""
    x: int = 100
    y: int = 100
    width: int = 800
    height: int = 600
    minimized: bool = False
    maximized: bool = False
    docked: Optional[str] = None  # "left", "right", "top", "bottom", None
    monitor_id: int = 0
    z_index: int = 0

class FloatingWindowManager:
    """Manages all floating chart windows"""

    def __init__(self):
        self._windows: Dict[str, WindowState] = {}
        self._focus_stack: List[str] = []  # Z-order

    def create_window(self, chart_id: str, initial_state: Optional[WindowState] = None) -> WindowState:
        """Create new floating window"""
        state = initial_state or WindowState()
        state.z_index = len(self._windows)
        self._windows[chart_id] = state
        self._focus_stack.append(chart_id)
        return state

    def remove_window(self, chart_id: str) -> bool:
        """Remove floating window"""
        if chart_id in self._windows:
            del self._windows[chart_id]
            self._focus_stack.remove(chart_id)
            return True
        return False

    def update_window_state(self, chart_id: str, state: WindowState) -> bool:
        """Update window position/size"""
        if chart_id in self._windows:
            self._windows[chart_id] = state
            return True
        return False

    def bring_to_front(self, chart_id: str) -> None:
        """Bring window to front (Z-order)"""
        if chart_id in self._focus_stack:
            self._focus_stack.remove(chart_id)
            self._focus_stack.append(chart_id)
            # Update z-indices
            for i, wid in enumerate(self._focus_stack):
                self._windows[wid].z_index = i

    def dock_window(self, chart_id: str, edge: str) -> bool:
        """Dock window to screen edge"""
        if chart_id not in self._windows:
            return False

        state = self._windows[chart_id]
        state.docked = edge

        # Calculate docked position/size
        if edge == "left":
            state.x = 0
            state.y = 0
            state.width = 400  # Half screen
            state.height = 1080  # Full height
        # ... similar for right, top, bottom

        return True

    def save_layout(self, filename: str) -> None:
        """Save window layout to file"""
        layout = {
            chart_id: {
                "x": state.x,
                "y": state.y,
                "width": state.width,
                "height": state.height,
                "docked": state.docked,
                "z_index": state.z_index
            }
            for chart_id, state in self._windows.items()
        }
        with open(filename, 'w') as f:
            json.dump(layout, f, indent=2)

    def load_layout(self, filename: str) -> None:
        """Load window layout from file"""
        with open(filename, 'r') as f:
            layout = json.load(f)

        for chart_id, state_dict in layout.items():
            self._windows[chart_id] = WindowState(**state_dict)
```

---

## 🔧 Datenformat-Erweiterung

### Extended Protocol:

```python
# python/Receiver/message.py

from dataclasses import dataclass
from typing import Optional

@dataclass
class PlotDataPoint:
    """Extended data point with optional Z coordinate"""
    id: int  # 0-255
    value: float  # Y coordinate
    timestamp: Optional[float] = None  # X coordinate
    z_value: Optional[float] = None  # Z coordinate (for 3D charts)

    def get_dimensions(self) -> int:
        """Return number of dimensions in this data point"""
        if self.z_value is not None:
            return 3  # X, Y, Z
        return 2  # X, Y
```

### Embedded Protocol Extension:

```cpp
// ../PlotterEcu/lib/PlotterLib/src/plotter.h

// Neue send() Methode für 3D Daten
void send(uint8_t channelId, float yValue, float zValue, uint32_t currentTimeMs);
void send(uint8_t channelId, float yValue, float zValue, float timestamp);

// JSON Format:
// {"id":0,"value":25.5,"z":10.2,"timestamp":1.234}
```

### Backend Parser Extension:

```python
# python/Backend/backend.py

def _parse_data_point(self, interface: str, payload: bytes) -> PlotDataPoint | None:
    """Parse with optional Z coordinate"""
    # ...
    if isinstance(decoded, dict):
        data_id = decoded.get("id")
        value = decoded.get("value")  # Y
        timestamp = decoded.get("timestamp")  # X
        z_value = decoded.get("z")  # Z (optional)

        return PlotDataPoint(
            id=data_id,
            value=float(value),
            timestamp=float(timestamp) if timestamp else None,
            z_value=float(z_value) if z_value else None
        )
```

---

## 📋 VOLLSTÄNDIGER IMPLEMENTIERUNGS-TASKPLAN

### 🏃 Phase 1: Basis-Architektur (3-4 Wochen)

#### Woche 1: Backend Fundament

**Task 1.1: Chart-Type System**
- [ ] `BaseChart` abstrakte Klasse implementieren
- [ ] `ChartType` Enum definieren
- [ ] `XYLineChart` Implementierung
- [ ] `ChartFactory` für Chart-Erstellung
- [ ] Unit Tests für Chart-Types

**Task 1.2: Window Manager**
- [ ] `WindowState` Dataclass
- [ ] `FloatingWindowManager` Klasse
- [ ] Z-Order Verwaltung
- [ ] Docking-Logik
- [ ] Layout Save/Load

**Task 1.3: Data Point Extension**
- [ ] `PlotDataPoint` um `z_value` erweitern
- [ ] Parser für 3D-Daten
- [ ] Validierung nach Dimensions
- [ ] Embedded Protocol updaten (`plotter.h`)

#### Woche 2: QML Floating Window System

**Task 1.4: FloatingChartWindow Component**
- [ ] `FloatingChartWindow.qml` erstellen
- [ ] Custom Window Chrome (Title, Buttons)
- [ ] Drag & Drop Movement
- [ ] Resize Handles
- [ ] Minimize/Maximize/Close Logic

**Task 1.5: Window Manager Integration**
- [ ] QML ↔ Python Bindings
- [ ] Window Position Sync
- [ ] Z-Order Management in QML
- [ ] Focus Handling

**Task 1.6: Docking System**
- [ ] Snap-to-Edge Detection
- [ ] Docking Indicators (Visual Feedback)
- [ ] Undock Functionality
- [ ] Edge Alignment

#### Woche 3: Chart Type Renderer System

**Task 1.7: Polymorphic Chart Rendering**
- [ ] `ChartTypeRenderer.qml` Interface
- [ ] `XYChartRenderer.qml` (QtCharts)
- [ ] Dynamic Component Loading
- [ ] Renderer Factory Pattern in QML

**Task 1.8: Chart Controls Abstraction**
- [ ] Universal Zoom/Pan Interface
- [ ] Chart-Type Specific Controls
- [ ] Keyboard Shortcuts
- [ ] Mouse/Touch Gestures

**Task 1.9: Integration Testing**
- [ ] Create Multiple Floating XY Charts
- [ ] Test Window Movement
- [ ] Test Docking
- [ ] Test Layout Save/Load

#### Woche 4: Data Routing & Assignment

**Task 1.10: Smart Data Router**
- [ ] Auto-detect Chart-Type von Daten
- [ ] Line-to-Chart Assignment UI
- [ ] Default Chart Creation
- [ ] Multi-Chart Data Distribution

**Task 1.11: Migration from Old System**
- [ ] Alte `ChartWindow.qml` deprecate
- [ ] `ChartContainer.qml` entfernen
- [ ] Backward Compatibility Layer
- [ ] Migration Tool für alte Configs

---

### 🚀 Phase 2: 3D Chart Support (3-4 Wochen)

#### Woche 5-6: 3D Chart Backend

**Task 2.1: XYZScatterChart Implementation**
- [ ] `XYZScatterChart` Klasse
- [ ] 3D Data Structures
- [ ] Camera & Rotation State
- [ ] Axis Management (X, Y, Z)

**Task 2.2: XYZSurfaceChart Implementation**
- [ ] `XYZSurfaceChart` Klasse
- [ ] Grid-basierte Daten
- [ ] Surface Interpolation
- [ ] Mesh Generation Logic

**Task 2.3: 3D Data Processing**
- [ ] Batch Point Processing
- [ ] Surface Grid Building
- [ ] Performance Optimization
- [ ] Memory Management

#### Woche 7-8: 3D Chart QML/Qt3D

**Task 2.4: Qt3D Integration**
- [ ] Qt3D Module Setup
- [ ] `XYZChartRenderer.qml` mit Scene3D
- [ ] 3D Scatter Plot Renderer
- [ ] 3D Surface Plot Renderer

**Task 2.5: 3D Controls**
- [ ] Camera Controls (Orbit, Pan, Zoom)
- [ ] Rotation via Mouse Drag
- [ ] Touch Gestures für Mobile
- [ ] Reset Camera Button

**Task 2.6: 3D Visual Enhancements**
- [ ] Axis Labels in 3D
- [ ] Grid Lines
- [ ] Lighting Setup
- [ ] Material/Shader Config

**Task 2.7: Performance Optimization**
- [ ] Level-of-Detail (LOD)
- [ ] Frustum Culling
- [ ] Point Cloud Decimation
- [ ] GPU Instancing für viele Points

---

### 🎨 Phase 3: UI/UX Polish (2 Wochen)

#### Woche 9: Advanced Window Features

**Task 3.1: Window Snapping**
- [ ] Magnetic Snapping zwischen Windows
- [ ] Grid Snapping (optional)
- [ ] Smart Layout Suggestions
- [ ] Quick-Tile Shortcuts (Win+Arrow)

**Task 3.2: Window Persistence**
- [ ] Auto-Save Layout on Exit
- [ ] Workspace Profiles
- [ ] Named Layout Presets
- [ ] Import/Export Layouts

**Task 3.3: Multi-Monitor Support**
- [ ] Monitor Detection
- [ ] Cross-Monitor Drag
- [ ] Per-Monitor DPI Scaling
- [ ] Fullscreen auf Second Monitor

#### Woche 10: Chart Management UI

**Task 3.4: Chart Gallery / Overview**
- [ ] Thumbnail View aller Charts
- [ ] Quick Switch zwischen Charts
- [ ] Mini-Map für große Layouts
- [ ] Search/Filter Charts

**Task 3.5: Chart Creation Wizard**
- [ ] Step-by-Step Chart Creation
- [ ] Template Selection (2D, 3D, etc.)
- [ ] Data Source Selection
- [ ] Visual Preview

**Task 3.6: Context Menus**
- [ ] Right-Click auf Window
- [ ] Chart-Type Conversion
- [ ] Duplicate Chart
- [ ] Export Chart (PNG, SVG)

---

### 🔌 Phase 4: Plugin System (2 Wochen)

#### Woche 11: Plugin Architecture

**Task 4.1: Plugin Interface**
- [ ] `IChartPlugin` Interface definieren
- [ ] Plugin Manifest Format (JSON)
- [ ] Plugin Discovery/Loading
- [ ] Plugin Lifecycle Management

**Task 4.2: Plugin API**
- [ ] Data Access API
- [ ] Rendering API (QML Components)
- [ ] Event System
- [ ] Settings API

**Task 4.3: Example Plugins**
- [ ] Heatmap Chart Plugin
- [ ] Bar Chart Plugin
- [ ] Pie Chart Plugin
- [ ] Custom Widget Plugin

#### Woche 12: Plugin UI Integration

**Task 4.4: Plugin Manager UI**
- [ ] Installed Plugins List
- [ ] Enable/Disable Plugins
- [ ] Plugin Settings Dialog
- [ ] Plugin Marketplace (optional)

**Task 4.5: Custom Chart Type Registration**
- [ ] Runtime Chart-Type Registration
- [ ] Plugin QML Component Loading
- [ ] Plugin Resource Management
- [ ] Hot-Reload für Development

---

### 🧪 Phase 5: Testing & Optimization (2 Wochen)

#### Woche 13: Comprehensive Testing

**Task 5.1: Unit Tests**
- [ ] Backend Chart-Type Tests
- [ ] Window Manager Tests
- [ ] Data Router Tests
- [ ] Plugin System Tests

**Task 5.2: Integration Tests**
- [ ] Multi-Window Scenarios
- [ ] 2D + 3D Charts zusammen
- [ ] High-Frequency Data Streams
- [ ] Memory Leak Detection

**Task 5.3: UI/UX Testing**
- [ ] User Acceptance Tests
- [ ] Accessibility Testing
- [ ] Keyboard Navigation
- [ ] Touch Screen Support

#### Woche 14: Performance Optimization

**Task 5.4: Profiling**
- [ ] CPU Profiling (Python)
- [ ] GPU Profiling (QML)
- [ ] Memory Profiling
- [ ] Identify Bottlenecks

**Task 5.5: Optimizations**
- [ ] Batch Rendering
- [ ] Lazy Window Creation
- [ ] Data Decimation
- [ ] Cache Layer

**Task 5.6: Documentation**
- [ ] User Manual Update
- [ ] Developer Documentation
- [ ] Plugin Development Guide
- [ ] Migration Guide

---

## 📁 Neue Dateistruktur

```
PlotterApp/
│
├── python/
│   ├── Backend/
│   │   ├── backend.py                      # MAJOR UPDATE: Chart routing
│   │   ├── Charts/                         # NEU
│   │   │   ├── __init__.py
│   │   │   ├── base_chart.py              # Abstract base
│   │   │   ├── xy_chart.py                # 2D Charts
│   │   │   ├── xyz_chart.py               # 3D Charts
│   │   │   ├── chart_factory.py           # Factory Pattern
│   │   │   └── chart_registry.py          # Global Registry
│   │   ├── Windows/                        # NEU
│   │   │   ├── __init__.py
│   │   │   ├── window_manager.py          # Window State Management
│   │   │   ├── docking_system.py          # Docking Logic
│   │   │   └── layout_persistence.py      # Save/Load
│   │   └── Plugins/                        # NEU
│   │       ├── __init__.py
│   │       ├── plugin_interface.py        # IChartPlugin
│   │       ├── plugin_loader.py           # Discovery & Loading
│   │       └── plugin_manager.py          # Lifecycle
│   │
│   └── Receiver/
│       └── message.py                      # UPDATE: z_value added
│
├── qml/
│   ├── content/
│   │   ├── App.qml                         # MAJOR UPDATE: Floating mode
│   │   ├── FloatingWorkspace.qml           # NEU: Main workspace
│   │   ├── FloatingChartWindow.qml         # NEU: Floating window
│   │   ├── WindowChrome.qml                # NEU: Title bar
│   │   ├── DockingOverlay.qml              # NEU: Docking indicators
│   │   │
│   │   ├── ChartTypes/                     # NEU: Polymorphic renderers
│   │   │   ├── ChartTypeRenderer.qml      # Interface
│   │   │   ├── XYChart.qml                # 2D Renderer
│   │   │   ├── XYZScatterChart.qml        # 3D Scatter
│   │   │   ├── XYZSurfaceChart.qml        # 3D Surface
│   │   │   └── CustomChartLoader.qml      # Plugin loader
│   │   │
│   │   ├── Managers/                       # NEU
│   │   │   ├── ChartGallery.qml           # Thumbnail overview
│   │   │   ├── ChartCreationWizard.qml    # New chart wizard
│   │   │   └── PluginManager.qml          # Plugin UI
│   │   │
│   │   └── ChartWindow/                    # DEPRECATED: Zu entfernen
│   │       └── ...                         # Old single-chart system
│   │
│   └── imports/
│       ├── ChartTypes/                     # NEU: Type definitions
│       │   └── ChartTypeEnums.qml
│       └── Windows/                        # NEU: Window utilities
│           └── WindowUtils.qml
│
├── embedded/
│   └── common/
│       ├── plotter.h                       # UPDATE: 3D send() methods
│       ├── plotter.cpp                     # UPDATE: 3D formatting
│       └── plotter_protocol.h              # UPDATE: Z coordinate
│
└── plugins/                                # NEU: Plugin directory
    ├── heatmap/
    │   ├── plugin.json
    │   ├── HeatmapChart.qml
    │   └── heatmap_backend.py
    └── ...
```

---

## 🎯 Kritische Entscheidungen & Trade-offs

### 1. Floating vs. Docked Default

**Entscheidung:** Start mit "Free Floating", aber Quick-Dock für Power-User

**Begründung:**
- Maximale Flexibilität
- Multi-Monitor first-class
- Docking als Convenience-Feature

### 2. QtCharts vs. Custom Rendering

**XY Charts:** QtCharts (bewährt, performant)
**XYZ Charts:** Qt3D (Hardware-accelerated)
**Plugins:** Beide möglich

**Begründung:**
- Nutze existing Libraries wo möglich
- Custom nur wenn nötig
- Plugin-System für experimentelles

### 3. Data Storage per Chart vs. Global

**Entscheidung:** Hybrid - Backend global, View-State per Chart

**Begründung:**
- Backend: Single source of truth
- Charts: Independent zoom/pan state
- Einfachere Synchronisation

### 4. Window Persistence Format

**Entscheidung:** JSON für Layouts, SQLite für große Datasets

**Begründung:**
- JSON human-readable für Debugging
- SQLite für Performance bei vielen Charts
- Migration zwischen Formaten möglich

---

## 🔥 Risiken & Mitigationen

### Risiko 1: Performance mit vielen Floating Windows

**Mitigation:**
- Lazy Window Creation (erst bei Bedarf)
- Inactive Windows pausieren Rendering
- LOD für 3D Charts
- Profiling-basierte Optimierung

### Risiko 2: Komplexität für Endnutzer

**Mitigation:**
- Default Layout beim ersten Start
- Guided Tour/Tutorial
- Template Layouts
- "Reset to Default" Option

### Risiko 3: Plugin-System Instabilität

**Mitigation:**
- Sandboxed Plugin Execution
- Plugin Crash Recovery
- Whitelist-System (optional)
- Extensive Plugin API Documentation

### Risiko 4: 3D Rendering Performance

**Mitigation:**
- Point Cloud Decimation
- Adaptive LOD
- GPU Instancing
- Fallback auf 2D-Projection bei Low-End Hardware

---

## 📊 Metriken & Erfolgs-Kriterien

### Performance-Ziele:

- **Window Creation:** < 100ms
- **Data Point Processing:** > 1000 points/sec pro Chart
- **3D Rendering:** > 30 FPS mit 10.000 Punkten
- **Memory:** < 100 MB pro Chart (idle)

### Usability-Ziele:

- **Chart Creation:** < 3 Klicks
- **Window Movement:** Smooth (kein Ruckeln)
- **Layout Save:** < 1 Sekunde
- **Plugin Installation:** < 5 Schritte

---

## 🚀 Rollout-Strategie

### Phase 1: Alpha (intern)
- Core Floating System
- Basic XY Charts
- Entwickler-Testing

### Phase 2: Beta (Early Adopters)
- 3D Charts hinzugefügt
- Plugin-System verfügbar
- User Feedback sammeln

### Phase 3: Release Candidate
- Alle Features komplett
- Performance-optimiert
- Dokumentation vollständig

### Phase 4: General Availability
- Stable Release
- Migration-Tools verfügbar
- Plugin Marketplace (optional)

---

## 💡 Next Steps - SOFORT

### Woche 1 Sprint Planning:

**Tag 1-2: Setup**
- [ ] Git Branch erstellen: `feature/floating-multicharttype`
- [ ] Backend Ordner-Struktur anlegen
- [ ] QML Struktur vorbereiten

**Tag 3-5: Backend Foundation**
- [ ] `BaseChart` Klasse implementieren
- [ ] `XYLineChart` als erste Implementierung
- [ ] `ChartFactory` erstellen

**Tag 6-7: QML Prototyp**
- [ ] `FloatingChartWindow.qml` Grundgerüst
- [ ] Einfaches Drag & Drop
- [ ] Test mit einem Chart

---

**GESCHÄTZTER GESAMTAUFWAND: 12-14 Wochen (3-3.5 Monate)**

**TEAM-GRÖßE EMPFOHLEN: 2-3 Entwickler**
- 1x Backend (Python/Qt)
- 1x Frontend (QML/QtQuick)
- 1x 3D/Graphics (Qt3D) - ab Phase 2

**BEGINN: Sobald genehmigt**
**ERSTE DEMO: Nach Woche 4**
**BETA: Nach Woche 10**
**RELEASE: Nach Woche 14**
