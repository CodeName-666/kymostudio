# Floating Multi-Chart-Type System

## Phase 2, Woche 2 - Implementierung abgeschlossen

### Überblick

Das Floating Window System ermöglicht es, mehrere Chart-Fenster gleichzeitig anzuzeigen, zu verschieben, zu docken und zu verwalten.

### Implementierte Komponenten

#### 1. FloatingChartWindow.qml
**Pfad:** `qml/content/FloatingWindows/FloatingChartWindow.qml`

Vollständige Floating Window Komponente mit:
- **Window Chrome**: Custom Titelleiste mit Minimize/Maximize/Close Buttons
- **Drag & Drop**: Verschieben durch Ziehen der Titelleiste
- **Docking System**: Snap-to-Edge Funktionalität (Links, Rechts, Oben, Unten)
- **Resize Handles**: Größenänderung über untere rechte Ecke
- **Z-Order Management**: Focus-Stack für Fenster-Layering
- **Chart Renderer Loader**: Dynamisches Laden von Chart-Typ-Komponenten

**Properties:**
```qml
property string chartId: ""           // Eindeutige ID
property string chartTitle: "Chart"   // Anzeigetitel
property string chartType: "xy_line"  // Chart-Typ (xy_line, xyz_surface, etc.)
property bool isDocked: false         // Docking-Status
property string dockPosition: ""      // Dock-Position ("left", "right", "top", "bottom")
```

**Funktionen:**
```qml
function dockToEdge(edge)            // Dockt Fenster an Bildschirmrand
function undock()                    // Löst Fenster vom Dock
function minimize()                  // Minimiert Fenster
function maximize()                  // Maximiert Fenster
function close()                     // Schließt Fenster
```

#### 2. XYChartRenderer.qml
**Pfad:** `qml/content/ChartTypes/XYChartRenderer.qml`

2D Chart Renderer für XY-Linien-Diagramme:
- **QtCharts Integration**: Verwendet QtCharts 2.3 für Hardware-beschleunigtes Rendering
- **Zoom & Pan**: Mausrad-Zoom und Drag-Pan Funktionalität
- **Control Panel**: Overlay-Steuerung für Zoom In/Out/Reset/Fit
- **Batch Updates**: Optimierte Punkt-Append-Funktionen
- **Performance**: 10.000 Punkte pro Serie mit Auto-Cleanup

**Public API:**
```qml
function createLine(uniqueId, displayName, color)      // Erstellt neue Linie
function removeLine(uniqueId)                          // Entfernt Linie
function appendPoint(uniqueId, x, y)                   // Fügt einzelnen Punkt hinzu
function appendPointsBatch(uniqueId, points)           // Fügt mehrere Punkte hinzu (schneller!)
function updateLine(uniqueId, properties)              // Aktualisiert Linieneigenschaften
function zoomIn()                                      // Zoomt 20% rein
function zoomOut()                                     // Zoomt 25% raus
function resetZoom()                                   // Setzt Zoom zurück
function fitToData()                                   // Passt Zoom an Daten an
```

#### 3. WindowManagerBridge (Python)
**Pfad:** `python/Backend/Windows/window_manager_bridge.py`

QObject-Bridge zwischen QML und Python:

**Signals:**
```python
windowCreated(str chartId)           # Fenster wurde erstellt
windowRemoved(str chartId)           # Fenster wurde entfernt
windowStateChanged(str chartId)      # Fenster-Status hat sich geändert
layoutSaved(str filename)            # Layout wurde gespeichert
layoutLoaded(str filename)           # Layout wurde geladen
```

**Slots (von QML aufrufbar):**
```python
createWindow(chartId: str) -> bool
removeWindow(chartId: str) -> bool
getWindowState(chartId: str) -> dict
updateWindowPosition(chartId: str, x: int, y: int, width: int, height: int)
dockWindow(chartId: str, edge: str, screen_width: int, screen_height: int) -> bool
undockWindow(chartId: str) -> bool
minimizeWindow(chartId: str) -> bool
maximizeWindow(chartId: str, screen_width: int, screen_height: int) -> bool
bringToFront(chartId: str)
saveLayout(filename: str) -> bool
loadLayout(filename: str) -> bool
```

### Integration

#### Python (main.py & plotter.py)
Die WindowManagerBridge wurde als Context Property "WindowManager" registriert:

```python
# main.py
from Backend.Windows.window_manager_bridge import WindowManagerBridge
window_manager = WindowManagerBridge()
plotter.set_window_manager(window_manager)

# plotter.py
def set_window_manager(self, window_manager: WindowManagerBridge):
    self.__window_manager = window_manager
    self.__context.setContextProperty("WindowManager", window_manager)
```

#### QML (App.qml)
Floating Windows Container und Verwaltungsfunktionen hinzugefügt:

```qml
// Container für Floating Windows
Item {
    id: floatingWindowsContainer
    anchors.fill: parent
    z: 100
    property var activeWindows: ({})
}

// Funktionen zum Erstellen/Entfernen
function createFloatingWindow(chartId, chartType, title, x, y, width, height)
function removeFloatingWindow(chartId)
```

### Tastenkürzel

- **Ctrl+N**: Erstellt neues XY Chart Floating Window
- **F11**: Erstellt Test-Floating-Window (für Entwicklung)

### Verwendung

#### Floating Window erstellen
```qml
// In App.qml oder anderen Komponenten
var chartId = "my_chart_" + Date.now()
createFloatingWindow(chartId, "xy_line", "Mein Chart", 100, 100, 800, 600)
```

#### Daten an Chart senden
```qml
// Einzelnen Punkt hinzufügen
var window = floatingWindowsContainer.activeWindows[chartId]
if (window && window.chartRenderer) {
    window.chartRenderer.appendPoint("line_id", x, y)
}

// Batch-Punkte (viel schneller!)
var points = [[0, 1.5], [1, 2.3], [2, 3.1], [3, 2.8]]
window.chartRenderer.appendPointsBatch("line_id", points)
```

#### Fenster docken
```qml
var window = floatingWindowsContainer.activeWindows[chartId]
if (window) {
    window.dockToEdge("left")   // oder "right", "top", "bottom"
}
```

### Testing

#### Manueller Test
1. Anwendung starten
2. **F11** drücken → Test-Fenster wird erstellt
3. Fenster testen:
   - Titelleiste ziehen → Fenster bewegt sich
   - An Bildschirmrand ziehen → Docking-Vorschau erscheint
   - Loslassen am Rand → Fenster dockt an
   - Resize-Handle (unten rechts) ziehen → Größe ändert sich
   - Minimize/Maximize/Close Buttons testen

#### Programmatischer Test
```qml
// Test-Funktion in App.qml oder ChartWindow.qml
function testFloatingWindows() {
    // Erstelle 3 Test-Windows
    for (var i = 0; i < 3; i++) {
        var id = "test_" + i
        var window = createFloatingWindow(
            id,
            "xy_line",
            "Test Chart " + i,
            100 + i * 50,
            100 + i * 50,
            600,
            400
        )

        // Erstelle Test-Linie
        if (window && window.chartRenderer) {
            window.chartRenderer.createLine("line_0", "Test Line", "#ff6b6b")

            // Füge Test-Daten hinzu
            var testData = []
            for (var x = 0; x < 100; x++) {
                var y = Math.sin(x * 0.1) * 10 + i * 5
                testData.push([x, y])
            }
            window.chartRenderer.appendPointsBatch("line_0", testData)
            window.chartRenderer.fitToData()
        }
    }
}
```

### Nächste Schritte (Phase 2, Woche 3-4)

1. **XYZ Chart Renderer** erstellen
   - Qt3D Integration für 3D-Visualisierung
   - 3D-Kamera-Steuerung (Orbit, Pan, Zoom)
   - Z-Achse und 3D-Gitter

2. **3D-Datenrouting** implementieren
   - PlotDataPoint mit z_value in Charts integrieren
   - Backend-Events für 3D-Punkte

3. **Layout-Persistence** verbessern
   - Save/Load von Window-Layouts
   - Session-Management

4. **Performance-Optimierung**
   - WebGL Renderer für große Datenmengen
   - Dezimierung und Level-of-Detail

### Dateien

```
qml/content/
├── FloatingWindows/
│   ├── FloatingChartWindow.qml   (442 Zeilen, vollständig)
│   └── README.md                  (diese Datei)
├── ChartTypes/
│   └── XYChartRenderer.qml        (461 Zeilen, vollständig)
└── App.qml                        (erweitert mit Floating Window Support)

python/
├── Backend/Windows/
│   ├── window_manager_bridge.py   (228 Zeilen, vollständig)
│   ├── window_manager.py          (vorhanden aus Phase 1)
│   └── window_state.py            (vorhanden aus Phase 1)
├── main.py                        (erweitert)
└── Plotter/plotter.py             (erweitert)
```

### Status

✅ Phase 2, Woche 2 - **ABGESCHLOSSEN**
- FloatingChartWindow.qml Komponente
- Window Chrome (Titelleiste, Buttons)
- Drag & Drop Bewegung
- Docking System UI
- Window Manager QML Bridge
- XYChartRenderer.qml für 2D-Charts
- Integration in Hauptanwendung
- Test-Funktionen und Keyboard Shortcuts

🔄 Phase 2, Woche 3-4 - **AUSSTEHEND**
- XYZ Chart Renderer (3D)
- 3D-Kamera-Steuerung
- Datenrouting für 3D-Punkte
