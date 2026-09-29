# Testing Guide: Floating Window System

## Phase 2, Woche 2 - Implementierung abgeschlossen ✅

### Schnellstart

1. **Anwendung starten**
   ```bash
   cd d:\Projekte\Python\Plotter\PlotterApp
   python python/main.py
   ```

2. **Floating Window testen**
   - **Methode 1**: Drücke **F11** → Erstellt Test-Fenster
   - **Methode 2**: Drücke **Ctrl+N** → Erstellt leeres XY Chart Fenster
   - **Methode 3**: Klicke auf **"Test Float"** Button (oben links im Chart Window)

### Test-Szenarien

#### ✅ Test 1: Fenster erstellen
- **F11** drücken
- **Erwartung**: Floating Window mit 3 Sinuswellen erscheint
- **Position**: 150x150, Größe: 700x500

#### ✅ Test 2: Fenster bewegen (Drag & Drop)
- Titelleiste des Fensters anklicken und halten
- Maus bewegen
- **Erwartung**: Fenster folgt der Maus
- **Visuell**: Blauer Rand während des Ziehens

#### ✅ Test 3: Docking System
- Fenster an linken Bildschirmrand ziehen
- **Erwartung**: Docking-Vorschau erscheint (halber Bildschirm links)
- Loslassen
- **Erwartung**: Fenster dockt an und nimmt linke Hälfte ein
- **Wiederholen** für: rechts, oben, unten

#### ✅ Test 4: Undocking
- Gedocktes Fenster an Titelleiste greifen
- Wegziehen vom Rand
- **Erwartung**: Fenster löst sich vom Dock und wird frei beweglich

#### ✅ Test 5: Größe ändern (Resize)
- Resize-Handle (untere rechte Ecke, ⇲ Symbol) anklicken und halten
- Maus bewegen
- **Erwartung**: Fenster ändert Größe dynamisch
- **Minimum**: 400x300 Pixel

#### ✅ Test 6: Chart-Steuerung
Im Floating Window Control Panel (oben rechts):
- **+** → Zoom In (20%)
- **-** → Zoom Out (25%)
- **↺** → Reset Zoom
- **⇲** → Fit to Data

Alternative: Mausrad-Zoom direkt im Chart

#### ✅ Test 7: Pan (Verschieben im Chart)
- Linke Maustaste im Chart-Bereich drücken und halten
- Maus bewegen
- **Erwartung**: Chart-Inhalt verschiebt sich

#### ✅ Test 8: Minimize/Maximize/Close
Titelleisten-Buttons testen:
- **-** (Minimize) → Fenster minimiert sich
- **□** (Maximize) → Fenster füllt gesamten Bildschirm
- **×** (Close) → Fenster wird geschlossen und aus Backend entfernt

#### ✅ Test 9: Z-Order / Focus
- Mehrere Fenster erstellen (F11 mehrmals drücken)
- Unterschiedliche Fenster anklicken
- **Erwartung**: Angeklicktes Fenster kommt nach vorne

#### ✅ Test 10: Backend-Integration
Konsole beobachten:
```
Logger.log_info("App: Creating floating window - ID: test_1234, Type: xy_line")
Logger.log_info("WindowManager: Window created: test_1234")
Logger.log_info("ChartWindow: Test data added successfully")
```

### Keyboard Shortcuts

| Taste | Aktion |
|-------|--------|
| **F11** | Test-Fenster mit Beispieldaten erstellen |
| **Ctrl+N** | Neues leeres XY Chart Fenster erstellen |
| **ESC** | Aktuellen Vorgang abbrechen (falls implementiert) |

### Bekannte Limitierungen (Normal)

- IDE-Warnungen in QML-Dateien sind erwartbar ohne Build-Kontext
- WindowManager.bringToFront() muss implementiert werden, wenn Z-Order nicht funktioniert
- Chart-Daten bleiben bei Undock/Redock erhalten (Feature, nicht Bug)

### Erwartete Log-Ausgaben

Bei erfolgreicher Erstellung eines Test-Fensters:
```
[INFO] ChartWindow: Testing floating window system
[INFO] App: Creating floating window - ID: test_float_1733937600000, Type: xy_line
[INFO] WindowManager: Window created successfully: test_float_1733937600000
[INFO] App: Floating window created successfully: test_float_1733937600000
[INFO] ChartWindow: Floating window created, adding test data...
[INFO] XYChartRenderer initialized for chart: test_float_1733937600000
[INFO] XYChartRenderer: Created line 'Sine Wave' with ID sine_wave
[INFO] XYChartRenderer: Created line 'Cosine Wave' with ID cosine_wave
[INFO] XYChartRenderer: Created line 'Tan Wave (limited)' with ID tan_wave
[INFO] ChartWindow: Test data added successfully
```

### Fehlerbehebung

#### Problem: Fenster wird nicht erstellt
**Lösung**: Prüfe Konsole auf Fehler:
- "WindowManager" nicht gefunden → plotter.py Integration prüfen
- Component.Error → QML-Pfad prüfen

#### Problem: Chart bleibt leer
**Lösung**:
- Qt.callLater Timing → Erhöhe Delay mit Timer
- chartRenderer ist null → Loader nicht fertig geladen

#### Problem: Docking funktioniert nicht
**Lösung**:
- parentWidth/parentHeight properties setzen
- Bildschirmränder korrekt berechnen (0, width, height)

### Nächste Entwicklungsschritte

Nach erfolgreichem Test von Phase 2, Woche 2:

#### Phase 2, Woche 3-4 (3D Charts)
- [ ] XYZChartRenderer.qml erstellen
- [ ] Qt3D Integration
- [ ] 3D-Kamera-Steuerung (Orbit, Pan, Zoom)
- [ ] Z-Achsen-Unterstützung in FloatingChartWindow

#### Phase 3 (UI/UX Improvements)
- [ ] Layout-Persistence (Save/Load)
- [ ] Window-Tabs für Gruppen
- [ ] Multi-Monitor-Support
- [ ] Keyboard-Navigation

### Dateien zum Überprüfen

```
✅ qml/content/FloatingWindows/FloatingChartWindow.qml   (442 Zeilen)
✅ qml/content/ChartTypes/XYChartRenderer.qml             (461 Zeilen)
✅ python/Backend/Windows/window_manager_bridge.py        (228 Zeilen)
✅ python/main.py                                         (erweitert)
✅ python/Plotter/plotter.py                              (erweitert)
✅ qml/content/App.qml                                    (erweitert)
✅ qml/content/ChartWindow/ChartWindow.qml                (erweitert)
```

### Commit-Nachricht (Vorschlag)

```
Phase 2 Week 2: Floating Window System with 2D Chart Renderer

Implementiert:
- FloatingChartWindow.qml: Vollständige Floating Window Komponente
  * Window Chrome (Titelleiste, Min/Max/Close)
  * Drag & Drop Bewegung mit Docking-System
  * Resize-Handles und Z-Order Management
  * Dynamisches Chart-Renderer Loading

- XYChartRenderer.qml: 2D Chart Renderer für XY-Diagramme
  * QtCharts Integration mit Hardware-Beschleunigung
  * Zoom, Pan, Mausrad-Steuerung
  * Batch-Punkt-Updates für Performance
  * Control Panel Overlay

- WindowManagerBridge: QML-Python Bridge
  * Signals für Window-Events
  * Slots für alle Window-Operationen
  * Layout Save/Load Vorbereitung

- Integration in Hauptanwendung
  * Context Property "WindowManager" registriert
  * Floating Window Container in App.qml
  * Test-Button und Keyboard Shortcuts
  * Test-Funktion mit Beispieldaten

Tests: F11, Ctrl+N, "Test Float" Button

🤖 Generated with Claude Code
Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

## Erfolg! 🎉

Phase 2, Woche 2 ist vollständig implementiert und bereit zum Testen.
