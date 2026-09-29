import QtQuick 6.4
import Common 1.0

/**
 * SignalModel.qml
 *
 * Registry of known signals (uniqueId) independent of chart assignment.
 * Used to keep signals visible even when not assigned to any chart.
 */
ListModel {
    id: signalModel

    signal modelChanged()

    function getSignalIndex(uniqueId) {
        for (var i = 0; i < count; i++) {
            if (get(i).uniqueId === uniqueId) return i
        }
        return -1
    }

    function getSignal(uniqueId) {
        var idx = getSignalIndex(uniqueId)
        return idx === -1 ? null : get(idx)
    }

    function hasSignal(uniqueId) {
        return getSignalIndex(uniqueId) !== -1
    }

    function addOrUpdate(uniqueId, displayName, color, interfaceType, dataId, interfaceSettings) {
        if (!uniqueId || uniqueId === "") return false

        var idx = getSignalIndex(uniqueId)
        if (idx === -1) {
            append({
                "uniqueId": uniqueId,
                "displayName": displayName || uniqueId,
                "color": color || "#2196f3",
                "interfaceType": interfaceType || "Unknown",
                "dataId": (dataId !== undefined && dataId !== null) ? dataId : "",
                "interfaceSettings": interfaceSettings || {}
            })
            modelChanged()
            return true
        }

        if (displayName !== undefined) setProperty(idx, "displayName", displayName)
        if (color !== undefined) setProperty(idx, "color", color)
        if (interfaceType !== undefined) setProperty(idx, "interfaceType", interfaceType)
        if (dataId !== undefined) setProperty(idx, "dataId", dataId)
        if (interfaceSettings !== undefined) setProperty(idx, "interfaceSettings", interfaceSettings)

        modelChanged()
        return true
    }

    function removeSignal(uniqueId) {
        var idx = getSignalIndex(uniqueId)
        if (idx === -1) return false
        remove(idx)
        modelChanged()
        return true
    }

    function clearAll() {
        clear()
        modelChanged()
    }
}

