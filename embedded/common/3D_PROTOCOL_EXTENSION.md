# PlotterLib Protocol Extension - 1D, 2D and 3D Data

**Version:** 5.0
**Date:** 2025-12-19

## Overview

PlotterLib now supports flexible data transmission for 1D (Y-only), 2D (XY), and 3D (XYZ) plots. The new API provides clear separation between dimensions with optional timestamp support via callback mechanism.

## Key Changes from Version 4.x

### Breaking Changes
- ❌ **Removed**: `send(id, value, currentTimeMs)` - replaced with boolean parameter
- ❌ **Removed**: `send3D(id, y, z, ...)` - now requires X parameter
- ✅ **Changed**: 3D format now includes explicit X-value: `{"x":..., "value":..., "z":...}`

### New Features
- ✅ **Added**: `GetMillisecondCallback` - flexible time function callback
- ✅ **Added**: `send2D()` methods for explicit XY plots
- ✅ **Added**: Boolean `includeTimestamp` parameter for all methods
- ✅ **Improved**: 3D now supports full XYZ coordinates

## API Overview

### 1D Methods - Send Y-values only

```cpp
void send(uint8_t id, float y, bool includeTimestamp);
void send(uint8_t id, float y);  // Without timestamp
```

**Example:**
```cpp
plotter.send(0, temperature, true);   // {"id":0,"value":25.5,"timestamp":1.234}
plotter.send(0, temperature, false);  // {"id":0,"value":25.5}
plotter.send(0, temperature);         // {"id":0,"value":25.5}
```

### 2D Methods - Send X and Y values

```cpp
void send2D(uint8_t id, float x, float y, bool includeTimestamp);
void send2D(uint8_t id, float x, float y);  // Without timestamp
```

**Example:**
```cpp
plotter.send2D(0, position, temperature, true);   // {"id":0,"x":10.5,"value":25.5,"timestamp":1.234}
plotter.send2D(0, position, temperature, false);  // {"id":0,"x":10.5,"value":25.5}
plotter.send2D(0, position, temperature);         // {"id":0,"x":10.5,"value":25.5}
```

### 3D Methods - Send X, Y and Z values

```cpp
void send3D(uint8_t id, float x, float y, float z, bool includeTimestamp);
void send3D(uint8_t id, float x, float y, float z);  // Without timestamp
```

**Example:**
```cpp
plotter.send3D(0, xPos, yPos, zPos, true);   // {"id":0,"x":10.5,"value":25.5,"z":99.9,"timestamp":1.234}
plotter.send3D(0, xPos, yPos, zPos, false);  // {"id":0,"x":10.5,"value":25.5,"z":99.9}
plotter.send3D(0, xPos, yPos, zPos);         // {"id":0,"x":10.5,"value":25.5,"z":99.9}
```

## Timestamp Callback Mechanism

### Setup

The timestamp is generated via a user-provided callback function. This allows platform-independent time handling.

```cpp
// Define the callback type
typedef uint32_t (*GetMillisecondCallback)();

// Set the callback
void setMillisecondCallback(GetMillisecondCallback callback);
```

### Platform-Specific Examples

**Arduino/ESP32:**
```cpp
plotter.setMillisecondCallback(millis);
plotter.setStartTime(millis());
```

**STM32 HAL:**
```cpp
plotter.setMillisecondCallback(HAL_GetTick);
plotter.setStartTime(HAL_GetTick());
```

**FreeRTOS:**
```cpp
uint32_t getTickMs() {
    return xTaskGetTickCount() * portTICK_PERIOD_MS;
}
plotter.setMillisecondCallback(getTickMs);
plotter.setStartTime(getTickMs());
```

**Custom:**
```cpp
uint32_t myGetMillis() {
    return my_platform_get_milliseconds();
}
plotter.setMillisecondCallback(myGetMillis);
```

### Timestamp Behavior

| Condition | Behavior |
|-----------|----------|
| `includeTimestamp = true` && callback set | Timestamp included: `(currentMs - startMs) / 1000.0` |
| `includeTimestamp = true` && callback NOT set | No timestamp (callback missing) |
| `includeTimestamp = false` | No timestamp |
| Default (no parameter) | No timestamp |

## Protocol Format

### JSON Structure

All formats follow this pattern:
```json
{
  "id": 0,           // Channel ID (0-255) - REQUIRED
  "x": 10.5,         // X-axis value - OPTIONAL (2D/3D only)
  "value": 25.5,     // Y-axis value - REQUIRED
  "z": 99.9,         // Z-axis value - OPTIONAL (3D only)
  "timestamp": 1.23  // Time in seconds - OPTIONAL
}
```

### Field Descriptions

| Field | Type | Dimensions | Required | Description |
|-------|------|-----------|----------|-------------|
| `id` | Integer | All | Yes | Channel/line identifier (0-255) |
| `value` | Float | All | Yes | Y-axis measurement |
| `x` | Float | 2D, 3D | No | X-axis value |
| `z` | Float | 3D | No | Z-axis value |
| `timestamp` | Float | All | No | Time in seconds (separate from X) |

## Complete Examples

### Arduino - Multi-Sensor with Mixed Dimensions

```cpp
#include <plotter.h>

Plotter plotter(Serial);

void setup() {
    Serial.begin(115200);
    plotter.setStartTime(millis());
    plotter.setMillisecondCallback(millis);
}

void loop() {
    // 1D: Simple temperature reading
    float temp = readTemperature();
    plotter.send(0, temp, true);

    // 2D: Position vs. force
    float position = readPosition();
    float force = readForce();
    plotter.send2D(1, position, force, true);

    // 3D: 3-axis accelerometer
    float ax = readAccelX();
    float ay = readAccelY();
    float az = readAccelZ();
    plotter.send3D(2, ax, ay, az, false);  // No timestamp for this one

    delay(100);
}
```

**Serial Output:**
```json
{"id":0,"value":25.500000,"timestamp":0.100000}
{"id":1,"x":10.250000,"value":15.750000,"timestamp":0.100000}
{"id":2,"x":0.120000,"value":0.980000,"z":-0.050000}
```

### STM32 - 3D Surface Mapping

```cpp
#include "plotter.h"
#include "stm32f4xx_hal.h"

// Custom stream for STM32 UART
class UartStream : public PlotterStream {
public:
    size_t write(const uint8_t* data, size_t length) override {
        HAL_UART_Transmit(&huart2, data, length, 100);
        return length;
    }
};

UartStream uartStream;
Plotter plotter(uartStream);

void setup() {
    plotter.setStartTime(HAL_GetTick());
    plotter.setMillisecondCallback(HAL_GetTick);
}

void loop() {
    // Scan surface and send 3D coordinates
    for (float x = 0; x < 100; x += 5) {
        float y = measureHeight(x);
        float z = measureDepth(x);

        plotter.send3D(0, x, y, z, true);
        HAL_Delay(10);
    }
}
```

### ESP32 - WiFi + MQTT without Timestamp

```cpp
#include <plotter.h>
#include <WiFi.h>
#include <PubSubClient.h>

WiFiClient espClient;
PubSubClient mqtt(espClient);
Plotter plotter(mqtt);  // Send via MQTT

void setup() {
    // WiFi setup...
    // MQTT setup...

    // No timestamp needed - server will add it
}

void loop() {
    float sensor1 = readSensor1();
    float sensor2 = readSensor2();
    float sensor3 = readSensor3();

    // Send without timestamps
    plotter.send(0, sensor1);
    plotter.send(1, sensor2);
    plotter.send(2, sensor3);

    delay(1000);
}
```

## Memory Impact

- Buffer size increased from 80 to 96 bytes
- Maximum message length: ~85 characters
- RAM overhead: +16 bytes per Plotter instance
- Function pointer: +4 bytes (32-bit) / +8 bytes (64-bit)

## Migration Guide from v4.x

### Old Code (v4.x)
```cpp
plotter.send(0, value, millis());      // ❌ Deprecated
plotter.send3D(0, y, z, millis());     // ❌ Deprecated
```

### New Code (v5.0)
```cpp
// Setup callback once
plotter.setMillisecondCallback(millis);

// Use boolean parameter
plotter.send(0, value, true);          // ✅ New style
plotter.send3D(0, x, y, z, true);      // ✅ Includes X now!
```

## Use Cases

### 1D Charts
- Temperature over time
- Voltage monitoring
- Single-sensor logging

### 2D Charts
- XY position tracking
- Force vs. displacement
- Custom X-axis values (not time)

### 3D Charts
- 3D position tracking (robotics)
- Surface scanning
- Multi-axis sensor fusion
- Heatmap data (X, Y, temperature)

## PlotterApp Python Backend Support

The PlotterApp Python backend automatically detects and handles all formats:

```python
# PlotDataPoint structure in Python
@dataclass
class PlotDataPoint:
    id: int                        # Required
    value: float                   # Required (Y-axis)
    x: Optional[float] = None      # Optional (X-axis)
    z_value: Optional[float] = None # Optional (Z-axis)
    timestamp: Optional[float] = None # Optional (time)
```

The parser in `backend.py::_parse_data_point()` already supports all fields correctly.

## Chart Type Compatibility

| Chart Type | Dimensions | Recommended Method |
|------------|-----------|-------------------|
| Time Series | Y vs Time | `send(id, y, true)` |
| XY Line | X vs Y | `send2D(id, x, y)` |
| XY Scatter | X vs Y | `send2D(id, x, y)` |
| XYZ Surface | 3D | `send3D(id, x, y, z)` |
| XYZ Scatter | 3D | `send3D(id, x, y, z)` |

## Backwards Compatibility

The following methods remain unchanged for backwards compatibility:

```cpp
void send(uint8_t id, float y);  // Still works - no timestamp
```

**Note:** Old code using `send(id, value, millis())` will need to be updated to use the callback mechanism.

## References

- Header: [embedded/common/plotter.h](plotter.h)
- Implementation: [embedded/common/plotter.cpp](plotter.cpp)
- Protocol: [embedded/common/plotter_protocol.h](plotter_protocol.h)
- Python Parser: `python/Backend/backend.py::_parse_data_point()`
- Data Structure: `python/Receiver/message.py::PlotDataPoint`

---

**Questions or Issues?**
Please refer to the main README or open an issue on GitHub.
