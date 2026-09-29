# PlotterApp - Phase 2 Quickstart Guide

## 🎯 Aktueller Stand (2025-12-11)

**Branch:** `feature/floating-multicharttype`
**Status:** Phase 2 Woche 2 ✅ ABGESCHLOSSEN | Phase 2 Woche 3-4 🔴 AUSSTEHEND

---

## ✅ Was funktioniert bereits:

### 2D Floating Windows
- **Erstellen:** F11, Ctrl+N, oder "Test Float" Button
- **Features:** Drag & Drop, Docking, Resize, Zoom, Pan
- **Charts:** XY Line Charts mit 10.000 Punkten
- **Test:** `python python/main.py` → F11 drücken

### Backend Integration
- WindowManagerBridge verfügbar als QML "WindowManager"
- 3D Protocol ready (PlotDataPoint mit z_value)
- Alle Window-Operationen funktionstüchtig

---

## 🔴 Nächster Schritt: 3D Charts

### Hauptaufgabe:
**XYZChartRenderer.qml erstellen** (analog zu XYChartRenderer.qml)

### Prompt für nächste Session:
```
"Ich setze das PlotterApp-Projekt fort. Phase 2 Woche 2 ist abgeschlossen (2D Floating Windows).

Bitte lies zuerst:
1. ROADMAP_PHASE2_CONTINUATION.md (vollständige Fortsetzungsanleitung)
2. qml/content/ChartTypes/XYChartRenderer.qml (als Template)

Dann erstelle XYZChartRenderer.qml mit:
- QtQuick3D 6.4 für 3D-Visualisierung
- 3D-Achsensystem (X, Y, Z)
- Kamera-Steuerung (Orbit, Pan, Zoom)
- Scatter-Plot für 3D-Punkte
- appendPointsBatch3D() für Performance
- Control Panel wie in XYChartRenderer

Branch ist feature/floating-multicharttype, Submodule nicht vergessen!"
```

---

## 📂 Wichtigste Dateien

### ✅ Fertig (zum Nachschauen):
- `qml/content/FloatingWindows/FloatingChartWindow.qml` - Window Component
- `qml/content/ChartTypes/XYChartRenderer.qml` - 2D Chart (als Template!)
- `python/Backend/Windows/window_manager_bridge.py` - QML Bridge
- `TESTING_FLOATING_WINDOWS.md` - Test-Anleitung

### 🔴 Zu erstellen:
- `qml/content/ChartTypes/XYZChartRenderer.qml` - **HAUPTAUFGABE**
- 3D-Datenrouting in Python Backend
- Test-Funktion für 3D (test3DFloatingWindow)

---

## 🚀 Schnellstart nächste Session

```bash
# Repository auschecken
cd d:\Projekte\Python\Plotter\PlotterApp
git checkout feature/floating-multicharttype
git submodule update --init --recursive

# Status prüfen
git log --oneline -3
# Erwartung:
# f4415a2 Add comprehensive roadmap...
# 465cf1b Phase 2 Week 2: Backend Integration
# 8c3902f Phase 1 Week 1: Backend Foundation

# Testen was bereits funktioniert
python python/main.py
# → F11 drücken → Test-Window mit 2D Charts erscheint
```

---

## 📋 Task-Checkliste Phase 2 Woche 3-4

- [ ] XYZChartRenderer.qml erstellen (~500 Zeilen)
  - [ ] QtQuick3D Import und Scene3D Setup
  - [ ] 3D-Achsen und Gitter
  - [ ] Camera Controls (OrbitController oder custom)
  - [ ] Scatter-Plot-Rendering (Point-Instancing)
  - [ ] appendPointsBatch3D() Funktion
  - [ ] Control Panel (Zoom, Rotate, Reset)

- [ ] FloatingChartWindow.qml erweitern
  - [ ] getChartRendererQml() für xyz_scatter/xyz_surface
  - [ ] Icons für 3D-Chart-Typen

- [ ] Backend 3D-Routing
  - [ ] Events für 3D-Punkte (append_graph_point_3d)
  - [ ] Routing zu korrektem Chart basierend auf chartId

- [ ] Test & Doku
  - [ ] test3DFloatingWindow() Funktion
  - [ ] Keyboard Shortcut (Ctrl+Shift+N)
  - [ ] README und Testing Guide aktualisieren
  - [ ] Performance-Test (50k+ Punkte)

---

## 🎓 Quick-Reference: XYZChartRenderer API

### Erwartete Struktur (wie XYChartRenderer):
```qml
Item {
    id: root
    property string chartId: ""
    property string chartTitle: "3D Chart"

    // 3D-spezifische Properties
    property real cameraDistance: 50
    property real cameraElevation: 30
    property real cameraAzimuth: 45

    // Public API
    function createScatterPlot(uniqueId, displayName, color)
    function appendPoint3D(uniqueId, x, y, z)
    function appendPointsBatch3D(uniqueId, points)  // [[x,y,z], ...]
    function clearPoints(uniqueId)

    // Camera API
    function resetCamera()
    function zoomIn()
    function zoomOut()
    function orbitLeft()
    function orbitRight()
}
```

---

## 💡 Architektur-Kurzübersicht

```
QML (FloatingChartWindow)
  ├─ Loader
  │   ├─ XYChartRenderer.qml    ✅ (2D)
  │   └─ XYZChartRenderer.qml   🔴 TODO (3D)
  │
  └─ Calls → WindowManager (Context Property)
              └─ WindowManagerBridge (Python QObject)
                  └─ FloatingWindowManager
                      └─ Dict[chartId → WindowState]
```

---

## ⚡ Performance-Tipps

### Für 3D-Charts:
1. **Instancing verwenden**: Nicht jeden Punkt einzeln rendern
2. **Level-of-Detail**: Weniger Details bei Zoom-Out
3. **Batch-Updates**: `appendPointsBatch3D()` statt einzelne Punkte
4. **Point-Limit**: Max 50.000 Punkte, dann älteste entfernen
5. **GPU-Beschleunigung**: Qt Quick Scene3D mit useOpenGL

---

## 📞 Bei Problemen

### Fehler: "XYZChartRenderer.qml not found"
→ Prüfe Pfad in FloatingChartWindow.qml `getChartRendererQml()`

### Fehler: "WindowManager is undefined"
→ Prüfe plotter.py Zeile 41: `setContextProperty("WindowManager", ...)`

### 3D-Daten kommen nicht an
→ Prüfe Backend-Event-Routing und QML-Handler-Connections

---

## 📝 Git-Workflow

```bash
# Änderungen im QML Submodule committen
cd qml
git add content/ChartTypes/XYZChartRenderer.qml
git commit -m "Add 3D chart renderer with QtQuick3D"

# Hauptrepository mit Submodule-Update committen
cd ..
git add python/ qml
git commit -m "Phase 2 Week 3: 3D Chart Integration"
```

---

## ✅ Fertig wenn:

- [ ] F12 erstellt 3D-Test-Chart
- [ ] 3D-Punkte werden gerendert
- [ ] Kamera lässt sich steuern
- [ ] 50k+ Punkte ohne Performance-Probleme
- [ ] Dokumentation aktualisiert

---

**Für Details:** Siehe `ROADMAP_PHASE2_CONTINUATION.md` (627 Zeilen)

*Letzte Aktualisierung: 2025-12-11*
