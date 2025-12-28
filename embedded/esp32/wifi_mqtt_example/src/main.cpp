/**
 * @file main.cpp
 * @brief ESP32 WiFi + MQTT example using Plotter class
 *
 * Wireless sensor data streaming via MQTT protocol.
 * PlatformIO project - compile with: pio run -e esp32dev
 *
 * Required libraries:
 * - PubSubClient by Nick O'Leary (auto-installed via platformio.ini)
 *
 * @version 4.0
 * @date 2025-12-11
 */

#include <Arduino.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <math.h>
#include <plotter.h>

// WiFi credentials
const char* WIFI_SSID = "YourWiFiSSID";
const char* WIFI_PASSWORD = "YourWiFiPassword";

// MQTT broker settings
const char* MQTT_BROKER = "192.168.1.100";
const int MQTT_PORT = 1883;
const char* MQTT_CLIENT_ID = "ESP32_Plotter";
const char* MQTT_TOPIC_TX = "sensor/data";

#define SAMPLE_RATE_MS 100  // 10 Hz
#define PLOTTER_EXAMPLE_USE_WAVEFORMS 1  // 1 = sine + sawtooth, 0 = original example
#define WAVE_PERIOD_MS 2000UL
#define WAVE_MIN 0.0f
#define WAVE_MAX 3.3f

WiFiClient wifiClient;
PubSubClient mqttClient(wifiClient);

unsigned long lastSample = 0;
unsigned long lastReconnect = 0;

// Custom PlotterStream for MQTT
class MQTTStream : public PlotterStream {
private:
    PubSubClient& client;
    const char* topic;

public:
    MQTTStream(PubSubClient& mqttClient, const char* publishTopic)
        : client(mqttClient), topic(publishTopic) {}

    size_t write(const uint8_t* data, size_t length) override {
        // MQTT needs null-terminated string
        char buffer[128];
        if (length < sizeof(buffer) - 1) {
            memcpy(buffer, data, length);
            buffer[length] = '\0';
            if (client.publish(topic, buffer)) {
                return length;
            }
        }
        return 0;
    }
};

// Create MQTT stream and plotter
MQTTStream mqttStream(mqttClient, MQTT_TOPIC_TX);
Plotter plotter(mqttStream);

void setup() {
    Serial.begin(115200);
    delay(1000);

    Serial.println("# ESP32 WiFi + MQTT PlotterApp Example");
#if PLOTTER_EXAMPLE_USE_WAVEFORMS
    Serial.println("# Channel 0: Sine");
    Serial.println("# Channel 1: Sawtooth");
#endif

    // Connect to WiFi
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
    Serial.print("Connecting to WiFi");
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }
    Serial.println();
    Serial.print("Connected! IP: ");
    Serial.println(WiFi.localIP());

    // Configure MQTT
    mqttClient.setServer(MQTT_BROKER, MQTT_PORT);
    mqttClient.setKeepAlive(60);
    mqttClient.setBufferSize(256);

    // Set start time for plotter
    plotter.setStartTime(millis());

    // Initial MQTT connection
    reconnectMQTT();
}

void loop() {
    // Maintain MQTT connection
    if (!mqttClient.connected()) {
        unsigned long now = millis();
        if (now - lastReconnect > 5000) {
            lastReconnect = now;
            reconnectMQTT();
        }
    }
    mqttClient.loop();

    // Send example data
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
        float sensor1 = 20.0 + sin(currentTime / 1000.0) * 5.0;
        float sensor2 = 50.0 + cos(currentTime / 800.0) * 10.0;

        // Send data points
        plotter.send(0, sensor1, currentTime);
        plotter.send(1, sensor2, currentTime);
#endif
    }
}

void reconnectMQTT() {
    Serial.print("Connecting to MQTT broker...");
    if (mqttClient.connect(MQTT_CLIENT_ID)) {
        Serial.println("connected!");
    } else {
        Serial.print("failed, rc=");
        Serial.println(mqttClient.state());
    }
}
