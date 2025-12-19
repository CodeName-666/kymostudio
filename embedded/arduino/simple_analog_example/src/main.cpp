/**
 * @file main.cpp
 * @brief Simple Arduino example using Plotter class
 *
 * Reads analog sensor and sends data to PlotterApp.
 * PlatformIO project - compile with: pio run -e uno
 *
 * @version 5.0
 * @date 2025-12-19
 */

#include <Arduino.h>
#include <plotter.h>

#define SAMPLE_RATE_MS 100  // 10 Hz
#define ANALOG_PIN A0

Plotter plotter(Serial);  // Direct construction with Serial
unsigned long lastSample = 0;

void setup() {
    Serial.begin(115200);
    while (!Serial) {
        ; // Wait for serial port
    }

    // Set start time and callback for timestamps
    plotter.setStartTime(millis());
    plotter.setMillisecondCallback(millis);

    Serial.println("# Arduino Simple Analog Example v5.0");
    Serial.println("# Reading from pin A0");
    Serial.println("# Sending 1D data (Y-value) with timestamp");
}

void loop() {
    unsigned long currentTime = millis();

    if (currentTime - lastSample >= SAMPLE_RATE_MS) {
        lastSample = currentTime;

        // Read analog sensor
        int rawValue = analogRead(ANALOG_PIN);
        float voltage = (rawValue / 1023.0) * 5.0;

        // Send 1D data point (channel 0) with timestamp
        plotter.send(0, voltage, true);
    }
}
