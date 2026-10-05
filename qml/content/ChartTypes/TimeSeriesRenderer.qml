// SPDX-License-Identifier: GPL-3.0-only OR LicenseRef-KymoStudio-Commercial
// Copyright (c) 2026 Christof Seidel
import QtQuick 6.4
import QtQuick.Controls 6.4
import QtCharts 2.3
import Theme 1.0
import "ChartMath.js" as ChartMath

/**
 * TimeSeriesRenderer.qml
 *
 * Time Series Chart renderer for floating windows.
 * Displays Y values cyclically over time with automatic time axis management.
 * Perfect for monitoring single data streams in real-time.
 *
 * Features:
 * - Automatic time axis (X) management
 * - Configurable time window (default: 60 seconds)
 * - Auto-scrolling as new data arrives
 * - Multiple lines/signals supported
 * - Zoom and pan functionality
 *
 * Expected properties from parent FloatingChartWindow:
 * - chartId: Unique identifier for this chart instance
 * - chartTitle: Display name for the chart
 */
Item {
    id: root

    // Public properties that can be set by parent
    property string chartId: ""
    property string chartTitle: "Time Series"
    property var chartData: null  // Reference to chart data model

    // Time Series specific configuration
    property real timeWindow: 60.0  // Time window in seconds (default: 60s)
    property bool autoScroll: true  // Auto-scroll as new data arrives
    property bool autoScaleY: true  // Auto-scale Y axis to fit data
    property real initialYMin: 0
    property real initialYMax: 10
    property bool updatesSuspended: false

    // Internal state
    property var _graphs: ({})  // Dictionary of line series by lineKey
    property var _graphsByUniqueId: ({})  // uniqueId -> [lineKey]
    property real _currentTime: 0  // Current time position (in seconds)
    property real _startTime: 0    // Start time of visible window
    property var _pendingPoints: ({})
    property int maxPendingPointsPerSignal: 2000

    onUpdatesSuspendedChanged: {
        if (!updatesSuspended) flushPendingPoints()
    }
    // Axis scans touch every visible point. Coalesce them so high-frequency
    // batches do not rescan the complete series for every delivery.
    Timer {
        id: yAxisUpdateTimer
        interval: 125
        repeat: false
        onTriggered: if (root.autoScaleY) root.updateYAxisRange()
    }

    // Chart view component
    ChartView {
        id: chart
        anchors.fill: parent
        anchors.topMargin: 40
        // QtCharts antialiasing is expensive for continuously changing series.
        antialiasing: AppTheme.antialiasing
        backgroundColor: AppTheme.surfaces.panel
        legend.visible: false  // legend lives in the chart header
        legend.alignment: Qt.AlignBottom
        legend.labelColor: AppTheme.text.primary
        legend.font.pixelSize: 11

        theme: ChartView.ChartThemeDark
        animationOptions: ChartView.NoAnimation  // Better performance

        // Time Axis (X)
        ValueAxis {
            id: timeAxis
            // An 0 verankerte Teilstriche: die Null wird exakt beschriftet (nicht 1e-15).
            tickType: ValueAxis.TicksDynamic
            tickAnchor: 0
            tickInterval: ChartMath.niceStep(max - min, 6)
            min: 0
            max: root.timeWindow
            labelFormat: "%.4g s"
            labelsFont.pixelSize: 11; labelsFont.family: AppTheme.monoFamily
            labelsColor: AppTheme.text.secondary
            gridVisible: AppTheme.showGrid
            gridLineColor: AppTheme.surfaces.plotGrid
            minorGridLineColor: AppTheme.surfaces.muted
            titleText: qsTr("Zeit (s)")
            titleFont.pixelSize: 11
            titleFont.family: AppTheme.fontFamily
        }

        // Value Axis (Y)
        ValueAxis {
            id: valueAxis
            // An 0 verankerte Teilstriche: die Null wird exakt beschriftet (nicht 1e-15).
            tickType: ValueAxis.TicksDynamic
            tickAnchor: 0
            tickInterval: ChartMath.niceStep(max - min, 5)
            min: root.initialYMin
            max: root.initialYMax
            labelFormat: "%.4g"
            labelsFont.pixelSize: 11; labelsFont.family: AppTheme.monoFamily
            labelsColor: AppTheme.text.secondary
            gridVisible: AppTheme.showGrid
            gridLineColor: AppTheme.surfaces.plotGrid
            minorGridLineColor: AppTheme.surfaces.muted
            titleText: qsTr("Wert")
            titleFont.pixelSize: 11
            titleFont.family: AppTheme.fontFamily
        }

        // Mouse interaction area
        MouseArea {
            id: chartMouseArea
            anchors.fill: parent
            acceptedButtons: Qt.LeftButton | Qt.RightButton
            hoverEnabled: true

            property real lastMouseX: 0
            property real lastMouseY: 0
            property bool isPanning: false

            // Mouse wheel zoom
            onWheel: function(wheel) {
                var factor = wheel.angleDelta.y > 0 ? 0.9 : 1.1
                var plot = chart.plotArea
                if (plot.width <= 0 || plot.height <= 0) return
                var xRatio = Math.max(0, Math.min(1, (wheel.x - plot.x) / plot.width))
                var yRatio = Math.max(0, Math.min(1, 1 - (wheel.y - plot.y) / plot.height))
                var shift = (wheel.modifiers & Qt.ShiftModifier) !== 0
                var ctrl = (wheel.modifiers & Qt.ControlModifier) !== 0
                zoomChart(factor, !ctrl || shift, !shift || ctrl, xRatio, yRatio)
            }

            // Pan on left mouse drag
            onDoubleClicked: root.fitToData()

            onPressed: function(mouse) {
                if (mouse.button === Qt.LeftButton) {
                    lastMouseX = mouse.x
                    lastMouseY = mouse.y
                    isPanning = true
                    root.autoScroll = false
                    root.autoScaleY = false
                }
            }

            onReleased: function(mouse) {
                if (mouse.button === Qt.LeftButton) {
                    isPanning = false
                }
            }

            onPositionChanged: function(mouse) {
                if (isPanning && mouse.buttons & Qt.LeftButton) {
                    var dx = mouse.x - lastMouseX
                    var dy = mouse.y - lastMouseY
                    pan(dx, dy)
                    lastMouseX = mouse.x
                    lastMouseY = mouse.y
                }
            }
        }
    }

    ChartCursor {
        anchors.fill: chart
        chartView: chart
        enabled: AppTheme.showCrosshair
    }

    // Component initialization
    Component.onCompleted: {
        console.log("TimeSeriesRenderer initialized for chart:", chartId)
    }

    // ========== PUBLIC API ==========

    /**
     * Create a new data line
     */
    function _normalizeValueField(valueField) {
        return valueField === "x" ? "x" : "y"
    }

    function _buildLineKey(uniqueId, valueField) {
        var field = _normalizeValueField(valueField)
        return (root.chartId || "main") + "::" + uniqueId + "::" + field
    }

    function _formatDisplayName(displayName, valueField) {
        var suffix = valueField === "x" ? " (X)" : " (Y)"
        return displayName + suffix
    }

    function _registerLineKey(uniqueId, lineKey) {
        if (!_graphsByUniqueId[uniqueId]) {
            _graphsByUniqueId[uniqueId] = []
        }
        if (_graphsByUniqueId[uniqueId].indexOf(lineKey) === -1) {
            _graphsByUniqueId[uniqueId].push(lineKey)
        }
    }

    function _unregisterLineKey(uniqueId, lineKey) {
        if (!_graphsByUniqueId[uniqueId]) return
        var idx = _graphsByUniqueId[uniqueId].indexOf(lineKey)
        if (idx !== -1) {
            _graphsByUniqueId[uniqueId].splice(idx, 1)
        }
        if (_graphsByUniqueId[uniqueId].length === 0) {
            delete _graphsByUniqueId[uniqueId]
        }
    }

    function _getGraphsForUniqueId(uniqueId) {
        var keys = _graphsByUniqueId[uniqueId] || []
        var graphs = []
        for (var i = 0; i < keys.length; i++) {
            var graph = _graphs[keys[i]]
            if (graph) graphs.push(graph)
        }
        return graphs
    }

    function createLine(uniqueId, displayName, color, interfaceType, dataId, valueField) {
        var field = _normalizeValueField(valueField)
        var lineKey = _buildLineKey(uniqueId, field)
        if (_graphs[lineKey]) {
            console.warn("Line already exists:", lineKey)
            return null
        }

        // Create new line series
        var series = chart.createSeries(ChartView.SeriesTypeLine, displayName, timeAxis, valueAxis)
        series.color = color || Qt.rgba(Math.random(), Math.random(), Math.random(), 1)
        series.width = 2
        // GPU-drawn lines only on an OpenGL scene graph (see KymoStudio.prefer_opengl_scene_graph).
        series.useOpenGL = root.GraphicsInfo.api === GraphicsInfo.OpenGL

        _graphs[lineKey] = {
            lineKey: lineKey,
            uniqueId: uniqueId,
            valueField: field,
            series: series,
            displayName: displayName,
            color: series.color,
            visible: true,
            pointCount: 0,
            lastTime: 0
        }
        _registerLineKey(uniqueId, lineKey)

        console.log("Created time series line:", uniqueId, displayName, field)
        return series
    }

    /**
     * Append a single point to a line (with timestamp)
     */
    function _appendPointForGraph(graph, timestamp, value) {
        graph.pointCount = ChartMath.appendBatch(graph.series, [[timestamp, value]],
            AppTheme.displayPointLimit, typeof SeriesBridge !== "undefined" ? SeriesBridge : null)
        graph.lastTime = timestamp
        _currentTime = Math.max(_currentTime, timestamp)
        scheduleYAxisUpdate()
    }

    function appendPoint(uniqueId, timestamp, value) {
        appendPointsBatch(uniqueId, [[value, value, timestamp, true]])
    }

    /**
     * Append points in batch (optimized)
     */
    function appendPointsBatch(uniqueId, points) {
        var graphs = _getGraphsForUniqueId(uniqueId)
        if (!graphs.length || !points || !points.length) return
        if (root.updatesSuspended) { queuePendingPoints(uniqueId, points); return }
        for (var g = 0; g < graphs.length; g++) {
            var graph = graphs[g]
            if (!graph) continue
            var mapped = []
            for (var i = Math.max(0, points.length - AppTheme.displayPointLimit); i < points.length; i++) {
                var point = points[i]
                var t = point.length > 2 && point[2] !== null ? point[2] : point[0]
                // X(t) is meaningful only if the source actually supplies X.
                if (graph.valueField === "x" && point.length > 3 && point[3] === false) continue
                mapped.push([t, graph.valueField === "x" ? point[0] : point[1]])
                _currentTime = Math.max(_currentTime, t)
            }
            graph.pointCount = ChartMath.appendBatch(graph.series, mapped, AppTheme.displayPointLimit,
                typeof SeriesBridge !== "undefined" ? SeriesBridge : null)
            graph.lastTime = _currentTime
        }
        if (autoScroll && _currentTime > timeAxis.max) {
            var windowSize = timeAxis.max - timeAxis.min
            timeAxis.min = _currentTime - windowSize
            timeAxis.max = _currentTime
        }
        scheduleYAxisUpdate()
    }

    /**
     * Remove a data line
     */
    function removeLine(uniqueId, valueField) {
        var keys = []
        if (valueField !== undefined && valueField !== null && valueField !== "") {
            keys.push(_buildLineKey(uniqueId, valueField))
        } else if (_graphsByUniqueId[uniqueId]) {
            keys = _graphsByUniqueId[uniqueId].slice()
        }

        if (keys.length === 0) {
            return false
        }

        for (var i = 0; i < keys.length; i++) {
            var lineKey = keys[i]
            var graph = _graphs[lineKey]
            if (!graph) continue
            chart.removeSeries(graph.series)
            delete _graphs[lineKey]
            _unregisterLineKey(uniqueId, lineKey)
            console.log("Removed time series line:", uniqueId, graph.valueField)
        }
        return true
    }

    /**
     * Clear all points from a line
     */
    function _clearLineByKey(lineKey) {
        var graph = _graphs[lineKey]
        if (!graph) return
        graph.series.removePoints(0, graph.series.count)
        graph.pointCount = 0
        graph.lastTime = 0
    }

    function clearLine(uniqueId, valueField) {
        var keys = []
        if (valueField !== undefined && valueField !== null && valueField !== "") {
            keys.push(_buildLineKey(uniqueId, valueField))
        } else if (_graphsByUniqueId[uniqueId]) {
            keys = _graphsByUniqueId[uniqueId].slice()
        }
        for (var i = 0; i < keys.length; i++) {
            _clearLineByKey(keys[i])
        }
    }

    /**
     * Clear all lines
     */
    function clearAll() {
        _pendingPoints = ({})
        _currentTime = 0
        resetZoom()
        for (var lineKey in _graphs) {
            _clearLineByKey(lineKey)
        }
    }

    /**
     * Toggle line visibility
     */
    function toggleLineVisibility(uniqueId, visible) {
        var keys = _graphsByUniqueId[uniqueId] || []
        for (var i = 0; i < keys.length; i++) {
            var graph = _graphs[keys[i]]
            if (!graph) continue
            graph.visible = visible
            graph.series.visible = visible
        }
    }

    /**
     * Get a line by uniqueId
     */
    function getLine(uniqueId, valueField) {
        if (valueField !== undefined && valueField !== null && valueField !== "") {
            return _graphs[_buildLineKey(uniqueId, valueField)] || null
        }
        var keys = _graphsByUniqueId[uniqueId] || []
        if (keys.length === 0) return null
        return _graphs[keys[0]] || null
    }

    function updateLineProperties(uniqueId, valueField, displayName, color, visible) {
        var graph = getLine(uniqueId, valueField)
        if (!graph) return
        graph.displayName = displayName
        graph.color = color
        graph.visible = visible
        graph.series.name = displayName
        graph.series.color = color
        graph.series.visible = visible
    }

    // ========== ZOOM AND PAN FUNCTIONS ==========

    function zoomChart(factor, zoomX, zoomY, xRatio, yRatio) {
        if (zoomX === undefined) zoomX = true
        if (zoomY === undefined) zoomY = true
        if (xRatio === undefined) xRatio = 0.5
        if (yRatio === undefined) yRatio = 0.5
        if (zoomX) {
            var xRange = ChartMath.zoomRange(timeAxis.min, timeAxis.max, factor, xRatio)
            timeAxis.min = xRange[0]
            timeAxis.max = xRange[1]
            root.autoScroll = false
        }
        if (zoomY) {
            var yRange = ChartMath.zoomRange(valueAxis.min, valueAxis.max, factor, yRatio)
            valueAxis.min = yRange[0]
            valueAxis.max = yRange[1]
            root.autoScaleY = false
        }
    }

    function pan(dx, dy) {
        var plotArea = chart.plotArea
        if (plotArea.width <= 0 || plotArea.height <= 0) {
            return
        }
        var timeRange = timeAxis.max - timeAxis.min
        var valueRange = valueAxis.max - valueAxis.min

        var timeShift = -(dx / plotArea.width) * timeRange
        var valueShift = (dy / plotArea.height) * valueRange

        timeAxis.min += timeShift
        timeAxis.max += timeShift
        valueAxis.min += valueShift
        valueAxis.max += valueShift
    }

    function setTimeWindow(seconds) {
        if (!isFinite(seconds) || seconds <= 0) return
        root.timeWindow = seconds
        timeAxis.max = Math.max(seconds, _currentTime)
        timeAxis.min = timeAxis.max - seconds
        root.autoScroll = true
        root.autoScaleY = true
        scheduleYAxisUpdate()
    }

    function resetZoom() {
        timeAxis.min = 0
        timeAxis.max = root.timeWindow
        valueAxis.min = root.initialYMin
        valueAxis.max = root.initialYMax
        root.autoScroll = true
        root.autoScaleY = true
    }

    function fitToData() {
        var minY = Infinity
        var maxY = -Infinity
        var minT = Infinity
        var maxT = -Infinity

        for (var uniqueId in _graphs) {
            var graph = _graphs[uniqueId]
            if (!graph || !graph.visible) continue

            var series = graph.series
            for (var i = 0; i < series.count; i++) {
                var point = series.at(i)
                minT = Math.min(minT, point.x)
                maxT = Math.max(maxT, point.x)
                minY = Math.min(minY, point.y)
                maxY = Math.max(maxY, point.y)
            }
        }

        if (minT !== Infinity && maxT !== -Infinity) {
            var tr = ChartMath.paddedRange(minT, maxT)
            timeAxis.min = tr[0]; timeAxis.max = tr[1]
        }

        if (minY !== Infinity && maxY !== -Infinity) {
            var yr = ChartMath.paddedRange(minY, maxY, 0.1)
            valueAxis.min = yr[0]; valueAxis.max = yr[1]
        }

        root.autoScroll = false
        root.autoScaleY = false
    }

    function toggleAutoScroll() {
        root.autoScroll = !root.autoScroll
        if (root.autoScroll) {
            root.autoScaleY = true
            scheduleYAxisUpdate()
            // Jump to latest data
            var windowSize = timeAxis.max - timeAxis.min
            timeAxis.min = _currentTime - windowSize
            timeAxis.max = _currentTime
        }
    }

    function updateYAxisRange() {
        var minY = Infinity
        var maxY = -Infinity

        for (var uniqueId in _graphs) {
            var graph = _graphs[uniqueId]
            if (!graph || !graph.visible) continue

            var series = graph.series
            for (var i = 0; i < series.count; i++) {
                var point = series.at(i)
                // Only consider points in visible time window
                if (point.x >= timeAxis.min && point.x <= timeAxis.max) {
                    minY = Math.min(minY, point.y)
                    maxY = Math.max(maxY, point.y)
                }
            }
        }

        if (minY !== Infinity && maxY !== -Infinity) {
            var yr = ChartMath.paddedRange(minY, maxY, 0.1)
            valueAxis.min = yr[0]; valueAxis.max = yr[1]
        }
    }

    function scheduleYAxisUpdate() {
        if (root.autoScaleY && !yAxisUpdateTimer.running) {
            yAxisUpdateTimer.start()
        }
    }

    function queuePendingPoints(uniqueId, points) {
        if (!points || !points.length) return
        var pending = root._pendingPoints[uniqueId] || []
        root._pendingPoints[uniqueId] = ChartMath.tail(pending, points, root.maxPendingPointsPerSignal)
    }

    function flushPendingPoints() {
        var pendingBySignal = root._pendingPoints
        root._pendingPoints = ({})
        for (var uniqueId in pendingBySignal) {
            root.appendPointsBatch(uniqueId, pendingBySignal[uniqueId])
        }
    }

    function viewSettings() {
        return {xMin: timeAxis.min, xMax: timeAxis.max, yMin: valueAxis.min, yMax: valueAxis.max, timeWindow: root.timeWindow, autoScroll: root.autoScroll, autoScaleY: root.autoScaleY}
    }
    function setViewRange(xMin, xMax, yMin, yMax) {
        if (!isFinite(xMin) || !isFinite(xMax) || !isFinite(yMin) || !isFinite(yMax) || xMin >= xMax || yMin >= yMax) return
        root.autoScroll = false; root.autoScaleY = false
        timeAxis.min = xMin; timeAxis.max = xMax
        valueAxis.min = yMin; valueAxis.max = yMax
    }
    function trimToLimit() {
        for (var key in _graphs) {
            var graph = _graphs[key]
            var series = graph.series
            ChartMath.appendBatch(series, [], AppTheme.displayPointLimit, typeof SeriesBridge !== "undefined" ? SeriesBridge : null)
            graph.pointCount = series.count
        }
    }
}
