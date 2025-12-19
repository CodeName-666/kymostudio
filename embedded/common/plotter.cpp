/**
 * @file plotter.cpp
 * @brief Implementation of Plotter class
 *
 * @version 5.0
 * @date 2025-12-19
 */

#include "plotter.h"
#include <stdio.h>

// Default constructor
Plotter::Plotter()
    : stream(nullptr)
    , startTimeMs(0)
    , useTimestamp(true)
    , ownsStream(false)
    , getMillisecond(nullptr)
#ifdef ARDUINO
    , printStream(nullptr)
#endif
{
}

#ifdef ARDUINO
// Constructor with Print object
Plotter::Plotter(Print& printObj, bool enableTimestamp)
    : stream(nullptr)
    , startTimeMs(0)
    , useTimestamp(enableTimestamp)
    , ownsStream(true)
    , getMillisecond(nullptr)
    , printStream(new PrintStream(printObj))
{
    stream = printStream;
}
#endif

// Constructor with PlotterStream
Plotter::Plotter(PlotterStream& outputStream, bool enableTimestamp)
    : stream(&outputStream)
    , startTimeMs(0)
    , useTimestamp(enableTimestamp)
    , ownsStream(false)
    , getMillisecond(nullptr)
#ifdef ARDUINO
    , printStream(nullptr)
#endif
{
}

// Destructor
Plotter::~Plotter() {
#ifdef ARDUINO
    if (ownsStream && printStream) {
        delete printStream;
        printStream = nullptr;
    }
#endif
}

// Begin with PlotterStream
void Plotter::begin(PlotterStream& outputStream, bool enableTimestamp) {
#ifdef ARDUINO
    // Clean up any existing owned stream
    if (ownsStream && printStream) {
        delete printStream;
        printStream = nullptr;
    }
#endif

    stream = &outputStream;
    useTimestamp = enableTimestamp;
    startTimeMs = 0;
    ownsStream = false;
}

#ifdef ARDUINO
// Begin with Print object
void Plotter::begin(Print& printObj, bool enableTimestamp) {
    // Clean up any existing owned stream
    if (ownsStream && printStream) {
        delete printStream;
    }

    printStream = new PrintStream(printObj);
    stream = printStream;
    useTimestamp = enableTimestamp;
    startTimeMs = 0;
    ownsStream = true;
}
#endif

void Plotter::setStartTime(uint32_t startTime) {
    startTimeMs = startTime;
}

void Plotter::setMillisecondCallback(GetMillisecondCallback callback) {
    getMillisecond = callback;
}

// ============================================================
// 1D Methods: Send only Y-values
// ============================================================

void Plotter::send(uint8_t channelId, float yValue, bool includeTimestamp) {
    if (!stream) return;

    int len;

    if (includeTimestamp && getMillisecond) {
        uint32_t currentTimeMs = getMillisecond();
        float timestamp = (currentTimeMs - startTimeMs) / 1000.0f;
        len = snprintf(buffer, sizeof(buffer),
                      "{\"id\":%d,\"value\":%.6f,\"timestamp\":%.6f}\n",
                      channelId, yValue, timestamp);
    } else {
        len = snprintf(buffer, sizeof(buffer),
                      "{\"id\":%d,\"value\":%.6f}\n",
                      channelId, yValue);
    }

    if (len > 0 && len < (int)sizeof(buffer)) {
        stream->write((const uint8_t*)buffer, len);
    }
}

void Plotter::send(uint8_t channelId, float yValue) {
    send(channelId, yValue, false);
}

// ============================================================
// 2D Methods: Send X and Y values
// ============================================================

void Plotter::send2D(uint8_t channelId, float xValue, float yValue, bool includeTimestamp) {
    if (!stream) return;

    int len;

    if (includeTimestamp && getMillisecond) {
        uint32_t currentTimeMs = getMillisecond();
        float timestamp = (currentTimeMs - startTimeMs) / 1000.0f;
        len = snprintf(buffer, sizeof(buffer),
                      "{\"id\":%d,\"x\":%.6f,\"value\":%.6f,\"timestamp\":%.6f}\n",
                      channelId, xValue, yValue, timestamp);
    } else {
        len = snprintf(buffer, sizeof(buffer),
                      "{\"id\":%d,\"x\":%.6f,\"value\":%.6f}\n",
                      channelId, xValue, yValue);
    }

    if (len > 0 && len < (int)sizeof(buffer)) {
        stream->write((const uint8_t*)buffer, len);
    }
}

void Plotter::send2D(uint8_t channelId, float xValue, float yValue) {
    send2D(channelId, xValue, yValue, false);
}

// ============================================================
// 3D Methods: Send X, Y and Z values
// ============================================================

void Plotter::send3D(uint8_t channelId, float xValue, float yValue, float zValue, bool includeTimestamp) {
    if (!stream) return;

    int len;

    if (includeTimestamp && getMillisecond) {
        uint32_t currentTimeMs = getMillisecond();
        float timestamp = (currentTimeMs - startTimeMs) / 1000.0f;
        len = snprintf(buffer, sizeof(buffer),
                      "{\"id\":%d,\"x\":%.6f,\"value\":%.6f,\"z\":%.6f,\"timestamp\":%.6f}\n",
                      channelId, xValue, yValue, zValue, timestamp);
    } else {
        len = snprintf(buffer, sizeof(buffer),
                      "{\"id\":%d,\"x\":%.6f,\"value\":%.6f,\"z\":%.6f}\n",
                      channelId, xValue, yValue, zValue);
    }

    if (len > 0 && len < (int)sizeof(buffer)) {
        stream->write((const uint8_t*)buffer, len);
    }
}

void Plotter::send3D(uint8_t channelId, float xValue, float yValue, float zValue) {
    send3D(channelId, xValue, yValue, zValue, false);
}

void Plotter::setTimestampEnabled(bool enable) {
    useTimestamp = enable;
}

bool Plotter::isTimestampEnabled() const {
    return useTimestamp;
}
