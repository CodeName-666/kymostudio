import QtQuick 6.4
import Common 1.0

/**
 * MessageModel.qml
 *
 * Registry of known messages (uniqueId) with latest values and timing meta.
 * Filled via Backend signal `message_received(message)`.
 */
ListModel {
    id: messageModel

    signal modelChanged()

    function getMessageIndex(uniqueId) {
        for (var i = 0; i < count; i++) {
            if (get(i).uniqueId === uniqueId) return i
        }
        return -1
    }

    function getMessage(uniqueId) {
        var idx = getMessageIndex(uniqueId)
        return idx === -1 ? null : get(idx)
    }

    function hasMessage(uniqueId) {
        return getMessageIndex(uniqueId) !== -1
    }

    function toggleExpanded(uniqueId) {
        var idx = getMessageIndex(uniqueId)
        if (idx === -1) return false
        setProperty(idx, "expanded", !get(idx).expanded)
        modelChanged()
        return true
    }

    function setExpanded(uniqueId, expanded) {
        var idx = getMessageIndex(uniqueId)
        if (idx === -1) return false
        setProperty(idx, "expanded", !!expanded)
        modelChanged()
        return true
    }

    function addOrUpdateFromBackend(message) {
        if (!message || !message.uniqueId) return false

        var idx = getMessageIndex(message.uniqueId)
        if (idx === -1) {
            append({
                "uniqueId": message.uniqueId,
                "displayName": message.displayName || message.uniqueId,
                "interface": message.interface || "",
                "interfaceType": message.interfaceType || "Unknown",
                "dataId": (message.dataId !== undefined && message.dataId !== null) ? message.dataId : "",
                "x": (message.x !== undefined) ? message.x : null,
                "y": (message.y !== undefined) ? message.y : null,
                "z": (message.z !== undefined) ? message.z : null,
                "timestamp": (message.timestamp !== undefined) ? message.timestamp : null,
                "t": (message.t !== undefined) ? message.t : null,
                "rxTime": (message.rxTime !== undefined && message.rxTime !== null) ? message.rxTime : 0,
                "cycleTime": (message.cycleTime !== undefined) ? message.cycleTime : null,
                "rxCount": (message.rxCount !== undefined && message.rxCount !== null) ? message.rxCount : 0,
                "expanded": false
            })
            modelChanged()
            return true
        }

        // Keep expanded state stable across updates
        var wasExpanded = get(idx).expanded

        if (message.displayName !== undefined) setProperty(idx, "displayName", message.displayName || get(idx).displayName)
        if (message.interface !== undefined) setProperty(idx, "interface", message.interface || "")
        if (message.interfaceType !== undefined) setProperty(idx, "interfaceType", message.interfaceType || "Unknown")
        if (message.dataId !== undefined) setProperty(idx, "dataId", message.dataId)
        if (message.x !== undefined) setProperty(idx, "x", message.x)
        if (message.y !== undefined) setProperty(idx, "y", message.y)
        if (message.z !== undefined) setProperty(idx, "z", message.z)
        if (message.timestamp !== undefined) setProperty(idx, "timestamp", message.timestamp)
        if (message.t !== undefined) setProperty(idx, "t", message.t)
        if (message.rxTime !== undefined && message.rxTime !== null) setProperty(idx, "rxTime", message.rxTime)
        if (message.cycleTime !== undefined) setProperty(idx, "cycleTime", message.cycleTime)
        if (message.rxCount !== undefined && message.rxCount !== null) setProperty(idx, "rxCount", message.rxCount)

        setProperty(idx, "expanded", wasExpanded)
        modelChanged()
        return true
    }

    function removeMessage(uniqueId) {
        var idx = getMessageIndex(uniqueId)
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
