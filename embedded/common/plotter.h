/**
 * @file plotter.h
 * @brief Plotter C++ class for sending data to PlotterApp
 *
 * Modern C++ interface using abstract base class for maximum flexibility.
 * Works with Arduino Print objects, custom streams, and STM32.
 *
 * @version 5.0
 * @date 2025-12-19
 */

#ifndef PLOTTER_H
#define PLOTTER_H

#include <stdint.h>
#include <stdio.h>
#include "plotter_stream.h"

/**
 * @brief Function pointer type for getting current time in milliseconds
 *
 * This callback is used when timestamps are enabled.
 * Platform-specific implementations:
 * - Arduino/ESP32: millis()
 * - STM32 HAL: HAL_GetTick()
 * - FreeRTOS: xTaskGetTickCount()
 * - Custom: your platform's millisecond counter
 *
 * @return Current time in milliseconds since system start
 */
typedef uint32_t (*GetMillisecondCallback)();

/**
 * @brief Plotter class for streaming sensor data to PlotterApp
 *
 * Modern interface using dependency injection via PlotterStream.
 * Supports automatic JSON formatting and timestamp management.
 *
 * Example usage with Arduino:
 * @code
 * #include "plotter.h"
 *
 * Plotter plotter(Serial);
 *
 * void setup() {
 *     Serial.begin(115200);
 *     plotter.setStartTime(millis());
 * }
 *
 * void loop() {
 *     float value = analogRead(A0) * 5.0 / 1023.0;
 *     plotter.send(0, value, millis());
 *     delay(100);
 * }
 * @endcode
 *
 * Example with custom stream:
 * @code
 * class MyStream : public PlotterStream {
 * public:
 *     size_t write(const uint8_t* data, size_t length) override {
 *         // Custom implementation
 *         return my_send_function(data, length);
 *     }
 * };
 *
 * MyStream stream;
 * Plotter plotter(stream);
 * @endcode
 */
class Plotter {
private:
    PlotterStream* stream;              ///< Output stream
    uint32_t startTimeMs;               ///< Start time in milliseconds
    bool useTimestamp;                  ///< Whether to include timestamps
    char buffer[96];                    ///< Internal buffer for formatting (increased for 3D XYZ support)
    bool ownsStream;                    ///< Whether we own the stream object
    GetMillisecondCallback getMillisecond; ///< Callback for getting current time in milliseconds

#ifdef ARDUINO
    PrintStream* printStream;           ///< Owned PrintStream wrapper
#endif

public:
    /**
     * @brief Default constructor
     *
     * Must call begin() before use.
     */
    Plotter();

#ifdef ARDUINO
    /**
     * @brief Construct with Arduino Print object
     *
     * Automatically creates a PrintStream wrapper.
     * Most convenient way to use Plotter on Arduino/ESP32.
     *
     * @param printObj Reference to Print object (Serial, WiFiClient, etc.)
     * @param enableTimestamp Whether to include timestamps (default: true)
     *
     * @code
     * Plotter plotter(Serial);
     * @endcode
     */
    Plotter(Print& printObj, bool enableTimestamp = true);
#endif

    /**
     * @brief Construct with PlotterStream
     *
     * Use this for custom stream implementations.
     *
     * @param outputStream Reference to PlotterStream implementation
     * @param enableTimestamp Whether to include timestamps (default: true)
     *
     * @code
     * MyCustomStream stream;
     * Plotter plotter(stream);
     * @endcode
     */
    Plotter(PlotterStream& outputStream, bool enableTimestamp = true);

    /**
     * @brief Destructor
     *
     * Automatically cleans up owned PrintStream if created.
     */
    ~Plotter();

    /**
     * @brief Initialize with PlotterStream
     *
     * @param outputStream Reference to PlotterStream implementation
     * @param enableTimestamp Whether to include timestamps (default: true)
     */
    void begin(PlotterStream& outputStream, bool enableTimestamp = true);

#ifdef ARDUINO
    /**
     * @brief Initialize with Arduino Print object
     *
     * @param printObj Reference to Print object
     * @param enableTimestamp Whether to include timestamps (default: true)
     */
    void begin(Print& printObj, bool enableTimestamp = true);
#endif

    /**
     * @brief Set the start time for timestamp calculation
     *
     * Call this once during initialization with the current time.
     * All subsequent timestamps will be relative to this start time.
     *
     * @param startTime Current time in milliseconds
     *
     * @code
     * plotter.setStartTime(millis());  // Arduino
     * plotter.setStartTime(HAL_GetTick());  // STM32
     * @endcode
     */
    void setStartTime(uint32_t startTime);

    /**
     * @brief Set the callback function for getting current time
     *
     * This callback is used when timestamps are enabled and you use
     * methods with boolean timestamp parameter.
     *
     * @param callback Function pointer to millisecond counter
     *
     * @code
     * plotter.setMillisecondCallback(millis);      // Arduino
     * plotter.setMillisecondCallback(HAL_GetTick); // STM32
     * @endcode
     */
    void setMillisecondCallback(GetMillisecondCallback callback);

    // ============================================================
    // 1D Methods: Send only Y-values
    // ============================================================

    /**
     * @brief Send 1D data point (Y-value only)
     *
     * @param channelId Channel ID (0-255)
     * @param yValue Y-axis value (measurement)
     * @param includeTimestamp If true and callback is set, timestamp is included
     *
     * Output with timestamp: {"id":0,"value":y,"timestamp":t}
     * Output without: {"id":0,"value":y}
     *
     * @code
     * plotter.send(0, temperature, true);  // with timestamp
     * plotter.send(0, temperature, false); // without timestamp
     * @endcode
     */
    void send(uint8_t channelId, float yValue, bool includeTimestamp);

    /**
     * @brief Send 1D data point without timestamp (backward compatible)
     *
     * @param channelId Channel ID (0-255)
     * @param yValue Y-axis value
     *
     * @code
     * plotter.send(0, temperature);
     * @endcode
     */
    void send(uint8_t channelId, float yValue);

    // ============================================================
    // 2D Methods: Send X and Y values
    // ============================================================

    /**
     * @brief Send 2D data point (X and Y values)
     *
     * @param channelId Channel ID (0-255)
     * @param xValue X-axis value
     * @param yValue Y-axis value
     * @param includeTimestamp If true and callback is set, timestamp is included
     *
     * Output with timestamp: {"id":0,"x":x,"value":y,"timestamp":t}
     * Output without: {"id":0,"x":x,"value":y}
     *
     * @code
     * plotter.send2D(0, position, temperature, true);
     * @endcode
     */
    void send2D(uint8_t channelId, float xValue, float yValue, bool includeTimestamp);

    /**
     * @brief Send 2D data point without timestamp
     *
     * @param channelId Channel ID (0-255)
     * @param xValue X-axis value
     * @param yValue Y-axis value
     *
     * @code
     * plotter.send2D(0, position, temperature);
     * @endcode
     */
    void send2D(uint8_t channelId, float xValue, float yValue);

    // ============================================================
    // 3D Methods: Send X, Y and Z values
    // ============================================================

    /**
     * @brief Send 3D data point (X, Y, and Z values)
     *
     * @param channelId Channel ID (0-255)
     * @param xValue X-axis value
     * @param yValue Y-axis value
     * @param zValue Z-axis value
     * @param includeTimestamp If true and callback is set, timestamp is included
     *
     * Output with timestamp: {"id":0,"x":x,"value":y,"z":z,"timestamp":t}
     * Output without: {"id":0,"x":x,"value":y,"z":z}
     *
     * @code
     * plotter.send3D(0, xPos, yPos, zPos, true);
     * @endcode
     */
    void send3D(uint8_t channelId, float xValue, float yValue, float zValue, bool includeTimestamp);

    /**
     * @brief Send 3D data point without timestamp
     *
     * @param channelId Channel ID (0-255)
     * @param xValue X-axis value
     * @param yValue Y-axis value
     * @param zValue Z-axis value
     *
     * @code
     * plotter.send3D(0, xPos, yPos, zPos);
     * @endcode
     */
    void send3D(uint8_t channelId, float xValue, float yValue, float zValue);

    /**
     * @brief Enable or disable timestamps
     *
     * @param enable True to include timestamps, false to omit
     */
    void setTimestampEnabled(bool enable);

    /**
     * @brief Check if timestamps are enabled
     *
     * @return True if timestamps are enabled
     */
    bool isTimestampEnabled() const;
};

#endif // PLOTTER_H
