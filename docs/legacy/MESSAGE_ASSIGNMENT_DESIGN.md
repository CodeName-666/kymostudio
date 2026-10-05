# Message → Chart Assignment (Design Spec)

## Kontext / Problem

Aktuell kommt aus dem Backend pro `uniqueId` (z.B. `Serial_0`) ein Datenpunkt, der technisch bereits eine **Message** repräsentiert:

- `x` (optional): expliziter X-Wert (XY-Plot)
- `y` (immer): Messwert (im Protokoll: `value` bzw. `y`)
- `z` (optional): 3D-Wert
- `timestamp` (optional): Zeitstempel (Sekunden)

Die UI/Logik behandelt diese Quellen historisch als “Signale”, es fehlt aber eine saubere **Mapping-/Zuweisungslogik**, die bestimmt:

- welcher Teil der Message in welchen Chart gerendert wird (z.B. TimeSeries = `t` gegen `y` oder `t` gegen `x`)
- welcher Chart-Typ für welche Message “vorgeschlagen” wird
- wie eine XY-Message in 2 TimeSeries-Charts (X/t und Y/t) aufgeteilt werden kann

Dieses Dokument beschreibt die nötigen Änderungen in Backend, Models und UI.

---

## Ziele

1) **Zuweisung auf Chart-Typen mit Mapping**
- Eine Quelle (`uniqueId`) kann einem Chart zugewiesen werden.
- Für **TimeSeries** muss wählbar sein, ob als Value `x` oder `y` genutzt wird.
- Für **XY** ist Standard: `x` gegen `y`.
- Optional später: XYZ-Sonderfälle.

2) **Vorschläge (Smart Defaults)**
- XY-Message (hat `x` + `y`) → Vorschlag: **XY Chart** (xy_line/xy_scatter)
- Y-only-Message (kein `x`, aber `y`) → Vorschlag: **TimeSeries** (t gegen y)
- Trotzdem: Nutzer darf jederzeit manuell überschreiben (Override).

3) **Split einer XY-Message**
- Eine XY-Quelle kann automatisch aufgeteilt werden in zwei TimeSeries-Zuweisungen:
  - Chart A: `t` gegen `x`
  - Chart B: `t` gegen `y`

4) **UI-Integration**
- Sowohl im normalen `ChartsManager` als auch im Detailed View (`ChartManagerDialog`) müssen Assignment und Vorschlags-Workflows verfügbar sein.

---

## Nicht-Ziele (für Phase 1 dieses Features)

- Persistente Speicherung der Mapping-Regeln über App-Neustarts (kann später folgen).
- Re-Design der kompletten Chart-/Receiver-Architektur.
- Backend-seitiges “Routing pro Chart” (derzeit werden Daten global emittiert; Filtering passiert im Renderer/Model).

---

## Terminologie

- **Message-Quelle**: Ein Stream pro `uniqueId` (z.B. `Serial_0`). In jeder Message stecken Felder wie `x/y/z/timestamp`.
- **Signal (UI)**: Historische Bezeichnung; künftig entspricht ein Signal einer Message-Quelle oder (in TimeSeries) einem “Field-View” der Message.
- **Assignment**: Zuweisung einer Quelle zu einem Chart inkl. Mapping.
- **Mapping**: Regel, welche Felder auf Achsen/Value abgebildet werden (z.B. `valueField = "x"`).
- **`t`**: normierte Zeitachse (immer “Zeit”), unabhängig von `x`.

---

## Datenformate & Erkennung

### 1) Eingang (PlotDataPoint)

Backend erhält (vereinfacht) pro Update:

```json
{"id":0,"value":12.34,"x":1.23,"timestamp":4.56,"z":7.89}
```

Backend bildet daraus:

- `uniqueId = f"{interface}_{id}"`
- `x` optional
- `y = value` immer
- `z` optional
- `timestamp` optional
- `t` (neu, normiert)

### 2) Message-Typ-Erkennung (Capabilities)

Pro `uniqueId` werden aus dem letzten Message-Stand folgende Flags abgeleitet:

- `hasX = (x != null)`
- `hasZ = (z != null)`
- `hasTimestamp = (timestamp != null)`

Empfehlung:
- `hasX` → XY-Vorschlag
- `!hasX` → TimeSeries-Vorschlag (`t` gegen `y`)

---

## Architektur: Was geändert werden muss

### A) Backend: stabile Zeitachse `t`

**Problem:** TimeSeries muss “Zeit” anzeigen. `x` kann aber auch “Position” sein (XY). Daher darf TimeSeries nicht auf `x` angewiesen sein.

**Anforderung:**
- `t` muss **immer** Zeit darstellen.
- Wenn `timestamp` vorhanden: `t = timestamp - first_timestamp_per_uniqueId`
- Wenn `timestamp` fehlt: `t = rxTime - first_rxTime_per_uniqueId` (oder ein Auto-Index, aber `rxTime` ist vorzuziehen)

**Implikations:**
- `append_graph_point` muss `t` enthalten.
- `append_graph_points_batch` soll `[x, y, t]` senden (oder Objektliste; aktuell sind Arrays effizienter).

**Nebenwirkung:**
- XY-Charts nutzen weiterhin `x/y`.
- TimeSeries nutzt `t` als Zeitachse und konfiguriertes Value-Feld als y-Wert.

---

### B) Model: Mapping pro Line-Instanz speichern

Aktueller Zustand:
- `ChartLineModel` keyt Lines per `lineKey = "<chartId>::<uniqueId>"`
- Pro Chart ist eine Line pro `uniqueId` möglich.

Für Mapping braucht es zusätzliche Properties pro Line-Instanz, z.B.:

```js
{
  lineKey,
  uniqueId,
  chartId,
  chartType,
  displayName,
  color,
  // neu:
  mapping: {
    kind: "xy" | "time_series" | "xyz",
    valueField: "y" | "x",   // relevant für time_series
    timeField: "t"           // konstant; optional
  }
}
```

Minimal-Variante (für Phase 1):
- `valueField` als Top-Level Property für TimeSeries-Lines, z.B. `valueField: "y"|"x"`
- Optional `sourceKind`/`mappingKind`, um UI einfacher zu machen.

Wichtig:
- Editing (Name/Farbe) darf Mapping nicht verlieren.
- Anzeige-Name kann (optional) automatisch suffixen:
  - `Accel (Y)` / `Accel (X)`

---

### C) Renderer: Mapping auswerten

#### 1) XY
- Standard bleibt: `x` gegen `y`
- Für XY braucht es in Phase 1 kein neues Mapping (außer später für exotische Fälle).

#### 2) TimeSeries
TimeSeries muss beim Append entscheiden:
- Zeit = `t` (oder fallback)
- Value = je nach Mapping:
  - `valueField == "y"` → `point.y` bzw. Batch Index `1`
  - `valueField == "x"` → `point.x` bzw. Batch Index `0`

#### 3) XYZ (optional)
Wenn `z` vorhanden:
- XYZ-Renderer nutzt `x/y/z` (oder später ebenfalls Mapping erweitern).

---

### D) Zuweisungs-API: von “chartIds” zu “Assignments”

Aktuell:
- `setSignalChartsRequested(uniqueId, chartIds)`

Benötigt:
- pro Ziel-Chart optional Mapping-Details.

Vorschlag API:

```js
// QML signal
setSignalChartsRequested(string uniqueId, var assignments)

// assignments: Array von Objekten
[
  { chartId: "chart_...", valueField: "y" },      // time_series
  { chartId: "chart_...", valueField: "x" },      // time_series (Split)
  { chartId: "chart_...", /* no mapping */ }      // xy
]
```

Alternativ (minimal-invasiv):
- `setSignalChartsRequested(uniqueId, chartIds, optionsByChartId)`
- aber: Array-of-objects ist in QML meist einfacher.

ChartWindow-Logik:
- Unassign wie bisher (alles, was nicht in `assignments` vorkommt)
- Assign:
  - XY → `createLine(uniqueId, ...)`
  - TimeSeries → `createLine(uniqueId, ..., valueField)`
  - zusätzlich `ChartLineModel.addLine(..., valueField)`

---

## UI-Workflows (konkret)

### 1) Messages Tab: Quick Actions

Pro Message-Card:
- **Suggested: Create + Assign**
  - wenn `hasX` → create `xy_line` + assign
  - sonst → create `time_series` + assign (valueField=y)
- **Assign…** öffnet Assignment-Dialog (siehe unten)
- **Split to TimeSeries (X/Y)** (nur wenn `hasX`):
  - erstellt 2 time_series Charts (oder wählt vorhandene) und assigned:
    - TS1 valueField=x
    - TS2 valueField=y

### 2) Assign-Dialog: chartType-aware

Dialog listet verfügbare Charts und pro Chart wird angeboten:
- XY/XYZ: Checkbox “assign”
- TimeSeries: Checkbox + Dropdown/Segment “Value = y/x”
  - Option `x` nur aktiv, wenn Message `hasX` (aus `messageModel`)

Zusätzlich:
- Bereich “Recommended chart type” + Button “Create recommended chart”.

### 3) Signals Tab: identisch (Quelle = uniqueId)

Für “Signals” gelten dieselben Regeln; die UI sollte (wenn möglich) die letzten Message-Capabilities aus `messageModel` nutzen, um z.B. “x verfügbar” zu erkennen.

---

## Vorschlagslogik (Regeln)

### Baseline
- Wenn `hasX` → `suggestedChartType = "xy_line"`
- Sonst → `suggestedChartType = "time_series"` mit `valueField="y"`

### Override / Flexibilität
Auch wenn `hasX`, muss möglich sein:
- TimeSeries zu nutzen (Value = x oder y)
- Split

---

## Implementationsplan (Tasks)

### Backend
- [ ] `t`-Berechnung robust machen:
  - [ ] `t` bei fehlendem `timestamp` aus `rxTime` normieren
  - [ ] `append_graph_points_batch` immer als `[x,y,t]` senden
  - [ ] `append_graph_point` enthält `x,y,t,timestamp,z`

### Models
- [ ] `ChartLineModel`: optionales Feld `valueField` (string) pro Line
- [ ] `SignalModel` optional erweitern (capabilities / lastMessageFields), damit UI im Signals-Tab ebenfalls “x verfügbar” erkennt

### UI / Dialoge
- [ ] Assign-Dialog (ChartsManager + Detailed View):
  - [ ] pro ChartType dynamische Optionen
  - [ ] für TimeSeries valueField selection
  - [ ] Übergabe an `ChartWindow` als Assignments
- [ ] Messages-Tab:
  - [ ] Quick action “Create suggested chart + assign”
  - [ ] “Split to time series” action (wenn `hasX`)

### ChartWindow / Routing
- [ ] `setSignalCharts` auf Assignments umbauen
- [ ] `createLine` Aufrufe pro ChartType (XY/time_series/xyz) inkl. valueField
- [ ] Unassign-Logik an neue Datenstruktur anpassen

### Renderer
- [ ] `TimeSeriesRenderer`:
  - [ ] Mapping speichern (valueField)
  - [ ] Append: `t` als Zeitachse; Value aus x/y je nach mapping

---

## Akzeptanzkriterien (Manual Test Cases)

1) **XY Message → XY Chart vorgeschlagen**
- Eingang liefert `x` und `y`.
- UI schlägt XY Chart vor und erstellt auf Klick einen XY Chart + zeigt Linie korrekt (x/y).

2) **Y-only Message → TimeSeries vorgeschlagen**
- Eingang liefert nur `y` (+ optional timestamp).
- UI schlägt TimeSeries vor und erstellt/assigned (t/y).

3) **XY Message → TimeSeries (Value=y) möglich**
- Zuweisung in Dialog: time_series + valueField=y
- Chart zeigt `t` gegen `y` und scrollt korrekt.

4) **XY Message → TimeSeries (Value=x) möglich**
- wie oben, aber valueField=x
- Chart zeigt `t` gegen `x`.

5) **Split XY → 2 TimeSeries Charts**
- Button “Split” erstellt/assigned 2 Charts:
  - Chart A: x/t
  - Chart B: y/t

---

## Offene Entscheidungen (bitte vor Implementierung festzurren)

1) Darf ein **einzelner TimeSeries-Chart** beide Kurven (x und y) derselben `uniqueId` gleichzeitig enthalten?
   - Wenn ja: `lineKey` darf nicht nur `chartId::uniqueId` sein, sondern braucht einen weiteren Suffix (z.B. `chartId::uniqueId::x`).

2) Gibt es Messages, die “nur X” liefern (ohne `y/value`)?
   - Aktueller Parser verlangt `value/y`. Wenn “nur X” existiert, muss Protokoll/Parser angepasst werden.

3) Ist `timestamp` immer verfügbar? Falls nein:
   - `t` muss zuverlässig auf `rxTime` fallbacken (empfohlen).

