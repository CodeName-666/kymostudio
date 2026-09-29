import QtQuick 6.4
import Common 1.0
import Backend 1.0

/**
 * Data model for managing chart lines.
 * Each line represents a data source with unique ID, display name, color, and settings.
 */
ListModel {
    id: chartLineModel

    signal modelChanged()

    function buildLineKey(uniqueId, chartId, valueField) {
        var safeChartId = chartId || "main"
        var suffix = (valueField !== undefined && valueField !== null && valueField !== "") ? ("::" + valueField) : ""
        return safeChartId + "::" + uniqueId + suffix
    }

    /**
     * Add a new chart line to the model
     *
     * @param uniqueId - Unique identifier (format: "interface_id", e.g., "Serial_0")
     * @param displayName - User-friendly name for display
     * @param color - Line color (hex string or Qt color)
     * @param interfaceType - Interface type (Serial, MQTT, Telnet, Test)
     * @param dataId - Data ID (0-255) from the protocol
     * @param interfaceSettings - Interface-specific settings object
     * @param seriesRef - Reference to Qt Charts series object
     * @param chartId - ID of the chart this line belongs to (e.g., "main", "test_float_123")
     * @param chartTitle - Title of the chart this line belongs to (e.g., "Main Chart", "Test Chart")
     * @param valueField - Optional mapping field for time-series lines ("x" or "y")
     */
    function addLine(uniqueId, displayName, color, interfaceType, dataId, interfaceSettings, seriesRef, chartId, chartTitle, valueField) {
        var safeChartId = chartId || "main"
        var lineKey = buildLineKey(uniqueId, safeChartId, valueField)

        // Check if this line already exists on this chart
        if (getLineIndexByKey(lineKey) !== -1) {
            Logger.log_warning("ChartLineModel: Line " + uniqueId + " already exists on chart " + safeChartId)
            return false
        }

        append({
            "lineKey": lineKey,
            "uniqueId": uniqueId,
            "displayName": displayName,
            "color": color,
            "interfaceType": interfaceType,
            "dataId": dataId,
            "interfaceSettings": interfaceSettings || {},
            "visible": true,
            "seriesRef": seriesRef || null,
            "chartId": safeChartId,
            "chartTitle": chartTitle || "Main Chart",
            "valueField": valueField !== undefined ? valueField : null
        })

        modelChanged()
        Logger.log_info("ChartLineModel: Added line " + uniqueId + " (" + displayName + ") to chart " + safeChartId)
        return true
    }

    /**
     * Remove a chart line from the model
     *
     * @param lineKey - Unique key of the line instance to remove ("<chartId>::<uniqueId>")
     */
    function removeLine(lineKey) {
        var index = getLineIndexByKey(lineKey)
        if (index === -1) {
            Logger.log_warning("ChartLineModel: Cannot remove - line " + lineKey + " not found")
            return false
        }

        remove(index)
        modelChanged()
        Logger.log_info("ChartLineModel: Removed line " + lineKey)
        return true
    }

    function removeLineForChart(uniqueId, chartId, valueField) {
        return removeLine(buildLineKey(uniqueId, chartId, valueField))
    }

    /**
     * Update properties of an existing chart line
     *
     * @param lineKey - Unique key of the line instance to update
     * @param properties - Object with properties to update (displayName, color, interfaceSettings, etc.)
     */
    function updateLine(lineKey, properties) {
        var index = getLineIndexByKey(lineKey)
        if (index === -1) {
            Logger.log_warning("ChartLineModel: Cannot update - line " + lineKey + " not found")
            return false
        }

        for (var prop in properties) {
            if (properties.hasOwnProperty(prop)) {
                setProperty(index, prop, properties[prop])
            }
        }

        modelChanged()
        Logger.log_debug("ChartLineModel: Updated line " + lineKey)
        return true
    }

    function updateLineForChart(uniqueId, chartId, properties, valueField) {
        return updateLine(buildLineKey(uniqueId, chartId, valueField), properties)
    }

    function updateLinesByUniqueId(uniqueId, properties) {
        var updated = false
        for (var i = 0; i < count; i++) {
            if (get(i).uniqueId !== uniqueId) continue
            for (var prop in properties) {
                if (properties.hasOwnProperty(prop)) {
                    setProperty(i, prop, properties[prop])
                }
            }
            updated = true
        }
        if (updated) modelChanged()
        return updated
    }

    /**
     * Get a chart line by unique ID
     *
     * @param uniqueId - Unique identifier of the signal source
     * @returns Line object or null if not found
     */
    function getLine(uniqueId) {
        var mainLine = getLineForChart(uniqueId, "main")
        if (mainLine) return mainLine
        for (var i = 0; i < count; i++) {
            if (get(i).uniqueId === uniqueId) return get(i)
        }
        return null
    }

    function getLineByKey(lineKey) {
        var index = getLineIndexByKey(lineKey)
        return index === -1 ? null : get(index)
    }

    function getLineForChart(uniqueId, chartId, valueField) {
        var key = buildLineKey(uniqueId, chartId, valueField)
        return getLineByKey(key)
    }

    function hasLineForChart(uniqueId, chartId, valueField) {
        return getLineIndexByKey(buildLineKey(uniqueId, chartId, valueField)) !== -1
    }

    function hasAnyLine(uniqueId) {
        for (var i = 0; i < count; i++) {
            if (get(i).uniqueId === uniqueId) return true
        }
        return false
    }

    /**
     * Get index of a chart line by unique ID
     *
     * @param lineKey - Unique key of the line instance
     * @returns Index in the model or -1 if not found
     */
    function getLineIndexByKey(lineKey) {
        for (var i = 0; i < count; i++) {
            if (get(i).lineKey === lineKey) {
                return i
            }
        }
        return -1
    }

    function getLineIndexForChart(uniqueId, chartId, valueField) {
        return getLineIndexByKey(buildLineKey(uniqueId, chartId, valueField))
    }

    /**
     * Get all chart lines as an array
     *
     * @returns Array of all line objects
     */
    function getAllLines() {
        var lines = []
        for (var i = 0; i < count; i++) {
            lines.push(get(i))
        }
        return lines
    }

    function getAllUniqueIds() {
        var ids = ({})
        for (var i = 0; i < count; i++) {
            ids[get(i).uniqueId] = true
        }
        return Object.keys(ids)
    }

    /**
     * Toggle visibility of a chart line
     *
     * @param lineKey - Unique key of the line instance
     * @param visible - New visibility state (optional, toggles if not provided)
     */
    function toggleVisibility(lineKey, visible) {
        var index = getLineIndexByKey(lineKey)
        if (index === -1) {
            return false
        }

        var line = get(index)
        var newVisibility = visible !== undefined ? visible : !line.visible

        setProperty(index, "visible", newVisibility)

        // Update series visibility if series reference exists
        if (line.seriesRef) {
            line.seriesRef.visible = newVisibility
        }

        modelChanged()
        Logger.log_debug("ChartLineModel: Toggled visibility of " + lineKey + " to " + newVisibility)
        return true
    }

    function toggleVisibilityForChart(uniqueId, chartId, visible, valueField) {
        return toggleVisibility(buildLineKey(uniqueId, chartId, valueField), visible)
    }

    /**
     * Set series reference for a chart line
     *
     * @param lineKey - Unique key of the line instance
     * @param seriesRef - Reference to Qt Charts series object
     */
    function setSeriesRef(lineKey, seriesRef) {
        var index = getLineIndexByKey(lineKey)
        if (index === -1) {
            return false
        }

        setProperty(index, "seriesRef", seriesRef)
        modelChanged()
        Logger.log_debug("ChartLineModel: Set series reference for " + lineKey)
        return true
    }

    /**
     * Clear all chart lines
     */
    function clearAll() {
        Logger.log_info("ChartLineModel: Clearing all lines")
        clear()
        modelChanged()
    }

    /**
     * Get count of visible lines
     *
     * @returns Number of visible lines
     */
    function getVisibleCount() {
        var visibleCount = 0
        for (var i = 0; i < count; i++) {
            if (get(i).visible) {
                visibleCount++
            }
        }
        return visibleCount
    }

    /**
     * Get lines by interface type
     *
     * @param interfaceType - Interface type to filter by
     * @returns Array of line objects matching the interface
     */
    function getLinesByInterface(interfaceType) {
        var lines = []
        for (var i = 0; i < count; i++) {
            var line = get(i)
            if (line.interfaceType === interfaceType) {
                lines.push(line)
            }
        }
        return lines
    }

    /**
     * Get lines by chart ID
     *
     * @param chartId - Chart ID to filter by
     * @returns Array of line objects belonging to the specified chart
     */
    function getLinesByChart(chartId) {
        var lines = []
        for (var i = 0; i < count; i++) {
            var line = get(i)
            if (line.chartId === chartId) {
                lines.push(line)
            }
        }
        return lines
    }

    /**
     * Remove all lines belonging to a specific chart
     *
     * @param chartId - Chart ID to remove lines from
     */
    function removeLinesByChart(chartId) {
        Logger.log_info("ChartLineModel: Removing all lines from chart " + chartId)
        var i = count - 1
        while (i >= 0) {
            if (get(i).chartId === chartId) {
                remove(i)
            }
            i--
        }
        modelChanged()
    }

    function removeLinesByUniqueId(uniqueId) {
        Logger.log_info("ChartLineModel: Removing all lines for signal " + uniqueId)
        var i = count - 1
        while (i >= 0) {
            if (get(i).uniqueId === uniqueId) {
                remove(i)
            }
            i--
        }
        modelChanged()
    }

    function updateChartTitle(chartId, chartTitle) {
        var updated = false
        for (var i = 0; i < count; i++) {
            if (get(i).chartId !== chartId) continue
            setProperty(i, "chartTitle", chartTitle)
            updated = true
        }
        if (updated) modelChanged()
        return updated
    }
}
