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
#include <math.h>
#include <plotter.h>

#define SAMPLE_RATE_MS 100  // 10 Hz
#define PLOTTER_EXAMPLE_USE_WAVEFORMS 1  // 1 = sine + sawtooth, 0 = original example
#define WAVE_PERIOD_MS 2000UL
#define WAVE_MIN 0.0f
#define WAVE_MAX 5.0f
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
#if PLOTTER_EXAMPLE_USE_WAVEFORMS
    Serial.println("# Channel 0: Sine");
    Serial.println("# Channel 1: Sawtooth");
#else
    Serial.println("# Reading from pin A0");
    Serial.println("# Sending 1D data (Y-value) with timestamp");
#endif
}

void loop() {
    unsigned long currentTime = millis();

    if (currentTime - lastSample >= SAMPLE_RATE_MS) {
        lastSample = currentTime;

#if PLOTTER_EXAMPLE_USE_WAVEFORMS
        const float range = WAVE_MAX - WAVE_MIN;
        const float phase = (float)(currentTime % WAVE_PERIOD_MS) / (float)WAVE_PERIOD_MS;
        const float angle = phase * 6.283185307f;
        const float offset = WAVE_MIN + range * 0.5f;
        const float amplitude = range * 0.5f;
        float sineValue = offset + amplitude * sin(angle);
        float sawValue = WAVE_MIN + range * phase;

        plotter.send(0, sineValue, true);
        plotter.send(1, sawValue, true);
#else
        // Read analog sensor
        int rawValue = analogRead(ANALOG_PIN);
        float voltage = (rawValue / 1023.0f) * 5.0f;

        // Send 1D data point (channel 0) with timestamp
        plotter.send(0, voltage, true);
#endif
    }
}
