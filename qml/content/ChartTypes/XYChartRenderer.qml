import QtQuick 6.4
import QtQuick.Controls 6.4
import QtCharts 2.3
import Theme 1.0
import "ChartMath.js" as ChartMath

/**
 * XYChartRenderer.qml
 *
 * 2D Chart renderer for floating windows.
 * Displays XY line charts with full zoom, pan, and scroll functionality.
 *
 * Expected properties from parent FloatingChartWindow:
 * - chartId: Unique identifier for this chart instance
 * - chartTitle: Display name for the chart
 */
Item {
    id: root

    // Public properties that can be set by parent
    property string chartId: ""
    property string chartTitle: "XY Chart"
    property var chartData: null  // Reference to chart data model

    // Chart configuration
    property real initialXMin: 0
    property real initialXMax: 10
    property real initialYMin: 0
    property real initialYMax: 10
    property bool useScatterSeries: false
    // QtCharts OpenGL acceleration renders blank without an OpenGL scene graph
    // (e.g. software rendering), so it follows the active graphics API.
    property bool useOpenGL: GraphicsInfo.api === GraphicsInfo.OpenGL
    property bool updatesSuspended: false

    // Internal state
    property var _graphs: ({})  // Dictionary of line series by uniqueId
    property var _pendingPoints: ({})
    property int maxPendingPointsPerSignal: 2000

    onUpdatesSuspendedChanged: {
        if (!updatesSuspended) flushPendingPoints()
    }
    // Chart view component
    ChartView {
        id: chart
        anchors.fill: parent
        anchors.topMargin: 40
        // Continuous charts stay responsive at high point counts without MSAA.
        antialiasing: AppTheme.antialiasing
        backgroundColor: AppTheme.surfaces.panel
        legend.visible: false  // legend lives in the chart header
        legend.alignment: Qt.AlignBottom
        legend.labelColor: AppTheme.text.primary
        legend.font.pixelSize: 11

        theme: ChartView.ChartThemeDark
        animationOptions: ChartView.NoAnimation  // Better performance

        // X Axis
        ValueAxis {
            id: xAxis
            // An 0 verankerte Teilstriche: die Null wird exakt beschriftet (nicht 1e-15).
            tickType: ValueAxis.TicksDynamic
            tickAnchor: 0
            tickInterval: ChartMath.niceStep(max - min, 6)
            min: root.initialXMin
            max: root.initialXMax
            labelFormat: "%.4g"
            labelsFont.pixelSize: 11; labelsFont.family: AppTheme.monoFamily
            labelsColor: AppTheme.text.secondary
            gridVisible: AppTheme.showGrid
            gridLineColor: AppTheme.surfaces.plotGrid
            minorGridLineColor: AppTheme.surfaces.muted
            titleText: "X"
            titleFont.pixelSize: 11
            titleFont.family: AppTheme.fontFamily
        }

        // Y Axis
        ValueAxis {
            id: yAxis
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
            titleText: "Y"
            titleFont.pixelSize: 11
            titleFont.family: AppTheme.fontFamily
        }

        // Mouse interaction area
        MouseArea {
            id: chartMouseArea
            anchors.fill: parent
            acceptedButtons: Qt.LeftButton | Qt.RightButton
            hoverEnabled: true

            // Mouse wheel zoom (centered on cursor)
            onWheel: function(wheel) {
                var factor = wheel.angleDelta.y > 0 ? 0.9 : 1.1

                // Calculate mouse position in chart coordinates
                var plotArea = chart.plotArea
                if (plotArea.width <= 0 || plotArea.height <= 0) {
                    return
                }
                var mouseXRatio = Math.max(0, Math.min(1, (wheel.x - plotArea.x) / plotArea.width))
                var mouseYRatio = Math.max(0, Math.min(1, 1 - (wheel.y - plotArea.y) / plotArea.height))
                var shift = (wheel.modifiers & Qt.ShiftModifier) !== 0
                var ctrl = (wheel.modifiers & Qt.ControlModifier) !== 0
                if (!ctrl || shift) {
                    var xRange = ChartMath.zoomRange(xAxis.min, xAxis.max, factor, mouseXRatio)
                    xAxis.min = xRange[0]
                    xAxis.max = xRange[1]
                }
                if (!shift || ctrl) {
                    var yRange = ChartMath.zoomRange(yAxis.min, yAxis.max, factor, mouseYRatio)
                    yAxis.min = yRange[0]
                    yAxis.max = yRange[1]
                }
            }

            // Pan with left mouse button
            property real lastMouseX: 0
            property real lastMouseY: 0

            onDoubleClicked: root.fitToData()

            onPressed: function(mouse) {
                if (mouse.button === Qt.LeftButton) {
                    lastMouseX = mouse.x
                    lastMouseY = mouse.y
                }
            }

            onPositionChanged: function(mouse) {
                if (pressedButtons & Qt.LeftButton) {
                    var deltaX = mouse.x - lastMouseX
                    var deltaY = mouse.y - lastMouseY

                    // Convert pixel movement to chart coordinates
                    var plotArea = chart.plotArea
                    if (plotArea.width <= 0 || plotArea.height <= 0) {
                        return
                    }
                    var xRange = xAxis.max - xAxis.min
                    var yRange = yAxis.max - yAxis.min

                    var xShift = -(deltaX / plotArea.width) * xRange
                    var yShift = (deltaY / plotArea.height) * yRange

                    xAxis.min += xShift
                    xAxis.max += xShift
                    yAxis.min += yShift
                    yAxis.max += yShift

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

    /*******************************************************************
     * PUBLIC FUNCTIONS - Chart Manipulation
     ******************************************************************/

    /**
     * Zoom in by 20%
     */
    function zoomIn() {
        zoomChart(0.8)
    }

    /**
     * Zoom out by 25%
     */
    function zoomOut() {
        zoomChart(1.25)
    }

    /**
     * Zoom both axes by factor (proportional zoom)
     */
    function zoomChart(factor) {
        zoomAxis(xAxis, factor)
        zoomAxis(yAxis, factor)
    }

    /**
     * Zoom single axis by factor
     */
    function zoomAxis(axis, factor) {
        var range = axis.max - axis.min
        var center = (axis.max + axis.min) / 2
        var newRange = range * factor

        axis.min = center - newRange / 2
        axis.max = center + newRange / 2
    }

    /**
     * Reset zoom to initial view
     */
    function resetZoom() {
        xAxis.min = root.initialXMin
        xAxis.max = root.initialXMax
        yAxis.min = root.initialYMin
        yAxis.max = root.initialYMax
    }

    /**
     * Fit zoom to actual data range (with 10% padding)
     */
    function fitToData() {
        var minX = Infinity, maxX = -Infinity
        var minY = Infinity, maxY = -Infinity

        for(var graphId in _graphs) {
            var series = _graphs[graphId]
            if (!series.visible) continue
            for(var i = 0; i < series.count; i++) {
                var point = series.at(i)
                minX = Math.min(minX, point.x)
                maxX = Math.max(maxX, point.x)
                minY = Math.min(minY, point.y)
                maxY = Math.max(maxY, point.y)
            }
        }

        // Add 10% padding
        if(minX !== Infinity && maxX !== -Infinity) {
            var xr = ChartMath.paddedRange(minX, maxX, 0.1)
            xAxis.min = xr[0]; xAxis.max = xr[1]
        }

        if(minY !== Infinity && maxY !== -Infinity) {
            var yr = ChartMath.paddedRange(minY, maxY, 0.1)
            yAxis.min = yr[0]; yAxis.max = yr[1]
        }
    }

    /*******************************************************************
     * PUBLIC FUNCTIONS - Line Management
     ******************************************************************/

    /**
     * Create a new line series
     * @param uniqueId - Unique identifier for the line
     * @param displayName - Display name for the line
     * @param color - Line color (hex string or int)
     * @return LineSeries object
     */
    function createLine(uniqueId, displayName, color) {
        var seriesType = root.useScatterSeries ? ChartView.SeriesTypeScatter : ChartView.SeriesTypeLine
        var series = chart.createSeries(seriesType, displayName, xAxis, yAxis)

        if (color !== undefined) {
            series.color = color
        }

        if (root.useScatterSeries) {
            if (series.markerSize !== undefined) {
                series.markerSize = 8
            }
            if (series.borderColor !== undefined && color !== undefined) {
                series.borderColor = color
            }
        } else {
            series.width = 2
        }

        if (series.useOpenGL !== undefined) {
            series.useOpenGL = root.useOpenGL
        }

        _graphs[uniqueId] = series

        console.log("XYChartRenderer: Created series '" + displayName + "' with ID " + uniqueId)
        return series
    }

    /**
     * Remove a line series
     * @param uniqueId - Unique identifier of the line to remove
     */
    function removeLine(uniqueId) {
        if(_graphs[uniqueId]) {
            chart.removeSeries(_graphs[uniqueId])
            delete _graphs[uniqueId]
            console.log("XYChartRenderer: Removed line " + uniqueId)
        }
    }

    /**
     * Get a line series by ID
     * @param uniqueId - Unique identifier
     * @return LineSeries object or null
     */
    function getLine(uniqueId) {
        return _graphs[uniqueId] || null
    }

    /**
     * Append a single point to a line
     * @param uniqueId - Line identifier
     * @param x - X coordinate
     * @param y - Y coordinate
     */
    function appendPoint(uniqueId, x, y) {
        var series = _graphs[uniqueId]
        if(!series) return
        if (root.updatesSuspended) {
            queuePendingPoints(uniqueId, [[x, y]])
            return
        }

        // Limit maximum points for performance
        var maxPoints = AppTheme.displayPointLimit
        if(series.count >= maxPoints) {
            series.removePoints(0, 100)  // Remove oldest 100 points
        }

        series.append(x, y)
    }

    /**
     * Append multiple points at once (BATCH - much faster!)
     * @param uniqueId - Line identifier
     * @param points - Array of [x, y] tuples
     */
    function appendPointsBatch(uniqueId, points) {
        var series = _graphs[uniqueId]
        if (!series || !points || !points.length) return
        if (root.updatesSuspended) { queuePendingPoints(uniqueId, points); return }
        var accepted = []
        for (var i = 0; i < points.length; i++) {
            var p = points[i]
            // A clock coordinate is not a measured Cartesian X value.
            if (p.length > 3 && p[3] === false) continue
            accepted.push([p[0], p[1]])
        }
        ChartMath.appendBatch(series, accepted, AppTheme.displayPointLimit,
            typeof SeriesBridge !== "undefined" ? SeriesBridge : null)
    }

    /**
     * Clear all points from a line
     * @param uniqueId - Line identifier
     */
    function clearLine(uniqueId) {
        var series = _graphs[uniqueId]
        if(series) {
            series.clear()
        }
    }

    /**
     * Clear all lines
     */
    function clearAll() {
        _pendingPoints = ({})
        for(var graphId in _graphs) {
            _graphs[graphId].clear()
        }
    }

    /**
     * Update line properties
     * @param uniqueId - Line identifier
     * @param properties - Object with properties to update (name, color, width, etc.)
     */
    function updateLine(uniqueId, properties) {
        var series = _graphs[uniqueId]
        if(!series) {
            console.warn("XYChartRenderer: Line not found: " + uniqueId)
            return
        }

        if(properties.name !== undefined) {
            series.name = properties.name
        }
        if(properties.color !== undefined) {
            series.color = properties.color
        }
        if(properties.width !== undefined) {
            series.width = properties.width
        }
        if(properties.visible !== undefined) {
            series.visible = properties.visible
        }
    }

    /*******************************************************************
     * COMPONENT LIFECYCLE
     ******************************************************************/

    Component.onCompleted: {
        console.log("XYChartRenderer initialized for chart: " + root.chartId)
    }

    Component.onDestruction: {
        console.log("XYChartRenderer destroyed for chart: " + root.chartId)
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
        return {xMin: xAxis.min, xMax: xAxis.max, yMin: yAxis.min, yMax: yAxis.max}
    }
    function setViewRange(xMin, xMax, yMin, yMax) {
        if (!isFinite(xMin) || !isFinite(xMax) || !isFinite(yMin) || !isFinite(yMax) || xMin >= xMax || yMin >= yMax) return
        xAxis.min = xMin; xAxis.max = xMax
        yAxis.min = yMin; yAxis.max = yMax
    }
    function trimToLimit() {
        for (var key in _graphs) {
            var graph = _graphs[key]
            var series = graph
            ChartMath.appendBatch(series, [], AppTheme.displayPointLimit, typeof SeriesBridge !== "undefined" ? SeriesBridge : null)

        }
    }
}
