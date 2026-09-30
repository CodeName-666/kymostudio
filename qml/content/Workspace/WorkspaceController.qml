import QtQuick 6.4
import "../Models"

/**
 * Single owner of chart, signal, assignment and live-routing state.
 * Views express user intent through this interface and never mutate renderer
 * or workspace state through a second path.
 */
QtObject {
    id: root
    objectName: "workspaceController"

    property var backendInterface: null
    property var appController: null
    property var backendEvents: null

    property var chartModel: ListModel {}
    property var chartLineModel: ChartLineModel {}
    property var signalModel: SignalModel {}
    property var messageModel: MessageModel {}
    property var availableCharts: []
    property string activeChartId: ""
    // "tile" | "focus" | "free": how chart windows are arranged in the workspace.
    property string layoutMode: "tile"
    // Bumped on every assignment change so bindings can re-evaluate derived values.
    property int assignmentRevision: 0
    // uniqueId of the signal currently dragged from the source list (drop zones show while set).
    property string draggedSignalId: ""
    property int _nextChartNumber: 0
    property var _routeCache: ({})
    property var _restoredViews: ({})
    property Connections assignmentWatcher: Connections {
        target: root.chartLineModel
        function onModelChanged() { root._routeCache = ({}); root.assignmentRevision++ }
    }

    property var _windows: ({})
    property var _pending2D: ({})
    property var _pending3D: ({})
    property int maxPendingPointsPerSeries: 2000
    property bool initialized: false
    property int registeredWindowCount: 0

    signal chartsChanged()
    signal editLineRequested(string lineKey)
    signal addSignalRequested()
    signal chartActivated(string chartId)

    function initialize(controller, backend) {
        if (root.initialized) shutdown()
        root.appController = controller
        root.backendInterface = backend
        root.backendEvents = controller && controller.events ? controller.events() : null
        var events = root.backendEvents
        if (events) {
            if (events.newGraph) events.newGraph.connect(onNewGraph)
            if (events.message_received) events.message_received.connect(onMessageReceived)
            if (events.signals_removed) events.signals_removed.connect(onSignalsRemoved)
            if (events.append_graph_point) events.append_graph_point.connect(routeGraphPoint)
            if (events.append_graph_points_batch) events.append_graph_points_batch.connect(routeGraphPointsBatch)
            if (events.append_graph_point_3d) events.append_graph_point_3d.connect(routeGraphPoint3D)
            if (events.append_graph_points_batch_3d) events.append_graph_points_batch_3d.connect(routeGraphPointsBatch3D)
        }
        root.initialized = true
        _refreshAvailableCharts()
    }

    function shutdown() {
        var events = root.backendEvents
        if (events) {
            try { if (events.newGraph) events.newGraph.disconnect(onNewGraph) } catch (e) {}
            try { if (events.message_received) events.message_received.disconnect(onMessageReceived) } catch (e) {}
            try { if (events.signals_removed) events.signals_removed.disconnect(onSignalsRemoved) } catch (e) {}
            try { if (events.append_graph_point) events.append_graph_point.disconnect(routeGraphPoint) } catch (e) {}
            try { if (events.append_graph_points_batch) events.append_graph_points_batch.disconnect(routeGraphPointsBatch) } catch (e) {}
            try { if (events.append_graph_point_3d) events.append_graph_point_3d.disconnect(routeGraphPoint3D) } catch (e) {}
            try { if (events.append_graph_points_batch_3d) events.append_graph_points_batch_3d.disconnect(routeGraphPointsBatch3D) } catch (e) {}
        }
        root.backendEvents = null
        root.initialized = false
    }

    function _chartIndex(chartId) {
        for (var i = 0; i < chartModel.count; i++) {
            if (chartModel.get(i).chartId === chartId) return i
        }
        return -1
    }

    function chartTypeForId(chartId) {
        var index = _chartIndex(chartId)
        return index === -1 ? "" : chartModel.get(index).chartType
    }

    function chartTitleForId(chartId) {
        var index = _chartIndex(chartId)
        return index === -1 ? chartId : chartModel.get(index).chartTitle
    }

    function createChart(chartType, chartTitle, chartId, x, y, width, height) {
        if (chartModel.count >= 16) { warn("Maximal 16 Diagramme pro Arbeitsfläche."); return "" }
        if (["time_series", "xy_line", "xy_scatter", "xyz_scatter"].indexOf(chartType) === -1) return ""
        var resolvedId = chartId && chartId !== "" ? chartId : ("chart_" + chartType + "_" + Date.now() + "_" + (++_nextChartNumber))
        if (_chartIndex(resolvedId) !== -1) {
            console.warn("WorkspaceController: Chart already exists: " + resolvedId)
            return ""
        }
        var firstChart = chartModel.count === 0
        chartModel.append({
            chartId: resolvedId,
            chartType: chartType || "time_series",
            chartTitle: chartTitle || resolvedId,
            xPos: x !== undefined && x !== null ? x : 100,
            yPos: y !== undefined && y !== null ? y : 100,
            windowWidth: width !== undefined && width !== null ? width : 800,
            windowHeight: height !== undefined && height !== null ? height : 600,
            maximized: firstChart,
            minimized: false,
            restoreX: x !== undefined && x !== null ? x : 100,
            restoreY: y !== undefined && y !== null ? y : 100,
            restoreWidth: width !== undefined && width !== null ? width : 800,
            restoreHeight: height !== undefined && height !== null ? height : 600,
            zOrder: chartModel.count,
            docked: false,
            dockPosition: ""
        })
        activeChartId = resolvedId
        _refreshAvailableCharts()
        console.log("WorkspaceController: Created chart " + resolvedId)
        return resolvedId
    }

    function removeChart(chartId) {
        var index = _chartIndex(chartId)
        if (index === -1) return false

        var lineKeys = []
        for (var i = 0; i < chartLineModel.count; i++) {
            var line = chartLineModel.get(i)
            if (line.chartId !== chartId) continue
            signalModel.addOrUpdate(line.uniqueId, line.displayName, line.color, line.interfaceType, line.dataId, line.interfaceSettings)
            lineKeys.push(line.lineKey)
        }
        for (var k = 0; k < lineKeys.length; k++) removeChartLine(lineKeys[k])

        delete root._pending2D[chartId]
        delete root._pending3D[chartId]
        chartModel.remove(index)
        _refreshAvailableCharts()
        console.log("WorkspaceController: Removed chart " + chartId)
        return true
    }

    function renameChart(chartId, chartTitle) {
        var index = _chartIndex(chartId)
        if (index === -1 || !chartTitle) return false
        chartModel.setProperty(index, "chartTitle", chartTitle)
        chartLineModel.updateChartTitle(chartId, chartTitle)
        var window = root._windows[chartId]
        if (window) window.chartTitle = chartTitle
        _refreshAvailableCharts()
        return true
    }

    function updateChartGeometry(chartId, x, y, width, height) {
        var index = _chartIndex(chartId)
        if (index === -1) return
        chartModel.setProperty(index, "xPos", Math.round(x))
        chartModel.setProperty(index, "yPos", Math.round(y))
        chartModel.setProperty(index, "windowWidth", Math.round(width))
        chartModel.setProperty(index, "windowHeight", Math.round(height))
    }

    function updateChartDocking(chartId, docked, position) {
        var index = _chartIndex(chartId)
        if (index === -1) return
        chartModel.setProperty(index, "docked", !!docked)
        chartModel.setProperty(index, "dockPosition", position || "")
    }

    function updateChartWindowState(chartId, minimized, maximized, restoreGeometry) {
        var index = _chartIndex(chartId)
        if (index === -1) return
        chartModel.setProperty(index, "minimized", !!minimized)
        chartModel.setProperty(index, "maximized", !!maximized)
        if (restoreGeometry) {
            chartModel.setProperty(index, "restoreX", Math.round(restoreGeometry.x))
            chartModel.setProperty(index, "restoreY", Math.round(restoreGeometry.y))
            chartModel.setProperty(index, "restoreWidth", Math.round(restoreGeometry.width))
            chartModel.setProperty(index, "restoreHeight", Math.round(restoreGeometry.height))
        }
    }

    function bringToFront(chartId) {
        root.activeChartId = chartId
        root.chartActivated(chartId)
        var index = _chartIndex(chartId)
        if (index === -1) return
        var maxZ = 0
        for (var i = 0; i < chartModel.count; i++) maxZ = Math.max(maxZ, chartModel.get(i).zOrder)
        chartModel.setProperty(index, "zOrder", maxZ + 1)
    }

    function registerWindow(chartId, window) {
        if (!window) return
        root._windows[chartId] = window
        root.registeredWindowCount = Object.keys(root._windows).length
        Qt.callLater(function() { root.rendererReady(chartId) })
    }

    function unregisterWindow(chartId, window) {
        if (root._windows[chartId] === window) {
            delete root._windows[chartId]
            root.registeredWindowCount = Object.keys(root._windows).length
        }
    }

    function windowForChart(chartId) {
        return root._windows[chartId] || null
    }

    function rendererReady(chartId) {
        var window = root._windows[chartId]
        if (!window) return
        for (var i = 0; i < chartLineModel.count; i++) {
            var line = chartLineModel.get(i)
            if (line.chartId === chartId) _materializeLine(window, line)
        }
        _flushPendingForChart(chartId)
        var view = root._restoredViews[chartId]
        if (view && window.chartRenderer && window.chartRenderer.setViewRange) {
            var renderer = window.chartRenderer
            if (view.timeWindow !== undefined) renderer.timeWindow = view.timeWindow
            renderer.setViewRange(view.xMin, view.xMax, view.yMin, view.yMax)
            if (view.autoScroll !== undefined) renderer.autoScroll = view.autoScroll
            if (view.autoScaleY !== undefined) renderer.autoScaleY = view.autoScaleY
            delete root._restoredViews[chartId]
        }
    }

    function _materializeLine(window, line) {
        if (!window || !line) return null
        var series = window.createSeries(line.uniqueId, line.displayName, line.color, line.interfaceType, line.dataId, line.valueField)
        if (series) {
            window.updateSeries(line.uniqueId, line.valueField, line.displayName, line.color, line.visible)
        }
        return series
    }

    function _refreshAvailableCharts() {
        root._routeCache = ({})
        var charts = []
        for (var i = 0; i < chartModel.count; i++) {
            var chart = chartModel.get(i)
            charts.push({ chartId: chart.chartId, chartTitle: chart.chartTitle, chartType: chart.chartType })
        }
        root.availableCharts = charts
        root.chartsChanged()
    }

    function _extractDataId(uniqueId) {
        var parts = String(uniqueId).split("_")
        var result = parts.length ? parseInt(parts[parts.length - 1]) : 0
        return isNaN(result) ? 0 : result
    }

    function onNewGraph(uniqueId, displayName, color, interfaceType) {
        var existing = signalModel.getSignal(uniqueId)
        signalModel.addOrUpdate(
            uniqueId,
            existing ? existing.displayName : displayName,
            existing ? existing.color : color,
            interfaceType,
            _extractDataId(uniqueId),
            existing ? existing.interfaceSettings : {}
        )
    }

    function onMessageReceived(message) {
        messageModel.addOrUpdateFromBackend(message)
    }

    function onSignalsRemoved(uniqueIds) {
        if (!uniqueIds) return
        for (var i = 0; i < uniqueIds.length; i++) _removeSignalState(uniqueIds[i], false)
    }

    function addSignal(uniqueId, displayName, color, interfaceType, dataId, interfaceSettings) {
        if (root.backendInterface && root.backendInterface.set_signal_ignored) {
            root.backendInterface.set_signal_ignored(uniqueId, false)
        }
        if (root.backendInterface && root.backendInterface.update_chart_line) {
            root.backendInterface.update_chart_line(uniqueId, displayName, color.toString())
        }
        return signalModel.addOrUpdate(uniqueId, displayName, color, interfaceType, dataId, interfaceSettings)
    }

    function removeSignal(uniqueId) {
        return _removeSignalState(uniqueId, true)
    }

    function _removeSignalState(uniqueId, ignoreInBackend) {
        var keys = []
        for (var i = 0; i < chartLineModel.count; i++) {
            if (chartLineModel.get(i).uniqueId === uniqueId) keys.push(chartLineModel.get(i).lineKey)
        }
        for (var j = 0; j < keys.length; j++) removeChartLine(keys[j])
        signalModel.removeSignal(uniqueId)
        messageModel.removeMessage(uniqueId)
        if (root.backendInterface) {
            if (ignoreInBackend && root.backendInterface.set_signal_ignored) {
                root.backendInterface.set_signal_ignored(uniqueId, true)
            } else if (ignoreInBackend && root.backendInterface.remove_chart_line) {
                root.backendInterface.remove_chart_line(uniqueId)
            }
        }
        return true
    }

    function updateSignal(lineKey, displayName, color) {
        var line = chartLineModel.getLineByKey(lineKey)
        return line ? updateSignalById(line.uniqueId, displayName, color) : false
    }

    function updateSignalById(uniqueId, displayName, color) {
        var base = signalModel.getSignal(uniqueId)
        if (!base) return false
        signalModel.addOrUpdate(uniqueId, displayName, color, base.interfaceType, base.dataId, base.interfaceSettings)
        for (var i = 0; i < chartLineModel.count; i++) {
            var instance = chartLineModel.get(i)
            if (instance.uniqueId !== uniqueId) continue
            var instanceName = _lineDisplayName(displayName, instance.valueField)
            var instanceChartId = instance.chartId
            var instanceValueField = instance.valueField
            var instanceVisible = instance.visible
            chartLineModel.updateLine(instance.lineKey, { displayName: instanceName, color: color })
            var window = root._windows[instanceChartId]
            if (window) window.updateSeries(uniqueId, instanceValueField, instanceName, color, instanceVisible)
        }
        if (root.backendInterface && root.backendInterface.update_chart_line) {
            root.backendInterface.update_chart_line(uniqueId, displayName, color.toString())
        }
        return true
    }

    function setLineVisibility(lineKey, visible) {
        var line = chartLineModel.getLineByKey(lineKey)
        if (!line) return false
        var chartId = line.chartId
        var uniqueId = line.uniqueId
        var valueField = line.valueField
        var displayName = line.displayName
        var color = line.color
        var updated = chartLineModel.toggleVisibility(lineKey, visible)
        var window = root._windows[chartId]
        if (updated && window) window.updateSeries(uniqueId, valueField, displayName, color, visible)
        return updated
    }

    function removeChartLine(lineKey) {
        var line = chartLineModel.getLineByKey(lineKey)
        if (!line) return false
        var chartId = line.chartId
        var uniqueId = line.uniqueId
        var valueField = line.valueField
        var window = root._windows[chartId]
        if (window) window.removeSeries(uniqueId, valueField)
        var removed = chartLineModel.removeLine(lineKey)
        if (removed && !hasAssignedSignal(chartId, uniqueId)) {
            if (root._pending2D[chartId]) delete root._pending2D[chartId][uniqueId]
            if (root._pending3D[chartId]) delete root._pending3D[chartId][uniqueId]
        }
        return removed
    }

    function _assignmentKey(chartId, chartType, valueField) {
        return chartType === "time_series" || valueField ? chartId + "::" + (valueField || "y") : chartId
    }

    function _lineDisplayName(displayName, valueField) {
        return valueField ? displayName + " (" + String(valueField).toUpperCase() + ")" : displayName
    }

    function setSignalCharts(uniqueId, assignments) {
        assignments = assignments || []
        var desired = ({})
        for (var i = 0; i < assignments.length; i++) {
            var assignment = assignments[i]
            if (!assignment || !assignment.chartId) continue
            var chartType = assignment.chartType || chartTypeForId(assignment.chartId)
            if (!chartType) continue
            var valueField = chartType === "time_series" ? (assignment.valueField || "y") : null
            desired[_assignmentKey(assignment.chartId, chartType, valueField)] = {
                chartId: assignment.chartId,
                chartType: chartType,
                valueField: valueField
            }
        }

        var removeKeys = []
        for (var j = 0; j < chartLineModel.count; j++) {
            var current = chartLineModel.get(j)
            if (current.uniqueId !== uniqueId) continue
            var currentType = chartTypeForId(current.chartId)
            if (!desired[_assignmentKey(current.chartId, currentType, current.valueField)]) removeKeys.push(current.lineKey)
        }
        for (var r = 0; r < removeKeys.length; r++) removeChartLine(removeKeys[r])

        var base = signalModel.getSignal(uniqueId)
        if (!base) return false
        if (root.backendInterface && root.backendInterface.set_signal_ignored) root.backendInterface.set_signal_ignored(uniqueId, false)

        for (var key in desired) {
            var target = desired[key]
            if (chartLineModel.hasLineForChart(uniqueId, target.chartId, target.valueField)) continue
            var assignedCount = 0
            for (var countIndex = 0; countIndex < chartLineModel.count; countIndex++)
                if (chartLineModel.get(countIndex).chartId === target.chartId) assignedCount++
            if (assignedCount >= 64) { warn("Maximal 64 Kurven pro Diagramm."); continue }
            var title = chartTitleForId(target.chartId)
            var modelName = _lineDisplayName(base.displayName, target.valueField)
            chartLineModel.addLine(uniqueId, modelName, base.color, base.interfaceType, base.dataId, base.interfaceSettings, target.chartId, title, target.valueField)
            var line = chartLineModel.getLineForChart(uniqueId, target.chartId, target.valueField)
            var window = root._windows[target.chartId]
            if (window && line) _materializeLine(window, line)
        }
        return true
    }

    function signalAssignments(uniqueId) {
        var result = []
        for (var i = 0; i < chartLineModel.count; i++) {
            var line = chartLineModel.get(i)
            if (line.uniqueId === uniqueId)
                result.push({ chartId: line.chartId, chartType: chartTypeForId(line.chartId), valueField: line.valueField || null })
        }
        return result
    }

    /** Adds one chart assignment and keeps every existing one of the signal. */
    function assignSignal(uniqueId, chartId, valueField) {
        var assignments = signalAssignments(uniqueId)
        assignments.push({ chartId: chartId, chartType: chartTypeForId(chartId), valueField: valueField || null })
        return setSignalCharts(uniqueId, assignments)
    }

    function unassignSignal(uniqueId, chartId, valueField) {
        var line = chartLineModel.getLineForChart(uniqueId, chartId, valueField || null)
        return line ? removeChartLine(line.lineKey) : false
    }

    function getAvailableConnections() {
        if (!root.backendInterface || !root.backendInterface.get_connections) return []
        var connections = root.backendInterface.get_connections()
        var result = []
        for (var i = 0; i < connections.length; i++) {
            result.push({ id: connections[i].id, name: connections[i].name, type: connections[i].type, status: connections[i].status })
        }
        return result
    }

    function getUsedDataIds() {
        return chartLineModel.getAllUniqueIds()
    }

    function hasAssignedSignal(chartId, uniqueId) {
        for (var i = 0; i < chartLineModel.count; i++) {
            var line = chartLineModel.get(i)
            if (line.chartId === chartId && line.uniqueId === uniqueId) return true
        }
        return false
    }

    function _assignedChartIds(uniqueId, require3D) {
        var cacheKey = uniqueId + (require3D ? "::3d" : "::2d")
        if (root._routeCache[cacheKey]) return root._routeCache[cacheKey]
        var result = []
        var seen = ({})
        for (var i = 0; i < chartLineModel.count; i++) {
            var line = chartLineModel.get(i)
            if (line.uniqueId !== uniqueId || seen[line.chartId]) continue
            var is3D = String(chartTypeForId(line.chartId)).indexOf("xyz_") === 0
            if (is3D !== require3D) continue
            seen[line.chartId] = true
            result.push(line.chartId)
        }
        root._routeCache[cacheKey] = result
        return result
    }

    function _queue(target, chartId, uniqueId, points) {
        if (!target[chartId]) target[chartId] = ({})
        var pending = target[chartId][uniqueId] || []
        if (points.length >= root.maxPendingPointsPerSeries) pending = points.slice(points.length - root.maxPendingPointsPerSeries)
        else pending = pending.slice(Math.max(0, pending.length + points.length - root.maxPendingPointsPerSeries)).concat(points)
        target[chartId][uniqueId] = pending
    }

    function routeGraphPoint(uniqueId, point) {
        if (!point) return
        var x = point.x !== undefined ? point.x : 0
        var y = point.y !== undefined ? point.y : 0
        var t = point.t !== undefined ? point.t : x
        routeGraphPointsBatch(uniqueId, [[x, y, t, point.hasExplicitX !== false]])
    }

    function routeGraphPointsBatch(uniqueId, points) {
        if (!points || !points.length) return
        var chartIds = _assignedChartIds(uniqueId, false)
        for (var i = 0; i < chartIds.length; i++) {
            var chartId = chartIds[i]
            var window = root._windows[chartId]
            if (!window || !window.appendPointsBatch(uniqueId, points)) _queue(root._pending2D, chartId, uniqueId, points)
        }
    }

    function routeGraphPoint3D(uniqueId, point) {
        if (!point) return
        routeGraphPointsBatch3D(uniqueId, [[point.x || 0, point.y || 0, point.z || 0]])
    }

    function routeGraphPointsBatch3D(uniqueId, points) {
        if (!points || !points.length) return
        var chartIds = _assignedChartIds(uniqueId, true)
        for (var i = 0; i < chartIds.length; i++) {
            var chartId = chartIds[i]
            var window = root._windows[chartId]
            if (!window || !window.appendPointsBatch3D(uniqueId, points)) _queue(root._pending3D, chartId, uniqueId, points)
        }
    }

    function _flushPendingForChart(chartId) {
        var window = root._windows[chartId]
        if (!window) return
        var pending2D = root._pending2D[chartId] || ({})
        var pending3D = root._pending3D[chartId] || ({})
        delete root._pending2D[chartId]
        delete root._pending3D[chartId]
        for (var uniqueId in pending2D) {
            if (hasAssignedSignal(chartId, uniqueId)) window.appendPointsBatch(uniqueId, pending2D[uniqueId])
        }
        for (var uniqueId3D in pending3D) {
            if (hasAssignedSignal(chartId, uniqueId3D)) window.appendPointsBatch3D(uniqueId3D, pending3D[uniqueId3D])
        }
    }

    function warn(message) {
        if (appController && appController.ui_handle && appController.ui_handle.showStatusMessage)
            appController.ui_handle.showStatusMessage("warning", message)
        else console.warn(message)
    }

    function focusChart(chartId) {
        for (var id in _windows) {
            var window = _windows[id]
            if (window.isMinimized && id === chartId) window.toggleMinimize()
            if (window.isMaximized && id !== chartId) window.toggleMaximize()
        }
        var target = _windows[chartId]
        if (target) {
            target.isDocked = false
            updateChartDocking(chartId, false, "")
            if (!target.isMaximized) target.toggleMaximize()
        }
        bringToFront(chartId)
    }

    function tileCharts(width, height) {
        if (!chartModel.count || width <= 0 || height <= 0) return
        var count = chartModel.count
        var cols = Math.max(1, Math.min(count, Math.round(Math.sqrt(count * width / height))))
        var rows = Math.ceil(count / cols)
        var gap = 12
        for (var i = 0; i < count; i++) {
            var chartId = chartModel.get(i).chartId
            var window = _windows[chartId]
            if (window) {
                window.isDocked = false
                window.isMaximized = false
                window.isMinimized = false
            }
            updateChartDocking(chartId, false, "")
            updateChartWindowState(chartId, false, false, null)
        }
        Qt.callLater(function() {
            for (var n = 0; n < chartModel.count; n++) {
                var key = chartModel.get(n).chartId
                // The last row may hold fewer charts; they share its full width.
                var row = Math.floor(n / cols)
                var inRow = row === rows - 1 ? count - cols * (rows - 1) : cols
                var x = (n % cols) * width / inRow + gap / 2
                var y = row * height / rows + gap / 2
                var w = Math.max(100, width / inRow - gap)
                var h = Math.max(100, height / rows - gap)
                var item = _windows[key]
                if (item) { item.x = x; item.y = y; item.width = w; item.height = h; item.restoreGeometry = Qt.rect(x,y,w,h) }
                updateChartGeometry(key, x, y, w, h)
                updateChartWindowState(key, false, false, Qt.rect(x,y,w,h))
            }
        })
    }

    function fitAll() {
        for (var key in _windows) {
            var renderer = _windows[key].chartRenderer
            if (renderer && renderer.fitToData) renderer.fitToData()
        }
    }
    function clearDisplays() {
        _pending2D = ({}); _pending3D = ({})
        messageModel.clear()
        for (var key in _windows) {
            var renderer = _windows[key].chartRenderer
            if (renderer && renderer.clearAll) renderer.clearAll()
        }
    }
    function trimDisplays() {
        for (var key in _windows) {
            var renderer = _windows[key].chartRenderer
            if (renderer && renderer.trimToLimit) renderer.trimToLimit()
        }
    }

    function snapshot() {
        var result = {version: 1, charts: [], signals: [], assignments: []}
        for (var i = 0; i < chartModel.count; i++) {
            var chart = chartModel.get(i)
            var window = _windows[chart.chartId]
            var geometry = window && !window.isMaximized && !window.isMinimized ?
                Qt.rect(window.x, window.y, window.width, window.height) :
                window ? window.restoreGeometry : Qt.rect(chart.xPos, chart.yPos, chart.windowWidth, chart.windowHeight)
            var entry = {chartId: chart.chartId, chartTitle: chart.chartTitle, chartType: chart.chartType,
                xPos: geometry.x, yPos: geometry.y, windowWidth: Math.max(100, geometry.width), windowHeight: Math.max(100, geometry.height),
                maximized: window ? window.isMaximized : chart.maximized, minimized: window ? window.isMinimized : chart.minimized}
            if (window && window.chartRenderer && window.chartRenderer.viewSettings) entry.view = window.chartRenderer.viewSettings()
            result.charts.push(entry)
        }
        for (var j = 0; j < signalModel.count; j++) {
            var signal = signalModel.get(j)
            result.signals.push({uniqueId: signal.uniqueId, displayName: signal.displayName,
                color: String(signal.color), interfaceType: signal.interfaceType, dataId: Number(signal.dataId)})
        }
        for (var k = 0; k < chartLineModel.count; k++) {
            var line = chartLineModel.get(k)
            result.assignments.push({uniqueId: line.uniqueId, chartId: line.chartId,
                valueField: line.valueField || null, visible: line.visible})
        }
        return result
    }

    function restoreSnapshot(state) {
        if (!state || Object.keys(state).length === 0)
            state = {version: 1, charts: [], signals: [], assignments: []}
        if (state.version !== 1) return
        state.charts = state.charts || []; state.signals = state.signals || []; state.assignments = state.assignments || []
        chartLineModel.clear(); chartLineModel.modelChanged()
        signalModel.clearAll(); messageModel.clear()
        chartModel.clear(); _windows = ({}); registeredWindowCount = 0
        _pending2D = ({}); _pending3D = ({}); _restoredViews = ({})
        for (var i = 0; i < state.charts.length; i++) {
            var c = state.charts[i]
            if (c.view) _restoredViews[c.chartId] = c.view
            createChart(c.chartType, c.chartTitle, c.chartId, c.xPos, c.yPos, c.windowWidth, c.windowHeight)
            updateChartWindowState(c.chartId, !!c.minimized, !!c.maximized, Qt.rect(c.xPos,c.yPos,c.windowWidth,c.windowHeight))
        }
        for (var j = 0; j < state.signals.length; j++) {
            var signal = state.signals[j]
            addSignal(signal.uniqueId, signal.displayName, signal.color, signal.interfaceType, signal.dataId, {})
            var assigned = []
            for (var k = 0; k < state.assignments.length; k++) {
                var line = state.assignments[k]
                if (line.uniqueId === signal.uniqueId) assigned.push({chartId: line.chartId, valueField: line.valueField})
            }
            setSignalCharts(signal.uniqueId, assigned)
        }
        for (var n = 0; n < state.assignments.length; n++) {
            var assignment = state.assignments[n]
            var curve = chartLineModel.getLineForChart(assignment.uniqueId, assignment.chartId, assignment.valueField)
            if (curve && assignment.visible === false) setLineVisibility(curve.lineKey, false)
        }
        _refreshAvailableCharts()
    }
}
