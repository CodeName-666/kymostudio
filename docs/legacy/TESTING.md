# Testing Guide - ID-based Chart System

## 🎯 Testing Overview

Das neue ID-basierte System ermöglicht mehrere Chart-Linien über ein Interface. Hier sind verschiedene Test-Szenarien.

---

## 📋 Test-Szenarien

### **Test 1: Single ID mit Timestamp** ✅
**Ziel**: Eine Linie mit echten Timestamps testen

**Datenformat**:
```json
{"id": 0, "value": 23.5, "timestamp": 1234.567}
```

**Erwartetes Verhalten**:
- Chart-Linie: `Test_0` wird automatisch erstellt
- Display Name: `Test #0`
- X-Achse: Normalisiert auf Sekunden seit erstem Datenpunkt
- Y-Achse: 23.5

---

### **Test 2: Single ID ohne Timestamp** ✅
**Ziel**: Auto-Increment X-Achse testen

**Datenformat**:
```json
{"id": 1, "value": 42.0}
```

**Erwartetes Verhalten**:
- Chart-Linie: `Test_1` wird automatisch erstellt
- X-Achse: Auto-Increment (0, 1, 2, 3, ...)
- Y-Achse: 42.0

---

### **Test 3: Multiple IDs gleichzeitig** ✅
**Ziel**: Mehrere Linien über ein Interface

**Datenformat** (mehrere Nachrichten):
```json
{"id": 0, "value": 10.0}
{"id": 1, "value": 20.0}
{"id": 2, "value": 30.0}
```

**Erwartetes Verhalten**:
- 3 Chart-Linien werden erstellt: `Test_0`, `Test_1`, `Test_2`
- Jede Linie hat eigene Farbe (aus Palette)
- Alle Linien sind sichtbar und plotten parallel

---

### **Test 4: Fallback Plain Number** ✅
**Ziel**: Backward Compatibility testen

**Datenformat**:
```text
42.5
```

**Erwartetes Verhalten**:
- Chart-Linie: `Test_0` (Default ID = 0)
- X-Achse: Auto-Increment
- Y-Achse: 42.5

---

## 🧪 Test-Methoden

### **Methode 1: Test-Interface nutzen** ⭐ (Empfohlen)

#### **1.1 Single Sinus-Welle**
**Config in UI**:
- Interface: `Test`
- Type: `Sinus`
- ID: `0`
- Amplitude: `10`
- Frequency: `1.0`

**Start Test**:
1. App starten
2. Sidebar öffnen (Menü-Button)
3. Interface: "Test" auswählen
4. "Start" klicken

**Erwartung**: Eine Sinus-Welle erscheint als `Test #0`

---

#### **1.2 Multi-ID Test**
**Config ändern**:
```json
{
  "type": "Multi",
  "use_timestamp": true
}
```

**Erwartung**:
- 3 Linien erscheinen gleichzeitig:
  - `Test_0`: Sinus (Amplitude 10, Freq 1 Hz)
  - `Test_1`: Cosinus (90° verschoben)
  - `Test_2`: Schnellerer Sinus (Freq 2 Hz)

**Wie Config ändern**:
- Option A: `config/config.json` editieren
- Option B: UI Settings-Dialog (wenn implementiert)

---

### **Methode 2: Serial Interface** 🔌

#### **2.1 Setup mit Python Script**
**Sender-Script** (`test_serial_sender.py`):
```python
import serial
import json
import time
import math

ser = serial.Serial('COM3', 9600)  # Passe COM-Port an

for i in range(100):
    # Sende Daten mit ID 0
    data = {
        "id": 0,
        "value": 10 * math.sin(i * 0.1),
        "timestamp": time.time()
    }
    ser.write((json.dumps(data) + '\n').encode())
    time.sleep(0.1)

ser.close()
```

**Config in PlotterApp**:
- Interface: `Serial`
- Port: `COM3` (gleicher wie im Script)
- Baudrate: `9600`
- "Start" klicken

---

#### **2.2 Virtual Serial Ports**
**Windows**:
```bash
# com0com installieren
# https://sourceforge.net/projects/com0com/
# Erstellt z.B. COM10 <-> COM11 Paar
```

**Linux**:
```bash
# socat installieren
socat -d -d pty,raw,echo=0 pty,raw,echo=0
# Zeigt: /dev/pts/2 <-> /dev/pts/3
```

**Sender zu Virtual Port**:
```python
ser = serial.Serial('/dev/pts/2', 9600)  # Linux
# oder
ser = serial.Serial('COM10', 9600)  # Windows
```

**PlotterApp verbindet zu**:
- Linux: `/dev/pts/3`
- Windows: `COM11`

---

### **Methode 3: MQTT (für Netzwerk-Tests)** 🌐

#### **3.1 MQTT Broker starten**
```bash
# Mosquitto installieren
mosquitto -v
```

#### **3.2 Publisher Script**
```python
import paho.mqtt.client as mqtt
import json
import time
import math

client = mqtt.Client()
client.connect("localhost", 1883)

for i in range(100):
    # ID 0: Temperatur
    temp = {
        "id": 0,
        "value": 20 + 5 * math.sin(i * 0.1)
    }
    client.publish("sensor/data", json.dumps(temp))

    # ID 1: Luftfeuchtigkeit
    humidity = {
        "id": 1,
        "value": 60 + 10 * math.cos(i * 0.1)
    }
    client.publish("sensor/data", json.dumps(humidity))

    time.sleep(0.1)
```

**Config in PlotterApp**:
- Interface: `MQTT`
- Host: `localhost`
- Port: `1883`
- RX Topic: `sensor/data`

---

## 🔍 Was zu überprüfen ist

### **Backend (Python)**
✅ **Logs prüfen**:
```
[INFO] Auto-created line: Test_0 (Test #0)
[INFO] Auto-created line: Test_1 (Test #1)
[DEBUG] Parsed data point: id=0, value=23.5, timestamp=1234.567
```

✅ **Warnings beachten**:
```
[WARNING] Test: missing 'id' field in JSON
[WARNING] Test: 'id' must be integer 0-255, got 300
```

### **Frontend (QML)**
✅ **Chart Linien**:
- Werden automatisch erstellt beim ersten Datenpunkt
- Haben unterschiedliche Farben
- Display Name zeigt Interface + ID

✅ **ChartLineModel**:
```javascript
// Debug in QML Console (Ctrl+Shift+I in Qt)
console.log("Lines:", chartLineModel.count)
console.log("Line 0:", JSON.stringify(chartLineModel.get(0)))
```

---

## 🐛 Bekannte Probleme & Debugging

### **Problem: Keine Linie erscheint**
**Debug Steps**:
1. Backend-Logs checken: Kommt `_on_receiver_data` an?
2. Parse-Fehler?: `[WARNING]` Messages?
3. QML Event: Wird `newGraph` emitted?
   ```python
   # In backend.py _queue_event hinzufügen:
   logger.log_debug(f"Queue event: {signal_name} with {args}")
   ```

### **Problem: Linie friert ein**
**Mögliche Ursachen**:
- Visibility = false (nach Model-Integration)
- Receiver gestoppt
- Backend-Exception (Log prüfen)

### **Problem: X-Achse zeigt falsche Werte**
**Check**:
- Timestamp Normalization: Erster Wert sollte ~0 sein
- Auto-Increment: Sollte bei 0 starten und +1 pro Punkt

---

## 📊 Test-Checkliste

### **Sprint 1 Tests**
- [ ] Test 1: Single ID mit Timestamp
- [ ] Test 2: Single ID ohne Timestamp
- [ ] Test 3: Multiple IDs (Test-Interface "Multi" Mode)
- [ ] Test 4: Fallback Plain Number
- [ ] Backend-Logs zeigen Auto-Creation
- [ ] ChartLineModel enthält korrekte Daten
- [ ] Farben sind unterschiedlich für verschiedene IDs
- [ ] X-Achse normalisiert Timestamps korrekt
- [ ] Auto-Increment funktioniert ohne Timestamp

### **Erweiterte Tests (für später)**
- [ ] ID 0-255 Grenzwerte
- [ ] Ungültige ID (256, -1, "abc")
- [ ] Fehlende/ungültige Felder
- [ ] Unicode in JSON
- [ ] Sehr große Werte (overflow)
- [ ] Sehr hohe Datenrate (performance)

---

## 🚀 Schnellstart

**Einfachster Test** (2 Minuten):
1. App starten
2. Sidebar öffnen
3. Interface: "Test" wählen
4. In `config/config.json` Test-Config zu `"type": "Multi"` ändern
5. "Start" klicken
6. → Sollte 3 Linien gleichzeitig zeigen!

**Nächster Schritt**:
Wenn Sprint 1 funktioniert → **Sprint 2 starten** (UI: Liste + FAB Button)
