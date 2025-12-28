/**
 * @file multi_sensor_example.ino
 * @brief Arduino multi-channel example using Plotter class
 *
 * Demonstrates sending multiple sensor channels to PlotterApp.
 *
 * @version 2.0
 * @date 2025-12-10
 */

#include "../../common/plotter.h"
#include <math.h>

#define SAMPLE_RATE_MS 100  // 10 Hz
#define PLOTTER_EXAMPLE_USE_WAVEFORMS 1  // 1 = sine + sawtooth, 0 = original example
#define WAVE_PERIOD_MS 2000UL
#define WAVE_MIN 0.0f
#define WAVE_MAX 5.0f

Plotter plotter(Serial);  // Direct construction with Serial
unsigned long lastSample = 0;

void setup() {
    Serial.begin(115200);
    while (!Serial) {
        ; // Wait for serial port
    }

    // Set start time for timestamps
    plotter.setStartTime(millis());

    Serial.println("# Arduino Multi-Sensor Example");
#if PLOTTER_EXAMPLE_USE_WAVEFORMS
    Serial.println("# Channel 0: Sine");
    Serial.println("# Channel 1: Sawtooth");
#else
    Serial.println("# Channel 0: Temperature");
    Serial.println("# Channel 1: Humidity");
    Serial.println("# Channel 2: Pressure");
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

        plotter.send(0, sineValue, currentTime);
        plotter.send(1, sawValue, currentTime);
#else
        // Simulate sensor readings
        float temperature = 20.0 + sin(currentTime / 1000.0) * 5.0;
        float humidity = 50.0 + cos(currentTime / 800.0) * 10.0;
        float pressure = 1013.25 + sin(currentTime / 1200.0) * 20.0;

        // Send all three channels
        plotter.send(0, temperature, currentTime);
        plotter.send(1, humidity, currentTime);
        plotter.send(2, pressure, currentTime);
#endif
    }
}
