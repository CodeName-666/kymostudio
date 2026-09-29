# Multi-Chart Window Design für PlotterApp

**Version 1.0** - Implementierungsplan für mehrere frei bewegliche Chart-Fenster

## 🎯 Ziel

Ermögliche mehrere **unabhängige Chart-Fenster**, die:
1. ✅ Frei beweglich und größenveränderbar sind
2. ✅ Einzelne ChartLines zugewiesen bekommen
3. ✅ Individuell zoom-/scrollbar sind
4. ✅ Als Tabs oder Floating Windows organisiert werden können

---

## 📊 Aktuelle Architektur

### QML-Struktur (Ist-Zustand):

```
App.qml (Root)
└── ChartWindow.qml (EINZELNES Chart-Fenster)
    ├── ChartView (QtCharts)
    │   ├── LineSeries (Graph 1)
    │   ├── LineSeries (Graph 2)
    │   └── LineSeries (Graph N)
    ├── ChartsManager (Sidebar)
    ├── ChartControls (Zoom/Pan)
    └── ChartLineModel (Datenmodell)
```

### Python Backend (Ist-Zustand):

```python
class Backend:
    def __init__(self):
        self._graphs = {}  # {uniqueId: XYSeries}
        self._graph_buffers = {}  # Batch-Puffer

    def add_graph(self, uniqueId, series):
        """Fügt eine einzelne Linie hinzu"""

    def append_graph_point(self, uniqueId, point):
        """Fügt Punkt zu Linie hinzu"""
```

**Problem:**
- Nur **EIN** ChartView-Container
- Alle Lines in **EINEM** Chart
- Keine Chart-Verwaltung

---

## 🏗️ Neue Multi-Chart Architektur

### Option 1: Tab-basiert (Einfacher Start)

```
App.qml
└── ChartContainer.qml (NEU)
    ├── TabBar
    │   ├── Tab "Chart 1"
    │   ├── Tab "Chart 2"
    │   └── Tab "+"  (Add Chart)
    └── StackLayout
        ├── ChartWindow (Chart 1)
        │   ├── ChartView
        │   └── ChartLineModel
        ├── ChartWindow (Chart 2)
        │   ├── ChartView
        │   └── ChartLineModel
        └── ...
```

**Vorteile:**
- ✅ Einfach zu implementieren
- ✅ Bekannte UI-Pattern
- ✅ Wenig Code-Änderungen

**Nachteile:**
- ❌ Nur ein Chart sichtbar zur Zeit
- ❌ Nicht frei beweglich

### Option 2: Split-View (Flexibler)

```
App.qml
└── ChartContainer.qml (NEU)
    └── SplitView (horizontal/vertical)
        ├── ChartWindow (Chart 1)
        │   └── ChartView
        ├── Splitter (draggable)
        ├── SplitView (nested)
        │   ├── ChartWindow (Chart 2)
        │   ├── Splitter
        │   └── ChartWindow (Chart 3)
        └── ...
```

**Vorteile:**
- ✅ Mehrere Charts gleichzeitig sichtbar
- ✅ Größenanpassung per Drag
- ✅ Nested möglich (Grid-Layout)

**Nachteile:**
- ⚠️ Fixe Anordnung (kein Floating)
- ⚠️ Komplex bei vielen Charts

### Option 3: Floating Windows (Maximale Flexibilität)

```
App.qml
└── ChartContainer.qml (NEU)
    ├── ChartDockArea (Background)
    └── Repeater
        └── ChartFloatingWindow (x N)
            ├── Window (ApplicationWindow)
            │   ├── Title Bar (Custom)
            │   │   ├── "Chart 1"
            │   │   ├── Minimize/Maximize
            │   │   └── Close
            │   └── ChartWindow
            │       └── ChartView
            └── Drag Handle
```

**Vorteile:**
- ✅ Vollständig frei beweglich
- ✅ Überlappend möglich
- ✅ Dock/Undock möglich
- ✅ Multi-Monitor Support

**Nachteile:**
- 🔴 Komplex zu implementieren
- 🔴 State-Management schwierig
- 🔴 Window-Verwaltung nötig

### Option 4: Hybrid (EMPFOHLEN)

```
App.qml
└── ChartContainer.qml
    ├── TabView (Default-Mode)
    │   └── Charts als Tabs
    └── FloatingContainer (On-Demand)
        └── Undocked Charts als Windows
```

**Vorteile:**
- ✅ Einfach zu starten (Tabs)
- ✅ Fortgeschritten (Floating)
- ✅ Bester Kompromiss

---

## 🔧 Implementierungsplan

### Phase 1: Basis Multi-Chart Support (Tab-basiert)

#### 1.1 Backend-Erweiterungen

**Datei:** `python/Backend/backend.py`

```python
class Backend:
    def __init__(self):
        self._charts = {}  # NEU: {chartId: ChartData}
        self._graphs = {}  # ALT: {uniqueId: XYSeries}
        self._chart_line_assignments = {}  # NEU: {uniqueId: chartId}

@dataclass
class ChartData:
    """Repräsentiert ein Chart-Fenster"""
    id: str
    name: str
    lines: List[str]  # uniqueIds der zugeordneten Linien
    axis_x_min: float
    axis_x_max: float
    axis_y_min: float
    axis_y_max: float
    visible: bool = True
```

**Neue Methoden:**

```python
def create_chart(self, chart_id: str, name: str) -> None:
    """Erstellt neues Chart-Fenster"""

def remove_chart(self, chart_id: str) -> None:
    """Entfernt Chart-Fenster"""

def assign_line_to_chart(self, uniqueId: str, chart_id: str) -> None:
    """Weist ChartLine einem Chart zu"""

def remove_line_from_chart(self, uniqueId: str) -> None:
    """Entfernt ChartLine aus ihrem Chart"""

def get_chart_lines(self, chart_id: str) -> List[str]:
    """Liefert alle Lines eines Charts"""
```

#### 1.2 QML-Komponenten

**Neue Datei:** `qml/content/ChartContainer.qml`

```qml
import QtQuick
import QtQuick.Controls

Item {
    id: chartContainer

    // Model für Charts
    ListModel {
        id: chartsModel
        ListElement {
            chartId: "chart_1"
            chartName: "Chart 1"
        }
    }

    // Tab Bar
    TabBar {
        id: tabBar
        width: parent.width

        Repeater {
            model: chartsModel
            TabButton {
                text: model.chartName
                width: implicitWidth
            }
        }

        // "+" Button für neues Chart
        TabButton {
            text: "+"
            width: 40
            onClicked: createNewChart()
        }
    }

    // Chart Stack
    StackLayout {
        y: tabBar.height
        width: parent.width
        height: parent.height - tabBar.height
        currentIndex: tabBar.currentIndex

        Repeater {
            model: chartsModel
            ChartWindow {
                id: chartWindow
                chartId: model.chartId
                chartName: model.chartName
            }
        }
    }

    function createNewChart() {
        var newId = "chart_" + (chartsModel.count + 1)
        chartsModel.append({
            chartId: newId,
            chartName: "Chart " + (chartsModel.count + 1)
        })
        Backend.create_chart(newId, "Chart " + chartsModel.count)
    }
}
```

#### 1.3 ChartWindow Anpassungen

**Datei:** `qml/content/ChartWindow/ChartWindow.qml`

Änderungen:

```qml
ChartWindow {
    // NEU: Chart-spezifische Properties
    property string chartId: ""
    property string chartName: "Chart"

    // NEU: Nur Lines dieses Charts anzeigen
    chartLinesList.listView.model: ChartLineModel {
        id: chartLineModel
        chartId: parent.chartId  // Filter!
    }

    // NEU: AddChartLineDialog mit Chart-Zuweisung
    onChartLineAdded: function(...) {
        // ...
        Backend.assign_line_to_chart(uniqueId, chartId)
        chartLineModel.addLine(...)
    }
}
```

#### 1.4 ChartLineModel Filter

**Datei:** `qml/content/Models/ChartLineModel.qml`

```qml
QtObject {
    id: chartLineModel

    // NEU: Chart-Filter
    property string chartId: ""

    function addLine(uniqueId, ...) {
        // Nur hinzufügen wenn für dieses Chart
        if (Backend.get_line_chart(uniqueId) === chartId) {
            // ...
        }
    }

    function getAllLines() {
        // Nur Lines dieses Charts zurückgeben
        return lines.filter(line =>
            Backend.get_line_chart(line.uniqueId) === chartId
        )
    }
}
```

---

### Phase 2: Line-zu-Chart Zuweisung UI

#### 2.1 Context Menu für ChartLines

**Erweiterung:** `ChartsManager.qml`

```qml
delegate: MouseArea {
    // ...
    acceptedButtons: Qt.LeftButton | Qt.RightButton

    onClicked: (mouse) => {
        if (mouse.button === Qt.RightButton) {
            contextMenu.popup()
        }
    }

    Menu {
        id: contextMenu

        MenuItem {
            text: "Move to..."

            Menu {
                id: chartSelectionMenu
                Repeater {
                    model: chartsModel
                    MenuItem {
                        text: model.chartName
                        onTriggered: {
                            Backend.assign_line_to_chart(
                                model.uniqueId,
                                model.chartId
                            )
                        }
                    }
                }
            }
        }

        MenuItem {
            text: "Move to new chart"
            onTriggered: {
                var newChartId = createNewChart()
                Backend.assign_line_to_chart(
                    model.uniqueId,
                    newChartId
                )
            }
        }
    }
}
```

#### 2.2 Drag & Drop zwischen Charts

```qml
ChartsManager {
    // Drag source
    delegate: Item {
        Drag.active: dragArea.drag.active
        Drag.source: model.uniqueId
        Drag.hotSpot.x: width / 2
        Drag.hotSpot.y: height / 2

        MouseArea {
            id: dragArea
            drag.target: parent
        }
    }
}

ChartWindow {
    // Drop target
    DropArea {
        anchors.fill: parent

        onDropped: (drop) => {
            var uniqueId = drop.source
            Backend.assign_line_to_chart(uniqueId, chartId)
        }
    }
}
```

---

### Phase 3: Floating Windows (Optional)

#### 3.1 Undock-Funktion

**Neue Komponente:** `qml/content/ChartFloatingWindow.qml`

```qml
ApplicationWindow {
    id: floatingWindow
    width: 800
    height: 600
    visible: true

    property string chartId: ""
    property string chartName: ""

    title: chartName

    ChartWindow {
        anchors.fill: parent
        chartId: floatingWindow.chartId
        chartName: floatingWindow.chartName
    }
}
```

#### 3.2 Dock/Undock Toggle

```qml
TabButton {
    text: model.chartName

    Button {
        text: "⧉"  // Float icon
        anchors.right: parent.right
        onClicked: {
            floatChart(model.chartId)
        }
    }
}

function floatChart(chartId) {
    var component = Qt.createComponent("ChartFloatingWindow.qml")
    var window = component.createObject(null, {
        chartId: chartId,
        chartName: getChartName(chartId)
    })
    window.show()

    // Remove from tabs
    removeChartFromTabs(chartId)
}
```

---

## 📋 Dateistruktur (Neue/Geänderte Dateien)

```
python/Backend/
├── backend.py                          # GEÄNDERT: Chart-Management
└── chart_data.py                       # NEU: ChartData-Klasse

qml/content/
├── App.qml                             # GEÄNDERT: ChartContainer laden
├── ChartContainer.qml                  # NEU: Multi-Chart Container
├── ChartFloatingWindow.qml             # NEU: Floating Window
└── ChartWindow/
    ├── ChartWindow.qml                 # GEÄNDERT: chartId Property
    └── ChartLinesList/
        └── ChartsManager.qml           # GEÄNDERT: Context Menu

qml/content/Models/
└── ChartLineModel.qml                  # GEÄNDERT: Chart-Filter
```

---

## ⚙️ Implementierungs-Schritte (Priorisiert)

### Sprint 1: Basis Multi-Chart (1-2 Wochen)

- [ ] 1. Backend: `ChartData` Klasse erstellen
- [ ] 2. Backend: `create_chart()`, `remove_chart()` implementieren
- [ ] 3. Backend: `assign_line_to_chart()` implementieren
- [ ] 4. QML: `ChartContainer.qml` mit TabBar erstellen
- [ ] 5. QML: `ChartWindow.qml` um `chartId` erweitern
- [ ] 6. QML: `ChartLineModel` mit Chart-Filter
- [ ] 7. Test: 2-3 Charts erstellen und Lines zuweisen

### Sprint 2: Line-Zuweisung UI (1 Woche)

- [ ] 8. QML: Context Menu in `ChartsManager`
- [ ] 9. QML: "Move to Chart" Funktion
- [ ] 10. QML: "Move to new Chart" Funktion
- [ ] 11. Test: Lines zwischen Charts verschieben

### Sprint 3: Split-View (Optional, 1 Woche)

- [ ] 12. QML: SplitView-Modus als Alternative
- [ ] 13. QML: Toggle zwischen Tab/Split-View
- [ ] 14. Test: Grid-Layout mit 2x2 Charts

### Sprint 4: Floating Windows (Optional, 2 Wochen)

- [ ] 15. QML: `ChartFloatingWindow.qml`
- [ ] 16. QML: Dock/Undock Funktion
- [ ] 17. Backend: Window-State speichern/laden
- [ ] 18. Test: Charts undocken und bewegen

---

## 🎨 UI-Mockup

### Tab-basiert (Phase 1):

```
┌─────────────────────────────────────────────────────┐
│ [Chart 1] [Chart 2] [Chart 3] [+]                   │
├─────────────────────────────────────────────────────┤
│                                                     │
│  ┌───────────────────────────────────────────┐    │
│  │                                           │    │
│  │         Chart View                        │    │
│  │                                           │    │
│  │                                           │    │
│  └───────────────────────────────────────────┘    │
│  Lines:                                            │
│  □ Temperature                                     │
│  ☑ Humidity                                        │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### Split-View (Phase 3):

```
┌──────────────────────────┬──────────────────────────┐
│ Chart 1                  │ Chart 2                  │
│  ┌────────────────────┐  │  ┌────────────────────┐  │
│  │                    │  │  │                    │  │
│  │                    │  │  │                    │  │
│  └────────────────────┘  │  └────────────────────┘  │
├──────────────────────────┴──────────────────────────┤
│ Chart 3 (Full Width)                                │
│  ┌──────────────────────────────────────────────┐   │
│  │                                              │   │
│  └──────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
```

---

## 🔍 Technische Herausforderungen

### 1. Performance

**Problem:** Mehrere ChartViews = höhere CPU-Last

**Lösung:**
```qml
ChartView {
    // Nur aktive Charts rendern
    visible: isActiveTab || isFloating

    // Animation deaktivieren bei inaktiven Charts
    animationOptions: visible ? ChartView.SeriesAnimations : ChartView.NoAnimation
}
```

### 2. Daten-Synchronisation

**Problem:** Line-zu-Chart Zuordnung muss persistent sein

**Lösung:**
```python
# In backend.py
def save_workspace(self, filename: str):
    """Speichert Chart-Layout und Zuordnungen"""
    workspace = {
        "charts": [
            {
                "id": chart.id,
                "name": chart.name,
                "lines": chart.lines,
                "position": chart.position
            }
            for chart in self._charts.values()
        ]
    }
    with open(filename, 'w') as f:
        json.dump(workspace, f)
```

### 3. Signal-Routing

**Problem:** `append_graph_point` muss zum richtigen Chart

**Lösung:**
```python
def append_graph_point(self, uniqueId: str, point):
    """Routed to correct chart"""
    chart_id = self._chart_line_assignments.get(uniqueId)
    if chart_id:
        # Signal mit chart_id emittieren
        self._events.append_graph_point_to_chart.emit(chart_id, uniqueId, point)
```

---

## 📊 Migrations-Strategie

### Backward Compatibility

Alte Single-Chart Konfigurationen automatisch migrieren:

```python
def migrate_to_multi_chart(self):
    """Migriert alte Konfiguration zu Multi-Chart"""
    # Erstelle Default-Chart
    self.create_chart("chart_default", "Main Chart")

    # Verschiebe alle Lines zu Default-Chart
    for uniqueId in self._graphs.keys():
        self.assign_line_to_chart(uniqueId, "chart_default")
```

---

## 💡 Best Practices

1. **Starte mit Tabs** - Einfachste Implementierung zuerst
2. **Lazy Loading** - Charts nur bei Bedarf initialisieren
3. **State Management** - Zentrale Chart-Verwaltung im Backend
4. **Signale nutzen** - Events für Chart-Änderungen
5. **Performance** - Inactive Charts pausieren

---

## 📚 Nächste Schritte

1. ✅ Design-Review
2. [ ] Sprint 1 Planung
3. [ ] Backend-Erweiterung implementieren
4. [ ] QML-Prototyp erstellen
5. [ ] Testing & Iteration

---

**Geschätzte Gesamtaufwand:** 4-6 Wochen (abhängig von gewählten Features)
