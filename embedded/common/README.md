# PlotterLib - Embedded Sensor Data Streaming Library

**Version 5.0** - Lightweight C++ library for streaming sensor data to PlotterApp

## Features

✅ **Extremely Lightweight**
- Only ~140 lines of code (excluding comments)
- 100-104 bytes RAM per instance (96-byte buffer for 3D XYZ support)
- 2-3 KB Flash/ROM
- No external dependencies (no JSON libraries required)

✅ **Platform Support**
- Arduino (Uno, Nano, Mega, etc.)
- ESP32 (all variants)
- STM32 (all families)
- Any platform with C++11 compiler

✅ **Flexible Architecture**
- Abstract `PlotterStream` base class
- Easy to add new communication interfaces
- Supports Serial, WiFi, MQTT, USB CDC, UART, etc.
- Callback-based timestamp mechanism for platform independence

✅ **1D, 2D and 3D Data Support**
- **1D**: Y-value only (time series)
- **2D**: X and Y values (custom X-axis)
- **3D**: X, Y and Z values (full 3D plots)
- Optional timestamp support via callback
- Automatic protocol formatting

✅ **Simple API**
```cpp
Plotter plotter(Serial);
plotter.setStartTime(millis());
plotter.setMillisecondCallback(millis);  // NEW in v5.0

// 1D data (Y-only)
plotter.send(id, yValue, true);  // with timestamp

// 2D data (X and Y) - NEW in v5.0
plotter.send2D(id, xValue, yValue, true);

// 3D data (X, Y and Z) - IMPROVED in v5.0
plotter.send3D(id, xValue, yValue, zValue, true);
```

## Installation

### PlatformIO (Recommended)

Add to your `platformio.ini`:
```ini
lib_deps =
    PlotterLib=symlink://path/to/common
```

Or install from local folder:
```bash
cd your_project
pio lib install file://path/to/PlotterApp/embedded/common
```

### Arduino IDE

1. Copy the `common` folder to your Arduino libraries folder:
   - Windows: `Documents/Arduino/libraries/PlotterLib`
   - macOS: `~/Documents/Arduino/libraries/PlotterLib`
   - Linux: `~/Arduino/libraries/PlotterLib`

2. Restart Arduino IDE

3. Include in your sketch:
```cpp
#include <plotter.h>
```

## Quick Start

### 1D Example - Simple Temperature Reading

```cpp
#include <Arduino.h>
#include <plotter.h>

Plotter plotter(Serial);

void setup() {
    Serial.begin(115200);
    plotter.setStartTime(millis());
    plotter.setMillisecondCallback(millis);  // Set time callback
}

void loop() {
    float temperature = analogRead(A0) * 5.0 / 1023.0;
    plotter.send(0, temperature, true);  // 1D with timestamp
    delay(100);
}
```

**Output:**
```json
{"id":0,"value":3.250000,"timestamp":0.100000}
```

### 2D Example - Position vs Force (NEW in v5.0)

```cpp
#include <Arduino.h>
#include <plotter.h>

Plotter plotter(Serial);

void setup() {
    Serial.begin(115200);
    plotter.setStartTime(millis());
    plotter.setMillisecondCallback(millis);
}

void loop() {
    float position = readPositionSensor();
    float force = readForceSensor();

    plotter.send2D(0, position, force, true);  // 2D: X and Y with timestamp
    delay(100);
}
```

**Output:**
```json
{"id":0,"x":10.500000,"value":25.750000,"timestamp":0.100000}
```

### 3D Example - Full XYZ Coordinates (IMPROVED in v5.0)

```cpp
#include <Arduino.h>
#include <plotter.h>

Plotter plotter(Serial);

void setup() {
    Serial.begin(115200);
    plotter.setStartTime(millis());
    plotter.setMillisecondCallback(millis);
}

void loop() {
    // Read 3D position (e.g., robot arm or 3D scanner)
    float xPos = readXPosition();
    float yPos = readYPosition();
    float zPos = readZPosition();

    plotter.send3D(0, xPos, yPos, zPos, true);  // 3D: X, Y and Z with timestamp
    delay(100);
}
```

**Output:**
```json
{"id":0,"x":10.500000,"value":25.500000,"z":99.900000,"timestamp":0.100000}
```

### ESP32 (WiFi + MQTT)

```cpp
#include <WiFi.h>
#include <PubSubClient.h>
#include <plotter.h>

class MQTTStream : public PlotterStream {
    PubSubClient& client;
    const char* topic;
public:
    MQTTStream(PubSubClient& c, const char* t) : client(c), topic(t) {}

    size_t write(const uint8_t* data, size_t length) override {
        char buffer[128];
        if (length < sizeof(buffer) - 1) {
            memcpy(buffer, data, length);
            buffer[length] = '\0';
            return client.publish(topic, buffer) ? length : 0;
        }
        return 0;
    }
};

WiFiClient wifiClient;
PubSubClient mqttClient(wifiClient);
MQTTStream mqttStream(mqttClient, "sensor/data");
Plotter plotter(mqttStream);
```

### STM32 (USB CDC)

```cpp
#include "main.h"
#include <plotter.h>
#include <plotter_stm32.h>

CDCStream usbStream;
Plotter plotter(usbStream);

int main(void) {
    HAL_Init();
    // ... configure peripherals

    plotter.setStartTime(HAL_GetTick());
    plotter.setMillisecondCallback(HAL_GetTick);  // STM32 time callback

    while (1) {
        float voltage = read_adc() * 3.3f / 4095.0f;
        plotter.send(0, voltage, true);  // Send with timestamp
        HAL_Delay(100);
    }
}
```

## API Reference

### Class: Plotter

#### Constructors

```cpp
// Default constructor (must call begin() later)
Plotter();

// Arduino/ESP32 - Direct Print object
Plotter(Print& printObj, bool enableTimestamp = true);

// Custom stream implementation
Plotter(PlotterStream& outputStream, bool enableTimestamp = true);
```

#### Methods

```cpp
// Initialize with stream
void begin(PlotterStream& outputStream, bool enableTimestamp = true);
void begin(Print& printObj, bool enableTimestamp = true);  // Arduino only

// Set start time for timestamp calculation
void setStartTime(uint32_t startTime);

// Set callback for getting current time (NEW in v5.0)
void setMillisecondCallback(GetMillisecondCallback callback);

// ===== 1D Methods (Y-value only) =====
void send(uint8_t id, float yValue, bool includeTimestamp);
void send(uint8_t id, float yValue);  // Without timestamp

// ===== 2D Methods (X and Y values) - NEW in v5.0 =====
void send2D(uint8_t id, float xValue, float yValue, bool includeTimestamp);
void send2D(uint8_t id, float xValue, float yValue);  // Without timestamp

// ===== 3D Methods (X, Y and Z values) - IMPROVED in v5.0 =====
void send3D(uint8_t id, float xValue, float yValue, float zValue, bool includeTimestamp);
void send3D(uint8_t id, float xValue, float yValue, float zValue);  // Without timestamp

// Enable/disable timestamps (legacy, prefer callback + boolean parameter)
void setTimestampEnabled(bool enable);
bool isTimestampEnabled() const;
```

### Class: PlotterStream (Abstract)

Implement this interface to add new communication methods:

```cpp
class PlotterStream {
public:
    virtual size_t write(const uint8_t* data, size_t length) = 0;
    virtual ~PlotterStream() {}
};
```

### STM32 Streams (plotter_stm32.h)

```cpp
// USB CDC stream
class CDCStream : public PlotterStream {
    size_t write(const uint8_t* data, size_t length) override;
};

// UART stream
class UARTStream : public PlotterStream {
    UARTStream(void* huart_handle, uint32_t txTimeout = 100);
    size_t write(const uint8_t* data, size_t length) override;
};
```

## Data Format

PlotterLib sends data in JSON format:

**1D Format:**
```json
{"id":0,"value":3.14}
{"id":0,"value":3.14,"timestamp":1.234}
```

**2D Format (NEW in v5.0):**
```json
{"id":0,"x":10.5,"value":25.75}
{"id":0,"x":10.5,"value":25.75,"timestamp":1.234}
```

**3D Format (IMPROVED in v5.0):**
```json
{"id":0,"x":10.5,"value":25.5,"z":99.9}
{"id":0,"x":10.5,"value":25.5,"z":99.9,"timestamp":1.234}
```

**Field Descriptions:**
- `id`: Channel ID (0-255) - REQUIRED
- `value`: Y-axis value (float, 6 decimal places) - REQUIRED
- `x`: X-axis value (float, 6 decimal places) - OPTIONAL
- `z`: Z-axis value (float, 6 decimal places) - OPTIONAL
- `timestamp`: Time in seconds (float, 6 decimal places) - OPTIONAL

See [3D_PROTOCOL_EXTENSION.md](3D_PROTOCOL_EXTENSION.md) for complete protocol documentation.

## Examples

See the example projects in the parent directories:

- `arduino/simple_analog_example/` - Basic Arduino ADC reading
- `arduino/multi_sensor_example/` - Multiple channels
- `esp32/serial_example/` - ESP32 USB CDC
- `esp32/wifi_mqtt_example/` - Wireless data streaming
- `stm32/usb_cdc_example/` - STM32 USB Virtual COM Port
- `stm32/uart_example/` - STM32 UART communication

## Building Examples

### PlatformIO

```bash
# Arduino Uno
cd arduino/simple_analog_example
pio run -e uno -t upload

# ESP32
cd esp32/serial_example
pio run -e esp32dev -t upload

# STM32
cd stm32/usb_cdc_example
pio run -e nucleo_f401re -t upload
```

### Arduino IDE

1. Open the `.ino` file in the example folder
2. Select your board and port
3. Click Upload

## Performance

### Memory Footprint (v5.0)

| Platform | RAM Usage | Flash Usage |
|----------|-----------|-------------|
| Arduino (AVR) | 100-104 bytes | ~2.5 KB |
| ESP32 | 100-104 bytes | ~2.2 KB |
| STM32 | 100-104 bytes | ~2.2 KB |

**Changes from v4.x:**
- Buffer increased from 80 to 96 bytes (for full XYZ + timestamp support)
- Added callback pointer (+4/8 bytes)

### CPU Usage

- Per `send()` / `send2D()` / `send3D()` call: <250 CPU cycles
- Callback overhead: ~10 CPU cycles
- No dynamic memory allocation (except optional PrintStream wrapper)
- No heap fragmentation

### Comparison with ArduinoJson

| Metric | PlotterLib v5.0 | ArduinoJson |
|--------|-----------------|-------------|
| Flash Size | 2.2-2.5 KB | 15-20 KB |
| RAM Usage | 100-104 bytes | 200-500 bytes |
| CPU Cycles | <250 | 500-1000 |

## License

MIT License

## Contributing

Contributions are welcome! Please submit pull requests or open issues on GitHub.

## Support

For questions and support, please open an issue on the GitHub repository.
