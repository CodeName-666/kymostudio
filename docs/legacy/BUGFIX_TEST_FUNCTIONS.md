# Bugfix: Test-Funktionen konnten App nicht finden

**Datum:** 2025-12-11
**Problem:** Test-Funktionen `testFloatingWindow()` und `test3DFloatingWindow()` konnten `createFloatingWindow()` nicht finden

---

## Problem

Fehlermeldungen beim Klicken auf "Test 2D" / "Test 3D" Buttons oder F11/F12:

```
qml: INTERNAL LOG: ERROR - ChartWindow: Cannot find App.createFloatingWindow function
```

## Ursache

Die Test-Funktionen in `ChartWindow.qml` versuchten, die App-Instanz über die Parent-Hierarchie zu finden, aber die Suche funktionierte nicht zuverlässig, da die QML-Komponenten-Hierarchie komplex ist.

## Lösung

### 1. Property-Referenz hinzugefügt

**Datei:** `qml/content/ChartWindow/ChartWindow.qml`

```qml
ChartWindowUi {
    id: chartWindow
    objectName: "chartWindow"

    property var appRoot: null  // Will be set by App.qml
    // ...
}
```

### 2. Referenz in App.qml gesetzt

**Datei:** `qml/content/App.qml`

```qml
Component.onCompleted: {
    // ...

    // Set appRoot reference in chartWindow for test functions
    if (chartWindow) {
        chartWindow.appRoot = appRoot
        Logger.log_debug("App: Set chartWindow.appRoot reference")
    }

    // ...
}
```

### 3. Test-Funktionen aktualisiert

**Dateien:** `qml/content/ChartWindow/ChartWindow.qml`

```qml
function testFloatingWindow() {
    // Get App instance via property reference
    var app = chartWindow.appRoot

    // Fallback: Try parent search if appRoot not set
    if (app === null) {
        var p = parent
        while (p !== null) {
            if (p.createFloatingWindow !== undefined) {
                app = p
                break
            }
            p = p.parent
        }
    }

    if (app === null || app.createFloatingWindow === undefined) {
        Logger.log_error("ChartWindow: Cannot find App.createFloatingWindow function")
        return
    }

    // ... rest of function
}
```

Gleiches für `test3DFloatingWindow()`.

---

## Getestete Funktionen

Nach dem Fix sollten folgende Funktionen wieder arbeiten:

### UI-Buttons
- ✅ "Test 2D" Button (orange) → Erstellt 2D-Fenster mit Testdaten
- ✅ "Test 3D" Button (blau) → Erstellt 3D-Fenster mit Testdaten

### Keyboard-Shortcuts
- ✅ F11 → Erstellt 2D-Fenster mit Sinuswellen
- ✅ F12 → Erstellt 3D-Fenster mit Helix/Sphere/Random

### Direkte Funktionsaufrufe
- ✅ `chartWindow.testFloatingWindow()`
- ✅ `chartWindow.test3DFloatingWindow()`

---

## Geänderte Dateien

1. **qml/content/ChartWindow/ChartWindow.qml**
   - Added `appRoot` property (line 19)
   - Updated `testFloatingWindow()` (lines 694-718)
   - Updated `test3DFloatingWindow()` (lines 785-809)

2. **qml/content/App.qml**
   - Set `chartWindow.appRoot` reference in `Component.onCompleted` (lines 35-38)

---

## Testen

```bash
# Anwendung starten
python python/main.py

# Im UI testen:
# 1. "Test 2D" Button klicken → 2D-Fenster sollte erscheinen
# 2. "Test 3D" Button klicken → 3D-Fenster sollte erscheinen
# 3. F11 drücken → 2D-Fenster sollte erscheinen
# 4. F12 drücken → 3D-Fenster sollte erscheinen
```

**Erwartetes Ergebnis:** Keine Fehlermeldungen mehr, Fenster werden korrekt erstellt.

---

## Technische Details

### Warum die ursprüngliche Parent-Suche nicht funktionierte

Die QML-Komponenten-Hierarchie sieht so aus:

```
ApplicationWindow (AppUi)
  └─ Item (mainArea)
      └─ ChartWindow
```

Die Funktion `createFloatingWindow()` ist auf `App.qml` (erbt von `AppUi`) definiert, aber `ChartWindow.parent` zeigt auf `mainArea` (Item), nicht direkt auf `App`.

Items haben keine `createFloatingWindow` Funktion, daher schlug die Suche fehl.

### Warum die neue Lösung funktioniert

Mit der direkten Property-Referenz (`chartWindow.appRoot = appRoot`) umgehen wir die komplexe Hierarchie-Suche und haben einen direkten Zugriff auf die App-Instanz.

Der Fallback über die Parent-Suche bleibt als Backup erhalten, falls `appRoot` aus irgendeinem Grund nicht gesetzt wird.

---

**Status:** ✅ BEHOBEN
