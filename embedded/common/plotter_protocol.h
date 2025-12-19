/**
 * @file plotter_protocol.h
 * @brief PlotterApp Communication Protocol Reference
 *
 * This header documents the data format and protocol used for
 * communicating with PlotterApp via Serial, MQTT, WiFi, or other interfaces.
 *
 * The actual implementation is in plotter.h and plotter.cpp.
 * This file serves as protocol documentation and reference.
 *
 * @version 5.0
 * @date 2025-12-19
 */

#ifndef PLOTTER_PROTOCOL_H
#define PLOTTER_PROTOCOL_H

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @brief PlotterApp Communication Protocol
 *
 * The PlotterApp expects data in JSON format with the following structures:
 *
 * 1D Format (Y-value only):
 * {"id":0,"value":123.456789}
 * {"id":0,"value":123.456789,"timestamp":1.234567}
 *
 * 2D Format (X and Y values):
 * {"id":0,"x":10.5,"value":123.456789}
 * {"id":0,"x":10.5,"value":123.456789,"timestamp":1.234567}
 *
 * 3D Format (X, Y and Z values):
 * {"id":0,"x":10.5,"value":123.456789,"z":99.9}
 * {"id":0,"x":10.5,"value":123.456789,"z":99.9,"timestamp":1.234567}
 *
 * Plain number (fallback, single channel only):
 * 123.456789
 *
 * All formats must end with a newline character (\n).
 */

/**
 * @brief Data point structure
 *
 * Represents a single measurement point for plotting.
 *
 * @note ID must be in range 0-255
 * @note Each ID represents a different plot line
 * @note All fields except 'id' and 'value' are optional
 */
typedef struct {
    uint8_t id;          ///< Channel/Line ID (0-255)
    float x;             ///< X-axis value (optional, for 2D/3D plots)
    float value;         ///< Y-axis value (measurement)
    float z;             ///< Z-axis value (optional, for 3D plots)
    float timestamp;     ///< Time value in seconds (optional, separate from X)
} PlotDataPoint;

/**
 * @brief Protocol Constants
 */
#define PLOTTER_MIN_ID 0           ///< Minimum valid channel ID
#define PLOTTER_MAX_ID 255         ///< Maximum valid channel ID
#define PLOTTER_PRECISION 6        ///< Default decimal precision for float values
#define PLOTTER_BUFFER_SIZE 64     ///< Recommended buffer size for formatted data

/**
 * @brief JSON Field Names
 *
 * These are the exact field names expected by PlotterApp:
 * - "id": Channel identifier (integer 0-255) - REQUIRED
 * - "value": Y-axis measurement value (float) - REQUIRED
 * - "x": X-axis value (float) - OPTIONAL
 * - "z": Z-axis value (float) - OPTIONAL
 * - "timestamp": Time value in seconds (float) - OPTIONAL
 */
#define PLOTTER_FIELD_ID "id"
#define PLOTTER_FIELD_X "x"
#define PLOTTER_FIELD_VALUE "value"
#define PLOTTER_FIELD_Z "z"
#define PLOTTER_FIELD_TIMESTAMP "timestamp"

/**
 * @brief Protocol Examples
 *
 * 1D Examples (Y-value only):
 * {"id":0,"value":25.5}
 * {"id":0,"value":25.5,"timestamp":1.234}
 *
 * 2D Examples (X and Y values):
 * {"id":0,"x":10.5,"value":25.5}
 * {"id":0,"x":10.5,"value":25.5,"timestamp":1.234}
 *
 * 3D Examples (X, Y and Z values):
 * {"id":0,"x":10.5,"value":25.5,"z":99.9}
 * {"id":0,"x":10.5,"value":25.5,"z":99.9,"timestamp":1.234}
 *
 * Plain number (legacy, single channel only):
 * 25.5
 */

/**
 * @brief Data Format Requirements
 *
 * 1. JSON Structure:
 *    - Must be valid JSON object: {"key":value,...}
 *    - Field names must be lowercase
 *    - No spaces after colons (recommended for minimal size)
 *    - Must end with newline (\n)
 *
 * 2. Field Types:
 *    - "id": Integer (0-255)
 *    - "value": Float (6 decimal places recommended)
 *    - "timestamp": Float in seconds (6 decimal places recommended)
 *
 * 3. Float Formatting:
 *    - Use %.6f for consistent precision
 *    - Timestamp in seconds (not milliseconds!)
 *    - Convert milliseconds to seconds: timestamp = ms / 1000.0
 *
 * 4. Newline Termination:
 *    - Every message must end with \n
 *    - PlotterApp uses line-based parsing
 *
 * 5. Character Encoding:
 *    - UTF-8 encoding
 *    - ASCII subset recommended for best compatibility
 */

/**
 * @brief Timestamp Handling
 *
 * Timestamps should be in seconds (float), not milliseconds!
 *
 * Best practice:
 * 1. Set start time once: plotter.setStartTime(millis())
 * 2. Send relative timestamps: plotter.send(id, value, millis())
 *    The Plotter class automatically converts ms to seconds
 *
 * Manual calculation:
 * float timestamp = (currentTime_ms - startTime_ms) / 1000.0f;
 *
 * If timestamps are omitted:
 * - PlotterApp will auto-generate based on arrival time
 * - Less accurate for burst data or delayed transmission
 */

/**
 * @brief Channel ID Usage
 *
 * - Valid range: 0-255 (uint8_t)
 * - Each ID appears as separate line in PlotterApp
 * - Use consistent IDs for the same sensor/measurement
 * - Example mapping:
 *   ID 0: Temperature
 *   ID 1: Humidity
 *   ID 2: Pressure
 *   ID 3: Light level
 */

/**
 * @brief Error Handling
 *
 * PlotterApp will ignore or warn on:
 * - Invalid JSON syntax
 * - Missing required fields ("id" or "value")
 * - ID out of range (not 0-255)
 * - Non-numeric values
 * - Invalid UTF-8 encoding
 *
 * The Python backend logs warnings for debugging.
 */

/**
 * @brief Implementation Reference
 *
 * For actual implementation, use the Plotter class from plotter.h:
 *
 * @code
 * #include <plotter.h>
 *
 * Plotter plotter(Serial);
 *
 * void setup() {
 *     Serial.begin(115200);
 *     plotter.setStartTime(millis());
 *     plotter.setMillisecondCallback(millis);  // Set time callback
 * }
 *
 * void loop() {
 *     float temperature = readSensor();
 *
 *     // 1D: Send Y-value only
 *     plotter.send(0, temperature, true);  // with timestamp
 *
 *     // 2D: Send X and Y values
 *     plotter.send2D(1, position, temperature, true);
 *
 *     // 3D: Send X, Y and Z values
 *     plotter.send3D(2, xPos, yPos, zPos, false);  // without timestamp
 *
 *     delay(100);
 * }
 * @endcode
 *
 * See plotter.h for complete API documentation.
 */

#ifdef __cplusplus
}
#endif

#endif // PLOTTER_PROTOCOL_H
