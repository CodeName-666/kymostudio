// SPDX-License-Identifier: GPL-3.0-only OR LicenseRef-KymoStudio-Commercial
// Copyright (c) 2026 Christof Seidel
import QtQuick 6.4
import QtQuick.Controls 6.4
import QtQuick.Layouts 1.15

/**
 * XYChartView.qml
 *
 * XY chart view for floating windows.
 * This is a simple wrapper around XYChartRenderer.
 * State and routing are owned by WorkspaceController. This item only renders.
 */
Item {
    id: root

    // Public properties (passed from FloatingChartWindow)
    property string chartId: ""
    property string chartTitle: "XY Chart"
    property string chartType: "xy_line"

    // Chart configuration
    property real initialXMin: 0
    property real initialXMax: 10
    property real initialYMin: 0
    property real initialYMax: 10

    property bool updatesSuspended: false

    // Internal reference to the actual renderer (for internal use)
    property var _internalRenderer: chartRenderer

    // XY Chart Renderer - fills entire space
    XYChartRenderer {
        id: chartRenderer
        anchors.fill: parent

        chartId: root.chartId
        chartTitle: root.chartTitle
        initialXMin: root.initialXMin
        initialXMax: root.initialXMax
        initialYMin: root.initialYMin
        initialYMax: root.initialYMax
        useScatterSeries: root.chartType === "xy_scatter"
        updatesSuspended: root.updatesSuspended
    }

    /*******************************************************************
     * PUBLIC FUNCTIONS - Chart Line Management
     ******************************************************************/

    /**
     * Create a new rendered line. WorkspaceController owns its model entry.
     * @param uniqueId - Unique identifier for the line
     * @param displayName - Display name for the line
     * @param color - Line color (hex string)
     * @param interfaceType - Interface type (e.g., "Serial", "TCP")
     * @param dataId - Data stream identifier
     */
    function createLine(uniqueId, displayName, color, interfaceType, dataId) {
        var lineSeries = root._internalRenderer.createLine(uniqueId, displayName, color)
        console.log("XYChartView: Created line '" + displayName + "' with ID " + uniqueId + " for chart " + root.chartId)
        return lineSeries
    }

    /**
     * Remove a line
     * @param uniqueId - Unique identifier of the line to remove
     */
    function removeLine(uniqueId) {
        root._internalRenderer.removeLine(uniqueId)
        console.log("XYChartView: Removed line " + uniqueId)
    }

    /**
     * Get a rendered line by ID
     * @param uniqueId - Unique identifier
     * @return Line object from model or null
     */
    function getLine(uniqueId) {
        return root._internalRenderer.getLine(uniqueId)
    }

    function updateLineProperties(uniqueId, valueField, displayName, color, visible) {
        root._internalRenderer.updateLine(uniqueId, {
            name: displayName,
            color: color,
            visible: visible
        })
    }

    /**
     * Append a point to a line
     * @param uniqueId - Line identifier
     * @param x - X coordinate
     * @param y - Y coordinate
     */
    function appendPoint(uniqueId, x, y) {
        root._internalRenderer.appendPoint(uniqueId, x, y)
    }

    /**
     * Append multiple points (batch)
     * @param uniqueId - Line identifier
     * @param points - Array of [x, y] tuples
     */
    function appendPointsBatch(uniqueId, points) {
        root._internalRenderer.appendPointsBatch(uniqueId, points)
    }

    /**
     * Clear all points from a line
     * @param uniqueId - Line identifier
     */
    function clearLine(uniqueId) {
        root._internalRenderer.clearLine(uniqueId)
    }

    /**
     * Clear all lines
     */
    function clearAll() {
        root._internalRenderer.clearAll()
    }

    /**
     * Zoom in
     */
    function zoomIn() {
        root._internalRenderer.zoomIn()
    }

    /**
     * Zoom out
     */
    function zoomOut() {
        root._internalRenderer.zoomOut()
    }

    /**
     * Reset zoom
     */
    function resetZoom() {
        root._internalRenderer.resetZoom()
    }

    /**
     * Fit to data
     */
    function fitToData() {
        root._internalRenderer.fitToData()
    }

    function viewSettings() {
        return root._internalRenderer.viewSettings()
    }

    function setViewRange(xMin, xMax, yMin, yMax) {
        root._internalRenderer.setViewRange(xMin, xMax, yMin, yMax)
    }

    Component.onCompleted: {
        console.log("XYChartView initialized for chart: " + root.chartId)
    }

    Component.onDestruction: {
        console.log("XYChartView destroyed for chart: " + root.chartId)
    }
}
