/**
 * @file serial_example.ino
 * @brief ESP32 Serial (USB) example using Plotter class
 *
 * Simple example using ESP32's USB CDC for data streaming.
 * Works with ESP32-S2, ESP32-S3, ESP32-C3 (have native USB).
 * For older ESP32, use USB-to-Serial adapter on GPIO1/GPIO3.
 *
 * @version 2.0
 * @date 2025-12-10
 */

#include "../../common/plotter.h"
#include <math.h>

#define SAMPLE_RATE_MS 50
#define PLOTTER_EXAMPLE_USE_WAVEFORMS 1  // 1 = sine + sawtooth, 0 = original example
#define WAVE_PERIOD_MS 2000UL
#define WAVE_MIN 0.0f
#define WAVE_MAX 3.3f
#define ADC_PIN 34

Plotter plotter(Serial);  // Direct construction with Serial
unsigned long lastSample = 0;

void setup() {
    Serial.begin(115200);
    delay(1000);  // Wait for serial

#if !PLOTTER_EXAMPLE_USE_WAVEFORMS
    analogSetAttenuation(ADC_11db);  // 0-3.3V range
#endif

    // Set start time for timestamps
    plotter.setStartTime(millis());

    Serial.println("# ESP32 Serial PlotterApp Example");
#if PLOTTER_EXAMPLE_USE_WAVEFORMS
    Serial.println("# Channel 0: Sine");
    Serial.println("# Channel 1: Sawtooth");
#else
    Serial.println("# Reading from ADC pin 34");
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
        // Read ADC
        int rawValue = analogRead(ADC_PIN);
        float voltage = (rawValue / 4095.0f) * 3.3f;

        // Send data point (channel 0)
        plotter.send(0, voltage, currentTime);
#endif
    }
}
