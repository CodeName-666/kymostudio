# KymoStudio - Floating Multi-Chart-Type System
## Roadmap & Fortsetzungsanleitung für nächste Sessions

---

## 📍 Aktueller Stand (Stand: 2025-12-11)

### ✅ Abgeschlossen: Phase 2, Woche 2 - 2D Floating Window System

**Branch:** `feature/floating-multicharttype`

**Commits:**
- `465cf1b` - Phase 2 Week 2: Backend Integration
- `eaac217` - Phase 2 Week 2: QML Frontend (im qml Submodule)
- `8c3902f` - Phase 1 Week 1: Backend Foundation

### Implementierte Features:

#### Backend (Python)
1. **FloatingWindowManager** (`python/Backend/Windows/window_manager.py`)
   - Zentrale Verwaltung aller Floating Windows
   - WindowState-Tracking (Position, Größe, Dock-Status)
   - Layout Save/Load Funktionalität

2. **WindowState** (`python/Backend/Windows/window_state.py`)
   - Dataclass für Window-Zustand
   - Serialisierung zu JSON

3. **WindowManagerBridge** (`python/Backend/Windows/window_manager_bridge.py`)
   - QObject Bridge zwischen QML und Python
   - Signals: windowCreated, windowRemoved, windowStateChanged, layoutSaved, layoutLoaded
   - Slots: createWindow, removeWindow, updateWindowPosition, dockWindow, etc.
   - Als "WindowManager" Context Property in QML verfügbar

4. **BaseChart** (`python/Backend/Charts/base_chart.py`)
   - Abstrakte Basis für alle Chart-Typen
   - ChartType Enum (XY_LINE, XY_SCATTER, XYZ_SURFACE, XYZ_SCATTER)

5. **3D Protocol Support** (`python/Receiver/message.py`, `../KymoProbe/lib/KymoCore/src/kymo.h/cpp`)
   - PlotDataPoint mit z_value für 3D-Daten
   - send3D() Methoden in embedded library

#### Frontend (QML)
1. **FloatingChartWindow.qml** (`qml/content/FloatingWindows/FloatingChartWindow.qml` - 444 Zeilen)
   - Vollständige Floating Window Komponente
   - Window Chrome: Titelleiste mit Min/Max/Close Buttons
   - Drag & Drop: Fenster verschieben
   - Docking System: Snap-to-Edge (links, rechts, oben, unten)
   - Resize Handles: Größe ändern (untere rechte Ecke)
   - Z-Order Management: Focus-Stack
   - Dynamic Chart Loader: Lädt Chart-Renderer basierend auf chartType
   - Property Alias: `chartRenderer` für externen Zugriff

2. **XYChartRenderer.qml** (`qml/content/ChartTypes/XYChartRenderer.qml` - 506 Zeilen)
   - 2D Chart Renderer mit QtCharts 2.3
   - Hardware-Beschleunigung (useOpenGL)
   - Mausrad-Zoom (zentriert auf Cursor)
   - Drag-to-Pan (linke Maustaste)
   - Control Panel: Zoom In/Out, Reset, Fit to Data
   - Batch-Point-Updates für Performance (10.000 Punkte max)
   - API: createLine, removeLine, appendPoint, appendPointsBatch, updateLine, etc.

3. **App.qml Integration** (`qml/content/App.qml`)
   - FloatingWindows Container (z: 100)
   - createFloatingWindow() Funktion
   - removeFloatingWindow() Funktion
   - Keyboard Shortcuts: Ctrl+N, F11
   - objectName: "appRoot" für Component Discovery

4. **ChartWindow.qml Integration** (`qml/content/ChartWindow/ChartWindow.qml`)
   - "Test Float" Button (orange)
   - testFloatingWindow() Funktion
   - Generiert Test-Daten (Sinus, Cosinus, Tangens)
   - Verwendet Batch-Updates

#### Dokumentation
- **FloatingWindows/README.md** - Vollständige Feature-Dokumentation
- **TESTING_FLOATING_WINDOWS.md** - Test-Anleitung mit 10 Test-Szenarien

### Test-Befehle:
```bash
# Anwendung starten
cd d:\Projekte\Python\Plotter\KymoStudio
python python/main.py

# In der Anwendung:
# - F11: Test-Fenster mit 3 Sinuswellen erstellen
# - Ctrl+N: Leeres XY Chart Fenster erstellen
# - "Test Float" Button: Test-Fenster erstellen
```

---

## 🎯 Nächste Phase: Phase 2, Woche 3-4 (3D Charts)

### Ziel: 3D Chart Renderer mit Qt3D Integration

### Aufgaben-Übersicht:

#### 1. XYZChartRenderer.qml erstellen (🔴 Priorität: HOCH)
**Datei:** `qml/content/ChartTypes/XYZChartRenderer.qml`

**Anforderungen:**
- Qt3D Integration für 3D-Visualisierung
- 3D-Achsensystem (X, Y, Z) mit Beschriftungen
- 3D-Gitter für bessere räumliche Orientierung
- Punkt-Rendering (XYZ_SCATTER) oder Surface-Rendering (XYZ_SURFACE)
- Hardware-beschleunigte Darstellung

**Dependencies:**
```qml
import Qt3D.Core 2.15
import Qt3D.Render 2.15
import Qt3D.Input 2.15
import Qt3D.Extras 2.15
import QtQuick3D 6.4  // Alternative zu Qt3D
```

**Ähnliche Struktur wie XYChartRenderer.qml:**
- Root-Item mit chartId, chartTitle Properties
- Public API: createScatterPlot, createSurface, appendPoint3D, appendPointsBatch3D
- Camera Control Panel (Orbit, Pan, Zoom, Reset)
- Performance: 50.000+ Punkte mit Level-of-Detail

#### 2. 3D-Kamera-Steuerung implementieren (🔴 Priorität: HOCH)
**In XYZChartRenderer.qml:**

**Kamera-Modi:**
- **Orbit Mode**: Rotation um 3D-Objekt (Drag mit linker Maustaste)
- **Pan Mode**: Verschieben der Ansicht (Drag mit mittlerer Maustaste oder Shift+Drag)
- **Zoom Mode**: Mausrad oder +/- Buttons
- **Reset**: Zurück zur Standardansicht

**UI-Elemente:**
- Control Panel mit Kamera-Buttons
- Achsen-Ausrichtungs-Buttons (Front/Top/Side View)
- Projektions-Toggle (Perspektive/Orthographic)

#### 3. Z-Achsen-Datenrouting implementieren (🟡 Priorität: MITTEL)
**Dateien:**
- `python/Studio/studio.py` oder neuer Chart Controller
- `python/Backend/Charts/` - Neue Chart-Verwaltung

**Aufgabe:**
- PlotDataPoint mit z_value vom Backend empfangen
- Routing zu korrektem Floating Window basierend auf chartId
- 3D-Punkte an XYZChartRenderer weiterleiten
- Batch-Updates für 3D-Daten unterstützen

**Events erweitern:**
```python
# In studio.py oder neuem Controller
signals:
    append_graph_point_3d = Signal(str, object)  # (chartId, point with x,y,z)
    append_graph_points_batch_3d = Signal(str, list)  # (chartId, list of [x,y,z])
```

#### 4. FloatingChartWindow für 3D erweitern (🟢 Priorität: NIEDRIG)
**Datei:** `qml/content/FloatingWindows/FloatingChartWindow.qml`

**Änderungen:**
- Chart-Type-Icon für XYZ_SURFACE und XYZ_SCATTER hinzufügen
- Ensure Loader kann XYZChartRenderer.qml laden:
  ```qml
  function getChartRendererQml(chartType) {
      switch(chartType) {
          case "xy_line":
          case "xy_scatter":
              return "qrc:/qt/qml/content/ChartTypes/XYChartRenderer.qml"
          case "xyz_surface":
          case "xyz_scatter":
              return "qrc:/qt/qml/content/ChartTypes/XYZChartRenderer.qml"
          default:
              return ""
      }
  }
  ```

#### 5. Test-Integration für 3D (🟢 Priorität: NIEDRIG)
**In ChartWindow.qml oder App.qml:**

**Test-Funktion für 3D:**
```qml
function test3DFloatingWindow() {
    var chartId = "test_3d_" + Date.now()
    var window = createFloatingWindow(chartId, "xyz_scatter", "3D Test Chart", 200, 200, 800, 600)

    Qt.callLater(function() {
        if (window.chartRenderer) {
            // Generiere 3D-Testdaten (z.B. Helix, Kugel, etc.)
            var points3D = []
            for (var t = 0; t < 100; t++) {
                var angle = t * 0.1
                points3D.push([
                    Math.cos(angle) * 10,
                    Math.sin(angle) * 10,
                    t * 0.5
                ])
            }
            window.chartRenderer.appendPointsBatch3D("helix", points3D)
        }
    })
}
```

**Keyboard Shortcut hinzufügen:**
```qml
Shortcut {
    sequence: "Ctrl+Shift+N"
    onActivated: {
        var chartId = "float_3d_" + Date.now()
        createFloatingWindow(chartId, "xyz_scatter", "3D Chart", 100, 100, 800, 600)
    }
}
```

---

## 📋 Phase 3: UI/UX Improvements (Nach Phase 2)

### Ziele:
1. **Layout Persistence** - Save/Load von Window-Layouts
2. **Window Tabs** - Gruppierung von Charts in Tabs
3. **Multi-Monitor Support** - Fenster auf mehreren Bildschirmen
4. **Performance Optimization** - WebGL Renderer, Decimation

### Aufgaben:

#### 1. Layout Persistence (🔴 Priorität: HOCH)
**Backend (Python):**
- `WindowManagerBridge.saveLayout(filename)` vollständig implementieren
- `WindowManagerBridge.loadLayout(filename)` vollständig implementieren
- JSON-Format für Layout-Dateien definieren

**Frontend (QML):**
- "Save Layout" Button in UI
- "Load Layout" Button mit File-Picker
- Auto-Save beim Schließen der Anwendung

**JSON-Schema Beispiel:**
```json
{
    "version": "1.0",
    "windows": [
        {
            "chartId": "chart_1",
            "chartType": "xy_line",
            "title": "Temperature",
            "position": {"x": 100, "y": 100},
            "size": {"width": 800, "height": 600},
            "isDocked": false,
            "dockPosition": "",
            "isMinimized": false,
            "isMaximized": false,
            "zOrder": 1
        }
    ]
}
```

#### 2. Window Tabs (🟡 Priorität: MITTEL)
**Neue Komponente:** `qml/content/FloatingWindows/TabbedChartWindow.qml`

**Features:**
- Mehrere Charts in einem Fenster mit Tabs
- Tab-Leiste oben
- Drag & Drop zwischen Tab-Gruppen
- Context-Menü: "Move to new window", "Close tab"

#### 3. Multi-Monitor Support (🟡 Priorität: MITTEL)
**Backend:**
- Screen-Detection in Python
- Window-Position relativ zu Screen speichern

**Frontend:**
- Screen-Bounds in QML abrufen
- Docking auf Multi-Monitor-Setup anpassen

#### 4. Performance Optimization (🟢 Priorität: NIEDRIG)
**Techniken:**
- WebGL Chart Renderer (alternativ zu QtCharts)
- Data Decimation (z.B. Largest-Triangle-Three-Buckets Algorithm)
- Level-of-Detail für 3D-Charts
- Virtual Scrolling für große Datensätze

---

## 📂 Projekt-Struktur-Übersicht

```
KymoStudio/
├── python/
│   ├── Backend/
│   │   ├── Windows/
│   │   │   ├── window_manager.py           ✅ Implementiert
│   │   │   ├── window_state.py             ✅ Implementiert
│   │   │   └── window_manager_bridge.py    ✅ Implementiert
│   │   └── Charts/
│   │       ├── base_chart.py               ✅ Implementiert
│   │       ├── xy_chart.py                 ⚠️  TODO (optional)
│   │       └── xyz_chart.py                🔴 TODO
│   ├── Receiver/
│   │   └── message.py                      ✅ 3D-Support (z_value)
│   ├── Kymo/
│   │   └── studio.py                      ✅ WindowManager integriert
│   └── main.py                             ✅ WindowManager initialisiert
│
├── qml/                                    (Submodule)
│   └── content/
│       ├── FloatingWindows/
│       │   ├── FloatingChartWindow.qml     ✅ Implementiert (444 Zeilen)
│       │   ├── TabbedChartWindow.qml       🔴 TODO (Phase 3)
│       │   └── README.md                   ✅ Dokumentation
│       ├── ChartTypes/
│       │   ├── XYChartRenderer.qml         ✅ Implementiert (506 Zeilen)
│       │   └── XYZChartRenderer.qml        🔴 TODO (Phase 2 W3-4)
│       ├── App.qml                         ✅ Integration komplett
│       └── ChartWindow/
│           └── ChartWindow.qml             ✅ Test-Button hinzugefügt
│
├── embedded/
│   └── common/
│       ├── kymo.h                       ✅ send3D() Methoden
│       └── kymo.cpp                     ✅ 3D Protocol
│
├── FLOATING_MULTICHARTTYPE_REDESIGN.md     ✅ Haupt-Designdokument
├── TESTING_FLOATING_WINDOWS.md             ✅ Test-Anleitung
└── ROADMAP_PHASE2_CONTINUATION.md          📄 Diese Datei
```

**Legende:**
- ✅ Implementiert und getestet
- ⚠️  Optional/Nice-to-have
- 🔴 TODO - Hohe Priorität
- 🟡 TODO - Mittlere Priorität
- 🟢 TODO - Niedrige Priorität

---

## 🚀 Schnellstart für nächste Session

### Option 1: Phase 2, Woche 3-4 weiterführen (3D Charts)

**Empfohlener Start:**
1. Branch auschecken:
   ```bash
   cd d:\Projekte\Python\Plotter\KymoStudio
   git checkout feature/floating-multicharttype
   git submodule update --init --recursive
   ```

2. XYZChartRenderer.qml erstellen:
   ```
   User: "Erstelle XYZChartRenderer.qml für 3D-Chart-Visualisierung mit Qt3D.
   Orientiere dich an der Struktur von XYChartRenderer.qml und implementiere:
   - 3D-Achsensystem
   - Camera Controls (Orbit, Pan, Zoom)
   - Scatter-Plot-Rendering
   - Batch-3D-Point-Updates"
   ```

3. Referenzdateien:
   - `qml/content/ChartTypes/XYChartRenderer.qml` (als Template)
   - `qml/content/FloatingWindows/FloatingChartWindow.qml` (Loader-Integration)
   - `python/Backend/Windows/window_manager_bridge.py` (Backend-Integration)

### Option 2: Phase 3 starten (UI/UX Improvements)

**Empfohlener Start:**
1. Layout Persistence implementieren:
   ```
   User: "Implementiere Layout Save/Load Funktionalität.
   Erweitere WindowManagerBridge.saveLayout() und loadLayout()
   mit JSON-Serialisierung aller Window-States.
   Füge UI-Buttons in App.qml hinzu."
   ```

2. Referenzdateien:
   - `python/Backend/Windows/window_manager.py` (save_layout, load_layout Methoden)
   - `python/Backend/Windows/window_state.py` (to_dict, from_dict)

---

## 🔍 Wichtige Code-Stellen für Fortsetzung

### 1. Chart-Type-Zuordnung
**Datei:** `qml/content/FloatingWindows/FloatingChartWindow.qml:358-375`
```qml
function getChartRendererQml(chartType) {
    switch(chartType) {
        case "xy_line":
        case "xy_scatter":
            return "qrc:/qt/qml/content/ChartTypes/XYChartRenderer.qml"
        case "xyz_surface":    // 🔴 TODO: XYZChartRenderer hinzufügen
        case "xyz_scatter":
            return "qrc:/qt/qml/content/ChartTypes/XYZChartRenderer.qml"
        default:
            Logger.log_error("Unknown chart type: " + chartType)
            return ""
    }
}
```

### 2. Backend Chart-Daten-Routing
**Datei:** `python/Studio/studio.py` oder neuer Controller

**Aktuell:** Nur 2D-Daten-Events
```python
# In Backend oder Kymo:
events.append_graph_point.connect(qml_handler)  # 2D only
```

**TODO:** 3D-Events hinzufügen
```python
events.append_graph_point_3d.connect(qml_handler_3d)
events.append_graph_points_batch_3d.connect(qml_handler_3d_batch)
```

### 3. WindowManager Context Property
**Datei:** `python/Studio/studio.py:39-41`
```python
def set_window_manager(self, window_manager: WindowManagerBridge):
    self.__window_manager = window_manager
    self.__context.setContextProperty("WindowManager", window_manager)
```

**Von QML aus verwendbar:**
```qml
WindowManager.createWindow(chartId)
WindowManager.dockWindow(chartId, "left", screenWidth, screenHeight)
WindowManager.saveLayout("my_layout.json")
```

---

## 📖 Design-Dokumente

### Hauptdokumente:
1. **FLOATING_MULTICHARTTYPE_REDESIGN.md** - Vollständiger Design-Plan
2. **TESTING_FLOATING_WINDOWS.md** - Test-Szenarien und Anleitung
3. **qml/content/FloatingWindows/README.md** - API-Dokumentation

### Architektur-Übersicht:

```
┌─────────────────────────────────────────────────────────────┐
│                         QML Layer                           │
│  ┌────────────────┐  ┌──────────────────┐  ┌─────────────┐ │
│  │ FloatingChart  │  │  XYChartRenderer │  │ XYZChart    │ │
│  │ Window.qml     │  │  .qml            │  │ Renderer    │ │
│  │                │  │                  │  │ .qml (TODO) │ │
│  │  - Drag/Drop   │  │  - QtCharts 2.3  │  │             │ │
│  │  - Docking     │  │  - Zoom/Pan      │  │  - Qt3D     │ │
│  │  - Resize      │  │  - 10k points    │  │  - 3D Cam   │ │
│  └────────┬───────┘  └─────────┬────────┘  └──────┬──────┘ │
│           │                    │                   │        │
│           └────────────────────┴───────────────────┘        │
│                               │                             │
└───────────────────────────────┼─────────────────────────────┘
                                │ calls slots/emits signals
┌───────────────────────────────┼─────────────────────────────┐
│                   Context Property: "WindowManager"         │
│                               │                             │
│  ┌────────────────────────────▼──────────────────────────┐  │
│  │         WindowManagerBridge (QObject)                 │  │
│  │  - Signals: windowCreated, windowRemoved, ...        │  │
│  │  - Slots: createWindow, dockWindow, saveLayout, ...  │  │
│  └────────────────────────────┬──────────────────────────┘  │
│                               │                             │
└───────────────────────────────┼─────────────────────────────┘
                                │ Python
┌───────────────────────────────▼─────────────────────────────┐
│              FloatingWindowManager (Python)                 │
│  - _windows: Dict[str, WindowState]                        │
│  - create_window(), dock_window(), save_layout(), ...      │
│  └────────────────────────────┬──────────────────────────┘  │
│                               │                             │
│  ┌────────────────────────────▼──────────────────────────┐  │
│  │         WindowState (Dataclass)                       │  │
│  │  - chart_id, chart_type, x, y, width, height, ...    │  │
│  │  - to_dict(), from_dict() for JSON serialization     │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎓 Wichtige Erkenntnisse aus Phase 2 Woche 2

### Performance:
- **Batch-Updates sind essentiell**: `appendPointsBatch()` ist 10-100x schneller als einzelne `appendPoint()` Calls
- **OpenGL Acceleration**: `series.useOpenGL = true` für QtCharts aktivieren
- **Point-Limiting**: Max 10.000 Punkte pro Serie, dann älteste entfernen

### QML-Python Integration:
- **Context Properties sind der Schlüssel**: Einfacher als Singletons
- **Signals/Slots Pattern**: QML kann Python-Slots direkt aufrufen
- **Property Aliases**: `property alias chartRenderer: loader.item` für externen Zugriff

### Floating Window System:
- **MouseArea für Drag**: In Titelleiste, nicht über gesamtes Fenster
- **Docking Detection**: Edge-Detection über Position-Check, nicht über Events
- **Z-Order**: Explizites `bringToFront()` notwendig, automatisches Z-Ordering komplex

### Qt3D vs QtQuick3D:
- **Qt3D**: Vollständige 3D-Engine, aber komplexer
- **QtQuick3D**: Einfacher, moderner, besser mit QML integriert
- **Empfehlung für Phase 2 W3-4**: QtQuick3D 6.4 verwenden

---

## ✅ Commit-Checkliste für nächste Phase

### Vor dem Commit:
- [ ] Alle neuen QML-Dateien getestet (F11, Ctrl+N)
- [ ] Python-Code mit Type Hints versehen
- [ ] Docstrings für alle neuen Funktionen
- [ ] README.md aktualisiert (API-Änderungen)
- [ ] TESTING_*.md erweitert (neue Test-Szenarien)

### Commit-Struktur:
```bash
# QML Submodule zuerst
cd qml
git add content/ChartTypes/XYZChartRenderer.qml
git commit -m "Phase 2 Week 3: 3D Chart Renderer with Qt3D/QtQuick3D

- XYZChartRenderer.qml (500+ lines)
- 3D camera controls (orbit, pan, zoom)
- Scatter plot rendering
- Batch 3D point updates
- Control panel overlay

🤖 Generated with Claude Code
Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"

# Hauptrepository danach
cd ..
git add python/ qml
git commit -m "Phase 2 Week 3: 3D Chart Backend Integration

- Extended WindowManagerBridge for 3D charts
- 3D data routing from Receiver to XYZChartRenderer
- Updated FloatingChartWindow for xyz_scatter/xyz_surface
- Test function for 3D data

🤖 Generated with Claude Code
Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## 🆘 Troubleshooting für nächste Session

### Problem: QML Component nicht gefunden
**Lösung:**
- Prüfe qrc-Pfad: `qrc:/qt/qml/content/ChartTypes/XYZChartRenderer.qml`
- Stelle sicher, dass Datei in qml.qrc eingetragen ist (wenn verwendet)
- Verwende relative Pfade: `"../ChartTypes/XYZChartRenderer.qml"`

### Problem: WindowManager nicht verfügbar in QML
**Lösung:**
- Prüfe `studio.py:41`: `setContextProperty("WindowManager", window_manager)`
- Prüfe `main.py:72`: `kymo.set_window_manager(window_manager)`
- Console-Log in QML: `console.log(typeof WindowManager)`

### Problem: chartRenderer ist null
**Lösung:**
- Verwende `Qt.callLater()` oder `Timer` für Loader-Readiness
- Prüfe Loader.status: `if (loader.status === Loader.Ready)`
- Property Alias korrekt: `property alias chartRenderer: chartLoader.item`

### Problem: 3D-Daten kommen nicht an
**Lösung:**
- Prüfe PlotDataPoint.z_value in message.py
- Backend-Event korrekt gesendet: `append_graph_point_3d.emit(...)`
- QML Handler verbunden: `events.append_graph_point_3d.connect(handler3d)`

---

## 📞 Kontakt & Ressourcen

### Dokumentation:
- Qt Charts: https://doc.qt.io/qt-6/qtcharts-index.html
- Qt3D: https://doc.qt.io/qt-6/qt3d-index.html
- QtQuick3D: https://doc.qt.io/qt-6/qtquick3d-index.html
- PySide6: https://doc.qt.io/qtforpython-6/

### Git-Workflow:
```bash
# Feature-Branch erstellen
git checkout -b feature/3d-chart-renderer

# Submodule aktualisieren
git submodule update --remote --merge

# Nach Fertigstellung: Merge in main branch
git checkout feature/floating-multicharttype
git merge feature/3d-chart-renderer
```

---

## 🎉 Erfolgs-Kriterien für Phase 2 Abschluss

### Phase 2, Woche 3-4 ist abgeschlossen wenn:
- ✅ XYZChartRenderer.qml funktioniert und lädt 3D-Punkte
- ✅ 3D-Kamera-Steuerung implementiert (Orbit, Pan, Zoom)
- ✅ 3D-Daten vom Backend korrekt geroutet werden
- ✅ Test-Funktion für 3D-Charts funktioniert (z.B. F12 oder Ctrl+Shift+N)
- ✅ Dokumentation aktualisiert (README, Testing Guide)
- ✅ Mind. 50.000 3D-Punkte ohne Performance-Probleme

### Gesamt-Erfolg Phase 2:
- ✅ Floating Windows für 2D-Charts (Phase 2 W1-2) ✔️ ABGESCHLOSSEN
- ✅ Floating Windows für 3D-Charts (Phase 2 W3-4) 🔴 IN ARBEIT
- ✅ Beide Chart-Typen können parallel verwendet werden
- ✅ Docking, Resize, Z-Order funktionieren für alle Chart-Typen
- ✅ Performance-Ziele erreicht (10k 2D, 50k 3D Punkte)

---

**Viel Erfolg bei der Fortsetzung! 🚀**

*Generiert am: 2025-12-11*
*Branch: feature/floating-multicharttype*
*Commits: 465cf1b (main), eaac217 (qml submodule)*
