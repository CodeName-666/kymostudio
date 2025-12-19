/**
 * @file main.cpp
 * @brief Arduino multi-channel example using Plotter class
 *
 * Demonstrates sending multiple sensor channels to PlotterApp.
 * Shows 1D, 2D, and 3D data transmission in one example.
 * PlatformIO project - compile with: pio run -e uno
 *
 * @version 5.0
 * @date 2025-12-19
 */

#include <Arduino.h>
#include <plotter.h>

#define SAMPLE_RATE_MS 100  // 10 Hz

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

    Serial.println("# Arduino Multi-Sensor Example v5.0");
    Serial.println("# Channel 0: Temperature (1D with timestamp)");
    Serial.println("# Channel 1: Position vs Force (2D with timestamp)");
    Serial.println("# Channel 2: 3D Accelerometer (3D without timestamp)");
}

void loop() {
    unsigned long currentTime = millis();

    if (currentTime - lastSample >= SAMPLE_RATE_MS) {
        lastSample = currentTime;

        // 1D: Simple temperature reading with timestamp
        float temperature = 20.0 + sin(currentTime / 1000.0) * 5.0;
        plotter.send(0, temperature, true);

        // 2D: Position vs Force with timestamp
        float position = sin(currentTime / 800.0) * 100.0;
        float force = cos(currentTime / 800.0) * 50.0;
        plotter.send2D(1, position, force, true);

        // 3D: Accelerometer data (X, Y, Z) without timestamp
        float accelX = sin(currentTime / 500.0);
        float accelY = cos(currentTime / 600.0);
        float accelZ = sin(currentTime / 700.0) * 0.5;
        plotter.send3D(2, accelX, accelY, accelZ, false);
    }
}
